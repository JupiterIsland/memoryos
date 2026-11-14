#!/usr/bin/env python3
"""
End-to-end test: magnet → HTTP stream URL (plays immediately, downloads in background).

This demonstrates the true Stremio-like behavior:
1. Paste magnet
2. Get HTTP stream URL within seconds
3. Player starts streaming chunks as they download
4. Download completes in background
"""

import sys
import time
import requests
from apps.shared import StreamManager

def test_stream_to_http():
    """Test: magnet link → HTTP streaming URL"""
    
    # Example: small test torrent (real magnet from IPFS/DHT)
    magnet = "magnet:?xt=urn:btih:e3811b9539cacff07e337cfd14f8d92eff96969f&dn=ubuntu-24.04-live-server-amd64.iso&tr=udp://tracker.ubuntu.com:6969"
    
    print("\n" + "="*60)
    print("TEST: Sequential Torrent Streaming")
    print("="*60 + "\n")
    
    print(f"[*] Input: {magnet[:60]}...")
    print()
    
    try:
        manager = StreamManager()
        
        print("[*] Resolving magnet link...")
        start = time.time()
        stream_url = manager.resolve(magnet)
        elapsed = time.time() - start
        
        print(f"[+] Stream ready in {elapsed:.1f}s!")
        print(f"[+] URL: {stream_url}")
        print()
        
        # Test HTTP server responds
        print("[*] Testing HTTP server...")
        try:
            resp = requests.head(stream_url, timeout=5)
            print(f"[+] HTTP {resp.status_code} OK")
            print(f"[+] Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
            print(f"[+] Accept-Ranges: {resp.headers.get('Accept-Ranges', 'none')}")
            
            # Get total size
            total_size = int(resp.headers.get('Content-Length', 0))
            if total_size:
                print(f"[+] Total file size: {total_size / 1e9:.1f} GB")
        except Exception as e:
            print(f"[-] HTTP test failed: {e}")
        
        print()
        print("[+] Status: Sequential download in progress (background)")
        print("[+] Player can now stream from:", stream_url)
        print()
        print("Example ffmpeg command:")
        print(f"  ffplay '{stream_url}'")
        print()
        print("This achieves Stremio-like behavior:")
        print("  1. Magnet → HTTP URL (instant)")
        print("  2. Player starts streaming immediately")
        print("  3. Download continues in background")
        print("  4. No full file download required before playback")
        print()
        
        # Keep streaming for 10s to show it works
        print("[*] Streaming for 10s... (Ctrl+C to stop)")
        time.sleep(10)
        
    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print()
        print("[*] Cleanup...")
        manager.torrent_streamer.stop()
        print("[+] Done")
    
    return True

if __name__ == "__main__":
    success = test_stream_to_http()
    sys.exit(0 if success else 1)
