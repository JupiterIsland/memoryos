"""
Shared utilities for Jupiter TV apps (desktop + mobile).
Provides: stream resolution, memory persistence, data models.
"""

# Lazy imports to avoid circular deps

def __getattr__(name):
    if name == "StreamManager":
        from .stream_manager import StreamManager
        return StreamManager
    elif name == "TorrentStreamer":
        from .torrent_streamer import TorrentStreamer
        return TorrentStreamer
    elif name == "MemoryStore":
        from .memory_store import MemoryStore
        return MemoryStore
    elif name == "Channel":
        from .models import Channel
        return Channel
    elif name == "StreamConfig":
        from .models import StreamConfig
        return StreamConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["StreamManager", "TorrentStreamer", "MemoryStore", "Channel", "StreamConfig"]
