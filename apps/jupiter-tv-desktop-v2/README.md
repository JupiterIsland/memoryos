# Jupiter TV — Desktop Edition (DeepSeek V2)

This folder contains the desktop edition based on the jupiter.py UI.

Quick start
1. Create & activate a venv:
   python3 -m venv .venv
   source .venv/bin/activate
2. Install dependencies (root repo):
   pip install -r requirements.txt
3. Run the desktop UI:
   python apps/jupiter-tv-desktop-v2/jupiter.py

Demo CLI
   python apps/jupiter-tv-desktop-v2/demo_play.py "https://www.youtube.com/watch?v=..."

Notes
- The desktop edition uses QtMultimedia where available with an ffplay fallback.
- Replace Riva TTS stub with your Riva endpoint to enable speech commentary.
