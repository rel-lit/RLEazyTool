@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call "%~dp0_utf8_env.bat" 2>nul

set "TOOL_DIR=%~dp0"
set "VENV_DIR=%TOOL_DIR%.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "BACKEND=%TOOL_DIR%backend"
set "REQ=%TOOL_DIR%requirements.txt"

if not exist "%BACKEND%\main.py" (
    echo [ERROR] backend not found: "%BACKEND%"
    pause
    exit /b 1
)

if not exist "%REQ%" (
    echo [ERROR] requirements.txt not found: "%REQ%"
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [factory-balance] Creating virtual environment...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Install Python 3.10+ and ensure py or python is on PATH.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo [ERROR] venv python missing: "%VENV_PY%"
    pause
    exit /b 1
)

echo [factory-balance] Installing dependencies...
"%VENV_PY%" -m pip install -q -r "%REQ%"
if errorlevel 1 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)

if exist "%TOOL_DIR%frontend\package.json" (
    where npm >nul 2>&1
    if not errorlevel 1 (
        echo [factory-balance] Building frontend...
        pushd "%TOOL_DIR%frontend"
        if not exist "node_modules" (
            call npm install --no-fund --no-audit
            if errorlevel 1 (
                echo [WARN] npm install failed; API docs still at /docs
                popd
                goto :start_server
            )
        )
        call npm run build
        if errorlevel 1 (
            echo [WARN] Frontend build failed; API docs still at /docs
        )
        popd
    ) else (
        echo [WARN] npm not on PATH; skip frontend build
    )
)

:start_server
cd /d "%BACKEND%"

rem If a previous instance is still listening, stop it so we can bind 8765
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "127.0.0.1:8765" ^| findstr "LISTENING"') do (
    echo [factory-balance] Stopping previous server PID %%a ...
    taskkill /PID %%a /F >nul 2>&1
)
ping -n 2 127.0.0.1 >nul

if exist "%TOOL_DIR%frontend\dist\index.html" (
    echo Starting http://127.0.0.1:8765
    start "" "http://127.0.0.1:8765"
    "%VENV_PY%" -m uvicorn main:app --host 127.0.0.1 --port 8765
) else (
    echo [dev] Frontend not built. API docs: http://127.0.0.1:8765/docs
    echo Build: cd frontend ^& npm install ^& npm run build
    "%VENV_PY%" -m uvicorn main:app --host 127.0.0.1 --port 8765 --reload
)

pause
