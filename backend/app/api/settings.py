"""
api/settings.py
===============
用户设置 —— 保存 OCR / LLM API 密钥。
也需要登录保护。
"""

from fastapi import APIRouter, Depends
from ..models.user import User
from ..schemas.settings import SettingsUpdate, SettingsResponse
from ..utils.settings_manager import SettingsManager
from ..utils.security import get_current_user

router = APIRouter()


@router.get("", response_model=SettingsResponse, summary="读取当前设置")
async def get_settings(current_user: User = Depends(get_current_user)):
    s = SettingsManager.load()
    return SettingsResponse(
        ocr_provider=s.get("ocr_provider", "baidu"),
        baidu_configured=SettingsManager.is_baidu_configured(),
        llm_configured=SettingsManager.is_llm_configured(),
        llm_api_url=s.get("llm_api_url", ""),
        llm_model=s.get("llm_model", ""),
    )


@router.put("", response_model=SettingsResponse, summary="更新设置")
async def update_settings(data: SettingsUpdate, current_user: User = Depends(get_current_user)):
    SettingsManager.save(data.model_dump(exclude_unset=True))
    return await get_settings(current_user)


@router.get("/test", summary="测试 OCR 适配器是否可用")
async def test_ocr(current_user: User = Depends(get_current_user)):
    from ..ocr.adapter import get_adapter
    adapter = get_adapter()
    provider = SettingsManager.get_ocr_provider()
    return {
        "provider": provider,
        "adapter_class": adapter.__class__.__name__,
        "baidu_configured": SettingsManager.is_baidu_configured(),
        "llm_configured": SettingsManager.is_llm_configured(),
        "message": "如果适配器是 MockAdapter 说明还没配密钥，功能仍可本地演示",
    }
