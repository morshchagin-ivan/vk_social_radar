@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Run start.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 (
    echo.
    echo TESTS FAILED.
    pause
    exit /b 1
)

echo.
echo ALL TESTS PASSED.
pause
