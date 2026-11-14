# MemoryOS Developer Preview v0.1 — Release Checklist

Use this checklist before tagging and publishing **MemoryOS Developer Preview v0.1** (`v0.1.0-preview`).

---

## 1. Security & Credentials

- [x] `.env` is listed in `.gitignore` along with `.env.*`, `.env-backups/`, `.tokenlab-rotations.log`, and `.last-rotation`.
- [x] Full-repository regex scan (`tl-[0-9a-f]{16,}`) confirms **0** unredacted API keys in any tracked file.
- [x] `.env.example` contains placeholder values only (`TOKENLAB_API_KEY=tl-your-amd-tokenlab-key-here`).
- [ ] Run `.\Rotate-TokenLabKey.ps1 -Force` on your local Windows machine to rotate the `tl-9aa35a3...` key in `.env` and revoke the old key in the AMD Token Lab console.

---

## 2. Core Services & Dependency Diet

- [x] **Service 1 (`memoryos-router`)**: Starts cleanly via `python server.py --host 127.0.0.1 --port 5000` (with both FastAPI/Uvicorn and zero-dependency stdlib `ThreadingHTTPServer` fallback).
- [x] **Service 2 (`jupiter-desktop`)**: `apps/jupiter-tv-desktop-v2/app.py` wired to `QuietAdvisorClient`, CPU `cv2` MSE frame-delta extraction, and PyQt6 toast overlay (`quiet_advisor_ui.py`).
- [x] **Service 3 (`jupiter-vision-worker`)**: Heavy GPU packages (`torch`, `basicsr`, `realesrgan`, `faster-whisper`) isolated in `requirements-vision-worker.txt` (zero imports in router or desktop).

---

## 3. End-to-End Closed-Loop Verification

- [x] `python bootstrap.py` initializes `QuietAdvisorDB.sqlite`, ingests `memory/tokenlab_export.json`, and generates `d3`-scored recommendation cards.
- [x] `python verify_all_systems.py` completes with `0` errors and `0` `RuntimeWarning`s:
  - Prompt 1 (`"Reply with the single word: OK"`) -> `fast_light (MiniCPM5-2B)`
  - Prompt 2 (`"Write a 2-line Python function add(a, b)..."`) -> `balanced_code (Qwen3.8-27B)`
  - Quiet Advisor live loop + Jupiter TV AI Scene Navigator verified.
- [x] `POST /api/frame-delta` skips static frames (`skip_vision = True`) and escalates scene cuts (`skip_vision = False`).
- [x] `POST /api/acknowledge-card` (`[Acknowledge & Apply]`) writes `vram_thrashing_penalty = 1.5` and blocks local VRAM execution on subsequent requests (`local_execution_blocked = True`).

---

## 4. Documentation & Visual Proof Pack

- [x] `README.md` updated with **The Quiet Advisor** hero banner, 3-service architecture table, and Quick Start.
- [x] `INSTALL.md` created for brand-new users (Windows, Linux/WSL, and Docker).
- [x] `VALIDATION_SUMMARY.md` & `PROOF_OF_RESULTS.md` published with auditable telemetry metrics.
- [x] `/docs/proof-pack/` populated with:
  - [x] `quiet-advisor-dashboard.png`
  - [x] `tokenlab-usage.png`
  - [x] `architecture-overview.png`
  - [x] `telemetry-routing.png`
  - [x] `TEST_RESULTS.md`
  - [x] `DEMO.md`

---

## 5. Git Push & Release Tag

Run in Windows PowerShell from `C:\Users\RJMed\My Drive\memoryos`:

```powershell
git push origin main
git tag -a v0.1.0-preview -m "MemoryOS Developer Preview v0.1"
git push origin v0.1.0-preview
```
