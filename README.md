# MemoryOS: Decoupled 3-Service Architecture, Quiet Advisor & Jupiter TV Desktop v2

![The Quiet Advisor — Hardware-Aware AI Orchestration & Resource Routing](docs/quiet_advisor_banner.jpg)

> **Written Proof & Production Telemetry Audit (`2026-11-14T09:01:20Z`):** See [PROOF_OF_RESULTS.md](PROOF_OF_RESULTS.md) for the complete AMD Token Lab telemetry ledger (`78 / 10,000,000` micro-points used across `19` requests, `100%` local VRAM saved) and closed-loop verification results.

MemoryOS is a local-first hybrid AI runtime that isolates your local GPU (**NVIDIA RTX 3070 8GB**) from heavy VLM/LLM workloads by routing them through **Quiet Advisor** and **d3 gatekeeping** to **AMD Token Lab** (`https://api.tokenlab.amd.com/v1`), backed by `QuietAdvisorDB.sqlite` WAL telemetry and atomic NVMe JSON checkpoints.

---

## 1. Three-Service Microservice Split ("Dependency Diet")

To eliminate monolithic 15GB dependency bloat (`torch`, `basicsr`, `realesrgan`, `faster-whisper`) from the routing plane, MemoryOS is sliced into three independent services:

| Service | Role & Entrypoint | Dependencies (`requirements-*.txt`) | Target Footprint |
| :--- | :--- | :--- | :--- |
| **1. `memoryos-router`** | Standalone HTTP Brain & Quiet Advisor backend (`python server.py` -> `http://127.0.0.1:5000`), Token Lab API router, DuckDB TLB, SQLite telemetry (`QuietAdvisorDB.sqlite`) | `requirements-router.txt` (`openai`, `duckdb`, `fastapi`, `uvicorn`, `requests`, `pydantic`, `numpy`, `psutil` — **zero PyTorch/OpenCV/PyQt6**) | ~150 MB |
| **2. `jupiter-desktop`** | Thin PyQt6 desktop client (`apps/jupiter-tv-desktop-v2/app.py`) + CPU frame-delta (`cv2`/pure-Python MSE) + `MemoryOSRouterClient` HTTP bridge (`router_client.py`) | `requirements-desktop.txt` (`PyQt6`, `opencv-python-headless`, `requests`, `numpy`, `Pillow`) | Lean UI client |
| **3. `jupiter-vision-worker`** *(Optional)* | Optional local GPU worker only for users who decline AMD Token Lab remote offload | `requirements-vision-worker.txt` (`torch`, `basicsr`, `realesrgan`, `faster-whisper`) | Isolated heavy container |

---

## 2. Closed-Loop Bridge & Hardware Protection Feedback Loop

`jupiter-desktop` never imports `torch` or calls heavy VLMs blindly. Every frame and coding/analysis request follows a closed HTTP feedback loop against `memoryos-router` (`localhost:5000`):

```
Jupiter Desktop (PyQt6 + CPU MSE)
  │
  ├─ 1. POST /api/frame-delta  ──▶  d3 Gatekeeper (router.py / router_service.py)
  │     (mse_delta vs threshold)       └─ Low delta -> skip_vision=True (0 heavy tokens spent)
  │
  ├─ 2. POST /api/route        ──▶  MemoryOS Router (Qwen3.8-27B / Gemma-4-31B-IT / DeepSeek)
  │                                    ├─ Consults quiet_advisor_user_preferences in QuietAdvisorDB.sqlite
  │                                    └─ Logs every request + VRAM usage -> memoryos_inference_log
  │
  ├─ 3. VRAMThrashingDetector  ──▶  Surfaces vram_thrashing card (confidence=0.85) in UI / Toast / Web HUD
  │
  └─ 4. User clicks [Acknowledge & Apply] (POST /api/acknowledge-card)
        └─ Writes vram_thrashing_penalty = 1.5 & force_remote_offload = true
        └─ Subsequent prefer_local=True / VLM calls are BLOCKED locally (local_execution_blocked=True)
           and forced onto Gemma-4-31B-IT on AMD Token Lab (gpu_id="tokenlab-remote")!
```

### Core HTTP Endpoints (`server.py` / `src/memoryos/server.py`)

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Service health check and dependency mode (`fastapi` or stdlib `ThreadingHTTPServer` fallback) |
| `/api/state` | `GET` | Active Quiet Advisor cards, recent `memoryos_inference_log` telemetry, VRAM telemetry, and routing advice |
| `/api/frame-delta` | `POST` | Evaluates `mse_delta` (or `pixel_diff`/`histogram_diff`) through `d3` before calling vision inference |
| `/api/route` | `POST` | Routes `task_type` + `prompt` (e.g., `balanced_code` -> `Qwen3.8-27B`, `vision_ui_parse` -> `Gemma-4-31B-IT`), enforces `vram_thrashing_penalty`, and logs to `QuietAdvisorDB.sqlite` |
| `/api/acknowledge-card` | `POST` | `[Acknowledge & Apply]` webhook that records `vram_thrashing_penalty = 1.5` and `force_remote_offload = true` |
| `/api/detect` | `POST` | Runs `QuietAdvisorEngine` detectors across `QuietAdvisorDB.sqlite` and returns promoted cards |

> **Stdlib Resilience**: On hosts without `fastapi`/`uvicorn` installed, `python server.py` (or `python src/memoryos/server.py`) automatically starts an identical stdlib `ThreadingHTTPServer` HTTP API sharing the exact same `src/memoryos/router_service.py` handlers.

---

## 3. Repository Structure

| File / Module | Purpose |
| :--- | :--- |
| `server.py` & `src/memoryos/server.py` | Standalone `memoryos-router` HTTP service on `localhost:5000` (FastAPI + stdlib `ThreadingHTTPServer` fallback) |
| `src/memoryos/router_service.py` | HTTP-agnostic handlers (`process_frame_delta`, `process_route_request`, `process_acknowledge_card`) shared by FastAPI and stdlib servers |
| `src/memoryos/router.py` | Multi-model AMD Token Lab router (`route_task`, `route_to_gemma`, `gatekeep_frame_with_d3`, `mse_to_frame_delta`, `TASK_TYPE_TO_TIER`) + `vram_thrashing_penalty` local blocking |
| `src/memoryos/quiet_advisor_db.py` | SQLite WAL telemetry & preference store (`QuietAdvisorDB`, `acknowledge_card_sync`, `get_routing_advice_sync`, `record_routed_inference_sync`) |
| `schema.sql` | Canonical SQLite DDL (`memoryos_inference_log`, `quiet_advisor_cards`, `quiet_advisor_user_preferences`, `quiet_advisor_checkpoints`) |
| `quiet_advisor_detectors.py` | Detectors including `VRAMThrashingDetector` (`vram_thrashing`, confidence `0.85`), `ContextWasteDetector`, `ModelThrashingDetector`, `NVMeCheckpointDetector` |
| `quiet_advisor_scheduler.py` | Background scheduler & `CardActionHandler` (`acknowledge` / `action` -> `vram_thrashing_penalty: 1.5`) |
| `quiet_advisor_ui.py` | Standalone PyQt6 bottom-right toast with 400ms fade-in/out and `[Acknowledge & Apply]` action |
| `apps/quiet_advisor_ui/server.py` | Quiet Advisor Web Dashboard + WebSocket server + router bridge endpoints |
| `apps/jupiter-tv-desktop-v2/router_client.py` | Thin desktop HTTP client (`MemoryOSRouterClient`) + CPU MSE delta helper (`compute_mse_delta`) |
| `apps/jupiter-tv-desktop-v2/app.py` & `widgets.py` | Jupiter TV Desktop v2 PyQt6 app wired to `MemoryOSRouterClient` and `[Acknowledge & Apply]` closed-loop button |
| `Dockerfile-router` & `docker-compose-router.yml` | Lean ~150MB `memoryos-router` container definition (zero PyTorch/OpenCV) |
| `requirements-router.txt`, `requirements-desktop.txt`, `requirements-vision-worker.txt` | Separated service dependency manifests (`requirements.txt` -> router, `requirements-tv.txt` -> desktop) |

---

## 4. AMD Token Lab API & Coding Workflow Integration

Configure your `.env` from `.env.example`:

```bash
cp .env.example .env
# Set TOKENLAB_API_KEY=tl-... and TOKENLAB_BASE_URL=https://api.tokenlab.amd.com/v1
```

### Endpoint Schema (`POST /v1/systemone`)
Token Lab's `d3` endpoint requires `state` and `actions` as **JSON objects (`dict`)**, not arrays:
- `surface_now`: High-priority recommendation card or scene-change VLM trigger
- `defer_to_idle`: Queue silently until user is idle
- `ignore_noise`: Skip vision/notification (`skip_vision=True`)

### Option 1: Point VS Code Extensions / Aider Directly at AMD Token Lab

In PowerShell (using your key from `.env`):
```powershell
$env:OPENAI_API_BASE = "https://api.tokenlab.amd.com/v1"
$env:OPENAI_API_KEY  = "<your-TOKENLAB_API_KEY-from-.env>"  # e.g. tl-9aa35a3...

# Run Aider against AMD's 27B coding model
aider --model openai/Qwen3.8-27B
```
For Cline / Continue / Roo Code in VS Code, select **OpenAI Compatible**, set Base URL to `https://api.tokenlab.amd.com/v1`, paste your `TOKENLAB_API_KEY`, and set model ID to `Qwen3.8-27B`.

### Option 2: Route Coding Prompts Through Local `memoryos-router`

Every request sent through your local router at `http://localhost:5000/api/route` is routed to `Qwen3.8-27B` (for `balanced_code`) and logged to `QuietAdvisorDB.sqlite`:

```powershell
$body = @{
    task_type = "balanced_code"
    prompt    = "Write a clean Python HTTP client for MemoryOS frame delta checking."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/route" -Method Post -ContentType "application/json" -Body $body
```

---

## 5. Quick Start

```bash
# 1. Start the lean memoryos-router service (localhost:5000)
pip install -r requirements-router.txt
python server.py --host 127.0.0.1 --port 5000

# 2. (Optional) Initialize sample telemetry & run detectors
python bootstrap.py

# 3. Launch Jupiter TV Desktop v2 (in another terminal)
pip install -r requirements-desktop.txt
python apps/jupiter-tv-desktop-v2/app.py

# 4. Or launch the Quiet Advisor Web UI / standalone toast
python apps/quiet_advisor_ui/server.py --port 5000
python quiet_advisor_ui.py
```

Or run the lean router container via Docker Compose:
```bash
docker compose -f docker-compose-router.yml up --build
```
