# -*- mode: python ; coding: utf-8 -*-
"""
invoice_recognizer.spec
=======================
PyInstaller 打包配置 —— 把 backend + frontend 静态文件打成单个桌面 exe。

打包命令：
  cd backend
  pyinstaller invoice_recognizer.spec --clean --noconfirm

产物：
  backend/dist/InvoiceRecognizer.exe   （单文件 GUI 程序，~55MB）
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

BACKEND_DIR = Path(r"C:\Users\Shen Zerui\Documents\Trae-CN\temp_20261023_01\backend").resolve()
STATIC_DIR = BACKEND_DIR / "static"

# ---- hiddenimports ----
hiddenimports = collect_submodules("app") + [
    # ★ 入口导入 —— launcher.py 依赖这些，必须显式声明避免 PyInstaller 漏掉
    "main",                         # FastAPI app 本身
    "launcher",
    # Web 框架
    "fastapi", "starlette", "uvicorn",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    # DB
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.ext.asyncio",
    "aiosqlite",
    # HTTP
    "httpx", "requests",
    # Pydantic
    "pydantic", "pydantic.deprecated.decorator",
    # PyWebView 桌面 GUI —— 必须全部列出来
    "webview",
    "webview.platforms",
    "webview.platforms.winforms",
    "webview.platforms.winforms.cf",
    "webview.platforms.winforms.mshtml",
    "webview.platforms.edgechromium",
    "webview.platforms.edgechromium.edgechromium",
    # 系统互操作
    "clr", "clr_system", "System",
]

# ---- datas：前端 static 资源 → 打包后在 sys._MEIPASS/static/ ----
datas = []
if STATIC_DIR.exists():
    datas.append((str(STATIC_DIR), "static"))

block_cipher = None

a = Analysis(
    [str(BACKEND_DIR / "launcher.py")],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 砍掉没用的减小体积
        "tkinter", "test", "tests",
        "pandas", "numpy", "scipy", "matplotlib",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="InvoiceRecognizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # ← 关键！GUI 程序不要弹出黑色命令窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # 可以以后加 .ico 图标
)
