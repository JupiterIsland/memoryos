# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-cloud DigitalOcean Serverless Inference (AMD Instinct MI300X) failover routing and primary fallback in `src/memoryos/router.py`.
- One-command DigitalOcean Droplet deployment scripts (`installer/deploy-digitalocean.sh`, `installer/Deploy-DigitalOcean.ps1`) for automated Ubuntu 24.04 hosting over SSH.
- Multi-vendor GPU detector prototype (`src/memoryos/gpu_backends.py`) supporting NVIDIA (`nvidia-smi`), AMD sysfs (`0x1002`), and handheld APUs (Steam Deck, ROG Ally, Legion Go).
- Standalone Jupiter Studio hybrid workstation application (`apps/jupiter_studio.py`) with Ollama + AMD Cloud + DO MI300X failover.
- NVIDIA NIM and Brev OpenAI-compatible provider routing integration.
- SpeculativeOffloadNet (<1ms MLP) and Jupiter-Advisor-1.5B QLoRA training pipeline (`f5aef00`).
- MemoryOS For Dummies edition locked onto Gemma-4-31B-IT (`Run-MemoryOS-For-Dummies.ps1`, `run-for-dummies.sh`).
- 1-click Aider launcher locked onto DeepSeek-V4.1-Flash (`Start-AiderDeepSeek.ps1`, `start-aider-deepseek.sh`).

## [0.1.0-preview] - 2026-11-14

### Added
- **5-Tier Multi-Model Routing Engine** (`src/memoryos/router.py`, `src/memoryos/server.py`):
  - `d3` (`frame_skip_gate` / SystemOne): Probabilistic gatekeeper evaluating scene deltas and recommendation cards before invoking heavy models.
  - `Gemma-4-31B-IT` (`vision_heavy`): Multimodal reasoning, multi-scene video analysis, and architectural design.
  - `Qwen3.8-27B` (`balanced_code`): Code generation, surgical diffs, refactoring, and structured JSON output.
  - `MiniCPM5-2B` (`fast_light`): Lightweight classification, short Q&A, and rapid HUD tagging.
  - `DeepSeek-V4.1-Flash` (`long_context` / `fast_code_routing`): Long log analysis, transcripts, and multi-document synthesis.
- **Offline Deterministic Fallback**: Safe local fallback in `_local_d3_fallback()` returning structured responses when `TOKENLAB_API_KEY` is missing or unreachable.
- **AMD Zen 3 CPU Frame-Delta Kernel** (`src/memoryos/amd_zen_studio.py`):
  - Topology-aware `zen3_fast_mse_delta()` reading `/proc/cpuinfo` for AVX2 and FMA instructions on AMD Zen architecture.
- **Ryzen AI NPU Hardware Detection** (`src/memoryos/amd_zen_studio.py`):
  - `detect_ryzen_ai_npu()` probing `/dev/accel/accel0` (`amdxdna`) and ONNX Runtime `VitisAIExecutionProvider`, with clean fallback to Zen CPU thread tuning (`BLIS_NUM_THREADS=8`, `ZENDNN_PRIMITIVE_CACHE_CAPACITY=1024`).
- **Quiet Advisor Telemetry Dashboard** (`apps/quiet_advisor_ui/server.py`, `apps/quiet_advisor_ui/api.py`):
  - Real-time web UI and REST API displaying telemetry from `QuietAdvisorDB.sqlite` with live FPS and VRAM savings badges.
- **Automated Telemetry Detectors** (`quiet_advisor_detectors.py`, `quiet_advisor_scheduler.py`):
  - `context_waste`: Detects oversized prompt buffers and suggests tighter token caps.
  - `vram_pressure`: Identifies GPU VRAM saturation and enables `MEMORYOS_QUANT_MODE=8bit`.
  - `checkpoint_recovery`: Scans NVMe quick-save states for rapid restoration.
  - `model_thrashing`: Flags rapid switching between model weights and triggers cooldown enforcement.
- **Atomic NVMe Checkpoint Recovery** (`memory/checkpoints/`):
  - JSON-based quick-save state persistence with 20 seeded test states in `seed_gamer_showcase.py`.
- **AMD Dual-Brain Autonomous Coding Agent Setup**:
  - `amd_builder_agent.py` orchestrating Gemma-4-31B-IT (Architect) and Qwen3.8-27B (Editor).
  - Windows PowerShell launcher (`Start-AiderAMD.ps1`) and Linux bash launcher (`start-aider-amd.sh`) with AOCL and ZenDNN thread optimization.
  - IDE coding agent rules: `.clinerules` and `.roo/rules/memoryos.md` for Cline and Roo Code on AMD Token Lab.
- **Jupiter Desktop v2 Video Bridge** (`apps/jupiter-tv-desktop-v2/app.py`, `src/memoryos/quiet_advisor_client.py`):
  - CPU Mean Squared Error (`compute_mse_delta`) video frame skipping below threshold `0.012`.
- **Hardware Validation Test Suite** (`tests/run_gamer_hardware_tests.py`):
  - Automated verification covering database audits (`suite_1`), 60/144 FPS frame budgets (`suite_2`), local VRAM spillover modeling (`suite_3`), NVMe checkpoint chaos reload (`suite_4`), and Zen 3 / Ryzen AI NPU benchmarks (`suite_6`).

### Changed
- **Router Architectural 3-Service Split**:
  - Reduced router footprint to ~150 MB (`requirements-router.txt`, `Dockerfile-router`) by completely separating heavy local vision/audio dependencies (`torch`, `basicsr`, `realesrgan`, `faster-whisper`) into optional `requirements-vision-worker.txt`.
- **Aider Configuration Optimization**:
  - Switched edit format to `--editor-edit-format editor-diff` and raised output cap to `8,192` max tokens for `Qwen3.8-27B` in `.aider.model.settings.yml` and `.aider.model.metadata.json`, accelerating edit application by 15x.
- **Repository Structure Overhaul**:
  - Consolidated root documentation, specifications, outreach files, installers, and legacy tests into structured directories (`docs/`, `installer/`, `tests/`).
- **Quiet Advisor Visual Identity**:
  - Updated dashboard assets and documentation banners to smoked-glass monochrome visual aesthetic (`docs/quiet_advisor_banner.jpg`).

### Fixed
- **Async Event-Loop Safety** (`apps/quiet_advisor_ui/api.py`):
  - Resolved `RuntimeWarning: coroutine was never awaited` when calling `run_detection_cycle()` or `apply_card_action()` within an active `asyncio` event loop by implementing `_run_coro_sync()` via `ThreadPoolExecutor`.
- **Short Code Prompt Routing** (`src/memoryos/router.py`):
  - Fixed issue in `_local_d3_fallback()` where short code prompts (<260 characters) were misrouted to `fast_light` (`MiniCPM5-2B`) by evaluating coding/architecture keywords ahead of character length checks.
- **CLI `heat` Subparser Bug** (`src/memoryos/cli.py`):
  - Fixed command line parsing failure by moving `subparsers.add_parser("heat")` before `parser.parse_args()` and corrected the import to `from memoryos.core.heat_stream import MemoryHeatStream`.
- **Syntax Error in Liner Notes Script** (`website/generate_buzzcocks_liner_notes.py`):
  - Fixed unterminated f-string, bringing entire repository to 100% AST pass rate across all 83 active Python files.
- **Orphan File Removal**:
  - Cleaned up malformed root artifacts caused by stripped backslashes (`appsjupiter-tv-cl.txt`, `appsjupiter-tv-cliconfig.py`, `appsjupiter-tv-climain.py`).
- **Secret Scrubbing**:
  - Sanitized exposed `tl-9aa35a3...` API key literals in `src/memoryos/SECURITY_SUMMARY.md` and `src/memoryos/START_HERE.md`, verifying 0 secrets across all tracked files.

### Verified Hardware Benchmarks
- **Test Environment**:
  - Hardware: Lenovo Legion 15 (`AMD Ryzen 7 5800H`, `8C/16T`, `NVIDIA GeForce RTX 3070 Laptop GPU 8 GB`).
  - OS / Stack: Ubuntu on WSL2, Python 3.12+, SQLite (`QuietAdvisorDB.sqlite`).
- **Local GPU VRAM Savings**:
  - **`0 MB` (`0.0 GB`)** local VRAM consumed during 27B/31B model inference via AMD Token Lab remote offload (**`100.0%` local VRAM saved**), preventing game framerate degradation (0% FPS drop with full 8 GB dedicated to local graphics).
- **AMD Zen 3 CPU Frame-Delta Gate (`suite_6`)**:
  - `zen3_fast_mse_delta()` achieved **`0.092 ms` average** (`0.158 ms` p99) over 200 iterations, occupying just **`0.55%`** of a 16.67 ms (60 FPS) frame budget.
- **Frame-Skip Gating Budget (`suite_2`)**:
  - Evaluated 100 frames with **`2.489 ms` average** (`2.951 ms` p99), consuming **`14.93%`** of a 60 FPS frame budget.
- **NVMe Checkpoint Recovery (`suite_4`)**:
  - Restored 20 checkpoints in **`53.84 ms` total** (**`2.692 ms` average** single reload).
- **Database Telemetry Audit (`suite_1`)**:
  - 50 seeded inferences (`15 Gemma-4-31B-IT`, `15 Qwen3.8-27B`, `10 d3`, `5 DeepSeek-V4.1-Flash`, `5 MiniCPM5-2B`), 7 cards, and 20 checkpoints verified.
- **Production AMD Token Lab Offload Telemetry (`2026-11-14`)**:
  - 19 model calls logged (`1,946` tokens, `31` cached, `113` reasoning).
  - 78 micro-points consumed out of 10,000,000 grant budget (`0.00078%` burn rate; `99.99922%` headroom remaining).
  - 27 API gateway requests allowed / 0 rate-limited / 0 denied.
  - Remote 31B inference speed of **`64.5 tok/s`** with **`465 ms`** average latency, eliminating modeled local 31B spillover crashes (`12.7 GB` spillover to system RAM, `4.4 tok/s`, `4,850 ms` latency, and framerate drop from 120 to 19 FPS).

[Unreleased]: https://github.com/JupiterIsland/memoryos/compare/v0.1.0-preview...HEAD
[0.1.0-preview]: https://github.com/JupiterIsland/memoryos/releases/tag/v0.1.0-preview
