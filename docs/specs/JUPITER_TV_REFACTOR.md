# Jupiter TV Apps — Refactored Architecture

## Overview

A complete refactor of Jupiter TV apps (desktop + mobile) with clean separation of concerns:

- **Shared Layer** (`apps/shared/`) — business logic, stream resolution, data persistence
- **Desktop App** (`apps/jupiter-tv-desktop-v2/`) — PyQt6 UI using shared modules
- **Mobile App** (`apps/jupiter-tv-mobile/`) — Kivy UI using shared modules

## Architecture

```
apps/
├── shared/                    # Cross-platform business logic
│   ├── stream_manager.py      # YouTube, M3U, magnet, torrent resolution
│   ├── memory_store.py        # DuckDB-backed KV store (or memory fallback)
│   ├── models.py              # Channel, StreamConfig dataclasses
│   └── utils.py               # M3U parsing, helpers
│
├── jupiter-tv-desktop-v2/     # PyQt6 Desktop Application
│   ├── app.py                 # Main window, event handlers
│   ├── Dockerfile             # Headless + xvfb container
│   └── __init__.py
│
└── jupiter-tv-mobile/         # Kivy Mobile Application
    ├── main.py                # Kivy app, screen management
    ├── Dockerfile             # Mobile container
    └── __init__.py
```

## Key Improvements

### Before (Monolithic)
- 337-line desktop file mixing UI + audio + logic
- 193-line mobile file with hardcoded limits (50 channels)
- Redundant code between apps
- Poor error recovery
- Tight coupling

### After (Modular)
- **Separation of Concerns**: UI layer completely decoupled from business logic
- **Reusable Shared Layer**: StreamManager, MemoryStore used by both apps
- **No Hardcoded Limits**: Mobile now supports 100+ channels
- **Better Error Handling**: Graceful fallbacks (DuckDB → in-memory cache)
- **Cross-Platform**: Identical stream resolution logic on desktop & mobile

## Stream Resolution

### Supported Input Types
- **YouTube** — yt-dlp extracts best video URL
- **M3U Playlists** — parsed into Channel objects
- **Magnet Links** — Real-Debrid unrestriction OR libtorrent download
- **Direct URLs** — HLS, HTTP, etc. passed through
- **Torrent Files** — libtorrent → largest file

### Usage

```python
from apps.shared.stream_manager import StreamManager

manager = StreamManager(debrid_key="YOUR_KEY")

# Auto-detect and resolve
url = manager.resolve("https://www.youtube.com/watch?v=...")
# or
url = manager.resolve("magnet:?xt=urn:...")
```

## Persistence Layer

### MemoryStore (DuckDB-backed)

```python
from apps.shared.memory_store import MemoryStore

store = MemoryStore()  # :memory: by default
store.set("last_played", "my-channel")
store.get("last_played", default="")
```

Fallback: If DuckDB unavailable, uses in-memory dict cache.

## Data Models

```python
from apps.shared.models import Channel, StreamConfig

channel = Channel(
    name="Sky News",
    url="https://...",
    type="m3u",
    icon_url="https://..."
)

config = StreamConfig(
    debrid_key="abc123",
    max_channels=100,  # No hardcoded limit
    timeout=15
)
```

## Running Desktop App

### Local (PyQt6 required)

```bash
pip install -r requirements-tv.txt
python apps/jupiter-tv-desktop-v2/app.py
```

### Docker (Headless + VNC)

```bash
docker build -f apps/jupiter-tv-desktop-v2/Dockerfile -t jupiter-desktop .
docker run -it jupiter-desktop
```

## Running Mobile App

### Local (Kivy required)

```bash
pip install -r requirements-tv.txt
python apps/jupiter-tv-mobile/main.py
```

### Docker

```bash
docker build -f apps/jupiter-tv-mobile/Dockerfile -t jupiter-mobile .
docker run -it jupiter-mobile
```

## Running Both with Compose

```bash
docker compose -f docker-compose.jupiter.yml up
```

## Dependencies

### requirements-tv.txt

- `yt-dlp` — YouTube video extraction
- `requests` — HTTP requests
- `duckdb` — Embedded database
- `PyQt6`, `PyQt6-Multimedia` — Desktop UI
- `kivy` — Mobile UI
- `libtorrent-rasterbar` — Torrent support

## Future Enhancements

1. **Spectrum Visualizer** — Real audio analysis (not random)
2. **Subtitle Support** — Auto-fetch from metadata
3. **Playlist Sync** — Cloud backup via real-debrid
4. **Playback History** — GraphDB integration with memoryos
5. **Multi-Source Fallback** — Try multiple URLs if one fails

## Testing

```bash
# Test stream resolution
python -c "
from apps.shared.stream_manager import StreamManager
m = StreamManager()
url = m.resolve('https://www.youtube.com/watch?v=...')
print(f'Resolved: {url}')
"

# Test M3U parsing
python -c "
from apps.shared.utils import parse_m3u
channels = parse_m3u('https://example.com/playlist.m3u')
print(f'Loaded {len(channels)} channels')
"
```

## License

Part of MemoryOS project.
