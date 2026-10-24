"""
ocr/adapter.py
==============
OCR 适配器 —— 抽象基类 + 工厂方法。
所有 OCR 服务（百度、腾讯、LLM 等）都实现同一个 `recognize(image_bytes)` 接口，
后端上层业务代码只需依赖 OCRAdapter 抽象，不关心具体用的哪家服务。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..utils.settings_manager import SettingsManager


class OCRAdapter(ABC):
    """OCR 适配器抽象基类。"""

    @abstractmethod
    async def recognize(self, image_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        """
        识别图片并返回原始 OCR 结果。

        返回结构约定：
        {
            "raw": {...},           # OCR 服务原始返回（调试用）
            "text": "....",         # 纯文本识别结果（兜底用）
            "structured": {...},    # 若 OCR 直接返回结构化字段则放这里
        }
        """
        raise NotImplementedError


def get_adapter() -> OCRAdapter:
    """
    工厂方法 —— 根据用户设置返回对应的适配器实例。
    未配置任何密钥时，返回 MockAdapter（仅用于本地演示，解析模拟数据）。
    """
    provider = SettingsManager.get_ocr_provider()

    if provider == "baidu" and SettingsManager.is_baidu_configured():
        from .baidu_adapter import BaiduOCRAdapter
        return BaiduOCRAdapter()

    if provider == "llm" and SettingsManager.is_llm_configured():
        from .llm_adapter import LLMAdapter
        return LLMAdapter()

    # 未配置密钥 → 返回 Mock，让系统可以演示跑通流程
    from .mock_adapter import MockAdapter
    return MockAdapter()
