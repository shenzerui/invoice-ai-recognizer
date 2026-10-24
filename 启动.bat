@echo off
title Invoice Recognizer
cd /d "%~dp0"

echo ============================================
echo   Invoice Recognizer - One Click Start
echo ============================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)
echo [OK] Python
python --version

REM --- Check Node ---
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+ first.
    pause
    exit /b 1
)
echo [OK] Node.js
node --version
echo.

REM --- Backend deps ---
echo [1/3] Checking backend deps...
cd backend
python -c "import fastapi, sqlalchemy, httpx" 2>nul
if errorlevel 1 (
    echo Installing backend deps...
    python -m pip install -r requirements.txt
    if errorlevel 1 ( echo [ERROR] Backend install failed & cd .. & pause & exit /b 1 )
) else (
    echo Backend deps ready
)
cd ..

REM --- Frontend deps ---
echo [2/3] Checking frontend deps...
if not exist "frontend\node_modules" (
    echo Installing frontend deps...
    cd frontend
    call npm.cmd install --registry https://registry.npmmirror.com
    if errorlevel 1 ( echo [ERROR] Frontend install failed & cd .. & pause & exit /b 1 )
    cd ..
) else (
    echo Frontend deps ready
)

REM --- Start backend ---
echo [3/3] Starting backend on port 8000...
start "Backend" cmd /k "cd /d ""%~dp0backend"" && python main.py"

REM --- Start frontend ---
timeout /t 5 /nobreak >nul
echo [3/3] Starting frontend on port 5173...
start "Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm.cmd run dev"

REM --- Open browser ---
timeout /t 8 /nobreak >nul
start http://localhost:5173

echo.
echo ============================================
echo   DONE! Open http://localhost:5173
echo   Stop: close the Backend / Frontend windows
echo ============================================
echo.
pause
