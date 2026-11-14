#!/usr/bin/env python3
"""Root launcher for the lightweight MemoryOS Router + Quiet Advisor Server."""

from src.memoryos.server import app, main  # noqa: F401

if __name__ == "__main__":
    main()
