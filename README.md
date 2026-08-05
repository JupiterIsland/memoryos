# MemoryOS

MemoryOS is a local-first, tiered memory engine for AI workloads.
It provides a Thermal TLB (hot/cold block caching), a Temporal Graph (versioned knowledge persistence), and NVMe Checkpointing (reboot survival) in a single Python library.
Designed to be embedded into larger orchestration stacks (like Jupiter One), MemoryOS gives local AI a memory layer that survives power loss and adapts to available VRAM/RAM.
No cloud. No subscriptions. Runs on your hardware.

Status: v0.1.0-pre released. Desktop UI, visualizer, and yt-dlp stream fetching are live. Audio routing is the final remaining patch for Linux users.
