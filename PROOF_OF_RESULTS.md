# Proof of Results & Production Telemetry Audit — MemoryOS + The Quiet Advisor

![The Quiet Advisor — Hardware-Aware AI Orchestration & Resource Routing](docs/quiet_advisor_banner.jpg)

**Audit Timestamp:** `2026-11-14T09:01:20.170720Z`  
**Account / Grant Holder:** `RJMedia.ai@outlook.com` (`RJMedia.ai`)  
**AMD Token Lab Access Grant ID:** `1e13760b-0ff8-4528-9a2d-53d672a88dd2`  
**Subject ID:** `nb-ecd408cf0bf2975f8b2da9c1ea53ac50d0aa689217dbbb0a9aa35e4e1c5ab6ef`  
**Repository:** `https://github.com/JupiterIsland/memoryos`

---

## 1. Executive Summary of Verified Results

**MemoryOS + The Quiet Advisor + Jupiter Desktop v2** was architected and verified in production to eliminate local 8GB consumer GPU (**NVIDIA RTX 3070**) VRAM saturation during multimodal video analysis and coding workflows by routing tasks through **AMD Token Lab** (`https://api.tokenlab.amd.com/v1`).

| Metric | Verified Result | Source of Truth |
| :--- | :--- | :--- |
| **Local GPU VRAM Sacrificed for 27B/31B Inference** | **`0 MB` (`100.0%` local VRAM saved)** | `QuietAdvisorDB.sqlite` (`/api/state` -> `local_vram_saved_pct: 100.0`) |
| **AMD Token Lab Grant Allocated** | **`10,000,000` micro-points** | Token Lab Export (`points_history[0].points_granted`) |
| **AMD Token Lab Grant Consumed** | **`78` micro-points (`0.00078%` burn rate)** | Token Lab Export (`account.budget_used_micro: 78`) |
| **Remaining Grant Headroom** | **`9,999,922` micro-points (`99.99922%`)** | Token Lab Export (`2026-11-14T09:01:20Z`) |
| **API Gateway Requests Allowed / Rate-Limited / Denied** | **`27` allowed / `0` rate-limited / `0` denied** | Token Lab Export (`gateway_daily[0]`) |
| **Total Token Lab Model Calls Logged** | **`19` requests (`1,946` total tokens)** | Token Lab Export (`usage_totals`) |
| **Prompt Cache & Reasoning Tokens Verified** | **`31` cached tokens / `113` reasoning tokens** | Token Lab Export (`usage_daily`) |
| **Router Footprint After 3-Service Split** | **~150 MB (`0` PyTorch / `0` OpenCV deps in router)** | `requirements-router.txt` & `Dockerfile-router` |

---

## 2. Verified AMD Token Lab Multi-Model Breakdown (`2026-11-14T09:01:20Z`)

From the official AMD Token Lab telemetry export (`memory/tokenlab_export.json`):

| Model on AMD Instinct | Endpoint | Requests | Clean Completions | Prompt Tokens | Completion Tokens | Cached Tokens | Reasoning Tokens | Micro-Points Used |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`d3`** (SystemOne Gatekeeper) | `POST /v1/systemone` | `15` | `7` *(+8 early schema test 4xx)* | `1,456` | `0` | `0` | `0` | `52` |
| **`Gemma-4-31B-IT`** (Multimodal VLM) | `POST /v1/chat/completions` | `2` | `2` (`100%`) | `171` | `49` | `31` | `0` | `8` |
| **`Qwen3.8-27B`** (Code & Architecture) | `POST /v1/chat/completions` | `1` | `1` (`100%`) | `87` | `106` | `0` | `80` | `10` |
| **`MiniCPM5-2B`** (Fast Edge Triage) | `POST /v1/chat/completions` | `1` | `1` (`100%`) | `40` | `37` | `0` | `33` | `4` |
| **Total (Usage Ledger)** | — | **`19`** | **`11` (`100%` post-schema lock)** | **`1,754`** | **`192`** | **`31`** | **`113`** | **`74` (`78` billed)** |

### Chronological Proof of `/v1/systemone` Schema Resolution & Live Routing

1. **03:52:33 UTC – 04:11:58 UTC (Schema Discovery Trail)**:
   8 client errors (`finish_reason: "client_error"`, `0` points billed) were recorded against `d3` while identifying that `/v1/systemone` requires `state` and `questions`/`actions` as structured dictionaries rather than arrays.
2. **04:15:54 UTC – 04:52:14 UTC (100% Clean Multi-Model Production Run)**:
   Once the dictionary schema was locked in `src/memoryos/router.py`, **10 consecutive requests succeeded with `finish_reason: "stop"` and `has_error: false`**:
   - `04:15:54.995392 UTC` — **`d3`**: `136` prompt tokens, `5` micro-points (`stop`)
   - `04:16:50.495654 UTC` — **`d3`**: `216` prompt tokens, `8` micro-points (`stop`)
   - `04:16:53.656274 UTC` — **`Gemma-4-31B-IT`**: `68` prompt tokens, `14` completion tokens, `7` cached tokens, `3` micro-points (`stop`)
   - `04:25:11.669672 UTC` — **`d3`**: `170` prompt tokens, `6` micro-points (`stop`)
   - `04:25:12.603230 UTC` — **`MiniCPM5-2B`**: `40` prompt tokens, `37` completion tokens, `33` reasoning tokens, `4` micro-points (`stop`)
   - `04:25:12.864115 UTC` — **`d3`**: `179` prompt tokens, `6` micro-points (`stop`)
   - `04:25:20.395192 UTC` — **`Qwen3.8-27B`**: `87` prompt tokens, `106` completion tokens, `80` reasoning tokens, `10` micro-points (`stop`)
   - `04:25:21.499118 UTC` — **`d3`**: `312` prompt tokens, `11` micro-points (`stop`)
   - `04:25:23.918257 UTC` — **`Gemma-4-31B-IT`**: `103` prompt tokens, `35` completion tokens, `24` cached tokens, `5` micro-points (`stop`)
   - `04:52:14.954727 UTC` — **`d3`**: `314` prompt tokens, `11` micro-points (`stop`)

---

## 3. Verified End-to-End Closed-Loop Test Results

All four stages of the local-to-remote hybrid architecture were verified against `memoryos-router` (`localhost:5000`) and `QuietAdvisorDB.sqlite`:

1. **CPU Frame-Delta Gatekeeping (`POST /api/frame-delta`)**:
   - **Static Video Frame (`mse_delta = 0.0020` / `0.0033`)**: `d3` scored `choice = "ignore"`, returning `skip_vision = True` in `<4 ms` and saving a 31B VLM call.
   - **Scene Transition Cut Frame (`mse_delta = 19,599.46` / `19,600.0`)**: `d3` scored `choice = "surface_now"`, returning `skip_vision = False` and escalating the frame to `Gemma-4-31B-IT`.
2. **Coding & Architecture Proxy (`POST /api/route`)**:
   - Submitting `{"task_type": "balanced_code", "prompt": "..."}` routed directly to `Qwen3.8-27B` (`gpu_id = "tokenlab-remote"`, `latency_ms = 42.02` in local fallback / `~281 ms` average in `QuietAdvisorDB.sqlite`).
3. **VRAM Thrashing Detection (`POST /api/detect` -> `VRAMThrashingDetector`)**:
   - Simulated local RTX 3070 saturation (`6,900–7,000 MB` VRAM, `97%` utilization across 3 runs) automatically generated a `vram_thrashing` Quiet Advisor card (`confidence = 0.85`, `recommended_action = "force_tokenlab_offload"`).
4. **Closed-Loop Policy Enforcement (`POST /api/acknowledge-card`)**:
   - Clicking **`[Acknowledge & Apply]`** persisted `vram_thrashing_penalty = 1.5` and `force_remote_offload = true` in `quiet_advisor_user_preferences`.
   - Subsequent requests with `prefer_local = True` returned `local_execution_blocked = True`, `user_preference_penalty = 1.5`, and forced remote execution onto `Gemma-4-31B-IT` (`gpu_id = "tokenlab-remote"`).
