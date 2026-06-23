@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [base-converter] First run, initializing...
    call setup.bat
    if errorlevel 1 exit /b 1
)

set PYTHONIOENCODING=utf-8
set PORT=8766

echo [base-converter] Starting server on http://127.0.0.1:%PORT%/
echo [base-converter] Browser will open automatically.

start "base-converter server" .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port %PORT%

timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:%PORT%/"

endlocal
