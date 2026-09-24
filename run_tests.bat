@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Install requirements-dev.txt in .venv first.
    exit /b 1
)

".venv\Scripts\python.exe" scripts\run_quality_gates.py
exit /b %errorlevel%
