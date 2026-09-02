#!/usr/bin/env python3
"""
Streamlined stream resolution engine with HTTP torrent streaming.
Handles: YouTube, magnet links, torrent, HLS, direct URLs.
"""

import os
import time
try:
    import libtorrent as lt
except ImportError:
    lt = None

from yt_dlp import YoutubeDL
import requests
from .torrent_stream import TorrentStreamer


class StreamManager:
    """Unified stream resolver for all input types."""

    def __init__(self, debrid_key=None, torrent_dir="/tmp/jptv"):
        self.debrid_key = debrid_key
        self.torrent_dir = torrent_dir
        self.torrent_streamer = TorrentStreamer(save_path=torrent_dir)
        os.makedirs(torrent_dir, exist_ok=True)

    def resolve(self, url):
        """Auto-detect input type and resolve to playable URL/path."""
        if url.startswith("magnet:") or url.endswith(".torrent"):
            return self._resolve_torrent(url)
        else:
            return self._resolve_generic(url)

    def _resolve_torrent(self, url):
        """Resolve magnet/torrent using Real-Debrid, HTTP streaming, or libtorrent."""
        if self.debrid_key:
            return self._debrid_unrestrict(url)
        elif url.startswith("magnet:"):
            # Use HTTP streaming for immediate playback while downloading
            return self.torrent_streamer.stream_magnet(url)
        else:
            raise RuntimeError("No torrent backend: install libtorrent or set debrid_key")

    def _debrid_unrestrict(self, link):
        """Real-Debrid unrestriction (magnet/torrent → direct URL)."""
        headers = {"Authorization": f"Bearer {self.debrid_key}"}
        resp = requests.post(
            "https://api.real-debrid.com/rest/1.0/unrestrict/link",
            data={"link": link},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("download") or data.get("streaming") or data

    def _resolve_generic(self, url):
        """YouTube/HLS/direct URL → playable URL."""
        ydl_opts = {"quiet": True, "no_warnings": True, "format": "best"}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "url" in info:
                return info["url"]
            formats = info.get("formats") or []
            if formats:
                best = max(formats, key=lambda f: f.get("height") or 0)
                return best.get("url")
            return url
