"""
launcher.py —— pywebview 桌面窗口版

启动流程：
  1. FastAPI/uvicorn 在后台线程起服务（127.0.0.1:8000）
  2. 等待后端就绪（最多 30s）
  3. 主线程调用 webview.create_window + webview.start()
     → 弹出独立桌面窗口（EdgeChromium WebView2）
     → 窗口关闭 = 程序退出（daemon 线程自动清理）

编码安全：
  PyInstaller console=False 模式下 sys.stdout 是 GBK 流
  所有日志只用 ASCII 或写 UTF-8 文件，避免 UnicodeEncodeError
"""

import sys
import threading
import time
import uvicorn
from pathlib import Path

from main import app  # noqa: E402

# —— 调试日志路径 ——
if getattr(sys, "frozen", False):
    LOG_FILE = Path(sys.executable).resolve().parent / "launcher_debug.log"
else:
    LOG_FILE = Path(__file__).parent / "launcher_debug.log"


def log(msg):
    """UTF-8 写文件 + 安全 print 到控制台（防 GBK 崩溃）。"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    try:
        safe = msg.encode("gbk", errors="replace").decode("gbk")
        print(safe, flush=True)
    except Exception:
        pass


HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _run_uvicorn():
    """后台线程 —— 跑 FastAPI。"""
    try:
        log("[thread] uvicorn starting...")
        uvicorn.run(
            app, host=HOST, port=PORT,
            log_level="warning", access_log=False,
            log_config=None,
        )
    except Exception as e:
        log(f"[thread] uvicorn CRASH: {type(e).__name__}: {e}")


def _wait_backend(timeout: int = 30) -> bool:
    """轮询后端直到 ready。"""
    import urllib.request
    for i in range(timeout):
        time.sleep(1)
        try:
            urllib.request.urlopen(URL, timeout=1)
            log(f"[main] [OK] Backend ready after {i + 1}s")
            return True
        except Exception:
            pass
    return False


def _show_error_window(html_path: Path):
    """后端起不来时，用 webview 显示一个错误页。"""
    import webview
    try:
        webview.create_window(
            "启动失败",
            html=str(html_path.read_text(encoding="utf-8")),
            width=520, height=360,
            resizable=False,
        )
        webview.start()
    except Exception as e:
        log(f"[main] failed to show error window: {e}")


def main():
    # 清日志
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch(exist_ok=True)
    LOG_FILE.write_text("")

    log(f"{'='*40}")
    log(f"exe={getattr(sys, 'frozen', False)} py={sys.version_info.major}.{sys.version_info.minor}")
    log(f"LOG_FILE={LOG_FILE}")
    log(f"{'='*40}")

    # 1. 起 FastAPI（daemon 线程，主进程退它也退）
    threading.Thread(target=_run_uvicorn, daemon=True).start()

    # 2. 等后端就绪
    if not _wait_backend():
        log("[main] [FAIL] Backend never started after 30s")
        # 写错误页
        err_html = LOG_FILE.parent / "backend_error.html"
        err_html.write_text(
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>启动失败</title></head>"
            f"<body style='font-family:-apple-system,sans-serif;padding:40px;'>"
            f"<h1 style='color:#ff3b30'>启动失败</h1>"
            f"<p>后端服务未能正常启动。</p>"
            f"<p style='color:#666;font-size:12px;'>日志文件: {LOG_FILE}</p>"
            f"</body></html>",
            encoding="utf-8",
        )
        _show_error_window(err_html)
        return

    # 3. 打开 pywebview 独立窗口（EdgeChromium WebView2）
    import webview

    log("[main] [OK] Creating pywebview window...")
    webview.create_window(
        title="票据识别管理系统",
        url=URL,
        width=1280,
        height=820,
        min_size=(1024, 640),
        resizable=True,
        text_select=True,       # 允许用户复制文字
    )

    # edgechromium 在 Win10+ 上默认有 WebView2 Runtime；强制指定确保不 fallback 到 mshtml
    try:
        webview.start(debug=False, gui="edgechromium")
    except Exception as e:
        log(f"[main] edgechromium not available ({e}), trying default backend...")
        webview.start(debug=False)

    log("[main] Window closed. Exiting.")


if __name__ == "__main__":
    main()
