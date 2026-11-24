---
name: jupiter-studio-ops
description: >-
  Operational runbook for building, testing, running, and shipping Jupiter Studio
  on Windows + WSL2 (native Windows loopback for AMD Lemonade and Ollama, PyInstaller
  Google Drive lock workaround, Windows PowerShell git pushes, force-tracking signed
  model checkpoints in gitignored memory/, and NEON Control Plane validation).
  Use when launching Jupiter Studio servers, compiling JupiterStudio.exe, debugging
  Lemonade/Ollama connectivity, or preparing commits and CI runs in memoryos.
---

# Jupiter Studio Windows + WSL2 Operations Runbook

Follow these verified procedures whenever operating, building, or shipping `memoryos` / Jupiter Studio from this hybrid Windows + WSL2 environment.

## 1. Launch Jupiter Studio Natively on Windows (All Local + Cloud Servers Live)
WSL2 NAT cannot reach Windows `127.0.0.1:13305` (AMD Lemonade Server) unless `networkingMode=mirrored` or `--host 0.0.0.0` is enabled. Always launch the full local-silicon Studio instance natively via Windows PowerShell:

```powershell
powershell.exe -NoProfile -Command 'cd "C:\Users\RJMed\My Drive\memoryos"; python -B apps/jupiter_studio.py --no-browser --port 7860'
```

Verify readiness:
```powershell
powershell.exe -NoProfile -Command '(Invoke-RestMethod http://127.0.0.1:7860/api/models) | ConvertTo-Json -Depth 4'
powershell.exe -NoProfile -Command '(Invoke-RestMethod http://127.0.0.1:7860/api/control-plane/health) | ConvertTo-Json -Depth 4'
```

## 2. Build `JupiterStudio.exe` Without Google Drive File Locks
PyInstaller cleans `build/` before compiling, which raises `PermissionError: [WinError 5] Access is denied` inside synced `My Drive` folders. Build in `%TEMP%` and copy the resulting executable into `dist/`:

```powershell
powershell.exe -NoProfile -Command '
cd "C:\Users\RJMed\My Drive\memoryos"
$work = Join-Path $env:TEMP "jupiter_pyi_build"
$dist = Join-Path $env:TEMP "jupiter_pyi_dist"
if (Test-Path $work) { Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue }
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist -ErrorAction SilentlyContinue }
python -m PyInstaller --noconfirm --clean --workpath $work --distpath $dist installer/JupiterStudio.spec
if ($LASTEXITCODE -eq 0) {
  Copy-Item -Force "$dist\JupiterStudio.exe" "C:\Users\RJMed\My Drive\memoryos\dist\JupiterStudio.exe"
}
'
```

## 3. Git Status, Force-Tracking Signed Checkpoints & Pushing via Windows
WSL2 lacks git push credentials and can report false DrvFs CRLF/filemode diffs.
- Run `git status`, `git add`, `git commit`, and `git push` through `powershell.exe -NoProfile -Command 'cd "C:\Users\RJMed\My Drive\memoryos"; ...'`.
- **`memory/` is gitignored:** Whenever signed model checkpoints or Modelfiles change, force-add them explicitly or CI (`MemoryOS CI` / `Windows Clean Install`) will fail:
  ```powershell
  git add -f memory/models/frank_v1.json memory/models/Modelfile.frank memory/models/speculative_offload_v1.json
  ```

## 4. Refresh Companion Ollama Model (`frank`)
After updating `memory/models/Modelfile.frank`:
```powershell
powershell.exe -NoProfile -Command 'cd "C:\Users\RJMed\My Drive\memoryos"; ollama create frank -f memory/models/Modelfile.frank; ollama list'
```

## 5. Pre-Push Validation Gate
Run all three checks before committing or pushing:
1. One-command NEON Control Plane harness (must exit `0` with `NEON STATUS: CERTIFICATION READY`):
   ```bash
   python3 NEON_SINGLE_FILE.py
   ```
2. Syntax check + full 12-module CI test suite:
   ```bash
   PYTHONPATH=. python3 -B -W error::DeprecationWarning -m unittest \
     tests/test_quiet_advisor_detectors.py \
     tests/test_jupiter_studio.py \
     tests/test_speculative_offload.py \
     tests/test_memory_keeper.py \
     tests/test_frank.py \
     tests/test_cross_silicon_profiles.py \
     tests/test_ops_console.py \
     tests/test_control_plane.py \
     tests/test_nvidia_telemetry_safety.py \
     tests/test_workspace_pack.py \
     tests/test_nvidia_brev_router.py \
     tests/test_heatstream.py
   ```
3. Restore fixture files if modified by `test_heatstream.py`:
   ```powershell
   powershell.exe -NoProfile -Command 'cd "C:\Users\RJMed\My Drive\memoryos"; git checkout -- graph/heat_stream_state.json temporal_graph/heat_stream_state.json 2>$null'
   ```
