"""
ocr/baidu_adapter.py
====================
百度 OCR 适配器 —— 调用百度智能云增值税发票识别接口。

百度 OCR 返回字段示例（vat_invoice）：
{
    "invoice_type": "elevat_special",
    "invoice_code": "...",
    "invoice_number": "...",
    "invoice_date": "2024-08-15",
    "buyer_name": "...",
    "seller_name": "...",
    "amount_without_tax": 1234.56,
    "tax_amount": 156.23,
    "total_amount": 1390.79,
    ...
}
"""

import base64
import httpx
import requests
from typing import Dict, Any
from .adapter import OCRAdapter
from ..config import DEFAULT_BAIDU_OCR_URL, DEFAULT_BAIDU_TOKEN_URL


class BaiduOCRAdapter(OCRAdapter):
    """百度 OCR —— 增值税发票专用接口。"""

    def __init__(self):
        settings = self._load_settings()
        self.api_key = settings["baidu_api_key"]
        self.secret_key = settings["baidu_secret_key"]
        self._token: str = ""

    # ---------- 内部 ----------
    @staticmethod
    def _load_settings() -> Dict[str, Any]:
        from ..utils.settings_manager import SettingsManager
        return SettingsManager.load()

    def _get_access_token(self) -> str:
        """获取百度 OCR access_token（有缓存）。"""
        if self._token:
            return self._token
        resp = requests.get(
            DEFAULT_BAIDU_TOKEN_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key,
            },
            timeout=10,
        )
        resp.raise_for_status()
        self._token = resp.json().get("access_token", "")
        return self._token

    # ---------- 对外 ----------
    async def recognize(self, image_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        token = self._get_access_token()
        url = f"{DEFAULT_BAIDU_OCR_URL}?access_token={token}"

        # 百度 OCR vat_invoice 接口要求 image 参数必须是 base64 编码字符串
        b64_str = base64.b64encode(image_bytes).decode("utf-8")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                data={"image": b64_str},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()

        # 百度 OCR 错误处理
        if "error_code" in data:
            raise RuntimeError(f"百度 OCR 错误: {data.get('error_msg', '未知错误')}")

        # 百度 vat_invoice 接口有两种返回格式：
        #   老版带 "result" 包装，新版直接顶层 words_result
        # 统一展开成一个结构化 dict，方便 parser.py 处理
        structured = data.get("result") or data.get("words_result") or {}
        if isinstance(structured, dict):
            # 百度返回的商品多行字段都是 [{row:"1", word:"35.50"}, {row:"2", word:"44.30"}, ...] 这种结构
            # 处理策略：
            #   - 金额类字段 (CommodityAmount / CommodityTax) → 累加所有行，得到整张发票合计
            #   - 非金额类 commodity 数组 (CommodityName / CommodityUnit ...) → 保留原样，留给 type_extra 用
            AMOUNT_ARRAY_KEYS = {"CommodityAmount", "CommodityTax"}
            for k, v in structured.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "word" in v[0]:
                    if k in AMOUNT_ARRAY_KEYS:
                        # 金额类 → 累加所有行
                        total = 0.0
                        for row in v:
                            try:
                                total += float(str(row["word"]).replace(",", "").replace("¥", "").strip() or "0")
                            except (ValueError, TypeError):
                                pass
                        structured[k] = round(total, 2)
                    else:
                        # 非金额类 → 只取第一行代表值（完整数组保留给 type_extra）
                        structured[k] = v[0]["word"]

        return {
            "raw": data,
            "text": "",
            "structured": structured,
        }
