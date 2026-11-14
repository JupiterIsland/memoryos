# Jupiter TV - Windows Installation Guide

## Quick Install (Recommended)

### Option 1: GUI Installer
```bash
# Double-click: windows-installer.py
# Or from command line:
python windows-installer.py
```

Then:
1. Click "Install"
2. Wait for dependencies to install
3. Shortcuts appear on Desktop automatically
4. Launch "Jupiter Desktop.lnk" or "Jupiter Mobile.lnk"

### Option 2: Batch Script
```bash
# Desktop version
run-desktop.bat

# Mobile version
run-mobile.bat
```

### Option 3: Command Line
```bash
# Desktop
python apps/jupiter-tv-desktop-v2/app.py

# Mobile
python apps/jupiter-tv-mobile/main.py
```

---

## Prerequisites

### 1. Python 3.11+
```bash
# Check if installed
python --version

# Download from: https://www.python.org/downloads/
# During install, CHECK: "Add Python to PATH"
```

### 2. FFmpeg (Optional, for Real Scene Detection)
```bash
# Check if installed
ffmpeg -version

# Install via Chocolatey (if installed)
choco install ffmpeg

# Or Scoop
scoop install ffmpeg

# Or manual: https://ffmpeg.org/download.html
```

### 3. Git (Recommended)
```bash
# Download: https://git-scm.com/download/win
# Or: choco install git
```

---

## Installation Steps

### Step 1: Download
```bash
# Via Git (recommended)
git clone https://github.com/your-repo/jupiter-tv.git
cd jupiter-tv

# Or: Download ZIP from GitHub and extract
```

### Step 2: Install Dependencies
```bash
# Automatic (GUI installer)
python windows-installer.py

# Or manual:
pip install -r requirements-tv.txt
pip install -r requirements-tv-locked.txt
```

### Step 3: Verify Installation
```bash
python -c "from apps.shared.ai import SceneDetector; print('[OK] Scene detection ready')"
```

### Step 4: Run Application
```bash
# Desktop
run-desktop.bat

# Mobile
run-mobile.bat
```

---

## Troubleshooting

### "Python not found"
```
Error: Python not found
Solution: 
  1. Download Python 3.11+ from python.org
  2. Run installer
  3. CHECK: "Add Python to PATH"
  4. Restart command prompt
  5. Retry
```

### "Module not found" (PyQt6, Kivy, etc.)
```
Error: ModuleNotFoundError: No module named 'PyQt6'
Solution:
  python -m pip install --upgrade pip
  pip install -r requirements-tv-locked.txt
```

### "FFmpeg not found" (Scene Detection)
```
Warning: ffmpeg NOT found
Solution:
  1. Download from https://ffmpeg.org/download.html
  2. Extract to C:\ffmpeg
  3. Add to PATH:
     - Right-click Start Menu
     - System
     - Advanced system settings
     - Environment Variables
     - Add C:\ffmpeg\bin to PATH
  4. Restart command prompt
  5. Verify: ffmpeg -version
```

### "Port already in use"
```
Error: Address already in use
Solution:
  # Find process using port 11434 (Ollama)
  netstat -ano | findstr :11434
  
  # Kill process (replace PID with actual number)
  taskkill /PID <PID> /F
  
  # Or change port in docker-compose.julius.yml
```

### "Out of memory"
```
Error: MemoryError / OOM
Solution:
  1. Close other applications
  2. Increase available RAM
  3. Use lighter Ollama model: ollama pull mistral:7b
  4. Reduce resolution/quality settings
```

---

## Shortcuts

### Desktop Shortcuts
After installation, shortcuts appear at:
- Desktop: `Jupiter Desktop.lnk`, `Jupiter Mobile.lnk`
- Start Menu: `JupiterTV` folder

### Quick Launch
```
Win + R
type: %PROGRAMFILES%\JupiterTV\run-desktop.bat
press: Enter
```

---

## Configuration

### Environment Variables
Create `.env` file in JupiterTV folder:

```
# Torrent cache location
TORRENT_DIR=C:\Users\<YourUsername>\AppData\Local\Temp\jupiter-tv

# Ollama endpoint (if using Docker)
OLLAMA_HOST=http://localhost:11434

# FFmpeg path (if not in PATH)
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
```

---

## Docker Integration (Windows)

### Install Docker Desktop
```
Download: https://www.docker.com/products/docker-desktop
Then enable WSL2:
  1. Settings → Resources → WSL integration
  2. Enable integration with default distro
```

### Run Full Stack
```bash
# In PowerShell (admin)
docker compose -f docker-compose.julius.yml up
```

---

## Performance Tips

### For Slower Machines
```bash
# Use lightweight Ollama model
ollama pull mistral:7b

# Or disable AI features (scene detection fallback)
# Edit run-desktop.bat and add:
set OLLAMA_SKIP=1
```

### For Better Performance
```bash
# Install PyQt6 hardware acceleration
pip install PyQt6-OpenGL

# Use native Windows themes
set QT_STYLE_OVERRIDE=windowsvista
```

---

## Uninstall

### Via GUI Installer
```bash
# Run uninstaller
python windows-installer.py
# (Will show uninstall option)

# Or find in:
Control Panel → Programs → Programs and Features → Jupiter TV → Uninstall
```

### Manual Uninstall
```bash
# Remove folder
rmdir /s C:\Users\<Username>\AppData\Local\JupiterTV

# Remove shortcuts
del "%USERPROFILE%\Desktop\Jupiter*.lnk"

# Remove from Start Menu
rmdir /s "%APPDATA%\Microsoft\Windows\Start Menu\Programs\JupiterTV"

# Clean pip
pip uninstall -r requirements-tv.txt -y
```

---

## Getting Help

### Check Logs
```bash
# Logs are printed to console
# For persistent logging:
python run-desktop.bat > jupiter-desktop.log 2>&1

# View log file
type jupiter-desktop.log
```

### Test Installation
```bash
# Run test suite
python test_scene_detection_mvp.py

# Test stream manager
python -c "
from apps.shared import StreamManager
m = StreamManager()
print('[OK] Stream manager loaded')
"

# Test AI module
python -c "
from apps.shared.ai import SceneDetector
d = SceneDetector()
print('[OK] Scene detector loaded')
"
```

### GitHub Issues
Report issues at: https://github.com/your-repo/julius-tv/issues

---

## Advanced

### Command Line Options
```bash
# Desktop with debug output
python apps/julius-tv-desktop-v2/app.py --debug

# Mobile headless
python apps/julius-tv-mobile/main.py --headless

# Scene detection test
python apps/julius-tv-desktop-v2/app.py --test-detection /path/to/video.mp4
```

### Build Custom Installer
```bash
# Install NSIS
choco install nsis

# Build
makensis installer\JupiterTV.nsi

# Output: JupiterTV-v0.1.0-installer.exe
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 7 SP1 | Windows 10/11 |
| Python | 3.11 | 3.11+ |
| RAM | 4 GB | 8 GB |
| Disk | 2 GB | 10 GB |
| CPU | 2 cores | 4 cores |
| GPU | Not needed | Optional |

---

## FAQ

**Q: Can I use Jupiter TV without FFmpeg?**  
A: Yes, but scene detection will use uniform chunks fallback instead of real shot detection.

**Q: Does it work with VPN?**  
A: Yes, but torrent streaming may be blocked by some VPNs. Try with VPN disabled.

**Q: Can I use it on multiple PCs?**  
A: Yes, install on each machine. Settings are per-machine in `%APPDATA%\JupiterTV`.

**Q: Is it safe?**  
A: All processing is local (no data sent to cloud). Torrent streaming is private (between you and peers).

**Q: How do I update?**  
A: Pull latest from GitHub: `git pull`  
Then reinstall deps: `pip install -r requirements-tv-locked.txt`

---

## Support

- **Documentation**: https://github.com/your-repo/julius-tv/wiki
- **Issues**: https://github.com/your-repo/julius-tv/issues
- **Discord**: https://discord.gg/your-invite
- **Email**: support@julius-tv.dev

---

**Status**: ✅ Windows installer complete  
**Version**: v0.1.0  
**Last Updated**: 2024
