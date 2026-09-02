#!/usr/bin/env python3
"""
Real torrent streaming: sequential download + HTTP range-request server.
Magnet → metadata → HTTP stream URL (playable immediately while downloading).
"""

import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import libtorrent as lt
except ImportError:
    lt = None


class TorrentHandler(BaseHTTPRequestHandler):
    """HTTP handler supporting Range requests for partial file streaming."""

    file_path = None
    file_size = None

    def do_GET(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.send_error(404, "File not found")
            return

        # Re-check file size each request (growing file)
        try:
            size = os.path.getsize(self.file_path)
        except OSError:
            self.send_error(404)
            return

        # Parse Range header for partial content
        range_header = self.headers.get("Range")
        if range_header:
            try:
                range_val = range_header.split("=")[1]
                start, end = range_val.split("-")
                start = int(start) if start else 0
                end = int(end) if end else size - 1
                end = min(end, size - 1)

                self.send_response(206)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(self.file_path, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(end - start + 1))
            except (ValueError, IndexError):
                self.send_error(416, "Range Not Satisfiable")
        else:
            # Full file request
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(self.file_path, "rb") as f:
                self.wfile.write(f.read())

    def log_message(self, format, *args):
        pass  # Suppress logs


class TorrentStreamer:
    """Stream largest file from magnet/torrent via HTTP (sequential download)."""

    def __init__(self, save_path="/tmp/jptv", port=8765):
        if not lt:
            raise RuntimeError("libtorrent not installed")
        self.save_path = save_path
        self.port = port
        self.session = None
        self.handle = None
        self.server = None
        os.makedirs(save_path, exist_ok=True)

    def start_torrent(self, magnet_uri):
        """Resolve magnet → enable sequential download → return file path."""
        self.session = lt.session()
        params = {
            "save_path": self.save_path,
            "storage_mode": lt.storage_mode_t.storage_mode_sparse,
        }
        self.handle = lt.add_magnet_uri(self.session, magnet_uri, params)
        self.session.start_dht()

        # Wait for metadata
        timeout = time.time() + 60
        while not self.handle.has_metadata():
            if time.time() > timeout:
                raise TimeoutError("Magnet metadata timeout")
            time.sleep(0.5)

        # Enable sequential download
        self.handle.set_sequential_download(True)

        info = self.handle.get_torrent_info()
        files = info.files()
        largest_idx = max(
            range(files.num_files()),
            key=lambda i: files.file_size(i),
        )
        file_path = os.path.join(self.save_path, files.file_path(largest_idx))
        return file_path

    def start_http_server(self, file_path):
        """Start HTTP server serving the file with Range support."""
        TorrentHandler.file_path = file_path
        TorrentHandler.file_size = 0

        self.server = HTTPServer(("127.0.0.1", self.port), TorrentHandler)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
        return f"http://127.0.0.1:{self.port}/stream"

    def stream_magnet(self, magnet_uri):
        """Magnet → sequential download → HTTP streaming URL."""
        file_path = self.start_torrent(magnet_uri)
        http_url = self.start_http_server(file_path)
        return http_url

    def stop(self):
        """Cleanup."""
        if self.server:
            self.server.shutdown()
        if self.session:
            self.session.pause()


if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) < 2:
        print("Usage: python torrent_stream.py <magnet_uri>")
        sys.exit(1)
    
    streamer = TorrentStreamer()
    try:
        url = streamer.stream_magnet(sys.argv[1])
        print(f"✅ Streaming at: {url}")
        print("(Keep process running to serve file)")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"❌ Error: {e}")
