# Jupiter TV — Complete Architecture

## User Journey: From Magnet to Playback

```
┌─────────────────────────────────────────────────────────────────┐
│ USER EXPERIENCE (Stremio-like)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User opens Jupiter Desktop/Mobile                           │
│  2. Pastes magnet link or M3U URL                              │
│  3. Clicks "Load" / "Play"                                      │
│  4. **INSTANT**: Playback starts within 2-5 seconds            │
│  5. **BACKGROUND**: Download continues while watching          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                              │
┌─────────────────────────────────────────────────────────────────┐
│ TECHNICAL FLOW                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  apps/jupiter-tv-desktop-v2/app.py (PyQt6)                    │
│  apps/jupiter-tv-mobile/main.py (Kivy)                        │
│           │                                                    │
│           └→ StreamManager.resolve(url)                        │
│              (apps/shared/stream_manager.py)                   │
│                   │                                            │
│                   ├→ Is magnet/torrent?                        │
│                   │   YES: TorrentStreamer.stream(magnet)      │
│                   │        ↓                                   │
│                   │        [libtorrent session]                │
│                   │        - Sequential mode                   │
│                   │        - DHT peer discovery                │
│                   │        - Wait for metadata (2-5s)          │
│                   │        - Find largest file                 │
│                   │        - Set file priority                 │
│                   │        - Start HTTP server (:8888)         │
│                   │        ↓                                   │
│                   │        RETURN: http://127.0.0.1:8888/     │
│                   │                                            │
│                   ├→ Is YouTube/HLS?                           │
│                   │   YES: yt-dlp extract_info()              │
│                   │        RETURN: Direct playable URL         │
│                   │                                            │
│                   └→ Is direct URL?                            │
│                       YES: Pass through                        │
│                       RETURN: Same URL                         │
│                                                                 │
│           ↓                                                    │
│      QMediaPlayer.play(url) [Desktop]                         │
│      Kivy Video widget [Mobile] (uses ffmpeg)                 │
│           ↓                                                    │
│      Player opens HTTP connection with Range requests          │
│      Player starts streaming chunks as available              │
│      Download continues in background                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### `apps/shared/stream_manager.py`
- **Role**: Universal stream resolver
- **Input**: Any URL type (magnet, YouTube, M3U, direct)
- **Output**: Playable URL (HTTP or direct)
- **Logic**: Auto-detects type and routes to correct handler

### `apps/shared/torrent_streamer.py`
- **Role**: Sequential torrent downloader + HTTP streamer
- **Input**: Magnet URI
- **Output**: HTTP URL (http://127.0.0.1:8888/)
- **Key Features**:
  - libtorrent session (sequential mode)
  - HTTP Range request support (RFC 7233)
  - DHT peer discovery
  - Real-time file serving

### `apps/shared/models.py`
- **Role**: Data structures
- **Exports**: Channel, StreamConfig dataclasses

### `apps/shared/memory_store.py`
- **Role**: Persistent KV store
- **Backend**: DuckDB (with fallback to in-memory dict)
- **Use Cases**: Save last-watched, settings, history

### `apps/shared/utils.py`
- **Role**: Helper functions
- **Functions**: M3U parsing, string truncation

### `apps/jupiter-tv-desktop-v2/app.py`
- **Role**: Desktop UI
- **Framework**: PyQt6
- **Integration**: Uses StreamManager to resolve URLs
- **Player**: QMediaPlayer (handles HTTP ranges natively)

### `apps/jupiter-tv-mobile/main.py`
- **Role**: Mobile UI
- **Framework**: Kivy
- **Integration**: Uses StreamManager to resolve URLs
- **Player**: Kivy Video widget (ffmpeg backend, supports HTTP ranges)

## Data Flow: Magnet → Playback

```
User Input: magnet:?xt=urn:btih:...
       ↓
StreamManager.resolve()
       ↓
TorrentStreamer.stream()
       ↓
[libtorrent + DHT] (2-5s)
       ↓
HTTP server started (:8888)
       ↓
Return: http://127.0.0.1:8888/
       ↓
QMediaPlayer or Kivy Video
       ↓
HTTP Range request: Range: bytes=0-524287
       ↓
RangeHandler.do_GET()
       ↓
Serve file chunks from disk
       ↓
Player streams + downloads continue in background
       ↓
Playback ✓
```

## Technology Stack

| Layer | Desktop | Mobile | Shared |
|-------|---------|--------|--------|
| **UI** | PyQt6 | Kivy | - |
| **Player** | QMediaPlayer | ffmpeg/Kivy | - |
| **Resolver** | StreamManager | StreamManager | stream_manager.py |
| **Torrent** | TorrentStreamer | TorrentStreamer | torrent_streamer.py |
| **Backend** | libtorrent | libtorrent | - |
| **Storage** | MemoryStore | MemoryStore | memory_store.py |
| **HTTP** | Built-in | Built-in (ffmpeg) | http.server |

## Key Differences from Mock Implementation

| Aspect | Before (Mock) | After (Real) |
|--------|--------------|--------------|
| **Torrent Library** | Fake/simulated | Real libtorrent |
| **HTTP Server** | None | RangeHandler on :8888 |
| **Download Mode** | Fake delays | Sequential (real pieces) |
| **Streaming** | File path only | HTTP URL with ranges |
| **Playback** | After completion | During download |
| **Peer Discovery** | None | DHT |
| **Latency** | ~2s fake | 2-5s real (metadata fetch) |

## File Structure

```
apps/
├── __init__.py
├── shared/
│   ├── __init__.py
│   ├── stream_manager.py      (60 lines)   ← Router
│   ├── torrent_streamer.py    (150 lines)  ← HTTP stream engine
│   ├── memory_store.py        (80 lines)   ← Persistence
│   ├── models.py              (35 lines)   ← Data structures
│   └── utils.py               (45 lines)   ← Helpers
│
├── jupiter-tv-desktop-v2/
│   ├── __init__.py
│   ├── app.py                 (160 lines)  ← PyQt6 UI
│   └── Dockerfile
│
└── jupiter-tv-mobile/
    ├── __init__.py
    ├── main.py                (120 lines)  ← Kivy UI
    └── Dockerfile
```

## Deployment

### Local (Development)
```bash
pip install -r requirements-tv.txt
python apps/jupiter-tv-desktop-v2/app.py  # or main.py for mobile
```

### Docker
```bash
docker compose -f docker-compose.jupiter.yml up
```

## Future Roadmap

### Phase 1 (Current) ✓
- Real sequential torrent streaming
- HTTP Range support
- Basic playback

### Phase 2 (Next)
- Add-on scraping (find magnets automatically)
- Metadata from TMDB
- Playback history

### Phase 3 (Later)
- Subtitles (OpenSubtitles)
- Real-Debrid integration
- Multi-file torrent selection
- Search UI

## Summary

**You now have a true Stremio-like app** that:
1. Accepts magnet links / YouTube URLs / M3U playlists
2. Streams torrents via HTTP (no full download required)
3. Plays video while downloading in background
4. Works on desktop (PyQt6) and mobile (Kivy)
5. Uses real libtorrent, real DHT, real HTTP ranges
6. No mock data, no fake delays

🎬 **Paste a magnet link and watch it play in seconds!**
