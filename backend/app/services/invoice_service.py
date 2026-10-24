"""
services/invoice_service.py
===========================
票据历史记录业务 —— 搜索、分页、更新、删除、导出。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from ..models.invoice import Invoice
from ..schemas.invoice import InvoiceUpdate


class InvoiceService:
    """票据 CRUD & 搜索 & 导出服务。"""

    @staticmethod
    async def list_invoices(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        ticket_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict:
        """
        列表查询（带分页 + 多条件筛选）。

        参数:
            ticket_type: 票据类型枚举值
            start_date / end_date: 开票日期范围（字符串格式，如 "2024-01-01"）
            keyword: 模糊搜索关键词（号码 / 代码 / 购买方 / 销售方）
        """
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        conditions = []
        if ticket_type:
            conditions.append(Invoice.ticket_type == ticket_type)
        if start_date:
            conditions.append(Invoice.invoice_date >= start_date)
        if end_date:
            conditions.append(Invoice.invoice_date <= end_date)
        if keyword:
            like = f"%{keyword}%"
            conditions.append(or_(
                Invoice.invoice_number.like(like),
                Invoice.invoice_code.like(like),
                Invoice.buyer.like(like),
                Invoice.seller.like(like),
                Invoice.seller.like(like),
                Invoice.tags.like(like),
                Invoice.remark.like(like),
            ))

        where = and_(*conditions) if conditions else None

        # 总数
        count_stmt = select(func.count(Invoice.id))
        if where:
            count_stmt = count_stmt.where(where)
        total = (await session.execute(count_stmt)).scalar_one()

        # 数据
        stmt = select(Invoice)
        if where:
            stmt = stmt.where(where)
        stmt = stmt.order_by(desc(Invoice.created_at)).offset((page - 1) * page_size).limit(page_size)
        rows = (await session.execute(stmt)).scalars().all()

        items = [r.to_dict() for r in rows]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    @staticmethod
    async def get_by_id(session: AsyncSession, inv_id: int) -> Invoice | None:
        return await session.get(Invoice, inv_id)

    @staticmethod
    async def update(session: AsyncSession, inv_id: int, data: InvoiceUpdate) -> Invoice | None:
        inv = await session.get(Invoice, inv_id)
        if not inv:
            return None

        update_fields = data.model_dump(exclude_unset=True)

        # 标签特殊处理
        if "tags" in update_fields:
            inv.set_tags_list(update_fields.pop("tags") or [])

        # 普通字段直接覆盖
        for key, value in update_fields.items():
            if hasattr(inv, key) and value is not None:
                setattr(inv, key, value)

        inv.updated_at = datetime.now()

        # 如果金额相关字段被修改，重新校验
        if any(k in update_fields for k in ["amount", "tax", "total_amount"]):
            from ..utils.validator import validate_amount
            v = validate_amount(inv.amount, inv.tax, inv.total_amount)
            inv.validation_passed = v.passed
            inv.validation_message = v.message

        session.add(inv)
        await session.commit()
        await session.refresh(inv)
        return inv

    @staticmethod
    async def delete(session: AsyncSession, inv_id: int) -> bool:
        inv = await session.get(Invoice, inv_id)
        if not inv:
            return False
        # 同时删除本地图片文件
        if inv.image_path:
            try:
                from pathlib import Path
                p = Path(inv.image_path)
                if p.exists():
                    p.unlink()
            except Exception:
                pass  # 图片删不掉不要阻塞数据库删除
        await session.delete(inv)
        await session.commit()
        return True

    @staticmethod
    async def list_all_for_export(
        session: AsyncSession,
        ticket_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        """不分页取全部（用于导出）。"""
        result = await InvoiceService.list_invoices(
            session, page=1, page_size=10000,
            ticket_type=ticket_type, start_date=start_date, end_date=end_date,
        )
        return result["items"]
