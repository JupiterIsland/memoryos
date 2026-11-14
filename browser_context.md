## MemoryOS Architecture Overview
> **Category:** `architecture`
MemoryOS is a tiered memory engine with TLB Hot Cache (volatile fast access), Temporal Graph (relationships), and NVMe Checkpoints (persistent storage). No cloud dependency - fully local-first.
- Source: `system_init`
- Confidence: 98%

---


## Heat Stream Engine Purpose
> **Category:** `heat_stream`
The Heat Stream monitors TLB Hot Cache for memory blocks with high access frequency and auto-formats them into Markdown snippets ready for LLM injection into system prompts.
- Source: `system_init`
- Confidence: 95%

---


## Browser App Context Sync
> **Category:** `browser_integration`
ContextSyncBridge provides one-click sync from CLI heat cache to browser context window. Supports auto-injection into LLM prompts via {HOT_CONTEXT} placeholder.
- Source: `system_init`
- Confidence: 92%

---


## User Preferences
> **Category:** `user_context`
User prefers alpine-based Docker images, efficient resource usage, and local-first approaches. Works with NVIDIA RTX 4090 on Windows PowerShell environment.
- Source: `conversation`
- Confidence: 88%

---


## Development Workflow - MemoryOS
> **Category:** `workflow`
Initialize with 'memoryos init', build index with 'memoryos index', scan hot cache with 'memoryos tlb scan', export to markdown, inject into browser app LLM context.
- Source: `documentation`
- Confidence: 90%