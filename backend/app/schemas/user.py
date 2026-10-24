"""
schemas/user.py
===============
用户注册/登录/当前用户信息的 Pydantic Schema。
"""

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """注册请求。"""
    username: str = Field(..., min_length=3, max_length=32, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserLogin(BaseModel):
    """登录请求。"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """登录成功返回。"""
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """当前用户信息（不返回密码）。"""
    id: int
    username: str
    created_at: str = ""

    class Config:
        from_attributes = True
