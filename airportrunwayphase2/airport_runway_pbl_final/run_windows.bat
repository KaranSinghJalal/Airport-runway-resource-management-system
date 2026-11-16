@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer from https://www.python.org/downloads/ and tick "Add Python to PATH".
  pause
  exit /b 1
)
echo Starting AirOps Airport Runway Management System...
echo When ready, open http://127.0.0.1:8000 in your browser.
echo Keep this window open while using the application.
python app\server.py
pause
