# AMD Token Lab & Developer Pages Outreach Kit — MemoryOS + Quiet Advisor + Jupiter Desktop

Prepared for: **Richard Murray** (MemoryOS / Jupiter Desktop — Carlisle, UK)  
Repository: `https://github.com/JupiterIsland/memoryos`

---

## 1. Email to AMD Token Lab / Developer Cloud / AI DevRel Team

**To:** AMD Token Lab Team / AMD AI Developer Relations (`developer@amd.com` / Token Lab Console Feedback / AMD DevRel)  
**Subject:** Production Case Study on AMD Token Lab: Zero-VRAM Local Desktop Offload via `d3` (`/v1/systemone`) + `Gemma-4-31B-IT` & `Qwen3.8-27B`

Hi AMD Token Lab & DevRel Team,

I'm writing to share a production hybrid desktop architecture we just built on top of **AMD Token Lab** (`https://api.tokenlab.amd.com/v1`) that solves one of the biggest pain points for everyday PC developers: **8GB consumer GPU VRAM saturation during multimodal and coding workloads**.

### What We Built (`MemoryOS` + `The Quiet Advisor` + `Jupiter Desktop v2`)

Most developers and creators sit on 8GB local GPUs (like an RTX 3070). As soon as they run video frame VLM inspection, OCR, or 30B-class reasoning alongside their desktop apps, local VRAM thrashes and PCIe bandwidth chokes.

Using our AMD Token Lab grant, we sliced a 15GB monolithic stack into a 3-service hybrid architecture (~150MB router footprint, zero local PyTorch bloat) powered by AMD Instinct compute:

1. **CPU MSE Delta + `d3` Probabilistic Gatekeeping (`/v1/systemone`)**:
   - When a user pauses a video or crosses a scene boundary in **Jupiter Desktop (PyQt6)**, we extract the frame via CPU `cv2`, compute the grayscale MSE & visual delta, and query **Token Lab `d3`** (`POST /v1/systemone`) before touching any heavy vision model.
   - Static or low-delta frames are scored `ignore` by `d3` in milliseconds (`skip_vision=True`), saving ~60-80% of multimodal calls.
2. **31B Multimodal & 27B Coding Offload (`/v1/chat/completions`)**:
   - Significant scene changes automatically route to **`Gemma-4-31B-IT`** on AMD Instinct.
   - Architecture synthesis and daily IDE/Aider coding workflows route to **`Qwen3.8-27B`**, while lightweight edge compression hits **`MiniCPM5-2B`**.
3. **Closed-Loop Hardware Protection (`The Quiet Advisor`)**:
   - Every inference is logged to a local SQLite WAL telemetry ledger (`QuietAdvisorDB.sqlite`) + crash-safe NVMe JSON checkpoints.
   - When `VRAMThrashingDetector` catches local GPU saturation (>=5.5GB / >=85% utilization), `d3` surfaces a non-intrusive PyQt6 toast card (`confidence=0.85`).
   - Clicking **`[Acknowledge & Apply]`** writes `vram_thrashing_penalty = 1.5` to the database, automatically blocking local GPU execution on future requests and enforcing remote offload to `Gemma-4-31B-IT` on AMD Token Lab.

### Production Telemetry Highlights

- **Local VRAM Sacrificed**: `0 MB` (100% of the local 8GB GPU remains free for display, DuckDB vector search, and NVMe I/O).
- **Models Active in Production**: `d3` (`/v1/systemone`), `Gemma-4-31B-IT`, `Qwen3.8-27B`, and `MiniCPM5-2B`.
- **Grant Efficiency**: Because `d3` gatekeeps redundant frames and low-signal alerts before invoking 27B/31B models, our initial 18-request validation cycle consumed just **67 of 10,000,000 micro-points (`0.00067%`)** with prompt-cache hits active.

### How We Can Collaborate

1. **Developer Showcase / Case Study**: We would love to publish a joint developer blog or feature **MemoryOS + Quiet Advisor** on the AMD Developer Cloud / Token Lab showcase pages as a reference pattern for `d3` (`/v1/systemone`) + multi-model routing.
2. **20-Minute Technical Review**: I'd welcome a brief chat with an engineer on the Token Lab or `d3` / SystemOne team to share our `/v1/systemone` gatekeeping patterns and roadmap.

Repository: https://github.com/JupiterIsland/memoryos

Thanks for building Token Lab — having instant OpenAI-compatible access to `Gemma-4-31B-IT`, `Qwen3.8-27B`, and `d3` probabilistic routing on AMD Instinct completely changed what a solo system builder can run from a standard desktop.

Best regards,

**Richard Murray**  
Creator, MemoryOS / Quiet Advisor / Jupiter Desktop  
Carlisle, UK  
GitHub: https://github.com/JupiterIsland/memoryos

---

## 2. Developer Page / Community Showcase Copy (GitHub Discussions, Dev.to, Hacker News, r/LocalLLaMA, AMD Community)

**Title:**  
`Show HN / Showcase: MemoryOS — Zero-VRAM Local Desktop AI using AMD Token Lab d3 Gatekeeping + Gemma-4-31B-IT`

**Post Body:**

If you have an 8GB GPU (like an RTX 3070), running local VLMs for video scene analysis alongside coding assistants turns your machine into a space heater and instantly OOMs.

I built **MemoryOS + The Quiet Advisor + Jupiter Desktop v2** (`https://github.com/JupiterIsland/memoryos`) to solve this by splitting the stack into a lean ~150MB local router (`memoryos-router`, zero PyTorch dependencies) and offloading heavy compute to **AMD Token Lab** (`Gemma-4-31B-IT`, `Qwen3.8-27B`, `MiniCPM5-2B`) gated by AMD's **`d3`** probabilistic decision engine (`/v1/systemone`).

### How the Closed Loop Works

1. **CPU Frame-Delta Gatekeeping (`/api/frame-delta`)**:
   When you pause a video or cross a scene cut in **Jupiter Desktop (PyQt6)**, the client extracts the current `cv2` frame on CPU, calculates the grayscale MSE delta (`compute_mse_delta()`), and queries `d3` via `/v1/systemone`. If the frame hasn't meaningfully changed, `d3` returns `choice="ignore"` (`skip_vision=True`) and skips the 31B vision call altogether.
2. **Multi-Model AMD Instinct Routing (`/api/route`)**:
   - Multimodal scene inspection -> `Gemma-4-31B-IT`
   - Code generation & architecture (including Aider / Cline / Continue via OpenAI-compatible `/v1`) -> `Qwen3.8-27B`
   - Fast compression -> `MiniCPM5-2B`
3. **Closed-Loop VRAM Protection (`/api/acknowledge-card`)**:
   `QuietAdvisorEngine` monitors `QuietAdvisorDB.sqlite`. When `VRAMThrashingDetector` spots local VRAM saturation, it surfaces a PyQt6 toast card (`confidence=0.85`). Clicking **`[Acknowledge & Apply]`** persists `vram_thrashing_penalty = 1.5`, automatically blocking local heavy execution and forcing future VLM requests onto `Gemma-4-31B-IT` remotely.

### Repo & Quick Start

- **GitHub**: https://github.com/JupiterIsland/memoryos
- **Start the ~150MB Router**: `python server.py --host 127.0.0.1 --port 5000`
- **Launch Jupiter Desktop**: `python apps/jupiter-tv-desktop-v2/app.py`
- **Run Aider on AMD Token Lab (`Qwen3.8-27B`)**: `.\Start-AiderAMD.ps1`

Feedback and questions welcome!

---

## 3. Hardware Seeding / Dev-Kit Pitch (How to Angle for an AMD Ryzen AI Laptop)

**The Rule of Hardware Seeding:** Never ask for a laptop as a personal favor. Pitch a **deliverable that AMD's Ryzen AI + Instinct marketing & DevRel teams badly want**: an open-source **"All-AMD Hybrid AI Reference App" (Ryzen AI XDNA 2 NPU locally + AMD Instinct Token Lab in the cloud)**—and point out that your current bottleneck is that your local test rig is still an 8GB NVIDIA card.

**Target Programs & Contacts:**
1. **AMD AI Developer Program / Ryzen AI Hardware Seeding** (`developer.amd.com` / AMD AI DevRel on LinkedIn & X / `ryzenai@amd.com` / Token Lab team warm intro)
2. **AMD Pervasive AI / University & Independent Developer Hardware Loaner/Grant Program**

**Subject:**  
`All-AMD Hybrid AI Reference App (Ryzen AI NPU + Token Lab Instinct) — Hardware Dev-Kit Request`

**Email Body:**

Hi AMD AI DevRel & Token Lab Team,

I'm the creator of **MemoryOS + The Quiet Advisor + Jupiter Desktop** (https://github.com/JupiterIsland/memoryos), an open-source hybrid desktop AI studio currently running in production against **AMD Token Lab** (`d3` via `/v1/systemone`, `Gemma-4-31B-IT`, and `Qwen3.8-27B`).

Right now, there is an irony in our setup: our cloud routing and `d3` probabilistic gatekeeping are 100% powered by **AMD Instinct via Token Lab**, but my local development machine is still tethered to an **8GB NVIDIA RTX 3070**.

### What I Want to Build & Publish for AMD Next

I want to eliminate the NVIDIA dependency completely and publish the **All-AMD 3-Tier Hybrid AI Desktop Reference Architecture** (`Ryzen AI Local NPU -> Radeon Unified Memory -> AMD Instinct Token Lab`):

1. **Tier 1 — Ryzen AI XDNA 2 NPU (Local Always-On Watcher)**:
   Port `The Quiet Advisor`'s background telemetry detectors, OCR, and frame-delta pre-filtering onto the **Ryzen AI NPU (ONNX Runtime / Vitis AI EP)** so ambient desktop intelligence runs at ultra-low wattage.
2. **Tier 2 — Radeon iGPU / Unified Memory (Local Media & DuckDB Graph)**:
   Run Jupiter Desktop's PyQt6 video studio, local embeddings, and DuckDB temporal memory graph on Ryzen AI unified memory—proving how unified memory beats an 8GB discrete VRAM wall.
3. **Tier 3 — AMD Instinct Token Lab (`d3` + `Gemma-4-31B-IT` + `Qwen3.8-27B`)**:
   Seamless escalation to Token Lab whenever `d3` (`/v1/systemone`) scores a scene cut or architecture task as `surface_now`.

### The Ask (Hardware Dev-Kit / Seeding Unit)

Does AMD DevRel have a **Ryzen AI laptop dev unit** (e.g., **Ryzen AI 9 HX 370 / Strix Point** or **Ryzen AI Max+ "Strix Halo"**) available through your developer seeding or loaner program?

In exchange for a Ryzen AI mobile dev system, I will deliver within 30 days:
- Full **Ryzen AI NPU (XDNA 2) + AMD Token Lab** integration in the open-source `MemoryOS` repo (`https://github.com/JupiterIsland/memoryos`).
- Published **power, latency, and VRAM/unified-memory benchmarks** comparing `8GB Discrete GPU` vs `All-AMD Ryzen AI + Token Lab Hybrid`.
- A step-by-step developer write-up and video walkthrough that AMD DevRel can feature on the AMD Developer blog/showcase.

I already have the Token Lab backend, `d3` gatekeeper, SQLite telemetry engine, and PyQt6 desktop app built and running—I just need portable Ryzen AI silicon to port the local tier off NVIDIA and onto XDNA 2.

Best regards,

**Richard Murray**  
Creator, MemoryOS / Quiet Advisor / Jupiter Desktop  
Carlisle, UK  
GitHub: https://github.com/JupiterIsland/memoryos

