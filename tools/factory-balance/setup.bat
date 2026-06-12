@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call "%~dp0_utf8_env.bat" 2>nul

set "VENV_DIR=%~dp0.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "REQ=%~dp0requirements.txt"

echo [factory-balance] Setup venv: %VENV_DIR%

if not exist "%VENV_PY%" (
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        exit /b 1
    )
)

"%VENV_PY%" -m pip install -r "%REQ%"
if errorlevel 1 exit /b 1

echo.
echo Done. Run tests:
echo   "%VENV_PY%" -m unittest discover -s tests -v
echo Start app:
echo   balance.bat
