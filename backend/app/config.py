"""
config.py
========
全局配置文件 —— 集中管理项目中所有可配置的路径、常量、票据类型枚举等。

两种运行模式自动适配：
  开发模式 (python main.py):
    BASE_DIR = backend/ 目录
  PyInstaller 打包成 exe 后:
    EXE_DIR   = exe 所在目录（数据持久化放这里）
    RESOURCE  = PyInstaller 解压到的临时目录（只读，放前端 static 资源）
    DB / uploads / settings 都放 exe 同级，这样重装不会丢数据
"""

import sys
from pathlib import Path
from typing import Dict


# ====== 运行模式判断 ======
def _resolve_dirs():
    """根据运行模式返回 (BASE_DIR, RESOURCE_DIR)。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后的 exe 模式
        # sys.executable → exe 的完整路径
        # sys._MEIPASS   → PyInstaller 解压到的临时目录（只读）
        exe_path = Path(sys.executable).resolve()
        exe_dir = exe_path.parent           # exe 同级目录（数据持久化）
        resource_dir = Path(sys._MEIPASS)   # 临时解压目录（静态资源）
        return exe_dir, resource_dir
    else:
        # 开发模式
        project_root = Path(__file__).resolve().parent.parent
        return project_root, project_root


BASE_DIR, RESOURCE_DIR = _resolve_dirs()

# ====== 路径配置 ======
# SQLite 数据库文件路径（exe 同级）
DB_PATH = BASE_DIR / "data" / "invoices.db"
# 票据图片上传保存目录（exe 同级）
UPLOAD_DIR = BASE_DIR / "uploads"
# 设置 JSON 文件路径（用于持久化用户填入的 OCR / LLM API 密钥，exe 同级）
SETTINGS_FILE = BASE_DIR / "data" / "settings.json"
# 前端静态资源目录（开发模式 → backend/static；exe 模式 → _MEIPASS 解压目录里的 static/）
STATIC_DIR = RESOURCE_DIR / "static"

# 确保数据目录存在（仅 BASE_DIR 下的可写目录）
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ====== 数据库连接 ======
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# ====== 服务配置 ======
HOST = "0.0.0.0"
PORT = 8000

# ====== 票据类型定义 ======
# 系统支持识别的所有票据类型，键值保持一致即可，新增类型只需在此处追加
TICKET_TYPES = {
    "vat_special":     "增值税专用发票",
    "vat_normal":      "增值税普通发票",
    "vat_electronic":  "增值税电子普通发票",
    "digital_special": "数电专用发票",
    "digital_normal":  "数电普通发票",
    "fixed":           "定额发票",
    "train":           "火车票",
    "bus":             "汽车票",
    "toll":            "通行费票据",
    "unknown":         "未知类型",
}

# ====== OCR / LLM 默认 API 地址 ======
# 后端内置两种适配器：百度 OCR（票据识别成熟）和 通用 LLM（兼容 OpenAI 请求格式）
DEFAULT_BAIDU_OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice"
DEFAULT_BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
DEFAULT_LLM_API_URL = "https://api.openai.com/v1/chat/completions"

# ====== 支持的图片扩展名 ======
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# ====== 单文件最大大小（字节） ======
MAX_UPLOAD_SIZE = 10 * 1024 * 1024   # 10 MB
