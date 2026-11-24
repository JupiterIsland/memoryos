# Installing MemoryOS // Jupiter Studio (`v2.2.0`)

> Looking for the fastest path? Read **[`QUICKSTART.md`](QUICKSTART.md)** to go from `git clone` to a live workstation in **under 5 minutes at $0.00**.

MemoryOS // Jupiter Studio (`v2.2.0`) runs on the **Python 3.11+ standard library** with **zero third-party runtime `pip` dependencies** — no 15 GB PyTorch install, no Docker daemon, and no manual `ffmpeg` setup required.

---

## 1. Prerequisites

- **Python:** `3.11+` (`3.11`, `3.12`, or `3.13`; standard installer from [python.org](https://www.python.org/downloads/) on Windows with **"Add Python to PATH"** enabled)
- **Git:** Any recent Git client (or download the release `.zip` archive)
- **OS:** Windows 10/11, Linux, or macOS
- **GPU:** Optional — works on CPU-only laptops (`Frank-v1` uses `0 MB` GPU VRAM), 8 GB consumer GPUs (e.g. RTX 3070 via Local Ollama), or cloud offload

---

## 2. Option A — Run From Source (Recommended)

### Windows (PowerShell)
```powershell
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos
Copy-Item .env.example .env
python -B verify.py --quick
python -B apps/jupiter_studio.py
```

### Linux / macOS
```bash
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos
cp .env.example .env
python3 -B verify.py --quick
python3 -B apps/jupiter_studio.py
```

Open **[http://127.0.0.1:7860](http://127.0.0.1:7860)**.

### Automated Clean-Room Install Audit (Windows)
To run the same transactional clean-install check executed in CI (validates Git, non-Store Python `3.11+`, isolated `.venv`, full `16`-module unit suite, `NEON_SINGLE_FILE.py`, EWC audit, and headless `/api/health` startup):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/clean_install_windows.ps1
```

---

## 3. Option B — Standalone Pre-Built Executables

Download pre-built single-file binaries from **[GitHub Releases](https://github.com/JupiterIsland/memoryos/releases/latest)** and verify against `SHA256SUMS.txt`:

- **Windows x64:** Extract `JupiterStudio-Windows-x64.zip` -> `JupiterStudio.exe`
- **macOS (Apple Silicon):** `tar -xzf JupiterStudio-macOS-arm64.tar.gz` -> `./JupiterStudio-macOS-arm64/JupiterStudio`
- **Linux x64:** `tar -xzf JupiterStudio-Linux-x64.tar.gz` -> `./JupiterStudio-Linux-x64/JupiterStudio`

> **Note:** Release binaries are built with PyInstaller (`installer/JupiterStudio.spec`) and are currently unsigned; Windows SmartScreen may prompt on first run. Place an optional `.env` file beside the executable if you wish to configure cloud keys.

---

## 4. Storage Paths & Zero-Spend Defaults

- **SQLite Vault & Ledger:** `./QuietAdvisorDB.sqlite` (created automatically on first launch; override via `QUIET_ADVISOR_DB` in `.env`).
- **Generated Videos:** `./outputs/video/` by default (`MEMORYOS_VIDEO_OUTPUT_DIR` in `.env`). No external drive letter is required.
- **Zero-Spend Safety Lock:** `.env.example` sets `MEMORYOS_VIDEO_MAX_JOB_USD="0.00"` by default so paid cloud video APIs cannot bill you unless you explicitly raise the cap.
