@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo [base-converter] venv already exists
    goto :end
)

echo [base-converter] Creating virtual environment...
py -m venv .venv
if errorlevel 1 (
    echo [base-converter] ERROR: Failed to create venv. Make sure Python is installed and 'py' is in PATH.
    pause
    exit /b 1
)

echo [base-converter] Installing dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [base-converter] ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [base-converter] Setup complete

:end
timeout /t 2 /nobreak >nul
