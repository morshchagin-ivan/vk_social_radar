@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo VK Social Radar v0.4.2
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/4] Virtual environment exists.
)

echo [2/4] Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [3/5] Installing Playwright Chromium if needed...
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :error

echo [4/5] Starting server at http://127.0.0.1:8765
start "VK Social Radar Server" cmd /k ""%CD%\.venv\Scripts\python.exe" "%CD%\run_server.py""

echo [5/5] Opening browser...
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8765"

echo.
echo Started successfully.
echo Close this window or press any key.
pause >nul
exit /b 0

:error
echo.
echo ERROR: installation or startup failed.
echo Check the messages above.
pause
exit /b 1
