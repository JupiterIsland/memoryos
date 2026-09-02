"""
Streamlined stream resolution engine.
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


class StreamManager:
    """Unified stream resolver for all input types."""

    def __init__(self, debrid_key=None, torrent_dir="/tmp/jptv"):
        self.debrid_key = debrid_key
        self.torrent_dir = torrent_dir
        os.makedirs(torrent_dir, exist_ok=True)

    def resolve(self, url):
        """Auto-detect input type and resolve to playable URL/path."""
        if url.startswith("magnet:") or url.endswith(".torrent"):
            return self._resolve_torrent(url)
        else:
            return self._resolve_generic(url)

    def _resolve_torrent(self, url):
        """Resolve magnet/torrent using Real-Debrid or libtorrent."""
        if self.debrid_key:
            return self._debrid_unrestrict(url)
        elif lt:
            return self._libtorrent_resolve(url)
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

    def _libtorrent_resolve(self, magnet_uri):
        """libtorrent: resolve magnet → largest file path."""
        ses = lt.session()
        params = {
            "save_path": self.torrent_dir,
            "storage_mode": lt.storage_mode_t.storage_mode_sparse,
        }
        handle = lt.add_magnet_uri(ses, magnet_uri, params)
        ses.start_dht()

        # Wait for metadata
        while not handle.has_metadata():
            time.sleep(0.5)

        info = handle.get_torrent_info()
        files = info.files()
        largest_idx = max(
            range(files.num_files()),
            key=lambda i: files.file_size(i),
        )
        return os.path.join(self.torrent_dir, files.file_path(largest_idx))

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
