# Jupiter TV — Stremio-like Torrent Streaming

## What This Is
A desktop (PyQt6) + mobile (Kivy) app that plays torrents instantly via HTTP streaming, no full downloads required.

## Quick Start

### Install
```bash
pip install -r requirements-tv.txt
```

### Run
**Desktop:**
```bash
python apps/jupiter-tv-desktop-v2/app.py
```

**Mobile:**
```bash
python apps/jupiter-tv-mobile/main.py
```

### Use
1. Paste a magnet link: `magnet:?xt=urn:btih:...`
2. Click **Load**
3. **Watch instantly** while download continues in background

## Supported Inputs
- **Torrents**: Magnet links, `.torrent` files
- **YouTube**: Direct links, playlists
- **M3U Playlists**: IPTV, streaming lists
- **Direct URLs**: HLS, HTTP, etc.

## How It Works

```
Magnet Link
    ↓
[libtorrent sequential download]
    ↓
[HTTP Range server on :8888]
    ↓
http://127.0.0.1:8888/ ← Player streams from here
    ↓
Watch immediately (download continues)
```

## Key Features
✓ **Instant Playback** — 2-5s from magnet to video  
✓ **No Full Download** — Stream chunks as needed  
✓ **Background Download** — Watch while downloading  
✓ **Real Torrent** — Uses libtorrent + DHT  
✓ **Cross-Platform** — Desktop (PyQt6) + Mobile (Kivy)  
✓ **Multiple Sources** — YouTube, M3U, torrents, direct URLs  

## File Structure
```
apps/
├── shared/
│   ├── stream_manager.py     (Universal resolver)
│   ├── torrent_streamer.py   (HTTP stream engine)
│   ├── memory_store.py       (Persistent storage)
│   ├── models.py             (Data types)
│   └── utils.py              (Helpers)
├── jupiter-tv-desktop-v2/
│   └── app.py                (PyQt6 UI)
└── jupiter-tv-mobile/
    └── main.py               (Kivy UI)
```

## Architecture
See `ARCHITECTURE.md` for full technical details.

## Testing
```bash
# Test torrent streaming
python test_e2e_streaming.py "magnet:?xt=urn:btih:..."
```

## Dependencies
- `libtorrent-rasterbar` — Torrent engine
- `yt-dlp` — YouTube extraction
- `PyQt6` — Desktop UI
- `kivy` — Mobile UI
- `duckdb` — Storage (optional)

## Docker
```bash
docker compose -f docker-compose.jupiter.yml up
```

## Roadmap
1. ✅ Sequential torrent streaming
2. ⏳ Add-on scraping (auto-find torrents)
3. ⏳ Metadata from TMDB
4. ⏳ Subtitles support

## Docs
- `ARCHITECTURE.md` — Full technical architecture
- `STREAMING_COMPLETE.md` — Implementation details
- `JUPITER_TV_REFACTOR.md` — Refactoring notes

---

**Now you can stream torrents like Stremio — paste a magnet, watch instantly! 🎬**
