@echo off
setlocal
cd /d "%~dp0"
echo.
echo ====================================================
echo    SYNBYTE - Local Campus Food System
echo ====================================================
echo.
py -3 --version >nul 2>&1
if %errorlevel% EQU 0 (
  set "PYTHON=py -3"
) else (
  python --version >nul 2>&1
  if %errorlevel% NEQ 0 (
    echo ERROR: Python 3 is not found.
    echo Install Python 3.10+ and enable Add Python to PATH.
    pause
    exit /b 1
  )
  set "PYTHON=python"
)
%PYTHON% -c "import flask,requests,PIL,qrcode" >nul 2>&1
if %errorlevel% NEQ 0 (
  echo Installing dependencies... (internet required once)
  %PYTHON% -m pip install -r requirements.txt
  if %errorlevel% NEQ 0 (
    echo Could not install dependencies. Check your internet connection.
    pause
    exit /b 1
  )
)
if not defined PORT set "PORT=5000"
echo Starting Flask in a separate terminal...
start "SYNBYTE Flask" cmd /k %PYTHON% app.py
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:%PORT%"
echo Open http://127.0.0.1:%PORT% if your browser did not open automatically.
echo To stop the site, press Ctrl+C in the Flask terminal.
