# NVIDIA backend assessment

**Assessment date:** 2026-11-15  
**Scope:** Review of the repository’s current NVIDIA/CUDA-related code, not a claim of NVIDIA certification or production readiness.

## Summary

MemoryOS already contains some CUDA-aware code and NVIDIA-related prototypes, but it does not currently have a complete, validated NVIDIA inference backend. The strongest existing starting point is the `apex_core` GPU device detector. Several surrounding features are placeholders or report synthetic values, so the project should be described as having **experimental CUDA detection/prototype code**, not as a tested NVIDIA version.

## What exists today

- [`apex_core/engine.py`](../../apex_core/engine.py) checks `torch.cuda.is_available()` and can return a CUDA device name. It also checks Apple MPS, but it does not implement full AMD ROCm selection despite a broad CUDA/ROCm docstring.
- The same engine currently uses mock model objects and simulated inference (`asyncio.sleep` plus generated placeholder text). Its model migration method is also a placeholder. It is not yet a real model-serving backend.
- `get_device_memory()` reports the device's **total** CUDA memory, not currently available memory. `get_device_utilization()` calculates allocated/reserved PyTorch memory, not NVIDIA's GPU compute utilization. These names and metrics should be corrected before using them for scheduling decisions.
- [`src/memoryos/router.py`](../../src/memoryos/router.py) has a `prefer_local` branch that hardcodes `local-rtx3070` and fixed GPU memory/utilization figures. This is a simulation/example path, not generic NVIDIA hardware detection or measured telemetry.
- [`src/memoryos/core/neural_memory_graph.py`](../../src/memoryos/core/neural_memory_graph.py) has optional `pynvml` telemetry, but on missing telemetry it returns fixed example numbers. The fallback must be labeled as simulated and must never influence real routing policy.
- [`src/memoryos/integrations/riva_voice.py`](../../src/memoryos/integrations/riva_voice.py) describes NVIDIA Riva integration, but its current speech methods simulate audio/transcription rather than making Riva API calls.
- [`requirements-apex.txt`](../../requirements-apex.txt) pins PyTorch 2.3.0 and Transformers 4.40.0. The dependency set and CUDA build/install matrix need review against the actual target systems before being called supported.
- The current README and release notes focus mainly on AMD Token Lab routing and an AMD Ryzen reference CPU. The repository has no clearly documented, end-to-end NVIDIA support matrix or reproducible NVIDIA inference benchmark yet.

## Recommended NVIDIA path

### Phase 1 — Correct the capability and telemetry layer

1. Replace the hardcoded RTX device label and metrics with runtime detection. Make device selection configurable and support multiple CUDA devices without assuming device index 0.
2. Separate **total**, **allocated**, **reserved**, and **free** VRAM metrics. Use a documented source for each value and distinguish PyTorch allocator statistics from whole-device telemetry.
3. Make missing telemetry explicit (`unavailable`), rather than returning plausible-looking synthetic values in production paths. Put deterministic fake metrics behind an explicit test/demo mode.
4. Add unit tests for CPU-only systems, CUDA unavailable, one GPU, multiple GPUs, telemetry library missing, and telemetry query errors.
5. Keep NVIDIA-specific imports optional so the core MemoryOS package remains usable without CUDA or NVML installed.

### Phase 2 — Implement one real local inference adapter

1. Select one supported inference runtime and a small set of tested model configurations. Avoid claiming support for TensorRT-LLM, CUDA graphs, KV-cache offload, or Riva until the corresponding code path is implemented and exercised.
2. Implement real model load, inference, unload, and error reporting behind a backend interface; keep the existing Token Lab/cloud route as a separate provider.
3. Validate VRAM pressure and fallback behavior with real requests. Log model/runtime versions, GPU model, driver, CUDA runtime, precision/quantization, prompt length, warm/cold state, latency distributions, and failures.
4. Benchmark on at least one NVIDIA GPU with a published, reproducible command and workload. Report p50/p95/p99 and tokens/second; avoid comparing unlike model, quantization, or serving configurations.

### Phase 3 — Add NVIDIA optimization features selectively

Only after the baseline adapter is correct, evaluate whether CUDA graphs, pinned host memory, KV-cache management, or TensorRT-LLM are appropriate for the selected runtime and workloads. Treat each as an optional capability with clear prerequisites, correctness tests, and measured before/after results. Riva should be a separate optional integration and should use the actual supported client/server API.

## Suggested acceptance criteria

- No hardcoded device names, VRAM capacities, or utilization values in production routing.
- CPU-only execution and package installation work without NVIDIA dependencies.
- Telemetry labels distinguish process allocator memory from total device usage and compute utilization.
- At least one real local inference path passes automated tests on a documented NVIDIA configuration.
- The published benchmark is reproducible and labels measured results, estimates, and simulated/demo data distinctly.
- Documentation states exact supported GPU, driver, CUDA/runtime, Python, and model combinations; unsupported configurations fail clearly.

## Practical conclusion

An NVIDIA-focused implementation is feasible, and the repository already has prototype pieces to build from. The first work should be accuracy and testability—not adding more NVIDIA-branded features. In particular, replace simulated telemetry and the mocked `apex_core` inference path before presenting MemoryOS as an NVIDIA-supported local inference solution.
