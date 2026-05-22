@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0..\.."
set "VENV_PY=%ROOT%\.venv\Scripts\python.exe"

if exist "%VENV_PY%" (
    "%VENV_PY%" main.py
) else (
    echo [提示] 未找到项目虚拟环境: %ROOT%\.venv
    echo.
    echo 请在项目根目录创建 .venv 并安装 merge 可选依赖:
    echo   cd /d "%ROOT%"
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r tools\merge\requirements.txt
    echo.
    echo 将使用系统 Python 启动（首次会自动装 requirements-core：pathspec、parsy 等）...
    py main.py
)
pause
