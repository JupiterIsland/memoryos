# Jupiter TV - Video AI Engine Setup Guide

## Quick Start

### 1. Run Setup Script
```bash
setup-video-ai.bat
```

This will:
- ✅ Check Python installation
- ✅ Check FFmpeg availability
- ✅ Create directory structure
- ✅ Install dependencies (PyTorch, OpenCV, RealESRGAN, etc.)
- ✅ Create configuration template

### 2. Place Videos
```
Copy video files to: input/
Supported formats: .mp4, .mkv, .avi, .mov, .flv
```

### 3. Run Processing
```bash
python main.py
```

Output saved to: `output/`

---

## What's Included

### Engine Modules
- **SceneDetector** — Detects scene boundaries using FFmpeg
- **VideoUpscaler** — Upscales videos 4x using RealESRGAN
- **VideoProcessingPipeline** — Orchestrates full workflow

### Directories Created
- `input/` — Place source videos here
- `output/` — Processed videos saved here
- `models/` — AI models cached here
- `config/` — Configuration files
- `logs/` — Process logs
- `engine/` — Core engine modules

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 |
| Python | 3.11+ |
| RAM | 8GB minimum (16GB recommended) |
| Disk | 20GB (for models + processing) |
| GPU | NVIDIA GPU with CUDA support (optional, CPU fallback available) |

---

## Installation Issues

### "Python not found"
```
1. Download Python 3.11+ from https://python.org
2. During install, CHECK "Add Python to PATH"
3. Restart setup-video-ai.bat
```

### "FFmpeg not found"
```
1. Download: https://ffmpeg.org/download.html
2. Or: choco install ffmpeg (if using Chocolatey)
Video processing will use FFmpeg if available
```

### Out of Memory
```
1. Reduce tile size in config\settings.py
2. Use CPU mode: MODEL_DEVICE = "cpu"
3. Process smaller videos first
```

### CUDA Out of Memory
```
If GPU out of memory:
1. Reduce tile size: TILE_SIZE = 256
2. Use CPU: MODEL_DEVICE = "cpu"
3. Close other GPU applications
```

---

## Configuration

Edit `config/settings.py`:

```python
# Device settings
MODEL_DEVICE = "cuda"  # "cuda" or "cpu"
MODEL_FP16 = True      # Use half precision for speed

# Upscaling
UPSCALE_FACTOR = 4     # 2, 3, or 4
UPSCALE_MODEL = "RealESRGAN_x4plus"

# Scene detection
SCENE_THRESHOLD = 0.3  # 0-1, higher = fewer scenes

# FFmpeg
FFMPEG_PRESET = "fast" # ultrafast, fast, medium, slow
```

---

## Usage Examples

### Basic Processing
```bash
python main.py
# Processes all videos in input/
```

### Programmatic Usage
```python
from engine import VideoProcessingPipeline

pipeline = VideoProcessingPipeline({
    "device": "cuda",
    "upscale_factor": 4,
})

result = pipeline.process_video(
    "input/video.mp4",
    "output/upscaled.mp4",
    detect_scenes=True,
    upscale=True
)

print(f"Detected {len(result['scenes'])} scenes")
```

### Batch Processing
```python
from engine import VideoProcessingPipeline

pipeline = VideoProcessingPipeline()

results = pipeline.process_batch(
    "input/",
    "output/",
    detect_scenes=True,
    upscale=True
)

for result in results:
    print(f"{result['input']}: {result['status']}")
```

---

## Performance Notes

### GPU Acceleration (Recommended)
- **Setup**: NVIDIA GPU + CUDA
- **Speed**: 10-30 FPS upscaling
- **Memory**: 6-8GB VRAM
- **Time**: ~20 minutes per hour of 1080p video

### CPU Processing (Slower)
- **Setup**: Any processor
- **Speed**: 0.5-2 FPS upscaling
- **Memory**: 16GB+ RAM
- **Time**: 2-6 hours per hour of 1080p video

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Black output video | Check input video format, try with CPU mode |
| Slow processing | Use GPU, reduce resolution, use "fast" preset |
| Model download fails | Check internet, increase timeout in code |
| OOM errors | Reduce tile size, use CPU mode, close other apps |

---

## What Happens During Setup

### Step 1: Directory Creation
Creates folders: input, output, models, config, logs, engine

### Step 2: Python Check
Verifies Python 3.11+ is installed and in PATH

### Step 3: FFmpeg Check
Optional; warns if FFmpeg not found but continues

### Step 4: Dependencies Installation
Installs via pip:
- PyTorch (300-500MB)
- OpenCV (100MB)
- RealESRGAN (50MB)
- Supporting libraries

**Total download**: ~1-2 GB  
**Total install time**: 10-20 minutes on first run

### Step 5: Configuration
Creates default settings in config/settings.py

---

## Next Steps

1. ✅ Run `setup-video-ai.bat`
2. ✅ Wait for dependencies to install
3. ✅ Place videos in `input/` folder
4. ✅ Run `python main.py`
5. ✅ Check results in `output/`

---

## Support

- Check setup output logs for errors
- Review `config/settings.py` for configuration options
- See troubleshooting section above for common issues

---

**Status**: ✅ Video AI Engine ready  
**Version**: 0.1.0  
**Last Updated**: 2024
