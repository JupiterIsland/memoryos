# Jupiter TV — Quick Demo Steps (Live Commentary)

This file shows the minimal steps to demo the Live AI Commentary feature locally.

1) Prepare environment
- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r apps/jupiter-tv/requirements.txt

2) Start a local LLM or use a stub
- Either run your local LLM HTTP endpoint (e.g., Ollama, Llama‑cpp web UI) and point the app to it, or use the default stubbed commentator which returns canned facts.

3) Run the app
- python apps/jupiter-tv/src/jupiter_tv.py

4) Paste a YouTube URL, HLS link, or magnet (if libtorrent is installed)
- Click LOAD
- Commentary appears in the log area; if voice is enabled and Riva is configured, commentary will be spoken.

5) Toggling & Settings
- Open Settings and set your Real‑Debrid token (optional) and toggle commentary/voice.

Troubleshooting
- If yt‑dlp fails to extract a stream, try a different format or provide the direct HLS URL.
- If libtorrent fails to install on your system, use Real‑Debrid for magnet links or test with HTTP/HLS streams.

Privacy & Legal
- Jupiter TV is a client application. Users are responsible for the content they play. Add a Terms of Service if you plan to distribute widely.
