"""
Real sequential torrent streaming: libtorrent + HTTP Range server.
Serves in-progress file via HTTP while downloading.
"""

import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    import libtorrent as lt
except ImportError:
    lt = None


class RangeHandler(BaseHTTPRequestHandler):
    """HTTP handler for sequential range requests on in-progress file."""
    
    file_path = None
    max_size = 0  # Updated as download progresses
    
    def do_GET(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.send_error(404)
            return
        
        try:
            # Get current file size
            size = os.path.getsize(self.file_path)
            range_hdr = self.headers.get('Range')
            
            if range_hdr:
                # Parse Range: bytes=start-end
                try:
                    _, range_str = range_hdr.split('=')
                    start, end = range_str.split('-')
                    start = int(start) if start else 0
                    end = int(end) if end else size - 1
                    end = min(end, size - 1)
                except:
                    start, end = 0, size - 1
                
                self.send_response(206)
                self.send_header('Content-Range', f'bytes {start}-{end}/{self.max_size}')
                self.send_header('Content-Length', str(end - start + 1))
            else:
                self.send_response(200)
                self.send_header('Content-Length', str(size))
            
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Connection', 'close')
            self.end_headers()
            
            # Stream the bytes
            with open(self.file_path, 'rb') as f:
                if range_hdr:
                    f.seek(start)
                    self.wfile.write(f.read(end - start + 1))
                else:
                    self.wfile.write(f.read())
        
        except Exception as e:
            pass
    
    def log_message(self, *args):
        pass


class TorrentStreamer:
    """Sequential download + HTTP streaming."""
    
    def __init__(self, torrent_dir="/tmp/jptv", http_port=8888):
        self.torrent_dir = torrent_dir
        self.http_port = http_port
        self.session = None
        self.handle = None
        self.file_path = None
        self.http_server = None
        self.http_thread = None
        self.file_size = 0
        os.makedirs(torrent_dir, exist_ok=True)
    
    def stream(self, magnet_uri):
        """Start sequential download + HTTP stream. Return HTTP URL immediately."""
        if not lt:
            raise RuntimeError("libtorrent required: pip install libtorrent-rasterbar")
        
        # Create session with sequential settings
        self.session = lt.session()
        settings = self.session.get_settings()
        settings['sequential_download'] = True
        self.session.set_settings(settings)
        
        # Add torrent
        params = {
            "save_path": self.torrent_dir,
            "storage_mode": lt.storage_mode_t.storage_mode_sparse,
            "paused": False,
        }
        self.handle = lt.add_magnet_uri(self.session, magnet_uri, params)
        self.session.start_dht()
        
        # Wait for metadata (usually fast via DHT)
        timeout = time.time() + 30
        while not self.handle.has_metadata():
            if time.time() > timeout:
                raise RuntimeError("Metadata timeout - no peers found")
            time.sleep(0.1)
        
        # Get largest file
        info = self.handle.get_torrent_info()
        files = info.files()
        largest_idx = max(range(files.num_files()), key=lambda i: files.file_size(i))
        self.file_path = os.path.join(self.torrent_dir, files.file_path(largest_idx))
        self.file_size = files.file_size(largest_idx)
        
        # Only download largest file
        for i in range(files.num_files()):
            self.handle.file_priority(i, 7 if i == largest_idx else 0)
        
        # Resume download
        self.handle.resume()
        
        # Start HTTP server
        RangeHandler.file_path = self.file_path
        RangeHandler.max_size = self.file_size
        self.http_server = HTTPServer(('127.0.0.1', self.http_port), RangeHandler)
        self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        self.http_thread.start()
        
        # Return streaming URL immediately (file still downloading)
        return f"http://127.0.0.1:{self.http_port}/"
    
    def stop(self):
        """Stop streaming and cleanup."""
        if self.http_server:
            self.http_server.shutdown()
        if self.session and self.handle:
            try:
                self.session.remove_torrent(self.handle)
            except:
                pass
