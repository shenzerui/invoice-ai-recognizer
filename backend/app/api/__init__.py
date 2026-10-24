"""
api/__init__.py
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .settings import router as settings_router
from .invoices import router as invoices_router
from .upload import router as upload_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(settings_router, prefix="/settings", tags=["设置"])
api_router.include_router(invoices_router, prefix="/invoices", tags=["票据"])
api_router.include_router(upload_router, prefix="/upload", tags=["上传识别"])
