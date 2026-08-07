# 🚀 MemoryOS - Distributed AI & Streaming Intelligence

[![GitHub Stars](https://img.shields.io/github/stars/JupiterIsland/memoryos?style=flat-square)](https://github.com/JupiterIsland/memoryos)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://github.com/JupiterIsland/memoryos/pulls)

**MemoryOS** is a next-generation distributed intelligence platform combining **DeepSeek-V3 AI**, **DuckDB vector memory**, and **multi-platform streaming** to create a unified broadcast ecosystem across desktop, mobile (Fire TV), and cloud infrastructure.

---

## 🌟 Flagship Features

### 🎸 **Jupiter ONE - Desktop Audio Broadcasting Engine**  
A complete, self-contained PyQt6 + FFmpeg audio player with:
- **Real-time spectrum visualization** (animated neon display)
- **YouTube stream extraction** via yt-dlp with fallback to ffplay
- **Qt6 Multimedia + FFmpeg backends** for maximum compatibility
- **Single-script deployment** — one executable, one signal

**Status:** ✅ [Merged in PR #4](https://github.com/JupiterIsland/memoryos/pull/4)

```bash
# Quick start
python apps/jupiter-tv-desktop-v2/jupiter.py
```

### 📱 **Fire TV Mobile App - Kivy/Kotlin v1**  
Enterprise-grade mobile broadcast client featuring:
- **Native TorrentService** for decentralized streaming
- **ExoPlayerActivity** for hardware-accelerated playback
- **Metadata engine** with AI-driven content enrichment
- **DuckDB MemoryOS backend** for offline-first state management

**Status:** ✅ [Merged in PR #4](https://github.com/JupiterIsland/memoryos/pull/4)

### 🧠 **DuckDB-Backed Memory System**
- **Vector embeddings** for semantic search across streams
- **Temporal memory** with time-windowed replay
- **Distributed sync** across devices
- **Sub-second query latency** at scale

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   MemoryOS Ecosystem                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🖥️  JUPITER ONE (Desktop)     📱 Fire TV (Mobile)    │
│  ├─ PyQt6 Audio Engine        ├─ Kivy Frontend       │
│  ├─ Spectrum Analyzer         ├─ Kotlin Backend      │
│  └─ YouTube Stream Resolver   └─ TorrentService      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│               DuckDB Vector Memory Layer                │
│  • Semantic search across all content                  │
│  • Temporal windowing & replay                         │
│  • Cross-device sync                                   │
├─────────────────────────────────────────────────────────┤
│            DeepSeek-V3 AI Intelligence                 │
│  • Real-time content classification                    │
│  • AI Director for adaptive streaming                  │
│  • Recommendation engine                               │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
memoryos/
├── apps/
│   └── jupiter-tv-desktop-v2/           # 🎸 Desktop App (PR #4)
│       ├── jupiter.py                   # Full PyQt6 + Audio Engine (336 lines)
│       ├── demo_play.py                 # Stream resolver CLI
│       └── README.md                    # Setup & docs
├── src/
│   ├── stream_manager.py                # URL → Stream pipeline
│   ├── memory_engine.py                 # DuckDB vector layer
│   └── ai_director.py                   # DeepSeek integration
├── requirements.txt                     # Python dependencies
└── README.md                            # (This file)
```

---

## 🔧 Installation

### Desktop (Jupiter ONE)

```bash
# 1. Clone & navigate
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch
python apps/jupiter-tv-desktop-v2/jupiter.py
```

**Requirements:**
- Python 3.9+
- PyQt6 + PyQt6-Multimedia
- FFmpeg (for audio playback)
- yt-dlp (YouTube extraction)

### Mobile (Fire TV)

```bash
cd apps/fire-tv-kotlin/
./gradlew assembleRelease
# Deploy to Fire TV device via adb
```

---

## 🎯 Recent Achievements

### ✅ PR #4: Fire TV Mobile App + Desktop Client (MERGED)
**Merged 2026-08-06** | Author: @JupiterIsland

**What's Included:**
- ✨ Full Kivy/Kotlin Fire TV application
- ✨ Native TorrentService for P2P streaming
- ✨ ExoPlayer activity for hardware acceleration
- ✨ Metadata enrichment engine
- ✨ AI Director stubs (DeepSeek-V3 hooks)
- ✨ Desktop PyQt6 audio engine with spectrum analyzer
- ✨ M3U parser & stream resolver

**Scope:** 370 additions across 3 files | 4 commits | 0 conflicts

[View Full PR →](https://github.com/JupiterIsland/memoryos/pull/4)

---

## 🎨 Desktop UI Showcase

### Jupiter ONE - Neon Aesthetic
```
┌────────────────────────────────────────────────┐
│ 🚀 JUPITER ONE - YOUR LOCAL BROADCAST ENGINE   │
├────────────────────────────────────────────────┤
│ YouTube URL: [Paste URL here...                 │ ▶ LOAD & PLAY
├────────────────────────────────────────────────┤
│               🎵 Spectrum Analyzer              │
│       ████ ███ █████ ██ ████ ███ ██ █ ██      │
│       Cyan/Magenta/Yellow color cycle           │
├────────────────────────────────────────────────┤
│ Status: ▶ Playing: "Song Title..."              │
├────────────────────────────────────────────────┤
│ Info Log:                                       │
│ ✅ Jupiter One initialized                      │
│ 📡 Ready to broadcast                           │
│ 🔄 Loading: https://www.youtube.com/...         │
│ ✅ Loaded: Song Name                            │
│ ✅ Audio playback started                       │
└────────────────────────────────────────────────┘
```

**Color Scheme:** Deep black/purple gradient background with neon cyan (#00ffff), hot pink (#ff1493), and green accents.

---

## 🚀 Usage Examples

### Play YouTube Audio
```python
from src.stream_manager import resolve_stream

# From CLI
python apps/jupiter-tv-desktop-v2/demo_play.py "https://www.youtube.com/watch?v=..."

# From Python
result = resolve_stream("https://www.youtube.com/watch?v=...")
print(f"Stream URL: {result['url']}")
print(f"Title: {result['title']}")
```

### Memory Query
```python
from src.memory_engine import MemoryOS

mem = MemoryOS()
# Semantic search across all indexed streams
results = mem.semantic_search("upbeat electronic music", top_k=5)
```

### AI Director
```python
from src.ai_director import AIDirector

director = AIDirector(model="deepseek-v3")
recommendation = director.get_next_stream(current_context)
```

---

## 📈 Roadmap

- [x] Desktop PyQt6 audio engine with spectrum visualization
- [x] Fire TV Kivy/Kotlin mobile client
- [x] M3U parser & torrent integration
- [x] DuckDB memory backend (v1)
- [ ] Real-time spectrum capture from audio input
- [ ] Kubernetes deployment (Edge)
- [ ] Web dashboard for memory analytics
- [ ] Multi-user sync & collaboration
- [ ] Mobile app store release

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📝 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🎓 References & Technologies

**Core Stack:**
- **Frontend:** PyQt6 (Desktop), Kivy (Mobile)
- **Backend:** Python 3.9+, Kotlin (Android)
- **AI/ML:** DeepSeek-V3, Embeddings
- **Storage:** DuckDB (Vector DB), SQLite (Local)
- **Media:** FFmpeg, yt-dlp, ExoPlayer
- **Streaming:** P2P Torrents, HTTP/DASH

**Inspiration:**
- YouTube-DL architecture
- Qt ecosystem best practices
- DuckDB vector search patterns
- Enterprise mobile app standards

---

## 📞 Contact & Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/JupiterIsland/memoryos/issues)
- **Pull Requests:** [Contribute code](https://github.com/JupiterIsland/memoryos/pulls)
- **Discussions:** [Ask questions](https://github.com/JupiterIsland/memoryos/discussions)

---

## ⭐ Show Your Support

If MemoryOS helps you, please give it a star! ⭐

```
  _   _ _____ _____ ___   __   ____    ___  ____    ___
 | | | |  ___|  __ \|  _| / _| / __ \ / _ \/ __ \ / _ \
 | |_| | |_  | |  | | |_ | |_ | |  | | | | | |  | | | | |
 |  _  |  _| | |  | |  _||  _|| |  | | | | | |  | | | | |
 | | | | |__ | |__| | |  | |_ | |__| | |_| | |__| | |_| |
 |_| |_|____||_____/|_|  |___| \____/ \___/ \____/ \___/
```

---

**Made with 🔥 by @JupiterIsland**  
**Last Updated:** August 2026
