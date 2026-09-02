"""
Data models for Jupiter TV: channels, streams, config.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Channel:
    """Represents a playable stream channel."""

    name: str
    url: str
    type: str = "unknown"  # youtube, m3u, magnet, direct
    icon_url: Optional[str] = None

    def __repr__(self):
        return f"<Channel {self.name}>"


@dataclass
class StreamConfig:
    """Global stream configuration."""

    debrid_key: Optional[str] = None
    torrent_dir: str = "/tmp/jptv"
    commentary_enabled: bool = True
    max_channels: int = 50
    timeout: int = 15
