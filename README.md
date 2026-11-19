# MemoryOS // Jupiter Studio

### Hardware-Aware AI Workstation for Multi-Model Routing, Project Context, and Live GPU Telemetry

![MemoryOS // The Quiet Advisor — Powered by AMD Token Lab](docs/memoryos_executive_banner.png)

[![Release: v1.0.0-RC1](https://img.shields.io/badge/Release-v1.0.0--RC1-ED1C24?style=for-the-badge&logo=amd&logoColor=white)](https://github.com/JupiterIsland/memoryos/releases/latest)
[![MemoryOS CI](https://img.shields.io/github/actions/workflow/status/JupiterIsland/memoryos/ci.yml?branch=main&style=for-the-badge&label=CI%20Tests)](https://github.com/JupiterIsland/memoryos/actions/workflows/ci.yml)
[![Download Jupiter Studio](https://img.shields.io/badge/Download-Jupiter_Studio-FF6A00?style=for-the-badge)](https://github.com/JupiterIsland/memoryos/releases/latest)
[![Local VRAM: 0 MB Consumed](https://img.shields.io/badge/Local_VRAM-0_MB_Consumed-10B981?style=for-the-badge)](PROOF_OF_RESULTS.md)
[![Architecture: Zero-VRAM Hybrid](https://img.shields.io/badge/Architecture-Zero--VRAM_Hybrid-38BDF8?style=for-the-badge)](ARCHITECTURE.md)

---

## Jupiter Studio RC1

![Jupiter Studio RC1 — Live Qwen3.8-27B Streaming & Speculative Neural Radar](docs/screenshots/jupiter_studio_live_stream.png)

> **Jupiter Studio is a hardware-aware AI workstation that automatically routes tasks between models, manages project context, and provides live system telemetry from a single desktop interface.**

* ✓ **Multi-model routing** — automatic routing across local and cloud AI models
* ✓ **Local and cloud AI** — run 27B–72B models while keeping local GPU VRAM free
* ✓ **Workspace-aware context** — bring repository files, uploads, and screenshots straight into chat
* ✓ **Hardware telemetry** — live GPU detection, VRAM usage, thermal guard, and health scoring
* ✓ **Persistent memory** — local SQLite telemetry ledger and atomic NVMe checkpoints
* ✓ **One-click Copilot export** — copy structured workspace bundles into IDE agents

| Sharp Smoked-Crystal Quantum Theme | Atari / Commodore B&amp;W Monochrome Mode |
| :---: | :---: |
| ![Jupiter Studio Quantum Smoked-Crystal](docs/screenshots/jupiter_studio_quantum.png) | ![Jupiter Studio Atari B&W Monochrome](docs/screenshots/jupiter_studio_daylight.png) |

---

## 60-Second Quick Start

### Option 1 — Download Standalone Binary (No Python Setup Required)
Grab the latest **`v1.0.0-rc1`** build from **[GitHub Releases](https://github.com/JupiterIsland/memoryos/releases/tag/v1.0.0-rc1)** (`SHA256SUMS.txt` included):
* **Windows:** `JupiterStudio-Windows-x64.zip` → extract → run `JupiterStudio.exe`
* **macOS (Apple Silicon):** `JupiterStudio-macOS-arm64.tar.gz` → `tar -xzf JupiterStudio-macOS-arm64.tar.gz` → `./JupiterStudio-macOS-arm64/JupiterStudio`
* **Linux:** `JupiterStudio-Linux-x64.tar.gz` → `tar -xzf JupiterStudio-Linux-x64.tar.gz` → `./JupiterStudio-Linux-x64/JupiterStudio`

### Option 2 — One-Command Source Launch
```bash
git clone https://github.com/JupiterIsland/memoryos.git && cd memoryos && cp .env.example .env && python3 -B apps/jupiter_studio.py
```
Then open **[http://127.0.0.1:7860](http://127.0.0.1:7860)** — see **[HOW_TO_USE_JUPITER_STUDIO.md](HOW_TO_USE_JUPITER_STUDIO.md)** for the plain-English walkthrough.

---

## Key Features (Ordered by User Value)

### 1. AI Workstation — One Place to Work With Multiple AI Models
* Single zero-dependency desktop interface (`Jupiter Studio`) with real-time streaming responses
* Unified access to local and cloud AI without juggling browser tabs
* **Dual Arena** side-by-side shootout to race two models on the same prompt
* Instant surface switching across **Quantum** (smoked-crystal dark), **Radeon** (crimson carbon), and **Atari B&W** (high-res monochrome)

### 2. Smart Model Routing — Automatically Sends Requests to the Best Model
* Multi-model orchestration across **AMD Token Lab**, **Hugging Face Inference Router**, **NVIDIA NIM**, **DigitalOcean MI300X**, **local DGX Spark (`vLLM`/`Flare`)**, and **Ollama**
* Fast local execution where appropriate with automatic cloud offload and instant `HTTP 429` failover when needed
* Resource-aware decisions driven by the `d3` router

### 3. Context & Workspace Intelligence — Bring Files, Projects, and Notes Into Conversations
* Built-in repository file picker with multi-file drag-and-drop and multimodal screenshot vision
* Automatic **secret-file upload blocker** (prevents `.env`, `.pem`, `.key`, and `credentials.json` from ever leaving your machine)
* One-click **Copilot Bundle Export** for VS Code, Cursor, and IDE coding agents

### 4. Real-Time Hardware Telemetry — See Exactly What the System Is Doing
* Live GPU detection, VRAM usage, temperature, and load monitoring (including DGX Spark / GB10 unified-memory fallback)
* **Live Pre-Send Speculative Neural Radar** showing offload probability, predicted route, draft token count, and VRAM saved as you type
* Composite `0–100` **Workstation Health Score** (`Grade A–F`)

### 5. MemoryOS Intelligence Layer — Persistent Knowledge and Workflow Continuity
* Local SQLite WAL telemetry ledger (`QuietAdvisorDB.sqlite`) with versioned migrations and parameterized queries
* **The Quiet Advisor** autonomous detectors for VRAM saturation, thermal throttling, context waste, and model thrashing
* Alert `CardState` lifecycle machine (`PENDING → TRIGGERED → ACKNOWLEDGED → RESOLVED`) with duplicate suppression and per-detector circuit breakers

### 6. Performance Optimisation — Reduce Waste and Improve Responsiveness
* Zero local studio VRAM allocation (`0 MB`) when offloading 27B–72B models to cloud accelerators
* `0.091 ms` AMD Zen 3 AVX2/FMA host-side CPU skip gate and `5.37 μs` pure-Python Speculative Offload MLP
* `3.07 ms` atomic NVMe checkpoint recovery and `94.0%` cellular tethering bandwidth reduction

### 7. Developer Features — Built for Builders
* Pure Python architecture with zero PyTorch/Electron bloat (`apps/jupiter_studio.py`, `src/memoryos/`, `quiet_advisor_detectors.py`)
* Automated **GitHub Actions CI** (`32/32` unit tests + `8/8` hardware benchmark suites) and cross-platform standalone release builds
* Open source under the MIT License with extensible provider and custom model support

---

## Technical Highlights & Verified Invariants

* **Formal Release Candidate:** `v1.0.0-RC1` ready for presentation to AMD Developer Relations and the AMD Token Lab engineering team.
* **Zero Host VRAM Consumption:** 100% of host GPU memory remains dedicated to client applications, gaming, or rendering; 27B- and 31B-parameter models run remotely on AMD Instinct compute with **0 MB local VRAM allocation**.
* **5.37 μs Speculative Offload Decision:** A local pure-Python neural forward pass determines offloading necessity in **5.37 μs**, allowing sub-millisecond host-side gating before any network request is dispatched.
* **0.091 ms AMD Zen 3 CPU Frame Gate:** Processes raw frame deltas in 91 μs using AVX2 and FMA SIMD, consuming only **0.55% of a 60 FPS frame window**.
* **3.07 ms Atomic Checkpoint Recovery:** Restores state snapshots from NVMe storage in ~3.07 ms per checkpoint (`61.43 ms` total across 20 checkpoints), ensuring crash-resilient session persistence.
* **94.0% Cellular Tethering Bandwidth Reduction:** Suppresses static video frames over mobile LTE hotspots, saving 385.5 MB and 205.6 seconds of airtime per 1,000 frames.

---

## Core Systems Architecture

```mermaid
flowchart TD
    UI["Client Workstation Layer<br/>Jupiter Studio UI • Quiet Advisor Dashboard • Dual Arena"]
    L1["Layer 1: Host-Side Telemetry &amp; Delta Gate<br/>AMD Zen 3 MSE Kernel (0.091 ms) • Speculative MLP (5.37 us)<br/>SQLite WAL Ledger + Migrations • NVMe Checkpoints (3.07 ms)"]
    L2["Layer 2: Probabilistic Gatekeeper<br/>AMD Token Lab d3 Aux-Router (POST /v1/systemone)<br/>State Evaluation &amp; Static Frame Suppression"]
    L3["Layer 3: Multi-Provider Inference (0 MB Local VRAM)<br/>AMD Token Lab (Gemma-4-31B-IT, Qwen3.8-27B, DeepSeek-V4.1-Flash)<br/>Hugging Face Router • NVIDIA NIM • DigitalOcean MI300X<br/>Local DGX Spark (vLLM / Flare) • Local Ollama"]

    UI --> L1 --> L2 --> L3
```

For full architectural specifications, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Verified Hardware Benchmarks

All figures are verified on physical AMD Ryzen hardware via the automated test suite [`tests/run_gamer_hardware_tests.py`](tests/run_gamer_hardware_tests.py).

* **Testbed Configuration:** Lenovo Legion 15
* **CPU:** AMD Ryzen 7 5800H (8 Cores / 16 Threads @ 3.19 GHz, Zen 3 architecture)
* **GPU:** NVIDIA GeForce RTX 3070 Laptop GPU (8 GB GDDR6) — *100% reserved for native display and gaming*
* **Host Memory:** 16 GB DDR4-3200
* **Storage:** PCIe Gen 3.0 x4 NVMe Solid-State Drive
* **OS:** Ubuntu 24.04 LTS on WSL2 / Linux x86_64

| Benchmark Suite | Evaluated Workload | Measured Result | Specification / Frame Budget | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Suite 1: Database Audit** | 50 Inferences, 7 Cards, 20 Checkpoints | Exact count match | 100.0% Local VRAM Saved | **PASS** |
| **Suite 2: Frame Budget** | 100-Frame CPU MSE Delta Timing | **2.713 ms** avg | Consumes 16.28% of 60 FPS (Zero lag) | **PASS** |
| **Suite 3: Laptop Shootout** | 50-Request Monolithic Workload | **14.7x vs modeled 12.7 GB VRAM-spillover baseline**, 90.4% latency drop | 0 MB local VRAM vs 12.7 GB spillover | **PASS** |
| **Suite 4: Chaos Recovery** | 20-Checkpoint NVMe Quick-Save Scan | **3.072 ms** per checkpoint reload | Total 20 CPs scanned in 61.43 ms | **PASS** |
| **Suite 5: Router Ping** | Local Port 5000 API Contract | Deterministic fallback | Verified contract response | **PASS** |
| **Suite 6: AMD Zen 3 Kernel** | 200 Iterations Zen 3 AVX2/FMA Gate | **0.091 ms** avg (**0.158 ms** p99) | Consumes 0.55% of 60 FPS budget | **PASS** |
| **Suite 7: Mobile Hotspot** | 1,000 Frames over Cellular Uplink | **94.0% Bandwidth Reduction** | 385.5 MB / 205.6 s airtime saved | **PASS** |
| **Suite 8: Speculative MLP** | 1,000 Forward Passes (Pure Python) | **5.37 μs** avg latency | Sub-millisecond pre-network host gate | **PASS** |

---

## Comparative Workload Tiering

| Workload Configuration | Hardware Tier | Local VRAM Spillover | AI Throughput | Average Latency (31B) | Client FPS Impact | Operational State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Un-gated Local 31B (Modeled)** | RTX 4080 Laptop (12 GB) | **12.7 GB** spilled to RAM | 4.4 tok/s | 4,850 ms | Drops from 120 -> 19 FPS | Severe Thrashing |
| **Un-gated Local 31B (Modeled)** | RTX 4090 Laptop (16 GB) | **8.6 GB** spilled to RAM | 7.2 tok/s | 3,120 ms | Drops from 144 -> 34 FPS | PCIe Spillover |
| **Lenovo Legion + MemoryOS** | **AMD Ryzen 7 5800H + 8 GB GPU** | **`0 MB` (Zero spillover)** | **64.5 tok/s** | **465 ms** | **0% Drop (Locked 120+ FPS)** | **Verified Production** |
| **Entry Rigs + MemoryOS (Modeled)** | Ryzen 780M / 880M iGPU or RTX 3050 | **`0 MB`** | **64.5 tok/s** | **465 ms** | **0% GPU penalty** | **Supported Baseline** |

---

## Quick Start & Verification

### 1. Prerequisites
* **Python:** `3.10+` (`3.12+` recommended)
* **OS:** Windows 11, Ubuntu / WSL2, or Linux x86_64
* **Dependencies:** Zero external matrix or CUDA framework dependencies required for router and dashboard execution.

### 2. Configuration & Verification

```bash
git clone -b beta https://github.com/JupiterIsland/memoryos.git
cd memoryos

# Copy reference configuration
cp .env.example .env

# Run automated hardware verification suite
PYTHONPATH=. python3 tests/run_gamer_hardware_tests.py
```

### 3. Launching System Interfaces

#### A. Jupiter Studio (Real-Time Hybrid Workstation)
```bash
python3 -B apps/jupiter_studio.py
```
*Access UI:* [http://127.0.0.1:7860](http://127.0.0.1:7860)

#### B. The Quiet Advisor Web Dashboard
```bash
python3 -B apps/quiet_advisor_ui/server.py --port 8765 --db QuietAdvisorDB.sqlite
```
*Access UI:* [http://127.0.0.1:8765](http://127.0.0.1:8765)

#### C. Standalone Core Microservice Router
```bash
python3 -B server.py --host 127.0.0.1 --port 5000 --db QuietAdvisorDB.sqlite
```

---

## Documentation Index

* **[AMD_RELEASE_CANDIDATE.md](AMD_RELEASE_CANDIDATE.md)** — Master Release Candidate Dossier for AMD Developer Relations & Token Lab
* **[ARCHITECTURE.md](ARCHITECTURE.md)** — Complete architectural specification and systems topology
* **[RELEASE_NOTES.md](RELEASE_NOTES.md)** — Production Release Notes for `v1.0.0-RC1`
* **[INSTALL.md](INSTALL.md)** — Enterprise installation and deployment guide
* **[PROOF_OF_RESULTS.md](PROOF_OF_RESULTS.md)** — Verified telemetry audit and Token Lab usage records
* **[VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md)** — Comprehensive static analysis and regression verification

---

## License & Governance

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details. Built and architected by Richard Murray (`JupiterIsland`).
