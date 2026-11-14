"""
Persistent memory store for Jupiter TV settings.
Simple key-value store backed by DuckDB (or :memory: fallback).
"""

import os
from datetime import datetime

try:
    import duckdb
except ImportError:
    duckdb = None


class MemoryStore:
    """Persistent KV store for app state and settings."""

    def __init__(self, db_path=None):
        if not duckdb:
            self.conn = None
            self._cache = {}
            return

        if db_path is None:
            db_path = ":memory:"
        elif os.path.exists(os.path.dirname(db_path)) or db_path == ":memory:":
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

        self.conn = duckdb.connect(db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_store (
                key VARCHAR PRIMARY KEY,
                value VARCHAR,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def get(self, key, default=""):
        """Retrieve value by key."""
        if not self.conn:
            return self._cache.get(key, default)
        try:
            result = self.conn.execute(
                "SELECT value FROM kv_store WHERE key = ?", [key]
            ).fetchone()
            return result[0] if result else default
        except Exception:
            return default

    def set(self, key, value):
        """Store key-value pair."""
        if not self.conn:
            self._cache[key] = str(value)
            return
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                [key, str(value)],
            )
        except Exception:
            pass

    def seed(self, key, default_value):
        """Set key only if not already present."""
        if not self.get(key):
            self.set(key, default_value)
