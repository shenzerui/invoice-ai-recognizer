"""
ocr/parser.py
=============
票据解析器 —— 把 OCR 原始 structured 字段统一映射为系统内部 InvoiceCreate 结构。

设计思路：
  - 不同 OCR 服务（百度、LLM、未来的腾讯）返回字段名不一样
  - 不同票据类型（增值税 vs 火车票 vs 定额）关键字段也不一样
  - 这一层做统一转换，下游 DB 和前端都只认 InvoiceCreate，不管上游用了什么 OCR

本轮修复（v2）：
  1. 移除 total_amount 的危险别名 "total" —— 避免 OCR 把"合计"（不含税）误填进来
  2. 新增 _strip_label_prefix() 清洗购销方字段值中的标签残留
  3. 新增 _clean_date() 统一日期格式为 YYYY-MM-DD
  4. 新增 _refine_type_by_codes() 基于代码/号码位数二次判定票种（数电 vs 增值电子）
  5. 发票代码为空但号码 20 位 → 数电票，代码字段明确写"数电票无代码"
  6. 去掉 amount/total_amount 中的"合计"行语义冲突（交由 validator 双校验兜底）

扩展方式：
  - 新增 OCR 服务 → 在 `parse_ocr_result` 里加一个字段别名映射
  - 新增票据类型 → 加一个 `parse_xxx()` 函数处理 type_extra
"""

import re
from typing import Dict, Any, Optional
from ..schemas.invoice import InvoiceCreate
from ..config import TICKET_TYPES


# ====== 字段别名映射表 ======
# 把各种 OCR 可能返回的字段名统一映射到系统内部字段名
# 覆盖：JSON key (LLM)、snake_case (旧百度)、PascalCase (百度 vat_invoice 新格式)
#
# ★ 重要：total_amount 别名里刻意去掉了 "total" —— OCR 很容易把"合计"(不含税) 填进 total
FIELD_ALIASES = {
    # 票据类型
    "ticket_type": [
        "ticket_type", "invoice_type", "invoice_kind", "type",
        "InvoiceType", "InvoiceTypeOrg",
    ],
    # 发票代码
    "invoice_code": [
        "invoice_code", "invoiceCode", "invoice_code_orig",
        "InvoiceCode", "InvoiceCodeConfirm",
    ],
    # 发票号码
    "invoice_number": [
        "invoice_number", "invoiceNumber", "invoice_num",
        "InvoiceNum", "InvoiceNumConfirm",
    ],
    # 开票日期
    "invoice_date": [
        "invoice_date", "invoiceDate", "date",
        "InvoiceDate", "InvoiceDateConfirm",
    ],
    # 金额（不含税）
    "amount": [
        "amount", "amount_without_tax", "amount_without_tax_orig",
        "CommodityAmount",
    ],
    # 税额
    "tax": [
        "tax", "tax_amount", "tax_amount_orig",
        "TotalTax", "CommodityTax",
    ],
    # 价税合计（含税总额）
    # ★ 严禁匹配 "total" —— 容易命中"合计"(不含税)
    "total_amount": [
        "total_amount", "totalAmount", "amount_with_tax",
        "TotalAmount", "AmountInFiguers",
        "价税合计", "合计金额",
    ],
    # 购买方
    "buyer": [
        "buyer", "buyer_name", "buyerName",
        "purchaser", "payer", "PurchaserName",
    ],
    # 销售方
    "seller": [
        "seller", "seller_name", "sellerName",
        "payee", "recipient", "SellerName",
    ],
}


def _pick(d: Dict[str, Any], key: str, default=None) -> Any:
    """从字典中按别名列表取值，取到第一个非空的。"""
    aliases = FIELD_ALIASES.get(key, [key])
    for alias in aliases:
        val = d.get(alias)
        if val not in (None, ""):
            return val
    return default


# ====== 字段清洗工具 ======
def _to_float(val) -> float:
    """
    安全转 float —— OCR 可能返回:
      - "1,234.56"   带千分位
      - "¥1,234.56"  带人民币符号
      - "￥1234.56"  带全角人民币符号
      - " 1234.56 "  带空白
    统一去符号/逗号/空白，保留 2 位小数。
    """
    if val is None or val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").replace("¥", "").replace("￥", "").strip()
            # 有些 OCR 返回 "1234.56元" —— 去掉末尾"元"
            val = val.replace("元", "").strip()
        return round(float(val), 2)
    except (ValueError, TypeError):
        return 0.0


def _to_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


# 清洗购销方字段值中的标签残留
# OCR / LLM 有时会把整段文字吐出来，例如 "购买方名称: 北京某某公司" → 应只取 "北京某某公司"
_LABEL_NOISE_PATTERNS = [
    # 复合前缀：购买方名称、销售方名称、购买方纳税人识别号、统一社会信用代码
    re.compile(r"^(购买方|销售方|购方|销方)?\s*(名称|纳税人识别号|统一社会信用代码|地址|电话|开户行|账号|识别号)\s*[:：,，]\s*"),
    re.compile(r"^(购买方|销售方|购方|销方)\s*[:：]\s*"),
    re.compile(r"^纳税人识别号\s*[:：]\s*"),
    re.compile(r"^统一社会信用代码\s*[:：]\s*"),
    # 尾部类：可能带税号/括号附加
    re.compile(r"\s*[（(].{0,40}[）)]\s*$"),
]


def _strip_label_prefix(raw: str) -> str:
    """
    清洗购销方字段值中的标签文字。
    规则：
      - 去掉前缀 "名称:", "购买方：", "纳税人识别号：" 等
      - 去掉尾部的税号括号 "(91110...)"
      - 多个逗号分隔时只取第一段有效公司名
    """
    s = _to_str(raw)
    if not s:
        return ""
    for pat in _LABEL_NOISE_PATTERNS:
        s = pat.sub("", s)
    # 全角/半角冒号统一处理
    s = s.replace("：", ":").strip()
    # 如果剩下还带 "名称:" 或 "纳税人识别号:" 再循环一次
    for pat in _LABEL_NOISE_PATTERNS:
        s = pat.sub("", s)
    # 多个公司名用"、"或","分隔时取第一个最像公司名的
    if "、" in s:
        parts = [p.strip() for p in s.split("、") if p.strip()]
        for p in parts:
            if "公司" in p or "行" in p or "院" in p or "厂" in p:
                s = p
                break
        else:
            s = parts[0] if parts else s
    return s.strip(" :：,，")


# 日期格式化：统一成 YYYY-MM-DD
def _clean_date(raw) -> str:
    """
    OCR 可能返回:
      - "2024-08-15"        标准
      - "2024/08/15"        斜杠
      - "2024年08月15日"    中文
      - "2024.08.15"        点
      - "20240815"          紧凑
    统一输出 YYYY-MM-DD；无法解析返回空串。
    """
    s = _to_str(raw)
    if not s:
        return ""

    # 去掉可能的时间部分（有些 OCR 带时分秒）
    s = re.sub(r"[T ].*$", "", s)
    s = s.strip()

    # 2024年08月15日 或 2024-08-15 或 2024/08/15 或 2024.08.15
    m = re.match(r"(\d{4})\s*[年\-/\.]\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})\s*日?", s)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"{y}-{int(mo):02d}-{int(d):02d}"

    # 纯 8 位数字 20240815
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return f"{y}-{int(mo):02d}-{int(d):02d}"

    # 6 位数字 240815 (YYMMDD) —— 补全 20 前缀
    m = re.match(r"^(\d{2})(\d{2})(\d{2})$", s)
    if m:
        y, mo, d = "20" + m.group(1), m.group(2), m.group(3)
        return f"{y}-{int(mo):02d}-{int(d):02d}"

    return s  # 实在解析不了保留原样


# ====== 各票据类型特有字段解析 ======
def _parse_vat_extra(raw: Dict[str, Any]) -> Dict[str, Any]:
    """增值税专/普/电子 —— 特有字段：税率、商品明细等。"""
    extra = {}
    for k in ["tax_rate", "taxRate", "commodity", "commodity_name", "remark"]:
        if raw.get(k) not in (None, ""):
            # 统一键名
            key = "税率" if "rate" in k.lower() else "商品明细" if "commodity" in k.lower() else "备注"
            extra[key] = raw[k]
    if raw.get("extra") and isinstance(raw["extra"], dict):
        extra.update(raw["extra"])
    return extra


def _parse_fixed_extra(raw: Dict[str, Any]) -> Dict[str, Any]:
    """定额发票 —— 特有字段：票面金额、收款单位。"""
    extra = {}
    if raw.get("face_amount"):
        extra["票面金额"] = raw["face_amount"]
    if raw.get("total_amount"):
        extra["票面金额"] = raw["total_amount"]
    if raw.get("seller"):
        extra["收款单位"] = raw["seller"]
    if raw.get("extra") and isinstance(raw["extra"], dict):
        extra.update(raw["extra"])
    return extra


def _parse_train_extra(raw: Dict[str, Any]) -> Dict[str, Any]:
    """火车票 —— 特有字段：起止站、车次、席别。"""
    extra = {}
    mapping = [
        ("starting_station", "起始站"), ("from", "起始站"), ("departure", "起始站"),
        ("ending_station", "到达站"), ("to", "到达站"), ("arrival", "到达站"),
        ("train_number", "车次"), ("trainNo", "车次"), ("车次", "车次"),
        ("seat_type", "席别"), ("seatType", "席别"), ("席别", "席别"),
        ("passenger_name", "乘客姓名"),
    ]
    for src_key, label in mapping:
        if raw.get(src_key) not in (None, "") and label not in extra:
            extra[label] = raw[src_key]
    if raw.get("extra") and isinstance(raw["extra"], dict):
        extra.update(raw["extra"])
    return extra


def _parse_bus_extra(raw: Dict[str, Any]) -> Dict[str, Any]:
    """汽车票 —— 特有字段：起止站、班次。"""
    extra = {}
    for k in ["starting_station", "startingStation", "from", "起始站"]:
        if raw.get(k):
            extra["起始站"] = raw[k]
            break
    for k in ["ending_station", "endingStation", "to", "到达站"]:
        if raw.get(k):
            extra["到达站"] = raw[k]
            break
    for k in ["shift", "班次", "bus_no"]:
        if raw.get(k):
            extra["班次"] = raw[k]
            break
    if raw.get("extra") and isinstance(raw["extra"], dict):
        extra.update(raw["extra"])
    return extra


def _parse_toll_extra(raw: Dict[str, Any]) -> Dict[str, Any]:
    """通行费票据 —— 特有字段：入口、出口。"""
    extra = {}
    for k in ["entrance", "入口", "entry"]:
        if raw.get(k):
            extra["入口"] = raw[k]
            break
    for k in ["exit", "出口", "outlet"]:
        if raw.get(k):
            extra["出口"] = raw[k]
            break
    if raw.get("extra") and isinstance(raw["extra"], dict):
        extra.update(raw["extra"])
    return extra


# 票据类型 → 特有字段解析函数
_TYPE_EXTRA_PARSERS = {
    "vat_special": _parse_vat_extra,
    "vat_normal": _parse_vat_extra,
    "vat_electronic": _parse_vat_extra,
    "digital_special": _parse_vat_extra,
    "digital_normal": _parse_vat_extra,
    "fixed": _parse_fixed_extra,
    "train": _parse_train_extra,
    "bus": _parse_bus_extra,
    "toll": _parse_toll_extra,
}


# 类型别名映射（不同 OCR 可能返回不同的类型字符串）
_TYPE_ALIAS_MAP = {
    "elevat_special":    "vat_special",
    "elevat_normal":     "vat_electronic",
    "elevat":            "vat_electronic",
    "vat_invoice_special": "vat_special",
    "vat_invoice_normal":  "vat_normal",
    "ele_vat":           "vat_electronic",
    # 数电票
    "digital_special":   "digital_special",
    "digital_normal":    "digital_normal",
    "digital":           "digital_normal",
    "数电专用":            "digital_special",
    "数电普通":            "digital_normal",
}


def _normalize_ticket_type(raw_type: str) -> str:
    """把各种票据类型字符串统一映射到内部枚举值。"""
    raw_type = _to_str(raw_type).lower()
    if raw_type in TICKET_TYPES:
        return raw_type
    if raw_type in _TYPE_ALIAS_MAP:
        return _TYPE_ALIAS_MAP[raw_type]
    # 关键词兜底
    if "digital" in raw_type or "数电" in raw_type or "全电" in raw_type:
        if "专" in raw_type or "special" in raw_type:
            return "digital_special"
        return "digital_normal"
    if "special" in raw_type or "专" in raw_type:
        return "vat_special"
    if "electronic" in raw_type or "电子" in raw_type or "elevat" in raw_type:
        return "vat_electronic"
    if "fixed" in raw_type or "定额" in raw_type:
        return "fixed"
    if "train" in raw_type or "火车" in raw_type or "高铁" in raw_type:
        return "train"
    if "bus" in raw_type or "汽车" in raw_type:
        return "bus"
    if "toll" in raw_type or "通行" in raw_type or "过路费" in raw_type:
        return "toll"
    if "normal" in raw_type or "普" in raw_type:
        return "vat_normal"
    return "unknown"


# ====== 类型精化：基于代码/号码位数二次判定 ======
def _refine_type_by_codes(
    ticket_type: str,
    invoice_code: str,
    invoice_number: str,
    raw_type_hint: str = "",
) -> tuple[str, str]:
    """
    根据发票代码 / 号码的位数规律二次修正票种：
      1. 发票号码 20 位 + 无发票代码/代码空 → 数电票（digital_special / digital_normal）
      2. 发票代码 12 位 + 发票号码 8 位 → 增值税电子普通发票（vat_electronic）

    返回: (final_type, final_code)
    """
    code = invoice_code
    number = invoice_number

    # 数电票：号码 20 位，无发票代码
    if len(number) == 20 and (not code or code in ("-", "无", "none", "null", "n/a", "")):
        # 从 raw_type_hint 或已有 ticket_type 判断专/普
        hint_lower = _to_str(raw_type_hint).lower()
        existing = _to_str(ticket_type).lower()
        if "专" in hint_lower or "special" in hint_lower or existing == "vat_special":
            return "digital_special", "数电票无代码"
        return "digital_normal", "数电票无代码"

    # 增值税电子普通发票：代码 12 位 + 号码 8 位
    if len(code) == 12 and len(number) == 8 and ticket_type in ("vat_normal", "unknown"):
        return "vat_electronic", code

    # 没命中特殊规则，保持原判定
    return ticket_type, code


# ====== 主入口 ======
def parse_ocr_result(ocr_result: Dict[str, Any], filename: str = "") -> InvoiceCreate:
    """
    把 OCR 返回结果解析为 InvoiceCreate。

    参数:
        ocr_result: OCRAdapter.recognize() 的返回值
        filename:   原始图片文件名（用于调试）
    返回:
        InvoiceCreate 实例
    """
    structured = ocr_result.get("structured") or ocr_result.get("raw") or {}
    structured = dict(structured)  # copy

    # ----- 原始值 -----
    raw_invoice_code = _to_str(_pick(structured, "invoice_code"))
    raw_invoice_number = _to_str(_pick(structured, "invoice_number"))
    raw_buyer = _to_str(_pick(structured, "buyer"))
    raw_seller = _to_str(_pick(structured, "seller"))
    raw_date = _to_str(_pick(structured, "invoice_date"))
    raw_amount = _pick(structured, "amount")
    raw_tax = _pick(structured, "tax")
    raw_total = _pick(structured, "total_amount")

    # ----- 1) 初步类型判定 -----
    raw_type = _pick(structured, "ticket_type", "unknown")
    ticket_type = _normalize_ticket_type(_to_str(raw_type))

    # 特判：百度老版直接返回中文类型字符串
    raw_bn_type = structured.get("InvoiceType") or structured.get("InvoiceTypeOrg") or ""
    if "专用" in str(raw_bn_type):
        ticket_type = "vat_special"
    elif "电子" in str(raw_bn_type) and "普通" in str(raw_bn_type):
        ticket_type = "vat_electronic"
    elif "电子" in str(raw_bn_type) and "专用" in str(raw_bn_type):
        ticket_type = "digital_special"  # 电子专用 = 数电专用
    elif "电子" in str(raw_bn_type):
        ticket_type = "vat_electronic"
    elif "普通" in str(raw_bn_type):
        ticket_type = "vat_normal"

    # ----- 2) 类型精化（基于代码/号码位数） -----
    ticket_type, final_invoice_code = _refine_type_by_codes(
        ticket_type, raw_invoice_code, raw_invoice_number, str(raw_type)
    )

    # ----- 3) 字段清洗 -----
    final_buyer = _strip_label_prefix(raw_buyer)
    final_seller = _strip_label_prefix(raw_seller)
    final_date = _clean_date(raw_date)
    final_amount = _to_float(raw_amount)
    final_tax = _to_float(raw_tax)
    final_total = _to_float(raw_total)

    # ----- 4) 价税合计兜底修正 -----
    # 场景 A: OCR 把"合计"(不含税) 误填进了 total_amount
    #   此时 amount ≈ total, tax 有值，但 amount + tax != total
    #   → 用 amount + tax 重新算 total（前提是 tax 和 amount 都有值且合理）
    # 场景 B: amount 缺失（百度 vat_invoice 不给不含税）
    #   → 用 total - tax 或 total（免税/零税率）兜底
    #
    # 注意：这里不做最终校验——最终校验交给 validator 走双校验 + 明细表比对
    if final_total > 0 and final_amount > 0 and final_tax > 0:
        # OCR 返回了三个值，检查是否 amount + tax ≈ total
        # 如果 total 明显小于 amount + tax（> 0.02 差异），大概率 total 是"合计"(不含税) 被误填
        expected = round(final_amount + final_tax, 2)
        diff = abs(expected - final_total)
        if diff > 0.02 and final_total < expected:
            # total 偏小 → 用 expected 覆盖（更可能是价税合计的正确值）
            final_total = expected
    elif final_amount == 0 and final_total > 0:
        if final_tax > 0:
            final_amount = round(final_total - final_tax, 2)
        else:
            # 免税 / 零税率 / 火车票等
            final_amount = round(final_total, 2)
    elif final_tax == 0 and final_total > 0 and final_amount > 0:
        computed_tax = round(final_total - final_amount, 2)
        if computed_tax >= 0:
            final_tax = computed_tax

    # ----- 5) 组装 InvoiceCreate -----
    data = InvoiceCreate(
        ticket_type=ticket_type,
        invoice_code=final_invoice_code,
        invoice_number=raw_invoice_number,
        invoice_date=final_date,
        buyer=final_buyer,
        seller=final_seller,
        amount=final_amount,
        tax=final_tax,
        total_amount=final_total,
    )

    # ----- 6) 特有字段 -----
    extra_parser = _TYPE_EXTRA_PARSERS.get(ticket_type)
    if extra_parser:
        data.type_extra = extra_parser(structured)
    else:
        data.type_extra = structured.get("extra", {}) if isinstance(structured.get("extra"), dict) else {}

    return data
