# MemoryOS `v0.2.0-beta.1` — Beta Testing Release Notes

`MemoryOS v0.2.0-beta.1` is the active **beta testing track** (`beta` branch), kept separate from the `v0.1.0-preview` baseline on `main`. It introduces multi-cloud **DigitalOcean Serverless Inference (AMD Instinct MI300X)** failover, one-command Ubuntu Droplet deployment over SSH, and the next-wave systems architecture roadmap generated with `DeepSeek-V4.1-Flash` on AMD Token Lab.

---

## At a Glance

* **Version:** `v0.2.0-beta.1` (`prerelease`)
* **Branch:** `beta` (separated from `main` / `v0.1.0-preview`)
* **Release Date:** 2026-11-15
* **Key Beta Additions:** DigitalOcean MI300X failover routing, 1-command SSH Droplet deploy (`deploy-digitalocean.sh` / `Deploy-DigitalOcean.ps1`), and `v0.2.0` systems roadmap
* **Stability:** Beta testing — intended for early testers validating multi-cloud failover and live Droplet hosting

---

## What's New in Beta

### 1. DigitalOcean Serverless Inference (AMD Instinct MI300X) Failover
* Added `do_client`, `DO_MODEL_MAP`, and `get_cloud_provider_status()` in [src/memoryos/router.py](src/memoryos/router.py) targeting `https://inference.do-ai.run/v1`.
* Updated `route_task(..., cloud_provider=None)` to support:
  * **Direct routing** (`cloud_provider="digitalocean"`, `digitalocean_mi300x_direct`).
  * **Automatic failover** from AMD Token Lab to DigitalOcean MI300X (`digitalocean_mi300x_failover`).
  * **Primary fallback** when `TOKENLAB_API_KEY` is unset and `DO_MODEL_ACCESS_KEY` is configured (`digitalocean_mi300x_primary`).

### 2. One-Command DigitalOcean Droplet Deployment
* Added [installer/deploy-digitalocean.sh](installer/deploy-digitalocean.sh) (Linux / WSL2) and [installer/Deploy-DigitalOcean.ps1](installer/Deploy-DigitalOcean.ps1) (Windows PowerShell) to provision an Ubuntu 24.04 Droplet (`--create-droplet` / `-CreateDroplet`) or deploy to an existing Droplet IP over Ed25519 SSH and start `memoryos-quiet-advisor.service` on port `80`.

### 3. Cleaned & Credible Release Documentation
* Rewrote [RELEASE_NOTES.md](RELEASE_NOTES.md) with an **At a Glance** summary, explicit **Measured vs. Modeled** benchmark methodology, **Known Limitations**, beginner-friendly **Quick Start**, and **Roadmap**.

---

## High-Tech `v0.2.x` Architecture Roadmap (Generated via `DeepSeek-V4.1-Flash` on AMD Token Lab)

1. **Zero-Copy SPSC Ring Buffer (`/dev/shm` + `io_uring`):**
   * Replace SQLite staging copies on the `d3` hot path with a lock-free single-producer/single-consumer ring in POSIX shared memory (`memfd_create` + `MAP_SHARED|MAP_POPULATE`), 64-byte cacheline-aligned head/tail indices, hardware `crc32c` validation, and `io_uring` `IORING_OP_WRITE_FIXED` registered buffers.
   * **Target Win:** Cut p99 gate-to-checkpoint latency from `~0.31 ms` to `<0.18 ms`, reduce gate jitter by `>=40%`, and drop steady-state syscalls/frame toward zero.
2. **Speculative Edge-to-Cloud KV Prefetch:**
   * Add a ~50 KB `int8` 2-layer MLP speculation head to Quiet Advisor predicting `P(offload_needed)` per frame delta: warm remote KV-cache shards and pre-tokenized context above `τ_hi`, skip network below `τ_lo`, and send a 128-byte context digest in between.
   * **Target Win:** Cut cold-start remote TTFT from `~410 ms` to `<90 ms` on cache hits.

---

## Quick Start (Beta Track)

```bash
git clone -b beta https://github.com/JupiterIsland/memoryos.git
cd memoryos
cp .env.example .env
# Add TOKENLAB_API_KEY and/or DO_MODEL_ACCESS_KEY to .env
python3 -B seed_gamer_showcase.py
python3 -B tests/run_gamer_hardware_tests.py
```
