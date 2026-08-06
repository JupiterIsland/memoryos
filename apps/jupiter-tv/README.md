# Jupiter TV (DeepSeek-V3) — App README

This directory contains the Jupiter TV desktop & mobile demos (DeepSeek‑V3). Jupiter TV is an AI‑enhanced media client that provides Live AI Contextual Commentary (voice or text) alongside video/audio streams. The features are intentionally modular so you can swap the LLM, TTS, or stream backend.

Quick highlights
- Live AI Commentary (novel): on‑the‑fly, locally generated facts and commentary synchronized with playback.
- Stream resolution: YouTube (yt‑dlp), HTTP/HLS, magnet -> Real‑Debrid or libtorrent fallback.
- MemoryOS: DuckDB local store for user preferences and commentary history.
- Mobile: Kivy + Buildozer Fire TV app with D‑pad navigation and M3U parser.

Demo (desktop)
1. Create and activate a Python venv:
   python3 -m venv .venv
   source .venv/bin/activate
2. Install dependencies (root repo):
   pip install -r requirements.txt
3. Run the full desktop demo (if present):
   python src/jupiter_tv.py
4. Or run the app in the apps folder:
   pip install -r apps/jupiter-tv/requirements.txt
   python apps/jupiter-tv/src/jupiter_tv.py

Notes
- Riva TTS is shipped as a stub (apps/jupiter-tv/src/tts/riva_stub.py). Replace with your Riva gRPC client to enable voice.
- For torrent streaming we recommend Real‑Debrid token for the best UX; otherwise enable libtorrent on the host.
- Do not commit API keys into the repo — use the local config (~/.config/jupitertv/config.json) or MemoryOS.

License
MIT — see the repository LICENSE file.
