@echo off
rem UTF-8 console for Python output (ASCII-only file for CMD compatibility)
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
