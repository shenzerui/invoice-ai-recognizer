"""
ocr/mock_adapter.py
===================
Mock 适配器 —— 用户未配置任何密钥时兜底使用。
会根据文件名（通过扩展名或文件名关键词猜测）返回模拟识别结果，
让整个系统流程可以在本地演示跑通。

答辩讲解时：如果老师问"没 OCR 密钥怎么办"，就展示这个 Mock 能跑通全流程。
"""

import random
from typing import Dict, Any
from .adapter import OCRAdapter


# 常见公司名用于 mock
_COMPANIES = ["北京某某科技有限公司", "上海某某贸易有限公司", "广州某某餐饮有限公司",
              "深圳某某物流有限公司", "杭州某某网络科技有限公司"]


def _mock_vat_invoice() -> Dict[str, Any]:
    amount = round(random.uniform(100, 5000), 2)
    tax = round(amount * 0.13, 2)
    return {
        "invoice_type": random.choice(["vat_special", "vat_normal", "vat_electronic"]),
        "invoice_code": f"{random.randint(10**9, 10**10-1)}",
        "invoice_number": f"{random.randint(10**7, 10**8-1)}",
        "invoice_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "buyer": random.choice(_COMPANIES),
        "seller": random.choice(_COMPANIES),
        "amount": amount,
        "tax": tax,
        "total_amount": round(amount + tax, 2),
        "extra": {"备注": "这是一条 Mock 识别结果"},
    }


def _mock_fixed_invoice() -> Dict[str, Any]:
    face_amount = random.choice([5, 10, 20, 50, 100])
    return {
        "invoice_type": "fixed",
        "invoice_code": f"{random.randint(10**9, 10**10-1)}",
        "invoice_number": f"{random.randint(10**7, 10**8-1)}",
        "invoice_date": "",
        "buyer": "",
        "seller": "",
        "amount": face_amount,
        "tax": 0,
        "total_amount": face_amount,
        "extra": {"票面金额": face_amount, "收款单位": random.choice(_COMPANIES)},
    }


def _mock_train_ticket() -> Dict[str, Any]:
    price = round(random.uniform(50, 1200), 2)
    seats = ["一等座", "二等座", "商务座", "硬卧", "软卧"]
    return {
        "invoice_type": "train",
        "invoice_code": "",
        "invoice_number": f"E{random.randint(10**8, 10**9-1)}",
        "invoice_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "buyer": "",
        "seller": "中国铁路",
        "amount": price,
        "tax": 0,
        "total_amount": price,
        "extra": {
            "起始站": random.choice(["北京", "上海", "广州", "深圳", "杭州"]) + "南",
            "到达站": random.choice(["南京", "武汉", "成都", "西安", "重庆"]) + "北",
            "席别": random.choice(seats),
            "车次": f"G{random.randint(1, 9999)}",
        },
    }


def _mock_bus_ticket() -> Dict[str, Any]:
    price = round(random.uniform(20, 300), 2)
    return {
        "invoice_type": "bus",
        "invoice_code": "",
        "invoice_number": f"{random.randint(10**7, 10**8-1)}",
        "invoice_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "buyer": "",
        "seller": "",
        "amount": price,
        "tax": 0,
        "total_amount": price,
        "extra": {
            "起始站": "汽车总站",
            "到达站": "汽车东站",
            "班次": f"B{random.randint(100, 999)}",
        },
    }


def _mock_toll_ticket() -> Dict[str, Any]:
    price = round(random.uniform(5, 100), 2)
    return {
        "invoice_type": "toll",
        "invoice_code": "",
        "invoice_number": f"{random.randint(10**7, 10**8-1)}",
        "invoice_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "buyer": "",
        "seller": "",
        "amount": price,
        "tax": 0,
        "total_amount": price,
        "extra": {
            "入口": "高速入口",
            "出口": "高速出口",
        },
    }


# 根据文件名关键词决定 mock 哪种票据
_KEYWORD_MAP = {
    "vat": _mock_vat_invoice, "special": _mock_vat_invoice, "normal": _mock_vat_invoice,
    "fixed": _mock_fixed_invoice, "定额": _mock_fixed_invoice,
    "train": _mock_train_ticket, "火车": _mock_train_ticket,
    "bus": _mock_bus_ticket, "汽车": _mock_bus_ticket,
    "toll": _mock_toll_ticket, "通行": _mock_toll_ticket,
}


class MockAdapter(OCRAdapter):
    """Mock OCR —— 本地演示用。"""

    async def recognize(self, image_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        fn_lower = filename.lower()
        for kw, fn in _KEYWORD_MAP.items():
            if kw in fn_lower or kw in filename:
                structured = fn()
                break
        else:
            structured = random.choice([
                _mock_vat_invoice, _mock_vat_invoice,  # 增值税票更常见
                _mock_fixed_invoice, _mock_train_ticket,
            ])()

        return {
            "raw": {"mock": True},
            "text": f"[Mock OCR] {filename} 模拟识别结果",
            "structured": structured,
        }
