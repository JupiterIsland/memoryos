# Installing MemoryOS Developer Preview v0.1

MemoryOS is a local-first **AI traffic controller, multi-model router, and VRAM protection engine** pairing **The Quiet Advisor** (`localhost:5000`) with **Jupiter Desktop v2** (`PyQt6` media & visual studio) and **AMD Token Lab** (`d3`, `Gemma-4-31B-IT`, `Qwen3.8-27B`, `MiniCPM5-2B`).

---

## 1. Prerequisites

- **Python:** `3.10+` (`3.11` or `3.12` recommended)
- **OS:** Windows 10/11, Linux, or macOS
- **GPU:** Any consumer GPU (e.g., 8GB NVIDIA RTX 3070 or AMD Radeon) or CPU-only mode — **0 MB of local VRAM is required** for 27B/31B model inference when connected to AMD Token Lab (and the router includes an automatic offline fallback when running without an API key).

---

## 2. Clone & Configure Environment (1 Minute)

### Windows (PowerShell)

```powershell
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos

Copy-Item .env.example .env
```

Open `.env` in any text editor and paste your AMD Token Lab key (optional — if left blank, MemoryOS automatically runs in deterministic offline fallback mode):

```ini
TOKENLAB_API_KEY=tl-your-amd-tokenlab-key-here
TOKENLAB_BASE_URL=https://api.tokenlab.amd.com/v1
QUIET_ADVISOR_DB=QuietAdvisorDB.sqlite
```

---

## 3. Install Dependencies (Choose Your Service)

MemoryOS is split into lean services so you never have to download a 15GB PyTorch monolith just to run the router or dashboard:

### Option A: Router + Quiet Advisor Web Dashboard Only (~150MB)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-router.txt
```

### Option B: Full Hybrid Desktop Setup (Router + Jupiter Desktop PyQt6 UI)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-router.txt -r requirements-desktop.txt
```

*(Note: Even before installing `fastapi` or `uvicorn`, `python server.py` works out of the box using Python's built-in HTTP server.)*

---

## 4. Initialize Telemetry & Verify Everything Works

Run the one-command bootstrap and verification suite:

```powershell
python bootstrap.py
python verify_all_systems.py
```

Expected output:
- Initializes `QuietAdvisorDB.sqlite` from `schema.sql`
- Ingests `memory/tokenlab_export.json` telemetry
- Verifies `d3` routing across `MiniCPM5-2B` (`fast_light`), `Qwen3.8-27B` (`balanced_code`), and `Gemma-4-31B-IT` (`vision_heavy`)
- Prints `ALL 3 SYSTEMS VERIFIED SUCCESSFULLY.`

---

## 5. Launch the Applications

### 1. Start the MemoryOS Router & Quiet Advisor Web Dashboard (`http://127.0.0.1:5000`)

```powershell
python server.py --host 127.0.0.1 --port 5000
```

Open **http://127.0.0.1:5000** in your browser to view live telemetry, `d3` probabilities, context waste detection, and `[Acknowledge & Apply]` recommendation cards.

### 2. Launch Jupiter Desktop v2 (PyQt6 Video & Visual AI Studio)

In a second terminal:

```powershell
python apps/jupiter-tv-desktop-v2/app.py
```

### 3. Launch the Standalone Quiet Advisor Desktop Toast

```powershell
python quiet_advisor_ui.py
```

---

## 6. Optional: Run the Router in Docker

```bash
docker compose -f docker-compose-router.yml up --build
```
