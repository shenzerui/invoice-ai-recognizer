"""
ocr/llm_adapter.py
==================
通用 LLM 适配器 —— 兼容 OpenAI Chat Completions 请求格式，支持 vision 能力。
模型会被提示词引导以 JSON 格式输出票据结构化字段。

优势：
  - 一个适配器覆盖所有票据类型（增值税专/普/电子、定额、火车、汽车、通行费…）
  - 用户可以用国内大模型（如豆包、通义、文心一言）的 API 兼容端点
"""

import base64
import json
import httpx
from typing import Dict, Any
from .adapter import OCRAdapter
from ..config import DEFAULT_LLM_API_URL


# 引导 LLM 输出结构化 JSON 的系统提示词
SYSTEM_PROMPT = """你是专业的票据识别助手。用户会上传一张票据图片，请你仔细识别图片中的文字内容，
并按要求输出结构化的 JSON。输出要求：

【通用格式约束】
1. 只输出 JSON，不要输出任何额外的解释或 markdown 代码块标记。
2. 识别到不确定的字段填空字符串 "" 或 0。
3. 金额字段：去掉人民币符号¥、千分位逗号，直接写数字（如 1234.56），保留 2 位小数。
4. 日期字段：统一 YYYY-MM-DD 格式（如 2024-08-15）。
5. 购销方名称：只输出公司/单位名称本身，严禁把"购买方名称:"、"纳税人识别号:"等标签文字和冒号带进值里。
6. 去除所有前后空白字符。

【★★★ 价税合计取值规则（最容易出错，请务必遵守）★★★】
- total_amount（价税合计）必须取自票面最下方「价税合计（小写）」或「价税合计」行对应的金额。
- 严禁把明细表格底部的「合计」、「金额合计」行金额填进 total_amount —— 那是"不含税金额合计"，属于 amount 字段。
- 判断标准：票面底部通常有两行并排的「价税合计」区域，左侧是大写金额，右侧是小写金额（带¥符号），取右侧小写那个。
- 如果票面有"合计金额: XXX + 税额: YYY"的布局，total_amount = XXX + YYY（把两个加起来）。

【发票类型枚举】
   - digital_special: 数电专用发票（全电专用发票，发票号码 20 位，无发票代码）
   - digital_normal:  数电普通发票（全电普通发票，发票号码 20 位，无发票代码）
   - vat_special:     增值税专用发票
   - vat_normal:      增值税普通发票
   - vat_electronic:  增值税电子普通发票（发票代码 12 位 + 发票号码 8 位）
   - fixed:           定额发票
   - train:           火车票 / 高铁票
   - bus:             汽车票
   - toll:            通行费票据（如 ETC 通行费、高速过路费）
   - unknown:         无法识别

输出 JSON 格式示例：
{
    "invoice_type": "vat_normal",
    "invoice_code": "1100214130",
    "invoice_number": "12345678",
    "invoice_date": "2024-08-15",
    "buyer": "北京某某科技有限公司",
    "seller": "上海某某贸易有限公司",
    "amount": 1234.56,
    "tax": 156.23,
    "total_amount": 1390.79,
    "extra": {"备注": "...", "发票专用章": "..."}
}

校验自检规则：输出前请自检 amount + tax == total_amount（允许 0.02 元误差）。
如果 amount + tax 和 total_amount 差超过 0.02 元，说明 total_amount 可能取错了（很可能取到了明细行的"合计"），请重新仔细看图票最下方。"""


class LLMAdapter(OCRAdapter):
    """通用大模型（Vision）适配器。"""

    def __init__(self):
        settings = self._load_settings()
        self.api_key = settings["llm_api_key"]
        self.api_url = settings.get("llm_api_url") or DEFAULT_LLM_API_URL
        self.model = settings.get("llm_model") or "gpt-4o-mini"

    @staticmethod
    def _load_settings() -> Dict[str, Any]:
        from ..utils.settings_manager import SettingsManager
        return SettingsManager.load()

    async def recognize(self, image_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        # 图片转 base64
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        mime = "jpeg" if ext in ("jpg", "jpeg") else "png"
        data_url = f"data:image/{mime};base64,{b64}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请识别这张票据图片并按要求输出 JSON。"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "max_tokens": 1500,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # 解析 LLM 返回
        try:
            content = data["choices"][0]["message"]["content"].strip()
            # 去除可能的 markdown 代码块包裹
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(content)
        except Exception as e:
            raise RuntimeError(f"LLM 返回解析失败: {e}; 原始返回: {data}")

        return {
            "raw": data,
            "text": content,
            "structured": parsed,
        }
