@echo off
setlocal enabledelayedexpansion
title Jupiter TV - Video AI Engine Setup

echo.
echo ========================================================
echo   JUPITER TV: Video AI Engine Environment Setup
echo ========================================================
echo.

:: Get working directory
cd /d "%~dp0"
echo [*] Working Directory: %CD%
echo.

:: 1. Create core directories
echo [1/6] Creating directory structure...
if not exist "engine" mkdir engine
if not exist "models" mkdir models
if not exist "config" mkdir config
if not exist "output" mkdir output
if not exist "logs" mkdir logs

:: Create Python package markers
type nul > engine\__init__.py
type nul > models\__init__.py
if not exist "config\__init__.py" type nul > config\__init__.py

echo [OK] Directories created
echo.

:: 2. Check Python
echo [2/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo.
    echo Solution:
    echo   1. Install Python 3.11+ from https://python.org
    echo   2. CHECK "Add Python to PATH" during installation
    echo   3. Restart this script
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i
echo.

:: 3. Check FFmpeg
echo [3/6] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] FFmpeg not found - video processing will be limited
    echo [WARN] Install via: choco install ffmpeg
    echo [WARN] Or download: https://ffmpeg.org/download.html
) else (
    echo [OK] FFmpeg found
)
echo.

:: 4. Verify requirements.txt
echo [4/6] Checking dependencies...
if not exist "requirements.txt" (
    echo [*] Creating requirements.txt...
    (
        echo # Jupiter TV - Video AI Engine
        echo torch^>=2.2.0
        echo torchvision^>=0.17.0
        echo numpy^>=1.24.0
        echo opencv-python^>=4.8.0
        echo tqdm^>=4.66.0
        echo basicsr^>=1.4.0
        echo realesrgan^>=0.3.0
        echo yt-dlp^>=2023.0.0
        echo requests^>=2.28.0
        echo Pillow^>=10.0.0
    ) > requirements.txt
    echo [OK] requirements.txt created
) else (
    echo [OK] requirements.txt found
)
echo.

:: 5. Install/Update dependencies
echo [5/6] Installing dependencies...
echo [*] This may take 10-20 minutes on first run...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed
    echo.
    echo Try manually:
    echo   python -m pip install -r requirements.txt -v
    echo.
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

:: 6. Create config template
echo [6/6] Creating configuration template...
if not exist "config\settings.py" (
    (
        echo # Jupiter TV - Video AI Engine Configuration
        echo.
        echo # Engine Settings
        echo ENGINE_NAME = "Jupiter Video AI"
        echo VERSION = "0.1.0"
        echo.
        echo # AI Model Settings
        echo MODEL_DEVICE = "cuda"  # or "cpu"
        echo MODEL_FP16 = True
        echo.
        echo # Processing Settings
        echo INPUT_DIR = "input"
        echo OUTPUT_DIR = "output"
        echo TEMP_DIR = ".temp"
        echo LOG_DIR = "logs"
        echo.
        echo # FFmpeg Settings
        echo FFMPEG_PRESET = "fast"  # ultrafast, fast, medium, slow
        echo VIDEO_CODEC = "libx264"
        echo AUDIO_CODEC = "aac"
        echo.
        echo # Upscaling
        echo UPSCALE_ENABLED = True
        echo UPSCALE_FACTOR = 4
        echo UPSCALE_MODEL = "RealESRGAN_x4plus"
        echo.
        echo # Scene Detection
        echo SCENE_DETECTION_ENABLED = True
        echo SCENE_THRESHOLD = 0.3
        echo.
        echo # Logging
        echo LOG_LEVEL = "INFO"
        echo LOG_FILE = "logs/engine.log"
    ) > config\settings.py
    echo [OK] Configuration template created
) else (
    echo [OK] Configuration exists
)
echo.

:: Verification
echo ========================================================
echo   SETUP COMPLETE!
echo ========================================================
echo.
echo Ready to use:
echo   - Scene detection: python -m engine.scene_detector
echo   - Video upscaling: python -m engine.upscaler
echo   - Full pipeline: python -m engine.pipeline
echo.
echo Directories:
echo   input/   - Place videos here
echo   output/  - Results saved here
echo   models/  - AI models cached here
echo   config/  - Configuration files
echo   logs/    - Process logs
echo.
echo Next steps:
echo   1. Edit config\settings.py if needed
echo   2. Place video files in input/ directory
echo   3. Run: python main.py
echo.
pause
