"""
api/auth.py
===========
用户注册 / 登录 / 当前用户信息。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserRegister, UserLogin, TokenResponse, UserInfo
from ..utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


@router.post("/register", response_model=UserInfo, status_code=status.HTTP_201_CREATED, summary="注册新用户")
async def register(data: UserRegister, session: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await session.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return _to_user_info(user)


@router.post("/login", response_model=TokenResponse, summary="登录 —— 返回 JWT")
async def login(data: UserLogin, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserInfo, summary="获取当前登录用户信息")
async def me(current_user: User = Depends(get_current_user)):
    return _to_user_info(current_user)


def _to_user_info(u: User) -> UserInfo:
    return UserInfo(
        id=u.id,
        username=u.username,
        created_at=u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
    )
