"""
models/__init__.py  —— 自动导出所有 ORM 模型
这样在 database.py 里 `from . import models` 就能触发全部模型注册。
"""
from .invoice import Invoice
from .user import User

__all__ = ["Invoice", "User"]
