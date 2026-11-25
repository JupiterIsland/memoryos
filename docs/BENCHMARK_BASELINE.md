# Reproducible Benchmark & Hardening Baseline (`v2.2.1`)

> **See the model. See the cost. See the route.**

This document records the canonical, reproducible verification baseline for **MemoryOS // Jupiter Studio (`v2.2.1`)**, captured directly from [`verify.py`](../verify.py) (`python -B verify.py --json`) in [`benchmarks/legion5_5800h_rtx3070_v2.2.1.json`](../benchmarks/legion5_5800h_rtx3070_v2.2.1.json).

---

## 1. Reproduce on Any Machine

```bash
git clone https://github.com/JupiterIsland/memoryos.git
cd memoryos
python3 -B verify.py --json
```

Zero third-party `pip` packages, zero PyTorch, zero Docker, and zero paid API calls are required (`MEMORYOS_VIDEO_MAX_JOB_USD=0` fail-closed spend lock).

---

## 2. Reference Hardware Environment

| Property | Measured Value |
| :--- | :--- |
| **Timestamp (UTC)** | `2026-11-25T00:20:25Z` |
| **Host System** | Lenovo Legion 5 (`82JY`) · `Windows-11-10.0.29712-SP0` |
| **Python Runtime** | `3.13.15` (pure standard library) |
| **CPU** | `AMD Ryzen 7 5800H with Radeon Graphics` (`16` logical threads) |
| **GPU** | `NVIDIA GeForce RTX 3070 Laptop GPU` (`8192 MB` VRAM · `0.0 MB` Python compute VRAM) |

---

## 3. Verification & Benchmark Results (`all_passed: true`)

| Gate / Benchmark | Scope & Condition | `v2.2.1` Baseline Result |
| :--- | :--- | :--- |
| **Core Syntax Gate (`py_compile`)** | `21` production Python modules | **`PASS` (`21 / 21`)** |
| **NEON Control Plane (`NEON_SINGLE_FILE.py`)** | Declarative plugins, budgets, circuit breakers, crash recovery, SHA-256 hash-chained ledger | **`CERTIFICATION READY` (`5 / 5 PASS`)** |
| **CI & Adversarial Test Suite** | `17` test modules (`171` unit, HTTP range, SSRF, Windows reserved-name, `NaN`/`Inf` budget fuzzing, 24-thread concurrency, `/v1` failover tests) | **`PASS` (`171 / 171` in `44.94s`)** |
| **Continual Offload Net (`4->8->1`)** | Task A -> Task B -> Task C anti-forgetting audit | Naive SGD `0.0%` · Sparse Replay `50.0%` · **EWC + Replay `100.0%`** (`10.83 us/call`) |
| **Frank-v1 Continual Router (`128->24->6`)** | `3,246` params, teaching unseen `vram_reclaim` phrase over 36-phrase curriculum (`45` A-GEM projections) | **EWC + A-GEM `94.44%` retained** vs Naive SGD `25.00%` (`470.56 us/call`, `0 MB` GPU VRAM) |
| **CPU Frame-Delta Gate (`64x36` MSE)** | `200` stride-sampled iterations vs `6.94 ms` (144 Hz) budget | **`0.173 ms` avg / `0.257 ms` p99** (`2.49%` of 144 Hz frame budget) |
