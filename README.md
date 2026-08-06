# 📺 Jupiter TV — AI‑Powered IPTV & Torrent Client

This repository contains the initial scaffold for "Jupiter TV": a rebrand and productized fork of Jupiter One focused on AI‑enhanced media streaming (IPTV, magnet/torrent links, YouTube/HLS) with a local LLM "TV technician" and Riva TTS voice output.

Quick start

1. Create and activate a Python virtualenv:
   python3 -m venv .venv
   source .venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app (development):
   ./start.sh

What’s included (minimal scaffold)
- src/jupiter_tv.py — process launcher (FastAPI + PyQt6)
- src/stream_manager.py — stream resolution: Real‑Debrid, libtorrent fallback, yt-dlp
- src/ai/technician.py — local LLM wrapper (stub)
- src/tts/riva_stub.py — Riva TTS stub (integration placeholder)
- src/ui/settings_stub.py — PyQt6 Settings widget stub
- README, LICENSE, .gitignore, CHANGELOG

Notes
- This is a scaffold and intentionally light; configure Real‑Debrid tokens and Riva endpoints before use.
- Do not commit secrets or API keys. Keep any production endpoints behind auth and HTTPS.

Next steps
- Test locally with a sample M3U / magnet link and a local LLM endpoint.
- I can follow up with a PR that adds a systemd unit, .deb packaging, and CI if you want.
