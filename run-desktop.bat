@echo off
REM Jupiter TV Desktop - Windows Launcher
REM Requires: Python 3.11+, PyQt6

cd /d "%~dp0"

title Jupiter Desktop - Scene Detection
echo.
echo ================================================
echo  JUPITER TV DESKTOP - SCENE DETECTION
echo ================================================
echo.
echo Working directory: %CD%
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found. Please install Python 3.11+
  echo Download: https://www.python.org/downloads/
  pause
  exit /b 1
)

REM Check if requirements file exists
if not exist "requirements-tv.txt" (
  echo ERROR: requirements-tv.txt not found
  echo Make sure you're in the Jupiter TV directory
  pause
  exit /b 1
)

REM Check dependencies
echo Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
  echo.
  echo Installing dependencies...
  python -m pip install -r requirements-tv.txt
  if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
  )
)

REM Check ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
  echo.
  echo WARNING: ffmpeg not found
  echo Scene detection will use uniform chunks fallback
  echo.
  echo To install ffmpeg:
  echo   1. Download from: https://ffmpeg.org/download.html
  echo   2. Or: choco install ffmpeg (if using Chocolatey)
  echo   3. Or: scoop install ffmpeg (if using Scoop)
  echo.
  pause
)

REM Run app
echo.
echo Starting Jupiter Desktop...
echo.

if not exist "apps\jupiter-tv-desktop-v2\app.py" (
  echo ERROR: apps\jupiter-tv-desktop-v2\app.py not found
  pause
  exit /b 1
)

python apps/jupiter-tv-desktop-v2/app.py

if errorlevel 1 (
  echo.
  echo ERROR: Application crashed
  echo Check the error messages above
  pause
  exit /b 1
)