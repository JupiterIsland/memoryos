# AMD Developer Relations outreach draft

**Status:** Draft only — not sent.  
**Suggested audience:** AMD Developer Relations or the appropriate Ryzen AI / ROCm developer-support contact.  
**Purpose:** Request technical direction and feedback on the AMD-specific paths in MemoryOS.

---

**Subject:** Request for technical feedback: MemoryOS AMD Ryzen frame-gating and inference routing

Hello AMD Developer Relations team,

I’m Richard Murray, an independent developer working on [MemoryOS](https://github.com/JupiterIsland/memoryos), an early-stage project exploring hardware-aware AI workload routing, frame-delta gating, telemetry, and checkpoint recovery.

The current preview includes an AMD-focused CPU frame-delta path and experimental hardware detection for Ryzen AI, alongside a remote model-routing path. The project is still a developer preview; I’m seeking technical feedback rather than presenting it as an AMD-supported or production-ready integration.

Would you be able to point me toward the right documentation, developer program, or engineering contact for questions about:

- detecting and selecting Ryzen AI NPU execution providers reliably across supported platforms;
- the recommended current runtime and deployment path for Ryzen AI / XDNA systems;
- best practices for evaluating CPU frame-gating latency and reporting repeatable benchmark results; and
- whether the project’s Ryzen AI / AOCL / ZenDNN descriptions align with AMD’s supported terminology and software stack?

The relevant implementation and notes are in the repository:

- [AMD hardware detection and Zen CPU frame-delta implementation](https://github.com/JupiterIsland/memoryos/blob/main/src/memoryos/amd_zen_studio.py)
- [Project README](https://github.com/JupiterIsland/memoryos/blob/main/README.md)
- [Preview release notes](https://github.com/JupiterIsland/memoryos/blob/main/RELEASE_NOTES.md)

If there is a public developer forum or a more suitable contact for these questions, a pointer would be greatly appreciated. I can provide a concise test setup and benchmark methodology if useful.

Thank you for your time,

Richard Murray  
Jupiter Island / RJMedia  
Carlisle, UK

---

## Before sending

- Confirm that the implementation and benchmark results linked above are current and reproducible.
- Include a short hardware/software test matrix if available; clearly label measured results and estimates.
- Do not imply AMD endorsement, partnership, certification, or support unless AMD has explicitly granted it.
- Use an official AMD contact or developer channel found through AMD’s current public website; no recipient address is assumed in this draft.
