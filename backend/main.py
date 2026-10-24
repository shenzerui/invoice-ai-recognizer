"""
backend/main.py
===============
FastAPI 主入口。

两种启动方式：
  开发模式（前后端分离）:
    cd backend && python main.py
    前端另外跑 vite dev server（npm run dev）

  打包后（单进程）:
    双击 exe 即可，FastAPI 自动托管前端静态文件 + 后端 API
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.api import api_router
from app.config import UPLOAD_DIR, STATIC_DIR


# ====== 启动 / 关闭生命周期 ======
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    mode = "exe" if getattr(sys, "frozen", False) else "dev"
    print(f"[OK] Invoice Recognizer started (mode: {mode}), DB ready")
    yield
    print("[OK] Server stopped")


app = FastAPI(
    title="票据识别管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# ====== CORS ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== API 路由 —— 必须在静态文件之前挂载 ======
app.include_router(api_router, prefix="/api")

# ====== 票据图片静态托管 ======
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ====== 前端 assets 静态托管（必须在 SPA fallback 之前！）======
# 否则 @app.get("/{full_path:path}") 会把 /assets/*.js 也给 fallback 成 index.html
if STATIC_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(STATIC_DIR / "assets")),
        name="static_assets",
    )


# ====== 前端 SPA fallback（Vue Router history 模式） ======
# 用户访问 /history /upload 这类前端路由时，FastAPI 返回 index.html 让前端接管
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str, request: Request):
    """除 /api/* /uploads/* /assets/* 外的所有 GET 请求 → 返回前端 index.html。"""
    # 显式跳过静态资源路径（双重保险）
    if full_path.startswith("assets/") or full_path.startswith("api/") or full_path.startswith("uploads/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")

    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": "Invoice Recognizer API",
        "tip": "前端静态资源未构建。开发模式请在 frontend/ 下运行 `npm run dev`",
    }


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
