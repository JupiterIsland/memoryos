# MemoryOS // The Quiet Advisor

### DLSS for AI: hardware-aware local model routing, AMD Ryzen frame gating, and NVMe checkpoint recovery

![The Quiet Advisor — Powered by AMD Token Lab](docs/quiet_advisor_banner.jpg)

[![Release: v0.1.0-preview](https://img.shields.io/badge/Release-v0.1.0--preview-ED1C24?style=for-the-badge&logo=amd&logoColor=white)](RELEASE_NOTES.md)
[![Status: Verified Preview](https://img.shields.io/badge/Status-Verified_Preview-2E8B57?style=for-the-badge)](RELEASE_NOTES.md)
[![Benchmarks: Lenovo Legion 15](https://img.shields.io/badge/Benchmarks-Lenovo_Legion_15-00AEEF?style=for-the-badge)](tests/run_gamer_hardware_tests.py)

MemoryOS is a local AI orchestration layer designed for workloads where GPU VRAM is limited but responsiveness still matters. It helps keep large models usable alongside active desktop work by routing inference intelligently, skipping redundant frames, and recovering safely from context and memory pressure.

The project centers around the Quiet Advisor runtime: a self-monitoring system that watches for context bloat, VRAM pressure, model thrashing, and unstable inference paths, then adjusts the workload before the user notices a slowdown.

- Project status: developer preview
- Release: `v0.1.0-preview`
- Primary hardware focus: AMD Ryzen / AMD Token Lab / mixed local + cloud inference
- Recommended entry point: `INSTALL.md`, `RELEASE_NOTES.md`

---

## What MemoryOS does

MemoryOS adds a lightweight control layer around local AI execution.

Instead of letting a model consume GPU memory and disrupt gameplay or creative work, MemoryOS can:

- detect stale or duplicate frames before they trigger a costly inference pass
- route tasks across multiple specialized models instead of forcing a single large model
- monitor telemetry for context bloat and model thrashing
- recover quickly using checkpoint-based state saves
- keep local inference responsive even when the machine is under memory pressure

This is designed to feel similar to a frame-gating and resource-management system: keep the user experience stable while the AI stack stays efficient.

---

## Core features

### 1. d3 frame gate
A CPU-side frame-delta gate reduces duplicate or static frames before expensive model work begins. The goal is to keep the AI stack from wasting cycles on low-value work.

### 2. Multi-model routing
Tasks are routed across different model roles depending on workload:

- `d3` for frame and state gating
- `Gemma-4-31B-IT` for deeper reasoning and architecture tasks
- `Qwen3.8-27B` for coding and code-oriented tasks
- `MiniCPM5-2B` for fast lightweight classification and routing decisions
- `DeepSeek-V4.1-Flash` for summarization and fast-pass tasks

### 3. Quiet Advisor telemetry
The Quiet Advisor monitors operational health and applies corrective behaviors before failures propagate. This includes checks for:

- prompt/context waste
- VRAM pressure
- checkpoint recovery
- model thrashing

### 4. Hardware-aware routing
The project includes AMD-aware tuning and hardware classification paths for:

- Ryzen CPU execution
- AMD AI stack detection
- cloud offload pathways
- local-first routing with failover support

---

## Quick start

See [INSTALL.md](INSTALL.md) for the full setup flow.

### Windows PowerShell

```powershell
cd "C:\path\to\memoryos"
python -B seed_gamer_showcase.py
python -B tests\run_gamer_hardware_tests.py
```

### Linux / WSL2 / macOS

```bash
cd ~/memoryos
python3 -B seed_gamer_showcase.py
python3 -B tests/run_gamer_hardware_tests.py
```

Then launch the dashboard and router if desired:

```bash
python3 -B server.py --host 127.0.0.1 --port 5000 --db QuietAdvisorDB.sqlite
python3 -B apps/quiet_advisor_ui/server.py --port 8765 --db QuietAdvisorDB.sqlite
```

---

## Benchmark snapshot

The project includes a hardware test suite in [tests/run_gamer_hardware_tests.py](tests/run_gamer_hardware_tests.py) and a benchmark write-up in [docs/proof-pack/GAMER_LAPTOP_BENCHMARK.md](docs/proof-pack/GAMER_LAPTOP_BENCHMARK.md).

Measured benchmark context:

- Hardware profile used in the repo: Lenovo Legion 15
- CPU: AMD Ryzen 7 5800H
- GPU: RTX 3070 8 GB
- Local optimized path: MemoryOS enabled

| Scenario | Result |
| :--- | :--- |
| Zen 3 frame-gate latency | `0.092 ms` average |
| Checkpoint reload latency | ~`2.692 ms` average over 20 checkpoints |
| Local VRAM usage | `0 MB` spillover in the measured path |
| Targeted workload posture | local-first inference with routing and recovery |

The repo also documents comparative baseline behavior against higher-end gaming laptops without MemoryOS, but those numbers should be read as workload-specific comparisons rather than universal performance guarantees.

---

## Release notes and validation

- [RELEASE_NOTES.md](RELEASE_NOTES.md) — full v0.1.0-preview changelog and feature summary
- [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md) — validation and verification notes
- [PROOF_OF_RESULTS.md](PROOF_OF_RESULTS.md) — proof and result summary
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) — release checklist and internal validation trail

---

## Documentation map

- [INSTALL.md](INSTALL.md) — setup and installation instructions
- [ARCHITECTURE.md](ARCHITECTURE.md) — system architecture overview
- [docs/proof-pack/](docs/proof-pack/) — benchmark pack, telemetry evidence, and proof material
- [docs/specs/](docs/specs/) — design and specification documents
- [src/memoryos/](src/memoryos/) — core logic
- [apps/](apps/) — dashboard and desktop interfaces

---

## Current status

This repository is still best understood as a developer preview and research-style product. It is intentionally focused on proving a practical local-AI bottleneck management approach for gaming and workstation workflows, rather than claiming universal compatibility across all hardware and inference stacks.

The beta branch contains additional experimentation around cloud routing and failover. The stable `main` branch remains the preview baseline.

---

## Contributing

Contributions are welcome. If you want to improve routing logic, benchmark coverage, deployment tooling, or the Quiet Advisor behavior, open a pull request.

---

## License

This project is open source. See the repository license file for usage terms.

---

## Why this project exists

MemoryOS is built for the gap between “AI can run locally” and “AI can run locally without ruining the desktop experience.”

The mission is simple:

- keep local inference useful
- keep the system responsive
- prevent memory and context spikes from dominating the desktop session
- make model routing and recovery a first-class part of the runtime

That is the core idea behind the Quiet Advisor and the MemoryOS architecture.
