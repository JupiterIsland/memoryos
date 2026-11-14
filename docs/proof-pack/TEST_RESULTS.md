# MemoryOS Proof of Work — Validation & Telemetry Results

**Status:** Working Developer Preview (Production Telemetry Verified)  
**Repository:** `https://github.com/JupiterIsland/memoryos`  
**Audit Timestamp:** `2026-11-14T09:01:20.170720Z`

---

## 1. Visual Proof Pack Index (`/docs/proof-pack/`)

| File | Evidence Captured |
| :--- | :--- |
| ![Quiet Advisor Dashboard](quiet-advisor-dashboard.png) | **`quiet-advisor-dashboard.png`** — Live Quiet Advisor Web Dashboard (`100% Remote` RTX 3070 VRAM isolation, `d3` aux-router scoring, `2.2%` context window used, `67–78 / 10M` micro-points, and multi-model latency bars). |
| ![Token Lab Usage](tokenlab-usage.png) | **`tokenlab-usage.png`** — Official AMD Token Lab account & request ledger (`RJMedia.ai@outlook.com`, key prefix `tl-9aa35a3`, `19` requests, `1,946` tokens, `27` gateway allowed / `0` denied). |
| ![Architecture Overview](architecture-overview.png) | **`architecture-overview.png`** — 3-Service Hybrid Architecture (`jupiter-desktop` PyQt6 + CPU `cv2` MSE -> `memoryos-router` ~150MB -> AMD Instinct Token Lab `d3` + `Gemma-4-31B-IT` + `Qwen3.8-27B`). |
| ![Telemetry & Routing](telemetry-routing.png) | **`telemetry-routing.png`** — Context Waste (`93%+` unused context window trapped) & VRAM Thrashing (`vram_thrashing_penalty = 1.5` closed loop) + multi-model latency distribution. |

---

## 2. Screenshot Evidence Summary

### MemoryOS Proof of Work

**Current validation results:**
- Quiet Advisor dashboard running (`http://127.0.0.1:5000`)
- SQLite WAL telemetry active (`QuietAdvisorDB.sqlite`)
- Token Lab model routing active (`https://api.tokenlab.amd.com/v1`)
- Context waste detector active (`~93%` unused context window identified with equivalent output quality)
- `d3` decision routing visible (`/v1/systemone` structured probability scoring: `surface_now`, `defer`, `ignore`)
- Multi-model latency telemetry visible
- NVMe atomic JSON checkpoint tracking active (`memory/checkpoints/`)
- `100%` remote inference offload demonstrated (`0 MB` local RTX 3070 VRAM consumed by 27B/31B models)

**Observed models:**
- `Gemma-4-31B-IT` (Multimodal VLM scene inspection & labeling)
- `Qwen3.8-27B` (Heavy code generation & architectural reasoning)
- `MiniCPM5-2B` (Low-latency edge summarization & triage)
- `DeepSeek-V4.1-Flash` (Fast structured JSON routing tier)
- `d3` (SystemOne probabilistic gatekeeper via `/v1/systemone`)

**Current dashboard metrics:**
- `6` seeded baseline / `19` Token Lab export / `26` total routed inferences logged
- `100%` remote offload (`0 MB` local VRAM sacrificed)
- Context optimisation & VRAM protection recommendations generated
- Detector actions (`[Acknowledge & Apply]`, `Dismiss`, `Mute Detector`) available through Web & PyQt6 UI

---

## 3. Core Positioning & Messaging Guide

### Category Positioning
Focus on the capabilities visibly proven in the telemetry dashboard:
- **AI Traffic Control**
- **AI Routing**
- **Context Optimisation**
- **VRAM Protection**
- **Memory-Aware Computing**

*(Avoid generic commodity labels like "AI Assistant", "AI Chat", or "AI Agent".)*

---

## 4. Ready-to-Publish Outreach & Social Copy

### A. AMD Developer Relations Follow-Up Email

**Subject:** MemoryOS Operational Evidence — `d3` Routing, Context Waste Telemetry & Multi-Model Offload on AMD Token Lab

Hi AMD Developer Relations,

Following my previous email, I wanted to share additional operational evidence from the **MemoryOS + Quiet Advisor** prototype (`https://github.com/JupiterIsland/memoryos`).

The Quiet Advisor dashboard is now operational and demonstrates:
- Multi-model routing telemetry
- Context waste detection
- `d3` recommendation scoring (`/v1/systemone`)
- NVMe atomic checkpoint tracking
- `100%` remote inference routing (`0 MB` local 8GB GPU VRAM sacrificed)
- SQLite WAL telemetry persistence

Current dashboard telemetry shows successful routing activity across:
- `Gemma-4-31B-IT`
- `Qwen3.8-27B`
- `MiniCPM5-2B`
- `DeepSeek-V4.1-Flash`
- `d3` (`/v1/systemone`)

One of the most interesting observations has been the **Context Waste Detector**. During testing it identified that approximately **93%+ of supplied context was unused** while maintaining equivalent output quality, creating a clear opportunity for token and latency reduction alongside `d3` frame-delta gatekeeping.

The project is progressing from architecture into measurable operational evidence (full proof pack in `/docs/proof-pack/`). I would be happy to share screenshots, telemetry captures, and a short demonstration walkthrough—and would love to discuss porting the local watcher tier onto a **Ryzen AI (XDNA 2 NPU)** dev unit to benchmark an all-AMD client-to-cloud reference stack.

Best regards,

**Richard Murray**  
MemoryOS / Jupiter Desktop  
Carlisle, UK  
https://github.com/JupiterIsland/memoryos

---

### B. Reddit Post (`r/LocalLLaMA`, `r/AMD`, `r/MachineLearning`)

**Title:** Built a local-first AI traffic controller & routing system called MemoryOS (VRAM protection + context waste detection + d3 routing)

Built a local-first AI routing system called **MemoryOS** (`https://github.com/JupiterIsland/memoryos`).

The idea was simple:

Most people don't have 48GB GPUs.

So instead of blindly throwing every task at a local model, MemoryOS calculates CPU `cv2` frame delta changes, checks context efficiency, tracks inference telemetry, and routes work only when it actually matters.

**Current features:**
- Quiet Advisor recommendation engine
- Context waste detection (`~93%` unused context trapped in testing)
- Multi-model routing (`Gemma-4-31B-IT`, `Qwen3.8-27B`, `MiniCPM5-2B`, `DeepSeek-V4.1-Flash`, gated by `d3`)
- SQLite WAL telemetry + closed-loop `[Acknowledge & Apply]` hardware penalty enforcement
- AMD Token Lab integration
- Dashboard with live routing statistics
- Video analysis workflows through Jupiter Desktop (PyQt6)

**Current dashboard result:**
- `100%` inference offload (`0 MB` local RTX 3070 VRAM used for 27B/31B inference)
- Context waste & VRAM thrashing detection
- Multi-model latency telemetry
- NVMe atomic checkpoint tracking

Still early, but it's at the stage where it is becoming a real platform rather than a collection of scripts. Proof pack and screenshots are in `/docs/proof-pack/`.

Feedback welcome.

---

### C. Discord Post

Been building something called **MemoryOS** (`https://github.com/JupiterIsland/memoryos`).

Think of it as an **AI traffic controller** rather than another chatbot.

Instead of loading huge models locally, it:
- Monitors workloads
- Detects context waste (`~93%` unused context window caught in live runs)
- Calculates CPU `cv2` frame changes before touching vision models
- Routes tasks to the correct model (`d3`, `Gemma-4-31B-IT`, `Qwen3.8-27B`, `MiniCPM5-2B`, `DeepSeek-V4.1-Flash`)
- Tracks SQLite + NVMe checkpoint telemetry
- Learns from user actions (`[Acknowledge & Apply]` closes the loop in the router)

Current dashboard is live with telemetry, routing statistics, and recommendation cards (`/docs/proof-pack/`).

Starting to feel less like a project and more like a platform.

---

### D. Banner Advert Copy

**MEMORYOS**  
Stop throwing every prompt at a giant model.  
**Detect. Route. Optimise.**

- Context Waste Detection
- Intelligent Model Routing
- Quiet Advisor Recommendations
- Telemetry Tracking
- Memory-Aware Workflows

*Built for real hardware. Not fantasy GPUs.*  
**MemoryOS + Jupiter Desktop** — `https://github.com/JupiterIsland/memoryos`
