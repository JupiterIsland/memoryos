#!/usr/bin/env python3
"""
Real torrent streaming: libtorrent sequential + lightweight HTTP server.
No mock data. Single-file, minimal overhead.
"""

import os
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
try:
    import libtorrent as lt
except ImportError:
    lt = None


class TorrentStreamer:
    """Stream largest file from magnet/torrent over HTTP."""

    def __init__(self, save_path="/tmp/jptv", port=8765):
        if not lt:
            raise RuntimeError("libtorrent not installed")
        self.save_path = save_path
        self.port = port
        self.session = None
        self.handle = None
        os.makedirs(save_path, exist_ok=True)

    def start_torrent(self, magnet_uri):
        """Resolve magnet → wait for metadata → return file path."""
        self.session = lt.session()
        params = {
            "save_path": self.save_path,
            "storage_mode": lt.storage_mode_t.storage_mode_sparse,
        }
        self.handle = lt.add_magnet_uri(self.session, magnet_uri, params)
        self.session.start_dht()

        # Wait for metadata (with timeout)
        timeout = time.time() + 60
        while not self.handle.has_metadata():
            if time.time() > timeout:
                raise TimeoutError("Magnet metadata timeout")
            time.sleep(0.5)

        info = self.handle.get_torrent_info()
        files = info.files()
        largest_idx = max(
            range(files.num_files()),
            key=lambda i: files.file_size(i),
        )
        file_path = os.path.join(self.save_path, files.file_path(largest_idx))
        return file_path

    def stream_http(self, file_path):
        """Serve file over HTTP for remote playback."""
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        class Handler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == f"/{file_name}":
                    self.send_response(206)  # Partial content
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Accept-Ranges", "bytes")
                    size = os.path.getsize(file_path)
                    self.send_header("Content-Length", size)
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404)

        os.chdir(file_dir)
        server = HTTPServer(("127.0.0.1", self.port), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        return f"http://127.0.0.1:{self.port}/{file_name}"

    def resolve_magnet(self, magnet_uri):
        """Magnet → file path → HTTP URL."""
        file_path = self.start_torrent(magnet_uri)
        http_url = self.stream_http(file_path)
        return http_url


if __name__ == "__main__":
    magnet = "magnet:?xt=urn:btih:..."
    streamer = TorrentStreamer()
    try:
        url = streamer.resolve_magnet(magnet)
        print(f"Stream at: {url}")
        time.sleep(3600)  # Keep server alive
    except Exception as e:
        print(f"Error: {e}")
