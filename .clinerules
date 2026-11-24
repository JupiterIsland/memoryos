# MemoryOS v0.1 — Roo Code & Cline Autonomous Agent Instructions

You are operating inside the **MemoryOS // The Quiet Advisor (`v0.1.0-preview`)** repository (`C:\Users\RJMed\My Drive\memoryos`), powered by **AMD Token Lab**.

## 1. Core Architecture
- **Router Service (`localhost:5000`)**: `server.py`, `src/memoryos/server.py`, `src/memoryos/router.py`
  - Routes across 5 AMD Token Lab models: `Gemma-4-31B-IT` (31B deep reasoning), `Qwen3.8-27B` (27B coding), `d3` (frame-skip & decision gate), `MiniCPM5-2B` (2B fast scout), and `DeepSeek-V4.1-Flash` (fast summary).
- **Quiet Advisor Web Dashboard (`localhost:8765`)**: `apps/quiet_advisor_ui/server.py`, `apps/quiet_advisor_ui/api.py`, `quiet_advisor_detectors.py`
  - Reads/writes telemetry and recommendation cards in `QuietAdvisorDB.sqlite` and NVMe quick-save checkpoints in `memory/checkpoints/`.
- **Jupiter Desktop v2 (`PyQt6` + `cv2`)**: `apps/jupiter-tv-desktop-v2/app.py`, `src/memoryos/quiet_advisor_client.py`
  - Runs CPU Mean Squared Error (`compute_mse_delta`) frame-skip checks in ~2.7ms before calling remote VLM analysis.

## 2. Mandatory Verification Commands Before Committing
After making any code change, always run:
1. `python -B verify_all_systems.py`
2. `python -B seed_gamer_showcase.py`
3. `python -B tests/run_gamer_hardware_tests.py`

## 3. Git & Security Rules
- Never hardcode or print the raw `TOKENLAB_API_KEY` from `.env`.
- Always commit under Git author `Jupiter Island <richardmurray2022@gmail.com>` (`@JupiterIsland`).
