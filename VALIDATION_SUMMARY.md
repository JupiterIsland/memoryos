# MemoryOS Developer Preview v0.1 — Hostile Validation Summary

**Version:** `v0.1.0-preview`  
**Audit Date:** `2026-11-14`  
**Repository:** `https://github.com/JupiterIsland/memoryos`

---

## 1. Static Analysis & Syntax Audit (`74` Active Python Files)

- **Scope:** All `74` active Python source files across `src/memoryos/`, `apps/quiet_advisor_ui/`, `apps/jupiter-tv-desktop-v2/`, `apps/shared/`, `apex_core/`, `backend/`, `engine/`, and root entrypoints (`server.py`, `bootstrap.py`, `verify_all_systems.py`, `quiet_advisor_detectors.py`, `quiet_advisor_scheduler.py`, `quiet_advisor_ui.py`).
- **Result:** **`74 / 74` files passed `ast.parse()` with `0` syntax errors.**
- **Dependency Diet Enforcement:** AST import scan confirmed **zero** `torch`, `basicsr`, `realesrgan`, or `faster-whisper` imports inside `src/memoryos/server.py`, `src/memoryos/router_service.py`, `src/memoryos/router.py`, `src/memoryos/quiet_advisor_db.py`, `requirements-router.txt`, and `requirements-desktop.txt`.

---

## 2. Import Audit & Fixes Applied

| File | Issue Identified | Fix Applied |
| :--- | :--- | :--- |
| `src/memoryos/cli.py` | `from memoryos.core.heatstream import HeatStream` imported a non-existent module name (`heatstream` without underscore) and `subparsers.add_parser("heat")` was placed **after** `parser.parse_args()`. | Moved `subparsers.add_parser("heat")` before `parser.parse_args()`, added `_SRC_DIR` path bootstrap, and updated import to `from memoryos.core.heat_stream import MemoryHeatStream`. |
| `apps/quiet_advisor_ui/api.py` | Calling `run_detection_cycle()` or `apply_card_action()` from inside an active `asyncio` event loop (e.g., `verify_all_systems.py` / `SceneAnalyzer.recap()`) raised `RuntimeError` inside `asyncio.run()` and emitted `RuntimeWarning: coroutine 'run_detection_cycle.<locals>._run' was never awaited`. | Added `_run_coro_sync()` helper that detects an active event loop (`asyncio.get_running_loop()`) and dispatches the coroutine via a single-worker `ThreadPoolExecutor`, eliminating the `RuntimeWarning`. |
| `src/memoryos/router.py` | In offline heuristic mode (`_local_d3_fallback()`), short coding prompts without an explicit `task_type` fell through to `fast_light` (`MiniCPM5-2B`) because `len(state_text) < 260` was evaluated before coding keywords. | Added coding/architecture keyword match (`python`, `function`, `code`, `class`, `refactor`, `architecture`, `sql`, `bug`) before `fast_light` so code prompts deterministically route to `balanced_code` (`Qwen3.8-27B`). |

---

## 3. Dead Code & Orphan File Cleanup

| File / Artifact | Issue Identified | Action Taken |
| :--- | :--- | :--- |
| `appsjupiter-tv-cl.txt` | Stray malformed root file created by stripped Windows backslashes (`apps\jupiter-tv-cli\...`). | Deleted from repository. |
| `appsjupiter-tv-cliconfig.py` | Orphaned duplicate config file at repository root with no callers. | Deleted from repository. |
| `appsjupiter-tv-climain.py` | Orphaned duplicate CLI file at repository root with no callers. | Deleted from repository. |
| `src/memoryos/SECURITY_SUMMARY.md` & `src/memoryos/START_HERE.md` | Contained unredacted `tl-9aa35a3...` API key literal from an earlier external agent session. | Scrubbed and replaced with `tl-9aa35a3...<REDACTED>`; verified `0` secret hits across all tracked files. |

---

## 4. Router & Dashboard Integration Verification

Verified live against `memoryos-router` (`http://127.0.0.1:5000`) and `QuietAdvisorDB.sqlite`:
- **`GET /health`**: Returns `200 OK` (`{"status": "healthy", "services": {"heat_stream": true, "quiet_advisor_db": true, "tlb": true}}`).
- **`GET /api/state`**: Returns live `active_cards`, `archived_cards`, `telemetry` (`26` total inferences, `100.0%` remote offload, `0 MB` local VRAM consumed), `preferences`, `checkpoints`, and `tokenlab` grant ledger (`78 / 10,000,000` micro-points used).
- **`POST /api/detect`**: Runs `QuietAdvisorScheduler` across `VRAMThrashingDetector`, `ContextWasteDetector` (`~93%` unused context window detection), `ModelThrashingDetector`, and `NVMeCheckpointDetector`.
- **`POST /api/acknowledge-card`**: Closes the loop from UI `[Acknowledge & Apply]` clicks -> writes `vram_thrashing_penalty = 1.5` and `force_remote_offload = true` to `quiet_advisor_user_preferences` -> blocks local GPU execution (`local_execution_blocked = True`) on subsequent `POST /api/route` requests.

---

## 5. Jupiter Desktop (`apps/jupiter-tv-desktop-v2/`) Integration Verification

- **HTTP Client (`quiet_advisor_client.py` & `router_client.py`)**:
  - `extract_cv2_frame()` decodes `cv2` BGR frames from `QVideoSink` PNG snapshots or `cv2.VideoCapture`.
  - `compute_mse_delta()` calculates 160x90 grayscale `float32` CPU MSE (`mse_delta` and normalized `mse`).
  - `QuietAdvisorClient` communicates with `/api/frame-delta`, `/api/route`, and `/api/acknowledge-card` with automatic offline fallback.
- **PyQt6 Video Playback Loop (`app.py`)**:
  - `on_playback_state_changed()` intercepts `QMediaPlayer.PlaybackState.PausedState`.
  - `update_slider_position()` detects scene transitions across `self.scene_markers`.
  - `evaluate_video_loop_frame()` runs CPU MSE delta -> `check_frame_delta()` -> skips static frames (`skip_vision = True`) or routes scene cuts (`skip_vision = False`) to `Gemma-4-31B-IT`.

---

## 6. Token Lab Routing Paths Verification

| Routing Tier | Task Type / Trigger | Target Model | Endpoint | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Probabilistic Gatekeeper** | Frame delta & card significance | `d3` | `POST /v1/systemone` | **Verified** (`15` calls, dict schema locked) |
| **Vision Heavy (VLM)** | `vision_heavy` / `vision_ui_parse` / image input | `Gemma-4-31B-IT` | `POST /v1/chat/completions` | **Verified** (`2` Token Lab + `6` local DB runs, prompt cache active) |
| **Balanced Code & Arch** | `balanced_code` / `heavy_architecture` | `Qwen3.8-27B` | `POST /v1/chat/completions` | **Verified** (`1` Token Lab + `2` local DB runs, reasoning tokens active) |
| **Fast Light (Edge)** | `fast_light` / `edge_compression` | `MiniCPM5-2B` | `POST /v1/chat/completions` | **Verified** (`1` Token Lab + `1` local DB run) |
| **Fast Code Routing** | `fast_code_routing` / `long_context` | `DeepSeek-V4.1-Flash` | `POST /v1/chat/completions` | **Verified** (configured & seeded in telemetry) |

---

## 7. Remaining Risks & Mitigations (`v0.1` Developer Preview)

1. **API Key Rotation**: Because `tl-9aa35a3...` appeared in an earlier chat session, run `.\Rotate-TokenLabKey.ps1 -Force` to issue a fresh Token Lab key in `.env` and revoke the old prefix in the AMD console.
2. **Optional Local Vision Worker (`requirements-vision-worker.txt`)**: Local PyTorch/RealESRGAN/Whisper execution is intentionally excluded from the default ~150MB router and desktop installs; users who want offline local VLM inference without AMD Token Lab must install `requirements-vision-worker.txt` separately.
3. **Windows File Locking on SQLite WAL**: When running inside cloud-synced folders (such as Google Drive `My Drive`), SQLite WAL mode can occasionally encounter file-sync locks under heavy concurrency; `QuietAdvisorDB` includes an automatic fallback to `/tmp/QuietAdvisorDB.sqlite` (or `QUIET_ADVISOR_DB` env override) if the primary path is locked.
