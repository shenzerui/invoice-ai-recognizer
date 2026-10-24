"""
api/invoices.py
===============
票据历史记录 —— 列表、详情、更新、删除、导出、图片访问。
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.invoice_service import InvoiceService
from ..schemas.invoice import InvoiceUpdate, InvoiceListResponse, InvoiceResponse
from ..config import UPLOAD_DIR

router = APIRouter()


@router.get("", response_model=InvoiceListResponse, summary="票据列表（分页 + 多条件筛选）")
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ticket_type: Optional[str] = Query(None, description="票据类型枚举值"),
    start_date: Optional[str] = Query(None, description="开票日期起始 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="开票日期结束 YYYY-MM-DD"),
    keyword: Optional[str] = Query(None, description="模糊搜索（号码/代码/购买方/销售方/标签/备注）"),
    session: AsyncSession = Depends(get_db),
):
    data = await InvoiceService.list_invoices(
        session, page=page, page_size=page_size,
        ticket_type=ticket_type, start_date=start_date, end_date=end_date, keyword=keyword,
    )
    # 把 dict 列表转回 Pydantic 模型
    return InvoiceListResponse(
        total=data["total"], page=data["page"], page_size=data["page_size"],
        items=[InvoiceResponse(**it) for it in data["items"]],
    )


@router.get("/types", summary="获取支持的票据类型枚举")
async def list_types():
    from ..config import TICKET_TYPES
    return [{"value": k, "label": v} for k, v in TICKET_TYPES.items()]


@router.get("/{inv_id}", response_model=InvoiceResponse, summary="单条票据详情")
async def get_invoice(inv_id: int, session: AsyncSession = Depends(get_db)):
    inv = await InvoiceService.get_by_id(session, inv_id)
    if not inv:
        raise HTTPException(404, "票据不存在")
    return InvoiceResponse(**inv.to_dict())


@router.put("/{inv_id}", response_model=InvoiceResponse, summary="更新票据（标签、备注、手动修正金额等）")
async def update_invoice(inv_id: int, data: InvoiceUpdate, session: AsyncSession = Depends(get_db)):
    inv = await InvoiceService.update(session, inv_id, data)
    if not inv:
        raise HTTPException(404, "票据不存在")
    return InvoiceResponse(**inv.to_dict())


@router.delete("/{inv_id}", summary="删除票据记录（连同本地图片）")
async def delete_invoice(inv_id: int, session: AsyncSession = Depends(get_db)):
    ok = await InvoiceService.delete(session, inv_id)
    if not ok:
        raise HTTPException(404, "票据不存在")
    return {"success": True}


@router.get("/{inv_id}/image", summary="获取票据图片文件")
async def get_invoice_image(inv_id: int, session: AsyncSession = Depends(get_db)):
    inv = await InvoiceService.get_by_id(session, inv_id)
    if not inv or not inv.image_path:
        raise HTTPException(404, "图片不存在")
    p = Path(inv.image_path)
    if not p.exists():
        raise HTTPException(404, "图片文件已丢失")
    media_type = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(str(p), media_type=media_type, filename=inv.image_filename)


@router.get("/export/excel", summary="导出 Excel")
async def export_excel(
    ticket_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    from ..utils.exporter import export_to_excel
    items = await InvoiceService.list_all_for_export(session, ticket_type, start_date, end_date)
    if not items:
        raise HTTPException(400, "没有可导出的数据")
    tmp_path = export_to_excel(items)
    return FileResponse(tmp_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename="invoices.xlsx")


@router.get("/export/json", summary="导出 JSON")
async def export_json(
    ticket_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    import json as _json
    items = await InvoiceService.list_all_for_export(session, ticket_type, start_date, end_date)
    if not items:
        raise HTTPException(400, "没有可导出的数据")
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    _json.dump(items, tmp, ensure_ascii=False, indent=2)
    tmp.close()
    return FileResponse(tmp.name, media_type="application/json", filename="invoices.json")
