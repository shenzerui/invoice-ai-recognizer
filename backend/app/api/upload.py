"""
api/upload.py
=============
票据上传识别接口 —— 支持单张、批量。
"""

from typing import List
from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.ocr_service import OCRService
from ..schemas.invoice import BatchUploadResult, InvoiceCreate
from ..utils.settings_manager import SettingsManager

router = APIRouter()


@router.post("/single", summary="单张图片上传识别")
async def upload_single(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    """上传一张票据图片，返回识别结果 + 校验信息 + 是否重复。"""
    bytes_data = await file.read()
    invoice_data, result = await OCRService.process_single(bytes_data, file.filename or "", session)

    payload = {
        **result.model_dump(),
        "invoice_data": invoice_data.model_dump() if result.success else None,
    }

    # 非重复且成功 → 自动入库
    if result.success and not result.is_duplicate:
        inv = await OCRService.save_invoice(session, invoice_data)
        payload["invoice_id"] = inv.id
        payload["message"] = result.message + "，已入库"

    return payload


@router.post("/batch", summary="批量图片上传识别")
async def upload_batch(
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
):
    """批量上传 —— 每张独立处理，返回各自状态。"""
    results = []
    for f in files:
        bytes_data = await f.read()
        invoice_data, result = await OCRService.process_single(bytes_data, f.filename or "", session)

        item = result.model_dump()

        if result.success and not result.is_duplicate:
            try:
                inv = await OCRService.save_invoice(session, invoice_data)
                item["invoice_id"] = inv.id
            except Exception as e:
                # 入库异常（例如并发唯一冲突）不阻塞后续处理
                item["success"] = False
                item["message"] = f"识别成功但入库失败: {e}"

        results.append(item)

    success_count = sum(1 for r in results if r["success"] and not r["is_duplicate"])
    dup_count = sum(1 for r in results if r["is_duplicate"])
    fail_count = sum(1 for r in results if not r["success"])

    return {
        "summary": {
            "total": len(files),
            "saved": success_count,
            "duplicates": dup_count,
            "failed": fail_count,
        },
        "results": results,
    }
