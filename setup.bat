@echo off
REM Jupiter TV - Simple Setup Script
REM Just handles Python + dependencies setup

title Jupiter TV Setup
cd /d "%~dp0"

echo.
echo ================================================
echo  JUPITER TV - SETUP & INSTALLATION
echo ================================================
echo.
echo Location: %CD%
echo.

REM Check Python
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found
  echo.
  echo Please install Python 3.11+ from:
  echo https://www.python.org/downloads/
  echo.
  echo IMPORTANT: Check "Add Python to PATH" during install
  echo.
  pause
  exit /b 1
)
echo [OK] Python found
echo.

REM Check requirements file
echo [2/3] Checking requirements file...
if not exist "requirements-tv.txt" (
  echo ERROR: requirements-tv.txt not found in:
  echo %CD%
  echo.
  echo Make sure you extracted the full Jupiter TV folder
  echo and are running this script from the root folder
  echo.
  pause
  exit /b 1
)
echo [OK] requirements-tv.txt found
echo.

REM Install dependencies
echo [3/3] Installing dependencies...
echo This may take 5-10 minutes on first run...
echo.
pip install --upgrade pip
pip install -r requirements-tv.txt

if errorlevel 1 (
  echo.
  echo ERROR: Installation failed
  echo Try running this command manually:
  echo   pip install -r requirements-tv.txt
  echo.
  pause
  exit /b 1
)

echo.
echo ================================================
echo  SETUP COMPLETE!
echo ================================================
echo.
echo To run Jupiter Desktop:
echo   run-desktop.bat
echo.
echo To run Jupiter Mobile:
echo   run-mobile.bat
echo.
echo Or run from Python directly:
echo   python apps/julius-tv-desktop-v2/app.py
echo.
pause
