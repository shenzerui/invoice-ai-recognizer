"""
schemas/settings.py
===================
用户设置相关 Schema —— 主要是 OCR / LLM API 密钥配置。
"""

from typing import Optional
from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    """用户更新 API 密钥设置。"""
    # OCR 服务选择：baidu（百度OCR）/ llm（大模型通用接口）
    ocr_provider: str = "baidu"

    # 百度 OCR
    baidu_api_key: Optional[str] = None
    baidu_secret_key: Optional[str] = None

    # 通用 LLM（兼容 OpenAI 请求格式）
    llm_api_key: Optional[str] = None
    llm_api_url: Optional[str] = None      # 可填自定义代理地址
    llm_model: Optional[str] = None        # 如 gpt-4o / doubao-pro 等


class SettingsResponse(BaseModel):
    """读取当前设置 —— 密钥字段只返回是否已配置，不回传明文。"""
    ocr_provider: str = "baidu"
    baidu_configured: bool = False
    llm_configured: bool = False
    llm_api_url: str = ""
    llm_model: str = ""
