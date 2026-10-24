"""
database.py
===========
SQLAlchemy 异步数据库连接与 Session 管理。
使用 sqlite + aiosqlite，单文件数据库，无需额外启动数据库服务。
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import SQLALCHEMY_DATABASE_URL

# SQLite 异步连接 —— aiossqlite 驱动
# 注意：sqlite 的 async 驱动名称是 sqlite+aiosqlite
ASYNC_DB_URL = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

# 创建异步引擎
engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,                  # 生产可关闭 SQL 日志
    future=True,
)

# Session 工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的父类。"""
    pass


async def get_db():
    """FastAPI 依赖注入 —— 获取一个数据库 Session。"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """启动时自动建表。"""
    from . import models  # noqa: F401  —— 必须先导入模型让 SQLAlchemy 认识它们
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
