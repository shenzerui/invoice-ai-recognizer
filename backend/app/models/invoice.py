"""
models/invoice.py
=================
票据（发票）ORM 模型。

设计思路：
  - 所有票据类型共用一张表 `invoices`，避免多表 JOIN 的复杂性
  - 公共字段（票据代码、号码、金额、税额、价税合计、开票日期等）用独立列
  - 各类型特有字段（如火车票的席别、定额发票的票面金额）统一放入 `type_extra` JSON 列
  - 这样新增票据类型时，只需在解析层扩展，无需改数据库结构 —— 非常适合答辩讲解
"""

from datetime import datetime
from sqlalchemy import String, Float, Date, DateTime, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.sqlite import JSON

from ..database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    # ====== 主键与基础信息 ======
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 所属用户（多租户隔离）
    user_id: Mapped[int] = mapped_column(default=0, index=True)
    # 票据类型枚举值，参见 config.TICKET_TYPES
    ticket_type: Mapped[str] = mapped_column(String(32), index=True, default="unknown")

    # ====== 标识字段（用于重复检测） ======
    invoice_code: Mapped[str] = mapped_column(String(64), default="")    # 发票代码
    invoice_number: Mapped[str] = mapped_column(String(64), default="", index=True)  # 发票号码

    # ====== 金额字段 ======
    amount: Mapped[float] = mapped_column(Float, default=0.0)      # 金额（不含税）
    tax: Mapped[float] = mapped_column(Float, default=0.0)         # 税额
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)  # 价税合计

    # ====== 日期与主体 ======
    invoice_date: Mapped[str] = mapped_column(String(32), default="")     # 开票日期（存字符串方便搜索，原始格式可能多样）
    buyer: Mapped[str] = mapped_column(String(255), default="")           # 购买方 / 付款方
    seller: Mapped[str] = mapped_column(String(255), default="")          # 销售方 / 收款方

    # ====== 扩展字段（各票据类型特有字段） ======
    # 用 JSON 存储不同票据类型的特有字段，解析层按类型填充
    type_extra: Mapped[dict] = mapped_column(JSON, default=dict)

    # ====== 图片存储 ======
    image_path: Mapped[str] = mapped_column(String(512), default="")     # 本地保存的图片路径
    image_filename: Mapped[str] = mapped_column(String(255), default="")  # 原始文件名

    # ====== 校验与用户标注 ======
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=True)   # 金额校验是否通过
    validation_message: Mapped[str] = mapped_column(Text, default="")        # 校验异常提示

    tags: Mapped[str] = mapped_column(Text, default="")      # 标签，逗号分隔存储
    remark: Mapped[str] = mapped_column(Text, default="")    # 备注

    # ====== 时间戳 ======
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ====== 索引 ======
    __table_args__ = (
        # (发票代码 + 发票号码) 联合唯一索引 —— 用于重复报销检测
        Index("ix_invoice_code_number", "invoice_code", "invoice_number", unique=True),
    )

    # ----- 便捷方法 -----
    def get_tags_list(self) -> list:
        """把逗号分隔的 tags 字符串解析为列表。"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def set_tags_list(self, tags: list):
        """把列表转为逗号分隔字符串存储。"""
        self.tags = ",".join(tags) if tags else ""

    def to_dict(self) -> dict:
        """序列化为前端友好的字典。"""
        return {
            "id": self.id,
            "ticket_type": self.ticket_type,
            "ticket_type_label": self._type_label(),
            "invoice_code": self.invoice_code,
            "invoice_number": self.invoice_number,
            "amount": self.amount,
            "tax": self.tax,
            "total_amount": self.total_amount,
            "invoice_date": self.invoice_date,
            "buyer": self.buyer,
            "seller": self.seller,
            "type_extra": self.type_extra or {},
            "image_path": self.image_path,
            "image_filename": self.image_filename,
            "validation_passed": self.validation_passed,
            "validation_message": self.validation_message,
            "tags": self.get_tags_list(),
            "remark": self.remark,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }

    def _type_label(self) -> str:
        from ..config import TICKET_TYPES
        return TICKET_TYPES.get(self.ticket_type, "未知")
