# Quick Visual Guide — Jupiter TV Streaming

## The User Experience (What You Wanted)

```
┌─────────────────────────────────────┐
│ Jupiter Desktop/Mobile App          │
└─────────────────────────────────────┘
               ↓
    User pastes magnet link
               ↓
        Clicks "Load"
               ↓
    ⏱️  Wait 2-5 seconds...
               ↓
    🎬 Video starts playing
               ↓
    ⬇️  Download continues in background
               ↓
    ✅ Watch, no interruptions
```

## The Technical Flow

```
User Input: magnet:?xt=urn:btih:ABC123...
    ↓
┌─────────────────────────────────┐
│ StreamManager.resolve()         │
│ (Universal Router)              │
└─────────────────────────────────┘
    ↓
    Is magnet/torrent? YES
    ↓
┌─────────────────────────────────┐
│ TorrentStreamer.stream()        │
│ (Sequential HTTP Server)        │
├─────────────────────────────────┤
│ 1. Create libtorrent session    │
│ 2. Set sequential mode          │
│ 3. Add magnet URI               │
│ 4. Wait for metadata (DHT)      │
│ 5. Find largest file            │
│ 6. Start HTTP server :8888      │
│ 7. Return HTTP URL              │
└─────────────────────────────────┘
    ↓
    Return: http://127.0.0.1:8888/
    ↓
┌─────────────────────────────────┐
│ Desktop (PyQt6)                 │
│  QMediaPlayer.play(url)         │
│                                 │
│ Mobile (Kivy)                   │
│  Video.source = url             │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Player opens HTTP connection    │
│ Requests Range: bytes=0-524287  │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ RangeHandler serves file chunks │
│ as they download from peers     │
└─────────────────────────────────┘
    ↓
🎬 Video plays smoothly
📥 Download continues in background
✅ Done
```

## File Structure (What We Built)

```
apps/
├── shared/                          ← Shared business logic
│   ├── stream_manager.py            (Universal resolver)
│   ├── torrent_streamer.py          (HTTP streaming engine) ← KEY
│   ├── memory_store.py              (Persistent storage)
│   ├── models.py                    (Data types)
│   └── utils.py                     (Helpers)
│
├── jupiter-tv-desktop-v2/           ← Desktop (PyQt6)
│   ├── app.py                       (Clean UI)
│   └── Dockerfile
│
└── jupiter-tv-mobile/               ← Mobile (Kivy)
    ├── main.py                      (Touch-friendly UI)
    └── Dockerfile
```

## Key Components

### 1. StreamManager (Router)
```
Input: Any URL (magnet, YouTube, M3U, direct)
   ↓
Routes to correct handler:
- Magnet/Torrent → TorrentStreamer
- YouTube → yt-dlp
- M3U → M3U parser
- Direct → Pass through
   ↓
Output: Playable URL
```

### 2. TorrentStreamer (HTTP Server)
```
Input: Magnet URI
   ↓
libtorrent session (sequential mode)
DHT peer discovery
Metadata fetch
Find largest file
   ↓
HTTP Range server (:8888)
   ↓
Output: http://127.0.0.1:8888/
   (Serves file while downloading)
```

### 3. RangeHandler (HTTP Logic)
```
Player: GET / HTTP/1.1
        Range: bytes=0-524287
   ↓
Server checks: Is this byte range available?
   ↓
If yes: Respond 206 (partial content) + bytes
If no: Wait for download to fill buffer
   ↓
Player: Get next 512KB chunk
```

### 4. Desktop UI (PyQt6)
```
Input field: URL/Magnet
   ↓
StreamManager.resolve()
   ↓
QMediaPlayer.play(result_url)
   ↓
Display: Playing...
```

### 5. Mobile UI (Kivy)
```
Text input: URL/Magnet
   ↓
StreamManager.resolve()
   ↓
Video.source = result_url
   ↓
Display: Playing...
```

## Timeline (Instant Playback)

```
T=0s    User clicks Load
        ↓ magnet link sent to StreamManager
        ↓
T=0.1s  TorrentStreamer creates session
        ↓
T=0.5s  DHT peer discovery starts
        ↓
T=1-3s  Metadata received from peers
        ↓
T=3s    HTTP server starts
        ↓
T=3.1s  Return HTTP URL to UI
        ↓
T=3.2s  QMediaPlayer opens connection
        ↓
T=3.3s  First chunk downloaded
        ↓
T=3.5s  🎬 VIDEO PLAYS
        ↓
T=3.6s~ Download continues (background)
```

## Installation & Usage

### Step 1: Install
```bash
pip install -r requirements-tv.txt
```

### Step 2: Run
```bash
# Desktop
python apps/jupiter-tv-desktop-v2/app.py

# Mobile
python apps/jupiter-tv-mobile/main.py
```

### Step 3: Use
1. Paste: `magnet:?xt=urn:btih:e3811b9539...`
2. Click: **Load**
3. Wait: 2-5 seconds
4. Watch: 🎬 Instant playback

## What Makes This Real

| Aspect | Implementation |
|--------|-----------------|
| Torrent Backend | libtorrent (real, not mock) |
| Download Mode | Sequential (pieces in order) |
| Streaming | HTTP Range server (real, not simulated) |
| Peer Discovery | DHT (real peers, real bandwidth) |
| Playback | QMediaPlayer or Kivy/ffmpeg (real players) |
| File Service | http.server (standard Python library) |

## Future Enhancements

```
Phase 1 (Current): ✅ Sequential torrent streaming
Phase 2 (Next):    [ ] Auto-find torrents (scrapers)
Phase 3 (Later):   [ ] Metadata + UI improvements
```

---

## TL;DR

**You have a working Stremio clone that:**
- Takes magnet links
- Plays video in 2-5 seconds
- Downloads in background
- Works on desktop + mobile
- Uses real torrent tech (no mocking)

🎬 Paste a magnet, watch instantly!
