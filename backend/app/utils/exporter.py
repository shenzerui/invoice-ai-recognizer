"""
utils/exporter.py
=================
导出工具：Excel（openpyxl）和原生 JSON。
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from ..config import TICKET_TYPES


def export_to_json(invoices: List[Dict[str, Any]]) -> str:
    """
    导出为 JSON —— 返回临时文件路径，由 FastAPI 的 FileResponse 提供下载。
    """
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(invoices, tmp, ensure_ascii=False, indent=2)
    tmp.close()
    return tmp.name


def export_to_excel(invoices: List[Dict[str, Any]]) -> str:
    """
    导出为 Excel —— 返回临时文件路径。
    金额校验不通过的行，价税合计单元格标红。
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "票据记录"

    # ====== 表头 ======
    headers = [
        "ID", "票据类型", "发票代码", "发票号码", "开票日期",
        "购买方", "销售方", "金额(不含税)", "税额", "价税合计",
        "校验状态", "标签", "备注", "创建时间",
    ]
    ws.append(headers)

    # 表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4472C4")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # ====== 数据行 ======
    red_fill = PatternFill("solid", fgColor="FFC7CE")
    red_font = Font(color="9C0006")

    for inv in invoices:
        row = [
            inv.get("id", ""),
            inv.get("ticket_type_label", inv.get("ticket_type", "")),
            inv.get("invoice_code", ""),
            inv.get("invoice_number", ""),
            inv.get("invoice_date", ""),
            inv.get("buyer", ""),
            inv.get("seller", ""),
            inv.get("amount", 0),
            inv.get("tax", 0),
            inv.get("total_amount", 0),
            "通过" if inv.get("validation_passed") else "异常",
            ",".join(inv.get("tags", [])) if isinstance(inv.get("tags"), list) else inv.get("tags", ""),
            inv.get("remark", ""),
            inv.get("created_at", ""),
        ]
        ws.append(row)

        # 校验异常 → 整行标红（第 10 列 = 价税合计）
        row_index = ws.max_row
        if not inv.get("validation_passed", True):
            for col_idx in range(1, len(headers) + 1):
                ws.cell(row=row_index, column=col_idx).fill = red_fill
                ws.cell(row=row_index, column=col_idx).font = red_font

    # ====== 列宽自适应 ======
    column_widths = [6, 14, 20, 18, 14, 24, 24, 12, 10, 14, 10, 18, 30, 20]
    for i, w in enumerate(column_widths, start=1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "A" + chr(64 + i - 26)].width = w

    # 保存到临时文件
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp_path = tmp.name
    tmp.close()
    wb.save(tmp_path)
    return tmp_path
