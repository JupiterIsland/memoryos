# MemoryOS + Quiet Advisor — 2-Minute Reproducible Demo Walkthrough

This guide walks through reproducing the exact telemetry and screenshots in `/docs/proof-pack/` on your machine or during a live screen-share with AMD Developer Relations.

---

## 1. Start the Lean `memoryos-router` (~150MB, Zero Local VRAM)

From the repository root (`C:\Users\RJMed\My Drive\memoryos`):

```powershell
# Start the router + Quiet Advisor Web UI on http://127.0.0.1:5000
python server.py --host 127.0.0.1 --port 5000
```

Open **`http://127.0.0.1:5000`** in your browser. You will see:
- **RTX 3070 Local VRAM Isolation:** `100% Remote`
- **Token Lab `d3` Aux-Router:** `surface_now` probability scoring
- **Context Window Efficiency:** Identifies `~93%–97%` unused context window (`2.2%–6.8%` used)
- **Token Lab Grant Ledger:** `RJMedia.ai@outlook.com` (`78 / 10,000,000` micro-points used across `Gemma-4-31B-IT`, `Qwen3.8-27B`, `MiniCPM5-2B`, and `d3`)

*(Reference screenshot: [`quiet-advisor-dashboard.png`](quiet-advisor-dashboard.png))*

---

## 2. Demonstrate CPU Frame-Delta Gatekeeping (`/api/frame-delta`)

In a second PowerShell terminal, send a static video frame delta followed by a scene-cut delta:

```powershell
# A. Static frame (MSE = 0.002) -> d3 scores "ignore" (skip_vision = True, 0 heavy VLM tokens spent)
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/frame-delta" -Method Post -ContentType "application/json" -Body '{"mse_delta": 0.002, "threshold": 12.0, "context_hint": "Pause on static concert frame"}'

# B. Scene cut frame (MSE = 19600.0) -> d3 scores "surface_now" (skip_vision = False, escalates to Gemma-4-31B-IT)
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/frame-delta" -Method Post -ContentType "application/json" -Body '{"mse_delta": 19600.0, "threshold": 12.0, "context_hint": "Scene cut to guitar solo"}'
```

---

## 3. Demonstrate Multi-Model Routing (`/api/route`)

Route a coding/architecture task through the local router to `Qwen3.8-27B` on AMD Token Lab:

```powershell
$body = @{
    task_type = "balanced_code"
    prompt    = "Write a compact Python function to compute grayscale MSE between two frames."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/route" -Method Post -ContentType "application/json" -Body $body
```

Every call writes an atomic JSON checkpoint to `memory/checkpoints/` and logs latency + token usage to `QuietAdvisorDB.sqlite`.

*(Reference visuals: [`tokenlab-usage.png`](tokenlab-usage.png) & [`architecture-overview.png`](architecture-overview.png))*

---

## 4. Demonstrate the Closed-Loop `[Acknowledge & Apply]` Hardware Guard

1. Click **`RUN DETECTION`** in the Web UI (or call `POST /api/detect`).
2. When `VRAMThrashingDetector` or `ContextWasteDetector` surfaces a recommendation card (`d3: surface_now`), click **`[Acknowledge & Apply]`** (or call `POST /api/acknowledge-card`).
3. `QuietAdvisorDB.sqlite` records `vram_thrashing_penalty = 1.5` and `force_remote_offload = true`.
4. Any subsequent request with `prefer_local = true` is automatically blocked from using local VRAM (`local_execution_blocked = true`) and forced onto `Gemma-4-31B-IT` on `tokenlab-remote`.

*(Reference visual: [`telemetry-routing.png`](telemetry-routing.png))*

---

## 5. Launch Jupiter Desktop v2 (PyQt6 Video Studio)

```powershell
python apps/jupiter-tv-desktop-v2/app.py
```

Load a video file and press **Play / Pause** or click any scene in the **Storyboard** tab:
- `on_playback_state_changed()` and `update_slider_position()` automatically extract the current `cv2` frame on CPU, compute the grayscale MSE delta, query `check_frame_delta()`, and update the **Frame FX & Vision** and **AI Telemetry** tabs in real time.
