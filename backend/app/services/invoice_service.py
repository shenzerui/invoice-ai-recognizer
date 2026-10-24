"""
services/invoice_service.py
===========================
票据历史记录业务 —— 搜索、分页、更新、删除、导出。
所有查询都按 user_id 隔离，确保用户间数据不可见。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from ..models.invoice import Invoice
from ..schemas.invoice import InvoiceUpdate


class InvoiceService:
    """票据 CRUD & 搜索 & 导出服务（user_id 多租户隔离）。"""

    @staticmethod
    async def list_invoices(
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        ticket_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict:
        """列表查询（带分页 + 多条件筛选 + user_id 过滤）。"""
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        conditions = [Invoice.user_id == user_id]
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
                Invoice.tags.like(like),
                Invoice.remark.like(like),
            ))

        where = and_(*conditions)

        count_stmt = select(func.count(Invoice.id)).where(where)
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = select(Invoice).where(where)
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
    async def get_by_id(session: AsyncSession, inv_id: int, user_id: int) -> Invoice | None:
        """按 id + user_id 查询（确保不能越权访问别人的数据）。"""
        result = await session.execute(
            select(Invoice).where(Invoice.id == inv_id, Invoice.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(session: AsyncSession, inv_id: int, user_id: int, data: InvoiceUpdate) -> Invoice | None:
        inv = await InvoiceService.get_by_id(session, inv_id, user_id)
        if not inv:
            return None

        update_fields = data.model_dump(exclude_unset=True)
        if "tags" in update_fields:
            inv.set_tags_list(update_fields.pop("tags") or [])
        for key, value in update_fields.items():
            if hasattr(inv, key) and value is not None:
                setattr(inv, key, value)
        inv.updated_at = datetime.now()

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
    async def delete(session: AsyncSession, inv_id: int, user_id: int) -> bool:
        inv = await InvoiceService.get_by_id(session, inv_id, user_id)
        if not inv:
            return False
        if inv.image_path:
            try:
                from pathlib import Path
                p = Path(inv.image_path)
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        await session.delete(inv)
        await session.commit()
        return True

    @staticmethod
    async def list_all_for_export(
        session: AsyncSession,
        user_id: int,
        ticket_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        """不分页取全部（用于导出）。"""
        result = await InvoiceService.list_invoices(
            session, user_id=user_id, page=1, page_size=10000,
            ticket_type=ticket_type, start_date=start_date, end_date=end_date,
        )
        return result["items"]
