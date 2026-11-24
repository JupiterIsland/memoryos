# Roadmap & Scope Split

This document separates what is **implemented, tested, and verified today** from **experimental modules and planned follow-up work**.

---

## Shipped & End-to-End Tested Today (`v2.x`)

Run `python3 -B verify.py` on your own machine to verify all of these locally:

* **Frank-v1 Continual-Learning Router (`src/memoryos/frank.py`):** Pure-Python `128->24->6` Hashing N-Gram MLP (`3,246` params) running on CPU (`~0.2–0.4 ms`), supporting online `POST /api/frank/teach` updates across 6 intents using **EWC + Experience Replay + A-GEM half-space gradient projection**, plus Confidence/OOD and Vault-priority guards.
* **Speculative Offload Continual Net (`src/memoryos/speculative_offload.py`):** `4->8->1` pure-Python continual MLP (`~6–8 us` per forward pass) with Fisher diagonal anchoring, replay provenance quarantine, OOD abstention, and SHA-256 checkpoint verification (`schema_version = 2`).
* **SQLite Memory Vault & Threads (`src/memoryos/memory_keeper.py`):** Persistent pinned facts (`continual_memory_facts`) and multi-turn threads in `QuietAdvisorDB.sqlite` (WAL mode), plus safe localhost Ollama weight unloading (`Free VRAM`, `keep_alive: 0`) and process GC.
* **Workstation Web UI (`apps/jupiter_studio.py` + `apps/jupiter_studio_ui.py`):** Dual Arena side-by-side comparison, `Ctrl+K` Command Palette, workspace file scanner (`WorkspacePack`), and **LIGHT / DARK / PURPLE GLASS** themes — runs completely offline with zero `.env` or Ollama using `Frank-v1`, or connects to Ollama / Lemonade / vLLM / Cloud APIs (`OpenAI`, `Google Gemini Interactions v1`, `AMD Token Lab`, `Groq`, `OpenRouter`, `Cerebras`, `NVIDIA NIM`, `DigitalOcean MI300X`, `HF Router`).
* **NEON Control Plane (`src/memoryos/control_plane.py` + `NEON_SINGLE_FILE.py`):** Circuit breakers, SHA-256 hash-chained SQLite ops ledger, crash recovery engine, and zero-exec declarative plugins with `allow_network: false` enforcement.
* **Network & Workspace Hardening (`apps/jupiter_studio.py`, `src/memoryos/server.py`, `src/memoryos/workspace_pack.py`):** Loopback-by-default binding (`--unsafe-lan` + mandatory launch token for LAN), `403` DNS-rebinding/CSRF guards, secret-file upload blocklist, and symlink-safe workspace path containment.

---

## Experimental / Planned Roadmap (Not Headline v2.x Claims)

* **Brand Rename Evaluation (`docs/NAME_RESEARCH.md`):** Selecting an unclaimed coined name to avoid collisions with Solana's `studio.jup.ag` (`Jupiter Studio`) and `BAI-LAB/MemoryOS` before wide promotion.
* **True Hardware NPU Execution Tiers:** Moving beyond XDNA/Zen readiness probes (`amd_zen_studio.py`) to tested end-to-end inference inside local `VitisAIExecutionProvider` pipelines.
* **Hardware-Isolated Subprocess Budgets (`control_plane.py`):** Upgrading NEON execution limits from cooperative thread timeouts + post-hoc CPU accounting to isolated worker subprocesses with `resource.setrlimit` (Linux/macOS) and Windows Job Objects.
* **Signed External Plugin Verification:** Adding Ed25519 signature verification with a code-pinned public key for third-party plugin packs (beyond local corruption-detection SHA-256 hashes).
* **Static Asset Split for UI Auditability:** Splitting `apps/jupiter_studio_ui.py` (~4.2k lines) into static HTML/CSS/JS files served directly by `jupiter_studio.py` while keeping zero build steps and the PyInstaller `.exe` bundle intact.
* **Clean-VM First-Run Matrix & Signed Releases:** Automated clean-VM tests (no Python, no `.env`, no Ollama preinstalled) and signed Windows installers to eliminate SmartScreen warnings.
* **Experimental Companion Utilities:** Console capture helpers (`ConsoleCompanionBridge` in `gpu_backends.py`), mobile/hotspot cost models, and legacy graph/UI modules under `apps/quiet_advisor_ui/` are experimental utilities rather than headline workstation features.
