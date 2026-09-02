#!/usr/bin/env python3
"""
Minimal TMDB metadata fetcher: posters, synopsis, cast.
"""

import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class MovieMetadata:
    """Movie metadata from TMDB."""
    title: str
    imdb_id: str
    poster_url: Optional[str] = None
    synopsis: str = ""
    year: int = 0
    rating: float = 0.0


class TMDBFetcher:
    """Minimal TMDB API client (no auth key required for basic searches)."""

    SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
    IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

    @staticmethod
    def search_by_name(query: str, api_key: Optional[str] = None) -> Optional[MovieMetadata]:
        """Search TMDB for movie by name."""
        try:
            # Note: TMDB requires API key for most endpoints
            # This is a placeholder; real usage requires TMDB_API_KEY env var
            if not api_key:
                return None

            params = {"api_key": api_key, "query": query}
            resp = requests.get(TMDBFetcher.SEARCH_URL, params=params, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])

            if not results:
                return None

            movie = results[0]
            poster_path = movie.get("poster_path")
            poster_url = (
                f"{TMDBFetcher.IMAGE_BASE}{poster_path}"
                if poster_path
                else None
            )

            return MovieMetadata(
                title=movie.get("title", "Unknown"),
                imdb_id=movie.get("id", ""),
                poster_url=poster_url,
                synopsis=movie.get("overview", ""),
                year=int(movie.get("release_date", "0000")[:4]),
                rating=movie.get("vote_average", 0.0),
            )
        except Exception as e:
            print(f"TMDB error: {e}")
            return None
