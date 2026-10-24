"""
database.py
===========
SQLAlchemy 异步数据库连接与 Session 管理。
使用 sqlite + aiosqlite，单文件数据库，无需额外启动数据库服务。

迁移策略：
  init_db() 只做 create_all（新表），已有表的新增列通过 run_migrations() 手动 ALTER TABLE。
  原因：SQLite 不支持 ALTER TABLE ADD COLUMN 之外的 DDL，且 SQLAlchemy 的 create_all
  只处理"不存在"的表，不会给已有表补列。
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import SQLALCHEMY_DATABASE_URL

# SQLite 异步连接 —— aiossqlite 驱动
ASYNC_DB_URL = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

# 创建异步引擎
engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
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
    """启动时自动建表（新表）。"""
    from . import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_migrations()


async def run_migrations():
    """
    给已有表补新增列 —— 首次加用户系统时，invoices 表可能还没有 user_id。
    幂等：如果列已经存在就跳过。
    """
    migrations = [
        ("invoices", "user_id", "INTEGER DEFAULT 0"),
    ]
    async with engine.begin() as conn:
        for table, column, col_def in migrations:
            rows = await conn.execute(text(f"PRAGMA table_info({table})"))
            existing = {r[1] for r in rows.fetchall()}
            if column not in existing:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                print(f"[migration] {table}.{column} added")
