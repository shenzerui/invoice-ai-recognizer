"""
utils/settings_manager.py
=========================
设置管理器 —— 用 JSON 文件持久化用户填入的 OCR / LLM API 密钥。
密钥只存本地，不回传前端明文，保障用户隐私。
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from ..config import SETTINGS_FILE


class SettingsManager:
    """单例风格的设置管理器，所有方法都是静态/类方法。"""

    _default: Dict[str, Any] = {
        "ocr_provider": "baidu",
        "baidu_api_key": "",
        "baidu_secret_key": "",
        "llm_api_key": "",
        "llm_api_url": "",
        "llm_model": "",
    }

    @classmethod
    def _ensure_file(cls) -> Path:
        """确保 JSON 文件存在。"""
        p = Path(SETTINGS_FILE)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(json.dumps(cls._default, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """读取全部设置。"""
        p = cls._ensure_file()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # 用默认值兜底，防止缺字段
            merged = {**cls._default, **data}
            return merged
        except Exception:
            return dict(cls._default)

    @classmethod
    def save(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """合并更新并持久化，返回更新后的完整设置。"""
        current = cls.load()
        # 空值字段清除（前端可能把 key 传 "" 表示要清空）
        for k, v in updates.items():
            if v is not None:
                current[k] = v
            elif k in current:
                # None 表示不更新该字段，跳过
                pass
        p = cls._ensure_file()
        p.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        return current

    @classmethod
    def is_baidu_configured(cls) -> bool:
        """百度 OCR 是否已配好密钥。"""
        s = cls.load()
        return bool(s.get("baidu_api_key") and s.get("baidu_secret_key"))

    @classmethod
    def is_llm_configured(cls) -> bool:
        """LLM 是否已配好 API Key。"""
        s = cls.load()
        return bool(s.get("llm_api_key"))

    @classmethod
    def get_ocr_provider(cls) -> str:
        """当前启用的 OCR 提供商。"""
        s = cls.load()
        return s.get("ocr_provider", "baidu")
