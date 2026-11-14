# WINDOWS INSTALLER - TROUBLESHOOTING

## Error: "could not open requirements.txt"

### Cause
The installer/launcher cannot find `requirements-tv.txt` file.

### Solutions

**Solution 1: Run from Correct Directory**
```bash
# Make sure you're in the Jupiter TV root directory
cd C:\Users\YourName\Downloads\jupiter-tv
# OR wherever you extracted it

# Then run:
python windows-installer.py
# OR:
run-desktop.bat
```

**Solution 2: Check File Exists**
```bash
# Verify requirements-tv.txt exists
dir requirements-tv.txt

# If not found, you may need to clone/download the full repository
git clone <repo-url>
cd jupiter-tv
```

**Solution 3: Run Batch with Full Path**
```bash
# Instead of double-clicking, open Command Prompt and run:
cd "C:\path\to\jupiter-tv"
run-desktop.bat
```

**Solution 4: Use Absolute Path**
```bash
# Create a new batch file with absolute path:
@echo off
cd /d "C:\path\to\jupiter-tv"
python windows-installer.py
```

---

## Error: "Python not found"

### Solutions

**Install Python 3.11+**
1. Download from: https://www.python.org/downloads/
2. **IMPORTANT**: CHECK "Add Python to PATH" during installation
3. Restart Command Prompt
4. Verify: `python --version`

---

## Error: "Failed to install dependencies"

### Solutions

**Update pip first**
```bash
python -m pip install --upgrade pip
```

**Install with verbose output**
```bash
pip install -r requirements-tv.txt -v
```

**Check disk space**
```bash
# Make sure you have 5GB+ free disk space
```

**Try locked requirements**
```bash
pip install -r requirements-tv-locked.txt
```

---

## Error: "Module not found" (PyQt6, Kivy, etc.)

### Solutions

**Reinstall dependencies**
```bash
pip install --force-reinstall -r requirements-tv-locked.txt
```

**Check Python version**
```bash
python --version
# Should be 3.11+
```

---

## FFmpeg Warning

### Solution (Optional)
FFmpeg is optional. You can:

1. **Ignore the warning** — Scene detection will use fallback mode
2. **Install FFmpeg**:
   ```bash
   # Via Chocolatey
   choco install ffmpeg
   
   # Or download from
   https://ffmpeg.org/download.html
   ```

---

## Application Won't Start

### Check the Log
```bash
# Run with output captured
python apps/julius-tv-desktop-v2/app.py > output.log 2>&1

# View log
type output.log
```

### Common Issues
- PyQt6 not installed: `pip install PyQt6`
- Missing files: Download full repository
- Corrupt installation: Delete `__pycache__` folders and reinstall

---

## Quick Fix Steps (In Order)

1. **Close everything** (especially Python/pip processes)
2. **Run Command Prompt as Admin**
3. **Navigate to directory**: `cd C:\path\to\julius-tv`
4. **Verify files exist**: `dir requirements-tv.txt`
5. **Update pip**: `python -m pip install --upgrade pip`
6. **Reinstall deps**: `pip install -r requirements-tv-locked.txt`
7. **Try again**: `python windows-installer.py`

---

## Still Not Working?

### Create Manual Install Script
```bash
@echo off
cd /d "%~dp0"
echo Installing Jupiter TV...
python -m pip install --upgrade pip
pip install -r requirements-tv-locked.txt
echo Done. Press any key to launch...
pause
python apps/julius-tv-desktop-v2/app.py
```

Save as `install-and-run.bat`, then double-click.

---

## Contact Support

If issues persist:
1. Screenshot error message
2. Include output of: `python --version`
3. Include output of: `pip list`
4. Report on GitHub: [your-repo]/issues

---

**Status**: Common issues documented  
**Last Updated**: 2024
