# MemoryOS // Jupiter Studio v2.0.0 Launch Checklist & Release Tracker

**Target Release:** `v2.0.0` ([GitHub Tag](https://github.com/JupiterIsland/memoryos/releases/tag/v2.0.0))  
**Automated Audit Script:** [`scripts/clean_install_windows.ps1`](scripts/clean_install_windows.ps1)  
**Windows CI Workflow:** [`.github/workflows/windows-clean-install.yml`](.github/workflows/windows-clean-install.yml)

---

## Executive Release Matrix

| Area | Status | Evidence / Verification Source |
| :--- | :---: | :--- |
| **Control Plane UI (`LIGHT` / `DARK` / `PURPLE GLASS`, `Operations \| Control Centre`, Crash Recovery)** | [x] Verified | Live Playwright QA on `:7860` (`final_step_10.png`) |
| **Persistent SQLite Threads (`/api/sessions`)** | [x] Verified | `tests/test_jupiter_studio.py::test_persistent_sqlite_sessions_crud_and_chat_persistence` |
| **Memory Keeper Vault + Free VRAM (`reclaim_memory`)** | [x] Verified | `tests/test_memory_keeper.py` + `/api/memory/*` HTTP tests |
| **EWC + Replay Continual Learning (`A -> B -> C`)** | [x] Verified | `memoryos.memory_keeper audit` (`Naive 0%` vs `EWC+Replay 100%`) |
| **OOD Abstention, Fisher Cap & Checksum Tamper Recovery** | [x] Verified | `tests/test_memory_keeper.py` (`Schema v2 + .corrupt quarantine`) |
| **NEON Control Plane (`ImmutableLedger`, `CircuitBreaker`, `BudgetEnforcer`, `DeclarativePluginLoader`)** | [x] Verified | `tests/test_control_plane.py` + `NEON_SINGLE_FILE.py` (`5/5`) |
| **Multi-Provider Routing & Cross-Silicon Profiles (18 Silicon Families, 13 Provider Groups)** | [x] Verified | `129 / 129` CI tests passing across all `12` test modules |
| **Windows Clean Install CI (`Python 3.11 / 3.12 / 3.13`)** | [x] Verified | `.github/workflows/windows-clean-install.yml` + `scripts/clean_install_windows.ps1` |
| **Fresh External Clean-Machine Manual Smoke Check** | [ ] Pending | Run `scripts/clean_install_windows.ps1` on a fresh non-dev machine |

---

## Pre-Launch Gate Verification

### Phase 1 - Core Runtime & Regression Safety
- [x] Full CI test suite passes with `-W error::DeprecationWarning` (`129 / 129` across all `12` test modules + `NEON_SINGLE_FILE.py` `5/5`)
- [x] Anti-forgetting audit passes (`Task A -> B -> C` retention = `100%`, Naive SGD baseline = `0%`)
- [x] OOD feature abstention (`decide_with_confidence`) returns `'digest'` with `confidence = 0.0`
- [x] SHA-256 checkpoint tamper protection (`ValueError` on mismatch) + graceful `.corrupt` quarantine fallback
- [x] Replay provenance quarantine excludes untrusted/external sources from EWC Fisher training
- [x] Secret upload blocker prevents `.env`, `.pem`, `.key`, `credentials.json`, and `.htpasswd` exfiltration

### Phase 2 - Documentation & Release Packaging
- [x] `README.md` rewritten cleanly for `v2.0.0`
- [x] `PROOF_OF_RESULTS.md` updated with empirical EWC retention, latency, and GPU idle wattage metrics
- [x] All `docs/screenshots/*` updated to live `v2.0.0` captures
- [x] `installer/JupiterStudio.spec` includes `src.memoryos.memory_keeper` hidden import
- [x] GitHub Releases cross-platform binaries built (`JupiterStudio-Windows-x64.zip`, `Linux-x64`, `macOS-arm64`)

### Phase 3 - Clean Install Audit (`clean_install_windows.ps1`)
Run from repository root on Windows 11 PowerShell:

```powershell
pwsh -File scripts/clean_install_windows.ps1
```

Checks enforced automatically:
1. Validates Windows OS, Git availability, Python `>= 3.11`, and rejects Windows Store `WindowsApps` Python stubs.
2. Creates an isolated temporary `.venv-clean-audit` and automatically rolls back created artifacts on any error.
3. Installs `requirements.txt`, bootstraps `.env` from `.env.example` if missing, executes the full unit test suite + EWC anti-forgetting audit, checks port availability, and verifies headless HTTP `/api/health` (`status = "ok"`).
