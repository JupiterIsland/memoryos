"""demo_play.py — resolve a URL via the existing stream_manager and print the result
"""
import sys
from src.stream_manager import resolve_stream

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python demo_play.py <url_or_magnet>")
        sys.exit(1)
    target = sys.argv[1]
    try:
        result = resolve_stream(target)
        print("Resolved:", result)
    except Exception as e:
        print("Error resolving stream:", e)
