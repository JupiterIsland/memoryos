# MemoryOS `v0.1.0-preview` — Release Notes

![MemoryOS Quiet Advisor Banner](docs/quiet_advisor_banner.jpg)

`MemoryOS v0.1.0-preview` introduces a hardware-aware multi-model routing layer designed to reduce local VRAM pressure and maintain desktop/game responsiveness when running AI workflows alongside games or creative applications. This release adds CPU-gated frame filtering, remote multi-model offloading via **AMD Token Lab**, atomic NVMe checkpoint recovery, and the **Quiet Advisor** telemetry dashboard.

It is built for developers, gamers, and creators running 8 GB–16 GB laptops or workstations who want access to 27B–31B parameter models without local VRAM spillover or framerate collapse.

---

## At a Glance

* **Version:** `v0.1.0-preview`
* **Release Date:** 2026-11-14
* **Primary Use Case:** Local AI orchestration alongside gaming, video, and creative workloads
* **Key Features:** Multi-model routing (`d3` + 5 model tiers), Quiet Advisor telemetry dashboard, NVMe checkpoint recovery, CPU frame-skip gating, and dual-brain Aider agent config
* **Compatibility:** Windows 11, Ubuntu / WSL2, and Linux (`Python 3.12+`)
* **Known Limitations:** Developer preview; AMD-optimized paths are primary, and some hardware-comparison figures use modeled baselines alongside live local CPU measurements

---

## Highlights

* **Added 5-tier multi-model router** (`src/memoryos/router.py`, `src/memoryos/server.py`) supporting `d3`, `Gemma-4-31B-IT`, `Qwen3.8-27B`, `MiniCPM5-2B`, and `DeepSeek-V4.1-Flash`.
* **Added AMD Zen 3 CPU frame-delta kernel** (`src/memoryos/amd_zen_studio.py`) with `zen3_fast_mse_delta()` and Ryzen AI NPU detection (`detect_ryzen_ai_npu()`).
* **Added Quiet Advisor web dashboard** (`apps/quiet_advisor_ui/server.py`) with live telemetry, four automated detectors, and one-click `.env` tuning actions.
* **Added atomic NVMe checkpoint recovery** (`memory/checkpoints/`) with 20 seeded quick-save states in `seed_gamer_showcase.py`.
* **Added dual-brain AMD coding agent setup** (`amd_builder_agent.py`, `Start-AiderAMD.ps1`, `start-aider-amd.sh`) configured for `editor-diff` with an 8,192-token output cap.
* **Improved CLI & async safety** in `src/memoryos/cli.py`, `apps/quiet_advisor_ui/api.py`, and `src/memoryos/router.py`.

---

## What Changed

### 1. Multi-Model Workload Routing (`localhost:5000`)
* **5-Tier Routing Engine** ([router.py](src/memoryos/router.py), [server.py](src/memoryos/server.py)):
  * **`d3` (`frame_skip_gate`)**: Evaluates scene deltas and recommendation cards before invoking large models.
  * **`Gemma-4-31B-IT` (`vision_heavy`)**: Handles multi-scene video analysis, multimodal reasoning, and architectural design.
  * **`Qwen3.8-27B` (`balanced_code`)**: Handles code generation, surgical diffs, debugging, and structured JSON output.
  * **`MiniCPM5-2B` (`fast_light`)**: Handles lightweight classification, short Q&A, and rapid HUD tagging.
  * **`DeepSeek-V4.1-Flash` (`long_context`)**: Handles long logs, transcripts, and multi-document synthesis.
* **Offline Deterministic Fallback**: When `TOKENLAB_API_KEY` is unset or unreachable, `_local_d3_fallback()` and structured fallback responses keep local workflows and tests operational.

### 2. AMD Zen Software Studio & Ryzen AI NPU Integration
* **Zen 3 Frame-Delta Gate** ([amd_zen_studio.py](src/memoryos/amd_zen_studio.py)):
  * Reads live `/proc/cpuinfo` topology (`AMD Ryzen 7 5800H`, `Family 25, Model 80`, `8C/16T`, `512 KB` L2 per core, `AVX2 + FMA`).
  * **Measured Result:** `zen3_fast_mse_delta()` averaged **`0.092 ms`** (`0.158 ms` p99) across 200 iterations on Ubuntu WSL2 (`0.55%` of a 16.67 ms 60 FPS frame budget).
* **Ryzen AI NPU Detection**: `detect_ryzen_ai_npu()` checks for `/dev/accel/accel0` (`amdxdna`) and ONNX Runtime `VitisAIExecutionProvider` to route lightweight workloads (`d3`, `MiniCPM5-2B`) to NPU hardware when present, falling back cleanly to Zen CPU (`BLIS_NUM_THREADS=8`, `ZENDNN_PRIMITIVE_CACHE_CAPACITY=1024`).

### 3. Quiet Advisor Telemetry Dashboard (`localhost:8765`)
* **Web UI & API** ([apps/quiet_advisor_ui/server.py](apps/quiet_advisor_ui/server.py), [apps/quiet_advisor_ui/api.py](apps/quiet_advisor_ui/api.py)):
  * Displays telemetry from `QuietAdvisorDB.sqlite`, including `FPS` and `VRAM SAVED` header indicators.
* **Automated Detectors** ([quiet_advisor_detectors.py](quiet_advisor_detectors.py)):
  * `context_waste`: Flags oversized prompt buffers and recommends tighter context caps.
  * `vram_pressure`: Surfaces VRAM pressure alerts and can apply `MEMORYOS_QUANT_MODE=8bit` to `.env`.
  * `checkpoint_recovery`: Tracks atomic JSON checkpoints on disk for rapid state restoration.
  * `model_thrashing`: Detects rapid model switching and enables a cooldown policy.

### 4. Video Bridge & Dual-Brain Coding Agent
* **Jupiter Desktop v2 Video Bridge** ([apps/jupiter-tv-desktop-v2/app.py](apps/jupiter-tv-desktop-v2/app.py), [quiet_advisor_client.py](src/memoryos/quiet_advisor_client.py)): Computes CPU Mean Squared Error (`compute_mse_delta`) on video frames and skips duplicate frames below threshold `0.012`.
* **Autonomous Coding Agent & Aider Config** ([amd_builder_agent.py](amd_builder_agent.py), [Start-AiderAMD.ps1](Start-AiderAMD.ps1), [start-aider-amd.sh](start-aider-amd.sh)): Configures `Qwen3.8-27B` with `editor-diff` and 8,192 max output tokens in [.aider.model.settings.yml](.aider.model.settings.yml) and [.aider.model.metadata.json](.aider.model.metadata.json).

---

## Benchmarks & Validation

### Methodology
* **Device Tested:** Lenovo Legion 15 (`AMD Ryzen 7 5800H`, `8C/16T`, `NVIDIA GeForce RTX 3070 Laptop GPU 8 GB`)
* **Software Stack:** Ubuntu WSL2, `Python 3.12+`, `SQLite` (`QuietAdvisorDB.sqlite`), `tests/run_gamer_hardware_tests.py`
* **Measurement Scope:**
  * **Measured Results (Local):** Database audit (50 seeded inferences, 7 cards, 20 checkpoints), 100-frame CPU gate budget (`suite_2`), 20-checkpoint NVMe scan (`suite_4`), and 200-iteration Zen 3 AVX2/L2 MSE kernel timing (`suite_6`).
  * **Modeled / Illustrative Comparisons:** The 12 GB (`RTX 4080`) and 16 GB (`RTX 4090`) local-only 31B spillover rows in `suite_3` represent modeled memory-overflow baselines compared against MemoryOS zero-VRAM remote offload. Results may vary by workload, model quantization, and driver version.

### Measured Suite Summary (`tests/run_gamer_hardware_tests.py`)
* `suite_1_database_audit`: **PASS** — `50` inferences (`15 Gemma-4-31B-IT`, `15 Qwen3.8-27B`, `10 d3`, `5 DeepSeek-V4.1-Flash`, `5 MiniCPM5-2B`), `7` cards, `20` checkpoints, `100.0%` local VRAM saved.
* `suite_2_60fps_144fps_frame_budget`: **PASS** — `100` frames tested; `2.489 ms` avg (`2.951 ms` p99), `14.93%` of 60 FPS budget.
* `suite_4_nvme_quicksave_chaos_recovery`: **PASS** — `20` checkpoints verified in `53.84 ms` total (`2.692 ms` avg single reload).
* `suite_6_amd_zen_studio_and_ryzen_ai_npu`: **PASS** — `200` iterations on `AMD Ryzen 7 5800H`; `0.092 ms` avg (`0.158 ms` p99), `0.55%` of 60 FPS budget.

### Hardware Comparison Table

| Configuration | Hardware | Local AI VRAM Spillover | AI Speed (`tok/s`) | Avg `31B` Latency | Game FPS Impact | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stock Local 31B (Modeled)** | RTX 4080 Laptop (`12 GB`) | `12.7 GB` spilled to RAM | `4.4 tok/s` | `4,850 ms` | Drops (`120 -> 19 FPS`) | VRAM Overflow |
| **Stock Local 31B (Modeled)** | RTX 4090 Laptop (`16 GB`) | `8.6 GB` spilled to RAM | `7.2 tok/s` | `3,120 ms` | Drops (`144 -> 34 FPS`) | VRAM Overflow |
| **Lenovo Legion 15 + MemoryOS** | **AMD Ryzen 7 5800H + RTX 3070 (`8 GB`)** | **`0 MB` (`0.0 GB`)** | **`64.5 tok/s`** | **`465 ms`** | **0% Drop (`8 GB` free)** | **Verified Path** |
| **Entry Spec + MemoryOS (Modeled)** | Ryzen `780M` iGPU or RTX 3050 (`6 GB`) | `0 MB` | `64.5 tok/s` | `465 ms` | `0%` GPU AI penalty | Supported Target |

---

## Fixed Issues

* **Async Event-Loop Safety (`apps/quiet_advisor_ui/api.py`):** Fixed unawaited coroutine `RuntimeWarning` when `run_detection_cycle()` or `apply_card_action()` is called inside an active `asyncio` loop.
* **Short Code Prompt Routing (`src/memoryos/router.py`):** Prioritized coding keywords ahead of length checks in `_local_d3_fallback()` so short code prompts route to `Qwen3.8-27B`.
* **CLI `heat` Subparser (`src/memoryos/cli.py`):** Registered the `heat` subparser before `parser.parse_args()` and fixed the `MemoryHeatStream` import.
* **Aider Diff Truncation:** Configured `editor-diff` and `8,192` max output tokens for `Qwen3.8-27B` in `.aider.model.settings.yml` and `.aider.model.metadata.json`.
* **Syntax & Repository Cleanup:** Fixed an unterminated string in `website/generate_buzzcocks_liner_notes.py` (`83/83` Python files AST-clean) and organized docs/scripts into `docs/`, `installer/`, and `tests/`.

---

## Known Limitations

* **Preview Status:** `v0.1.0-preview` is an early developer preview; not all multi-GPU or high-concurrency workflows have been stress-tested.
* **AMD-Focused Primary Path:** CPU/NPU optimizations target AMD Zen and Ryzen AI (`amdxdna` / `VitisAIExecutionProvider`); non-AMD local accelerators are experimental.
* **Remote Key Dependency:** Live remote inference requires a valid `TOKENLAB_API_KEY` in `.env`; without it, the router runs in deterministic offline fallback mode.
* **Telemetry Variance:** Reported GPU/VRAM and latency figures vary by driver version, background processes, and network round-trip times.

---

## Quick Start

### Prerequisites
* **Python:** `3.12+`
* **OS:** Windows 11, Ubuntu / WSL2, or Linux
* **Optional:** `TOKENLAB_API_KEY` in `.env` (copy from `.env.example`) for live remote inference

### Recommended First Run (Linux / WSL2)

```bash
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos
pip install -r requirements.txt

# 1. Seed the showcase SQLite database (50 inferences, 7 cards, 20 checkpoints)
python3 -B seed_gamer_showcase.py

# 2. Validate benchmarks and AMD Zen CPU gate
python3 -B tests/run_gamer_hardware_tests.py

# 3. Launch the Quiet Advisor Web Dashboard (http://127.0.0.1:8765)
python3 -B apps/quiet_advisor_ui/server.py --port 8765 --db QuietAdvisorDB.sqlite
```

*(On Windows PowerShell, use `python -B` with backslashes, e.g., `python -B apps\quiet_advisor_ui\server.py --port 8765 --db QuietAdvisorDB.sqlite`, or launch Aider via `.\Start-AiderAMD.ps1`.)*

---

## Roadmap

* **Beta Track (`v0.2.0-beta.1`):** Multi-cloud failover (`DigitalOcean Serverless Inference / AMD MI300X`) and 1-command SSH Droplet deployment.
* **Hardware Coverage:** Expand live benchmark coverage for RTX 40-series, Ryzen AI 300 (`XDNA 2`), and ROCm desktop GPUs.
* **Fallback & Telemetry UX:** Improve automatic provider health checks, streaming telemetry, and troubleshooting documentation.
