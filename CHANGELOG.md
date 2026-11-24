# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-RC1] - 2026-11-15

### Added
- **Formal Release Candidate Milestone for AMD Developer Relations & AMD Token Lab**:
  - Authored comprehensive technical release candidate dossier (`AMD_RELEASE_CANDIDATE.md`) covering architectural topology, benchmark matrices, hardware profiles, and deployment guides.
  - Designed official vector brand identity and banner assets (`assets/memoryos_executive_banner.svg`, `assets/memoryos_logo_mark.svg`, `assets/jupiter_studio_logo.svg`).
  - Integrated high-tech vector branding directly into Jupiter Studio and Quiet Advisor UI headers.
- **Speculative Offload MLP Decision Engine (`src/memoryos/speculative_offload.py`)**:
  - Implemented pure-Python `SpeculativeOffloadModel` forward pass computing $P(\text{offload})$ in 5.37 μs (`suite_8`), enabling sub-millisecond host-side gating before any network call.
- **Suite 7 (Mobile Hotspot Efficiency) & Suite 8 (Speculative MLP Speed) in Benchmark Suite**:
  - Expanded `tests/run_gamer_hardware_tests.py` to 8 complete benchmark suites covering database audits, 60/144 FPS frame budgets, laptop shootouts, NVMe recovery, live router pings, AMD Zen 3 kernels, cellular tethering, and microsecond MLP execution.
- **Jupiter Studio Hybrid AI Workstation (`apps/jupiter_studio.py`)**:
  - Standalone zero-dependency Python desktop workstation featuring real-time Server-Sent Events (SSE) token streaming, multi-provider execution switching, workspace context packing, and Copilot bundle export.
- **Multi-Cloud Failover to DigitalOcean Serverless AMD Instinct MI300X**:
  - Implemented `do_client`, `DO_MODEL_MAP`, and `get_cloud_provider_status()` in `src/memoryos/router.py` targeting `https://inference.do-ai.run/v1`.
- **NVIDIA NIM / Brev OpenAI-Compatible Routing**:
  - Added support for routing across NVIDIA NIM / Brev endpoints alongside AMD Token Lab.
- **Multi-Vendor GPU & Handheld APU Detection (`src/memoryos/gpu_backends.py`)**:
  - Added unified detector for NVIDIA (`nvidia-smi`), AMD sysfs (`0x1002`), and handheld gaming APUs (`ROG Ally`, `Legion Go`, `Steam Deck`).

### Changed
- **Architectural Specification Modernization**:
  - Fully rewrote `ARCHITECTURE.md` into an executive-grade four-tier architectural blueprint covering MemoryOS core, Quiet Advisor telemetry, AMD Token Lab cloud offloading, and client applications.
- **README & User-Facing Documentation Overhaul**:
  - Upgraded `README.md`, `RELEASE_NOTES.md`, and `BETA_RELEASE_NOTES.md` with executive-grade phrasing, verified benchmark tables, and clear technical framing.
- **Elevated Operator Primer**:
  - Transformed `MEMORYOS_FOR_DUMMIES.md` into an executive architecture and operator primer, eliminating informal analogies while maintaining accessibility.

### Verified Hardware Benchmarks (`tests/run_gamer_hardware_tests.py`)
- **Suite 1 (Database Audit):** 50 Inferences, 7 Cards, 20 Checkpoints, 100.0% local VRAM saved.
- **Suite 2 (Frame Budget):** 2.713 ms avg CPU MSE gate (16.28% of 60 FPS budget).
- **Suite 3 (Laptop Shootout):** 14.7x vs modeled 12.7 GB VRAM-spillover local baseline; 0 MB local VRAM used.
- **Suite 4 (Chaos Recovery):** 3.072 ms per checkpoint reload across 20 quick-saves.
- **Suite 5 (Router Contract):** Safe offline deterministic contract fallback.
- **Suite 6 (Zen 3 Kernel):** 0.091 ms avg CPU gate on AMD Ryzen 7 5800H (0.55% 60 FPS budget).
- **Suite 7 (Mobile Hotspot):** 94.0% cellular bandwidth reduction over iPhone XR LTE hotspot.
- **Suite 8 (Speculative MLP):** 5.37 μs average neural forward pass latency.

---

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
  - Real-time web UI and REST API displaying telemetry from `QuietAdvisorDB.sqlite` with live GPU FREE, VRAM SAVED, and INF/s badges.
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

### Fixed
- **Async Event-Loop Safety** (`apps/quiet_advisor_ui/api.py`): Resolved `RuntimeWarning: coroutine was never awaited` via `_run_coro_sync()`.
- **Short Code Prompt Routing** (`src/memoryos/router.py`): Resolved keyword evaluation precedence in `_local_d3_fallback()`.
- **CLI `heat` Subparser Bug** (`src/memoryos/cli.py`): Registered subparser before `parse_args()` and fixed imports.
