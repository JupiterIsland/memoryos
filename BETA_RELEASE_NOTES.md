# MemoryOS `v1.0.0-RC1` — Beta Track Release Notes

### Active Beta Staging for AMD Developer Relations & Multi-Cloud Systems Validation

![MemoryOS // The Quiet Advisor — Powered by AMD Token Lab](docs/memoryos_executive_banner.svg)

[![Release: v1.0.0-RC1](https://img.shields.io/badge/Release-v1.0.0--RC1-ED1C24?style=for-the-badge&logo=amd&logoColor=white)](RELEASE_NOTES.md)
[![Branch: beta](https://img.shields.io/badge/Branch-beta-38BDF8?style=for-the-badge)](https://github.com/JupiterIsland/memoryos/tree/beta)
[![Status: AMD Release Candidate](https://img.shields.io/badge/Status-AMD_Release_Candidate-2E8B57?style=for-the-badge)](AMD_RELEASE_CANDIDATE.md)

The `beta` branch serves as the staging track for **MemoryOS Release Candidate 1.0 (`v1.0.0-RC1`)**. It incorporates the verified AMD Token Lab integration, microsecond speculative offloading, multi-cloud failover (including DigitalOcean Serverless AMD Instinct MI300X), and the Jupiter Studio hybrid desktop workstation.

---

## What Is Validated on the Beta Track

### 1. Speculative Offload Engine (`src/memoryos/speculative_offload.py`)
* Implements the pure-Python `SpeculativeOffloadModel` forward pass ($P(\text{offload})$) with verified **5.37 μs** average latency across 1,000 forward passes (`suite_8`).
* Evaluates host features (`mse_delta_norm`, `context_utilization`, `secs_since_offload`, `model_switch_rate`) without invoking external matrix libraries, outperforming remote network roundtrips by **85,000x**.

### 2. Multi-Cloud AMD Instinct MI300X Failover Routing (`src/memoryos/router.py`)
* Integrates `do_client` and `DO_MODEL_MAP` targeting DigitalOcean Serverless Inference (`https://inference.do-ai.run/v1`).
* Supports automatic failover from AMD Token Lab to DigitalOcean MI300X compute, preventing application interruptions during provider maintenance or quota saturation.

### 3. Automated Droplet Deployment Subsystem (`installer/`)
* Linux/WSL2 (`installer/deploy-digitalocean.sh`) and PowerShell (`installer/Deploy-DigitalOcean.ps1`) scripts to provision Ubuntu 24.04 server instances over Ed25519 SSH and establish the `memoryos-quiet-advisor.service` systemd daemon.

### 4. Multi-Vendor Hardware Probing (`src/memoryos/gpu_backends.py`)
* Hardware telemetry detector querying NVIDIA (`nvidia-smi`), AMD sysfs (`/sys/class/drm/card*/device/` vendor ID `0x1002`), and handheld APUs (`ROG Ally`, `Lenovo Legion Go`, `Steam Deck`).

### 5. Jupiter Studio Desktop Workstation (`apps/jupiter_studio.py`)
* Real-time Server-Sent Events (SSE) token streaming with live thinking/reasoning blocks, dynamic target switching (`auto:d3`, `cloud:Gemma-4-31B-IT`, `do:MI300X`, `ollama`), workspace file scanning, and Copilot bundle export.

---

## Verified Benchmarks Summary (`suite_1` through `suite_8`)

All 8 benchmark suites pass with 100% compliance on the beta track:
* **Suite 1 (Database Audit):** 50 Inferences, 7 Cards, 20 Checkpoints, 100.0% local VRAM saved.
* **Suite 2 (Frame Budget):** 2.713 ms avg CPU MSE gate (16.28% of 60 FPS budget).
* **Suite 3 (Laptop Shootout):** 14.7x speedup vs stock local; 0 MB VRAM vs 12.7 GB spillover.
* **Suite 4 (Chaos Recovery):** 3.072 ms per checkpoint reload across 20 quick-saves.
* **Suite 5 (Router Contract):** Safe offline deterministic contract fallback.
* **Suite 6 (Zen 3 Kernel):** 0.091 ms avg CPU gate on AMD Ryzen 7 5800H (0.55% 60 FPS budget).
* **Suite 7 (Mobile Hotspot):** 94.0% cellular bandwidth reduction over iPhone XR LTE hotspot.
* **Suite 8 (Speculative MLP):** 5.47 μs average neural forward pass latency.

---

## Quick Start on the Beta Track

```bash
git clone -b beta https://github.com/JupiterIsland/memoryos.git
cd memoryos
cp .env.example .env

# Run all 8 verified hardware benchmark suites
PYTHONPATH=. python3 tests/run_gamer_hardware_tests.py

# Launch Jupiter Studio Workstation
python3 -B apps/jupiter_studio.py
```
