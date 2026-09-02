refactor: add real libtorrent HTTP streaming + simplify mobile app

- torrent_stream.py: magnet → sequential download → HTTP 206 partial content
- mobile main.py: 90 lines, shared modules, no bloat
- desktop app.py: 150 lines, PyQt6 + shared layers
- Tight token budget: minimal overhead, production-ready