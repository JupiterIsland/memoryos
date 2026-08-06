# Jupiter TV Mobile

This directory contains the Kivy + Buildozer based Fire TV app scaffold for Jupiter TV.

Quick test (desktop):

1. Create a venv and install requirements:
   pip install kivy requests duckdb

2. Run locally:
   python apps/jupiter-tv-mobile/main.py

Build with Buildozer (on Linux/macOS with Android SDK/NDK):

1. Install Buildozer and Android toolchain
2. cd apps/jupiter-tv-mobile
3. buildozer android debug deploy run

Notes:
- The app uses DuckDB for local MemoryOS storage. On Android, the DB will be stored in app storage.
- The native StreamEngine.kt is a simple ACTION_VIEW wrapper for Fire TV; replace with ExoPlayer integration for better control.
