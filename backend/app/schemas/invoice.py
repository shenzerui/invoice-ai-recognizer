"""
schemas/invoice.py
==================
票据相关的 Pydantic 请求/响应模型。
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class InvoiceBase(BaseModel):
    """票据基础字段 —— OCR 解析层返回的就是这个结构。"""
    ticket_type: str = "unknown"
    invoice_code: str = ""
    invoice_number: str = ""
    amount: float = 0.0
    tax: float = 0.0
    total_amount: float = 0.0
    invoice_date: str = ""
    buyer: str = ""
    seller: str = ""
    type_extra: Dict[str, Any] = Field(default_factory=dict)


class InvoiceCreate(InvoiceBase):
    """创建票据记录（后端内部用，包含图片路径和金额校验结果）。"""
    image_path: str = ""
    image_filename: str = ""
    validation_passed: bool = True
    validation_message: str = ""


class InvoiceUpdate(BaseModel):
    """更新票据 —— 用户可修改标签、备注，或手动修正 OCR 识别结果。"""
    ticket_type: Optional[str] = None
    amount: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None
    invoice_date: Optional[str] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    tags: Optional[List[str]] = None
    remark: Optional[str] = None
    type_extra: Optional[Dict[str, Any]] = None


class ValidationInfo(BaseModel):
    """金额校验结果。"""
    passed: bool
    message: str


class InvoiceResponse(InvoiceBase):
    """单条票据响应（包含数据库 ID、时间戳等）。"""
    id: int
    ticket_type_label: str = ""
    image_path: str = ""
    image_filename: str = ""
    validation_passed: bool = True
    validation_message: str = ""
    tags: List[str] = Field(default_factory=list)
    remark: str = ""
    created_at: str = ""

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """票据列表响应（带分页）。"""
    total: int
    page: int
    page_size: int
    items: List[InvoiceResponse]


class BatchUploadResult(BaseModel):
    """批量上传结果 —— 前端展示每张图片的处理情况。"""
    filename: str
    success: bool
    message: str = ""
    invoice_id: Optional[int] = None
    is_duplicate: bool = False
    validation_passed: bool = True
