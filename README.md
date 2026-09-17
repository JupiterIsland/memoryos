# MemoryOS - Distributed AI & Streaming Intelligence

[![GitHub Stars](https://img.shields.io/github/stars/JupiterIsland/memoryos?style=flat-square)](https://github.com/JupiterIsland/memoryos)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://github.com/JupiterIsland/memoryos/pulls)

**MemoryOS** is a distributed intelligence platform designed to orchestrate deep learning inference alongside multi-platform media streaming. It combines **DeepSeek-V3**, a **DuckDB vector memory** architecture, and a unified broadcast ecosystem to deliver low-latency inference and decentralized streaming across desktop, mobile (Fire TV), and edge infrastructure.

---

## Core Architecture

### Jupiter ONE: Desktop Audio Broadcasting Engine
A self-contained audio playback and extraction engine built on PyQt6 and FFmpeg.
*   **Real-time Spectrum Analysis:** Low-latency visualization pipeline.
*   **Dynamic Stream Extraction:** Leverages `yt-dlp` for URL resolution with seamless fallback to `ffplay`.
*   **Optimized Backend:** Utilizes Qt6 Multimedia and FFmpeg for maximum format compatibility and hardware offloading.
*   **Single-Script Deployment:** Engineered for minimal overhead—one executable, one signal.

### Fire TV Mobile Client: Kivy/Kotlin Integration
An enterprise-grade mobile broadcast client engineered for set-top box environments.
*   **Native TorrentService:** Decentralized, P2P streaming capabilities.
*   **Hardware Acceleration:** Integrated `ExoPlayerActivity` for efficient playback.
*   **DuckDB State Management:** Offline-first vector memory backend.
*   **AI Metadata Engine:** Real-time content enrichment via DeepSeek-V3 hooks.

### DuckDB Vector Memory System
The data persistence and retrieval layer powering MemoryOS intelligence.
*   **Vector Embeddings:** Semantic search execution across all indexed streams.
*   **Temporal Memory:** Time-windowed replay and state tracking.
*   **Distributed Sync:** Cross-device state replication.
*   **High-Throughput Querying:** Sub-second latency for vector retrieval at scale.

---

## System Diagrams

GitHub will automatically render the following architecture diagrams. 

### High-Level Ecosystem Topology

```mermaid
graph TD
    subgraph Clients["Client Layer"]
        J1["Jupiter ONE (Desktop)<br/>PyQt6 Audio Engine"]
        FTV["Fire TV (Mobile)<br/>Kivy / Kotlin Backend"]
    end

    subgraph Memory["DuckDB Vector Memory Layer"]
        VS["Semantic Search"]
        TW["Temporal Windowing"]
        CS["Cross-Device Sync"]
    end

    subgraph AI["Intelligence Layer"]
        DS["DeepSeek-V3 Integration"]
        AD["AI Director"]
        REC["Recommendation Engine"]
    end

    Clients <-->|State & Retrieval| Memory
    Memory <-->|Context & Embeddings| AI
    Clients <-->|Stream Classification| AI
