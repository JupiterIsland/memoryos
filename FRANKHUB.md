# FrankHub

**FrankHub is where Frank learns.**

FrankHub is the learning, memory, and audit center inside **[Jupiter Studio](README.md)**. It started with one practical question:

> If a local AI workstation adapts to how you work, how do you stop it from forgetting what worked yesterday?

---

## What Is Frank?

**Frank** (`Frank-v1`) is a lightweight local neural helper built specifically for Jupiter Studio ([`src/memoryos/frank.py`](src/memoryos/frank.py)).

* Frank is **not** a chatbot replacing frontier LLMs like GPT, DeepSeek, Gemma, or Qwen — those models do the heavy reasoning.
* Frank sits between you and your local/cloud model pool as a pure-Python standard-library `128→24→6` Hashing N-Gram MLP + Softmax router and offline workstation responder (`0 MB` GPU VRAM, `241–335 μs` CPU latency).
* An optional Ollama persona definition ([`memory/models/Modelfile.frank`](memory/models/Modelfile.frank)) lets you run a companion local model alongside the built-in neural core.

### Philosophy

```text
Be useful.
Don't get in the way.
```

* If Frank can route cleanly or answer from live hardware/vault telemetry, it does.
* If confidence is out-of-distribution (`OOD`), it abstains instead of guessing blindly.
* If Frank learns a new pattern, it retains earlier skills instead of overwriting them.
* Every continual update and checkpoint stays inspectable on disk.

---

## What Lives Inside FrankHub Today

Everything listed below is live and tested inside the **FrankHub** rail tab (`#pane-memory`) and `memoryos.memory_keeper`:

| Component | What It Does Today | Source |
| :--- | :--- | :--- |
| **Memory Vault** | Persists pinned facts, hardware rules, and workspace context across restarts in SQLite WAL (`continual_memory_facts`). | [`src/memoryos/memory_keeper.py`](src/memoryos/memory_keeper.py) |
| **Frank (`Frank-v1`) Live Teaching** | `Teach Frank` (`POST /api/frank/teach`) reinforces phrasing across **6 active intents**: `fast_code`, `architecture`, `large_design`, `cheap_bg`, `vram_reclaim`, and `memory_pin`. | [`src/memoryos/frank.py`](src/memoryos/frank.py) |
| **EWC + Experience Replay** | Incremental Fisher diagonal anchoring (`MAX_FISHER_VALUE = 20.0` in Frank; `25.0` in Speculative Router) paired with bounded experience replay (`MAX_REPLAY_EPISODES = 2000`) and provenance filtering (`TRUSTED_EPISODE_SOURCES`). | [`src/memoryos/speculative_offload.py`](src/memoryos/speculative_offload.py) |
| **Audit Frank (`A → B → C` Self-Test)** | Compares Naive SGD vs EWC + Replay sequential learning live in Studio (`POST /api/memory/audit`) — proving earlier skills stay at `100%` retention instead of collapsing to `0%`. | [`tests/test_memory_keeper.py`](tests/test_memory_keeper.py) |
| **Checkpoint Integrity & Quarantine** | Schema-versioned JSON checkpoints verified by `checksum_sha256`; corrupted or tampered checkpoints are automatically quarantined to `.json.corrupt` with clean fallback recovery. | [`memory/models/frank_v1.json`](memory/models/frank_v1.json) |
| **Active VRAM & RAM Reclaim** | One-click `Free VRAM & RAM` (`POST /api/memory/reclaim`) safely unloads idle Ollama models (`keep_alive: 0`) before a game or compile. | [`apps/jupiter_studio.py`](apps/jupiter_studio.py) |

---

## The Story & Project Lineage (No Hype)

A year ago I wasn’t trying to build Frank or Jupiter Studio. People kept talking about AI like an abstract mystery box, so I started tinkering on a consumer laptop to see what actually happened under the hood.

Instead of one grand master plan, Jupiter Studio emerged as multiple independent experiments gradually converged:

```text
┌──────────────────────────────────────────────────────────────┐
│                       PROJECT LINEAGE                        │
└──────────────────────────────────────────────────────────────┘

  2025
    │
    ├── Order 66
    │   Knowledge capture experiments for preserving
    │   useful AI conversations, research and ideas.
    │
    ├── MemoryOS
    │   Persistent memory and context retention systems
    │   for long-running AI workflows.
    │
    └── The Quiet Advisor
        Telemetry, monitoring and recommendation engine
        focused on hardware awareness and workflow signals.

  2026
    │
    ├── Gordon
    │   Local AI runtime, automation and orchestration
    │   experiments across multiple tools and models.
    │
    ├── AI Engine Master
    │   Multi-model routing and local/cloud inference
    │   pipeline research.
    │
    ├── Adaptive Tone Engine
    │   Behaviour-adaptation and contextual response
    │   experiments.
    │
    ├── AI Media Ops Console
    │   Metadata, transcript and media workflow
    │   automation platform.
    │
    ├── Video AI Engine
    │   Video processing and AI-assisted media
    │   enhancement experiments.
    │
    ├── JupiterOne
    │   First attempt to unify local AI, telemetry,
    │   audio systems and workstation automation.
    │
    ├── Frank
    │   Lightweight neural assistant using continual
    │   learning, EWC and experience replay.
    │
    ├── FrankHub
    │   Memory Vault, retention audits, replay buffers,
    │   checkpoint integrity and learning systems.
    │
    └── Jupiter Studio
        Unified AI workstation combining workspace,
        memory, routing, telemetry and orchestration.
```

A lot of experiments got binned along the way. The ideas that kept solving real problems — remembering hardware limits, reclaiming idle VRAM, routing workloads honestly, and preventing continual learners from forgetting — survived and converged into Jupiter Studio.

---

## Roadmap (Future Goals)

Ideas intentionally scoped for next releases (not yet shipped in `v2.0.0`):

* Expanded teaching intents (such as dedicated `research_tasks` and custom user-defined routing classes)
* Multi-session retention trend graphs & Fisher drift history inside the FrankHub panel
* Deeper per-project workspace memory scoping and automated teaching workflows

---

## Quick Verification

Run Frank's unit + HTTP suite and the 3-task continual retention audit locally:

```bash
PYTHONPATH=. python3 -B -m unittest tests/test_frank.py tests/test_memory_keeper.py
PYTHONPATH=.:src python3 -B -m memoryos.memory_keeper audit
```

See **[`LAUNCH_CHECKLIST.md`](LAUNCH_CHECKLIST.md)** for Windows clean-install automation and **[`docs/outreach/FRANKHUB_LAUNCH_PACK.md`](docs/outreach/FRANKHUB_LAUNCH_PACK.md)** for the GitHub, Discord, and LinkedIn rollout pack.
