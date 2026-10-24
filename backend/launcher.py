"""
launcher.py —— 最终版（无 webview，用默认浏览器）

启动流程：
  1. FastAPI 在后台线程起服务
  2. 等待后端就绪（最多 25s）
  3. 自动打开系统默认浏览器 → http://127.0.0.1:8000
  4. 主进程保持 alive（daemon 线程会自动一起退）
  5. 用户关闭浏览器后，exe 不会自己退（后台继续跑），
     想完全退出可以在托盘/任务管理器杀进程 —— 或者
     我们可以让用户关闭"票据识别管理系统"标签页时给出提示

为什么这样设计：
  - PyWebView + mshtml 在 IE 内核下跑 Vue3 有大量兼容坑（Promise/Proxy/CSS Grid...）
  - edgechromium 需要 WebView2 Runtime（Win10 默认没装，打包后 segfault）
  - 系统默认浏览器（Chrome/Edge/Firefox）自带现代 JS 引擎，完美渲染
  - 用户不装任何东西，双击即用

编码安全：
  - 所有 log() 输出只用 ASCII，避免 GBK codec 崩溃
  - 见下方 SAFE_EMOJI / 纯文本替代
"""

import sys
import threading
import time
import webbrowser
import uvicorn
from pathlib import Path

# —— 顶层导入 FastAPI app ——
from main import app  # noqa: E402

# —— 调试日志（exe 同级）——
if getattr(sys, "frozen", False):
    LOG_FILE = Path(sys.executable).resolve().parent / "launcher_debug.log"
else:
    LOG_FILE = Path(__file__).parent / "launcher_debug.log"

# —— 编码安全的日志函数 ——
# 关键：PyInstaller console=False 用 runw.exe bootloader，
# sys.stdout 会被换成一个只接受 GBK 的流，emoji / 特殊字符编不了
# 会直接抛 UnicodeEncodeError 导致 exe 崩掉
def log(msg):
    # 1. 先写文件（UTF-8，无编码问题）
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    # 2. 再安全地 print 到控制台（跳过编码错误）
    try:
        # 把所有非 ASCII 字符替换成 ? 防止 GBK 崩溃
        safe = msg.encode("gbk", errors="replace").decode("gbk")
        print(safe, flush=True)
    except Exception:
        pass   # 实在不行也别崩

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _run_uvicorn():
    """FastAPI 后台线程"""
    try:
        log("[thread] uvicorn starting...")
        # log_config=None 关键：PyInstaller console=False 没有 stderr，
        # uvicorn 默认 formatter 找不到 handler 会直接崩
        uvicorn.run(
            app, host=HOST, port=PORT,
            log_level="warning", access_log=False,
            log_config=None,
        )
    except Exception as e:
        log(f"[thread] uvicorn CRASH: {type(e).__name__}: {e}")


def _wait_backend():
    """轮询后端直到 ready"""
    import urllib.request
    for i in range(25):
        time.sleep(1)
        try:
            urllib.request.urlopen(URL, timeout=1)
            log(f"[main] [OK] Backend ready after {i+1}s")
            return True
        except Exception:
            pass
    return False


def main():
    # 清日志
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch(exist_ok=True)
    LOG_FILE.write_text("")

    log(f"{'='*40}")
    log(f"exe={getattr(sys, 'frozen', False)}  py={sys.version_info.major}.{sys.version_info.minor}")
    log(f"LOG_FILE={LOG_FILE}")
    log(f"{'='*40}")

    # 1. 起 FastAPI
    threading.Thread(target=_run_uvicorn, daemon=True).start()

    # 2. 等后端
    if not _wait_backend():
        log("[main] [FAIL] Backend never started after 25s")
        # 写个 HTML 错误页到临时文件让 webbrowser 打开
        tmp = LOG_FILE.parent / "backend_error.html"
        tmp.write_text(f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>启动失败</title></head><body style="font-family:sans-serif;padding:40px;">
<h1 style="color:#c00">启动失败 - 后端未响应</h1>
<p>详细日志: <code>{LOG_FILE}</code></p>
<p>请把这个文件发给开发者排查问题。</p>
</body></html>""", encoding="utf-8")
        webbrowser.open(tmp.as_uri())
        return

    # 3. 自动打开默认浏览器
    log(f"[main] [OK] Opening browser: {URL}")
    webbrowser.open(URL)

    # 4. 主进程保持 alive（daemon 子线程会自动跟主进程一起退）
    #    用户想完全退出 → 关浏览器标签页 + 在任务管理器杀 InvoiceRecognizer.exe
    log("[main] Running... Close this process in Task Manager to fully exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    log("[main] Exiting.")


if __name__ == "__main__":
    main()
