#!/usr/bin/env python3
"""
Minimal Torrentio scraper: query addon API to get magnets for movie/TV show.
No auth required. Simple REST calls.
"""

import requests
from typing import List
from .models import Channel


class TorrentioScraper:
    """Query Torrentio addon API for magnet links."""

    BASE_URL = "https://torrentio.strem.fun/manifest.json"
    STREAM_URL = "https://torrentio.strem.fun/stream/movie/{imdb_id}.json"

    @staticmethod
    def search_movie(imdb_id: str, quality="720p") -> List[Channel]:
        """Get magnet links for a movie (IMDB ID).
        Example: tt0816692 (Interstellar)
        """
        try:
            url = TorrentioScraper.STREAM_URL.format(imdb_id=imdb_id)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            streams = data.get("streams", [])
            channels = []

            for stream in streams:
                title = stream.get("title", "Unknown")
                link = stream.get("url", "")

                # Filter by quality if specified
                if quality and quality.lower() not in title.lower():
                    continue

                if link.startswith("magnet:"):
                    channels.append(
                        Channel(
                            name=title,
                            url=link,
                            type="torrentio",
                        )
                    )

            return channels
        except Exception as e:
            raise ValueError(f"Torrentio search failed: {e}")

    @staticmethod
    def search_tv(imdb_id: str, season: int = 1, episode: int = 1) -> List[Channel]:
        """Get magnet links for TV show episode.
        Example: tt0903747 S01E01 (Breaking Bad)
        """
        try:
            url = f"https://torrentio.strem.fun/stream/series/{imdb_id}:{season}:{episode}.json"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            streams = data.get("streams", [])
            channels = []

            for stream in streams:
                title = stream.get("title", "Unknown")
                link = stream.get("url", "")

                if link.startswith("magnet:"):
                    channels.append(
                        Channel(
                            name=title,
                            url=link,
                            type="torrentio",
                        )
                    )

            return channels
        except Exception as e:
            raise ValueError(f"Torrentio TV search failed: {e}")
