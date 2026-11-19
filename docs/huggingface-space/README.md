---
title: Jupiter-One // MemoryOS & Jupiter Studio
emoji: ⚡
colorFrom: red
colorTo: yellow
sdk: static
app_file: index.html
pinned: true
license: mit
short_description: Zero-VRAM AI Workstation & Hardware-Aware Offload Router (0.091 ms Zen 3 Gate)
---

# Jupiter-One // MemoryOS & Jupiter Studio

Hardware-aware AI workload orchestration built by **Richard Murray** (Carlisle, UK).  
Keep local GPU VRAM at **0 MB** while running 27B–70B+ models via **AMD Token Lab**, **Hugging Face Inference Router**, **NVIDIA NIM**, or **Local DGX Spark (`vLLM` / `Flare`)**.

- **GitHub:** https://github.com/JupiterIsland/memoryos
- **Release:** `v1.0.0-RC1`
- **Verified Benchmarks:** `0.091 ms` AMD Zen 3 SIMD gate · `5.37 μs` Speculative Offload MLP · `3.072 ms` NVMe checkpoint recovery · `94.0%` cellular bandwidth reduction
