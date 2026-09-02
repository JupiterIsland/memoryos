"""
Utility functions: M3U parsing, logging, helpers.
"""

import requests
from typing import List
from .models import Channel


def parse_m3u(url_or_path) -> List[Channel]:
    """Parse M3U playlist into Channel list."""
    try:
        if url_or_path.startswith("http"):
            raw = requests.get(url_or_path, timeout=10).text
        else:
            with open(url_or_path, "r", encoding="utf-8") as f:
                raw = f.read()

        channels = []
        lines = raw.split("\n")
        current_name = "Unknown"

        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF:"):
                current_name = line.split(",")[-1]
            elif line.startswith("http"):
                channels.append(Channel(name=current_name, url=line, type="m3u"))

        return channels
    except Exception as e:
        raise ValueError(f"M3U parse error: {e}")


def truncate(text, length=50):
    """Truncate string to length."""
    return text[: length - 3] + "..." if len(text) > length else text
