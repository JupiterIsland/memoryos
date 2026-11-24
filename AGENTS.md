# User Identity & System Context — Richard John Murray

## Builder Profile
- **Name:** Richard John Murray
- **Location:** Carlisle, England, UK
- **Role:** Technical Systems Builder, AI Infrastructure Architect, & Digital Archivist
- **GitHub Organization / Account:** `https://github.com/JupiterIsland`

## Core AI Infrastructure (Three Systems)
Richard John Murray designs and runs a unified AI infrastructure built from three core systems:

1. **MemoryOS (`JupiterIsland/memoryos`)**
   - Handles GPU-aware memory routing, hierarchical tier management, and checkpoint persistence.
2. **Jupiter One Hardware Reality**
   - Provides real-time VRAM analysis, hardware ROI recommendations, and multi-model scheduling across consumer GPUs.
3. **The Quiet Advisor**
   - Observes inference patterns, runs ten detector algorithms nightly, and generates one actionable insight per day based on real usage data.

## Five Public Repositories (`JupiterIsland`)
1. **`JupiterIsland/memoryos`**: "A tiered memory engine for local AI. TLB + Temporal Graph + NVMe checkpoints. Built for NVIDIA, architected for AMD Helios. No cloud."
2. **`JupiterIsland/rjmedia`**: RJMedia music archive landing page and project files (serves from root on `main` and `gh-pages`).
3. **`JupiterIsland/music-getaway`**: Python tools and scripts for musical archives and audio discovery.
4. **`JupiterIsland/.github`**: Organization profile, standards, community health files, and GitHub workflows.
5. **`JupiterIsland/archive-signal`**: Preserves and showcases rare music documentaries, broadcast recordings, interviews, restored footage, and cultural archives (MIT License).

## Technical Focus & Stack
- **Focus:** Inference optimization, GPU efficiency, multi-model orchestration, and exposing hidden patterns in user workflows.
- **Engineering Philosophy:** Build systems that reveal waste, improve throughput, and eliminate guesswork. The ecosystem consists of a memory engine, a hardware reality layer, a GPU inference runtime, and a daily insight system that teaches users how to use their own tools better.
- **Environment:** Docker, WSL2, Linux, Windows automation, consumer GPUs, and competitive model testing.

## Cultural Preservation & Archives (`JupiterIsland/rjmedia`)
- Founder of the 25-year Mansun & Paul Draper fan archives (*MansunMusicLovers* Yahoo! Group founded 15 Dec 2001, *pauldraper.tk*, *pauldraper-music.co.uk*, *Paul-Draper.net*) and the *RJMedia* YouTube channel (1,001,987+ views, 72,500+ watch hours).
- Filmed the first public playback of Paul Draper's debut solo song (*"Feeling My Heart Run Slow"*) at the Mansun convention in Chester (August 2014). *Louder Than War* credited the recording to *"Richard Murray of the Paul-Draper.net fansite"*, *Vanyaland* named him as the person who captured it, and *The Guardian* featured the video in its indie playlist.

## Active Repositories & Local Sync Paths
- **Local Website Root:** `C:\Dev\website`
- **GitHub Repo 1 (`rjmedia`):** `C:\Users\RJMed\.gemini\antigravity\scratch\rjmedia` -> `https://github.com/JupiterIsland/rjmedia.git`
- **GitHub Repo 2 (`memoryos`):** `C:\Users\RJMed\My Drive\memoryos` (WSL2: `/mnt/c/Users/RJMed/My Drive/memoryos`) -> `https://github.com/JupiterIsland/memoryos.git`

## Jupiter Studio Control Plane Guardrails
- **Architecture Mandate:** Jupiter Studio is a **Personal Intelligence Control Plane**, not an AI chat app. Models, providers, GPUs, and interfaces are replaceable **resources**; **operations, memory, recovery, and auditability** are the product. Every feature must increase operational capability and preserve crash explainability, auditability, and recovery.
- **Zero Arbitrary Plugin Execution:** Third-party plugins under `plugins/` MUST be declarative JSON packs (`manifest.json`, `operations.json`, `policies.json`) verified by SHA-256 checksum, `sdk_version == "1.0"`, schema validation, and runtime-enforced `PluginContext` permissions. Never load third-party plugin code via `importlib`, `exec()`, or `eval()`.
- **Pure-Python Stdlib Core:** Core MemoryOS, Jupiter Studio, `Frank-v1`, and Control Plane modules (`src/memoryos/frank.py`, `src/memoryos/ops_console.py`, `src/memoryos/control_plane.py`, `src/memoryos/memory_keeper.py`, `src/memoryos/speculative_offload.py`) must run on pure Python standard library with zero required `torch`, `numpy`, `sklearn`, or `onnxruntime` runtime dependencies.
- **Canonical Naming & Honest Copy:**
  - Always use **`NEON`** (never `NEO`) for the certification framework, directive (`NEON_FINAL_DIRECTIVE.md`), and validation harness (`NEON_SINGLE_FILE.py`).
  - The built-in zero-VRAM continual helper model is **`Frank`** (`Frank-v1`, `studio:frank`, `memory/models/Modelfile.frank`); its learning, memory, and audit center inside Studio is **`FrankHub`**.
  - Match documentation, UI labels, and benchmarks 1:1 to verified running code; explicitly separate shipped capabilities from roadmap items and avoid startup buzzwords.
- **Database Isolation in Tests:** Never write test sessions, operations ledger rows, or memory facts into production `QuietAdvisorDB.sqlite`; mock or patch `_get_studio_db_path` to a temporary directory.
