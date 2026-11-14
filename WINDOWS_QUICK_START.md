# WINDOWS QUICK START - Fix "requirements.txt" Error

## The Problem
"Error: could not open requirements.txt"

## The Solution

### Step 1: Download & Extract (If You Haven't Already)
```
1. Download Jupiter TV (ZIP file)
2. Extract to: C:\Users\YourName\Downloads\jupiter-tv
   (or anywhere you prefer)
```

### Step 2: Run Setup Script
```
1. Navigate to the extracted folder
2. Double-click: setup.bat
   (This handles everything automatically)
```

### Step 3: Run the App
```
After setup completes, you can now run:

Desktop:  Double-click run-desktop.bat
Mobile:   Double-click run-mobile.bat

Or use Command Prompt:
  cd C:\path\to\julius-tv
  run-desktop.bat
```

---

## If You Still Get an Error

### Check 1: Make Sure You're in the Right Folder
```
The file should be in the same folder as these files:
- setup.bat
- run-desktop.bat
- run-mobile.bat
- requirements-tv.txt  ← This must exist here
- apps/ (folder)
```

### Check 2: Verify the File Exists
```
Open Command Prompt and type:
  cd C:\path\to\julius-tv
  dir requirements-tv.txt

If it shows the file, great!
If "File not found", you may not have extracted properly.
```

### Check 3: Re-extract the Archive
```
1. Download the ZIP again
2. Right-click → Extract All
3. Make sure ALL files are extracted (not just some)
4. You should see these items in the extracted folder:
   - apps/ (folder with many files)
   - requirements-tv.txt (file)
   - run-desktop.bat (file)
   - setup.bat (file)
```

### Check 4: Run Manual Install
```
1. Open Command Prompt (as Admin)
2. Navigate: cd C:\path\to\julius-tv
3. Run: pip install -r requirements-tv.txt
4. Wait for it to complete
5. Then: python apps/julius-tv-desktop-v2/app.py
```

---

## Still Having Issues?

### Verify Python Works
```
Open Command Prompt and type:
  python --version

Should show: Python 3.11.x or higher

If it says "Python is not recognized":
  1. Reinstall Python from https://python.org
  2. CHECK "Add Python to PATH" during install
  3. Restart Command Prompt
  4. Try again: python --version
```

### Check File Permissions
```
Right-click requirements-tv.txt
Properties → Security
Make sure your user has "Read" permission

If not:
  1. Click Edit
  2. Select your username
  3. Check "Full Control"
  4. Click Apply
```

### Try Alternative Method
```
1. Open Command Prompt (as Admin)
2. cd C:\path\to\julius-tv
3. Run these commands one by one:
   python -m pip install --upgrade pip
   pip install yt-dlp
   pip install requests
   pip install duckdb
   pip install PyQt6
   pip install PyQt6-Multimedia
   pip install kivy
   pip install libtorrent-rasterbar
   pip install faster-whisper
   pip install ollama
   pip install scenedetect

4. Then: python apps/julius-tv-desktop-v2/app.py
```

---

## Step-by-Step for Complete Beginners

### First Time Setup

**Step 1: Install Python**
- Go to: https://www.python.org/downloads/
- Click "Download Python 3.11" (or latest)
- Run installer
- **IMPORTANT**: CHECK the box "Add Python to PATH"
- Click "Install Now"
- Wait for completion

**Step 2: Extract Jupiter TV**
- Download: `jupiter-tv.zip`
- Right-click → Extract All
- Choose: `C:\Users\YourName\Downloads\`
- Click Extract
- Wait for it to complete

**Step 3: Run Setup**
- Open the extracted `julius-tv` folder
- Double-click: `setup.bat`
- A Command Prompt window opens
- Wait for it to say "SETUP COMPLETE!"
- Press any key

**Step 4: Run the App**
- In the same folder, double-click: `run-desktop.bat`
- Jupiter Desktop should open!

---

## File Locations

Make sure your folder structure looks like this:

```
julius-tv/
├── setup.bat                    ← Run this first
├── run-desktop.bat              ← Then this
├── run-mobile.bat
├── requirements-tv.txt          ← THIS IS IMPORTANT
├── requirements-tv-locked.txt
├── docker-compose.julius.yml
├── windows-installer.py
├── apps/
│   ├── shared/
│   ├── julius-tv-desktop-v2/
│   └── julius-tv-mobile/
└── (other files)
```

---

## Troubleshooting Commands

```bash
# Check if Python installed
python --version

# Check if pip works
pip --version

# Check if requirements file exists
dir requirements-tv.txt

# Check current folder
cd

# Manually install all dependencies
pip install -r requirements-tv.txt -v

# Check what's installed
pip list
```

---

## FAQ

**Q: "Python is not recognized"**  
A: Python not installed. Download from https://python.org and CHECK "Add Python to PATH"

**Q: "requirements-tv.txt: No such file or directory"**  
A: You're not in the right folder. Make sure you're in the julius-tv root folder where setup.bat is located.

**Q: "Permission denied"**  
A: Run Command Prompt as Admin. Right-click → "Run as Administrator"

**Q: "pip is not recognized"**  
A: Python PATH not set. Restart Command Prompt after installing Python and checking "Add Python to PATH"

**Q: Installation takes forever**  
A: First install is slow. It's downloading and compiling dependencies. Can take 10-30 minutes. Don't close the window.

**Q: Setup completes but app won't start**  
A: Try: `python apps/julius-tv-desktop-v2/app.py` to see the actual error

---

## Need More Help?

See the full guide: `WINDOWS_INSTALLATION_GUIDE.md`

Or check: `WINDOWS_INSTALLER_TROUBLESHOOTING.md`

---

**If all else fails:**
```
1. Delete julius-tv folder
2. Download again
3. Extract to fresh location
4. Run setup.bat
5. Should work!
```

Good luck! 🚀
