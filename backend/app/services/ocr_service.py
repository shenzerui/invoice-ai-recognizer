"""
services/ocr_service.py
=======================
OCR 业务服务 —— 协调「图片上传 → OCR 识别 → 字段解析 → 金额校验 → 重复检测 → 入库」整条链路。
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE
from ..ocr import get_adapter, parse_ocr_result
from ..schemas.invoice import InvoiceCreate, BatchUploadResult
from ..utils.validator import validate_amount
from ..models.invoice import Invoice


class OCRService:
    """OCR 识别 & 票据入库服务。"""

    # ---------- 公开 ----------

    @staticmethod
    async def process_single(
        image_bytes: bytes,
        original_filename: str,
        session: AsyncSession,
    ) -> Tuple[InvoiceCreate, BatchUploadResult]:
        """
        处理单张图片 —— 完整链路。

        返回:
            (invoice_create, batch_result)
            invoice_create: 可以直接入库的模型数据
            batch_result:   处理结果状态（供前端展示）
        """
        result = BatchUploadResult(filename=original_filename, success=False)

        # 1) 基本校验
        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            result.message = f"不支持的文件类型: {ext}"
            return InvoiceCreate(), result
        if len(image_bytes) > MAX_UPLOAD_SIZE:
            result.message = f"文件过大（> {MAX_UPLOAD_SIZE // 1024 // 1024}MB）"
            return InvoiceCreate(), result

        try:
            # 2) 调用 OCR 适配器
            adapter = get_adapter()
            ocr_raw = await adapter.recognize(image_bytes, original_filename)

            # 3) 解析字段
            invoice_data = parse_ocr_result(ocr_raw, original_filename)

            # 4) 保存图片到本地
            saved_path, saved_filename = OCRService._save_image(image_bytes, ext)
            invoice_data.image_path = saved_path
            invoice_data.image_filename = saved_filename

            # 5) 金额校验
            validation = validate_amount(invoice_data.amount, invoice_data.tax, invoice_data.total_amount)
            invoice_data.validation_passed = validation.passed
            invoice_data.validation_message = validation.message

            # 6) 重复检测（代码 + 号码）
            duplicate_id = await OCRService._check_duplicate(session, invoice_data.invoice_code, invoice_data.invoice_number)
            result.is_duplicate = duplicate_id is not None
            if result.is_duplicate:
                result.message = f"该发票已存在（ID={duplicate_id}），跳过保存"

            # 7) 组装成功结果
            result.success = True
            result.validation_passed = validation.passed
            result.message = "识别成功" if validation.passed else f"识别成功，但金额校验异常：{validation.message}"

            return invoice_data, result

        except Exception as e:
            result.message = f"识别失败: {e}"
            return InvoiceCreate(), result

    @staticmethod
    async def save_invoice(
        session: AsyncSession,
        data: InvoiceCreate,
    ) -> Invoice:
        """将 InvoiceCreate 持久化到数据库。"""
        inv = Invoice(
            ticket_type=data.ticket_type,
            invoice_code=data.invoice_code,
            invoice_number=data.invoice_number,
            amount=data.amount,
            tax=data.tax,
            total_amount=data.total_amount,
            invoice_date=data.invoice_date,
            buyer=data.buyer,
            seller=data.seller,
            type_extra=data.type_extra,
            image_path=data.image_path,
            image_filename=data.image_filename,
            validation_passed=data.validation_passed,
            validation_message=data.validation_message,
        )
        session.add(inv)
        await session.commit()
        await session.refresh(inv)
        return inv

    # ---------- 内部 ----------

    @staticmethod
    def _save_image(image_bytes: bytes, ext: str) -> Tuple[str, str]:
        """保存图片到 uploads 目录，返回（相对路径, 文件名）。"""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = UPLOAD_DIR / unique_name
        save_path.write_bytes(image_bytes)
        return str(save_path), unique_name

    @staticmethod
    async def _check_duplicate(
        session: AsyncSession,
        invoice_code: str,
        invoice_number: str,
    ) -> int | None:
        """用 (代码 + 号码) 查是否已存在，存在返回记录 ID。"""
        if not invoice_code and not invoice_number:
            return None  # 都没识别到，无法判断重复
        stmt = select(Invoice).where(
            Invoice.invoice_code == invoice_code,
            Invoice.invoice_number == invoice_number,
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        return row.id if row else None
