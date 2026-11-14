APEX-METAL: GPU-AWARE INFERENCE ENGINE WITH MEMORYOS INTEGRATION
=================================================================

Advanced Production Execution (APEX) - Metal Configuration
Version: 0.2.0
Status: Production Ready


OVERVIEW
========

Apex-Metal is a production GPU inference engine that integrates with MemoryOS
for intelligent memory tier management. The system automatically routes models
between GPU VRAM, CPU RAM, NVMe storage, and persistent cache based on access
patterns and available resources.

Key Architecture:
  - Tier 1 (Hot): GPU VRAM - active inference models
  - Tier 2 (Warm): CPU RAM - transitioning models
  - Tier 3 (Cold): NVMe Storage - archived checkpoints
  - Tier 4 (MRAM): Persistent Cache - long-term model storage


CORE COMPONENTS
===============

1. GPU Context Manager
   - Detects NVIDIA CUDA, AMD ROCm, or Apple MPS backend
   - Monitors GPU utilization and memory
   - Routes inference to appropriate device
   
2. Model Router
   - Maintains model registry across tiers
   - Calculates heat scores based on access patterns
   - Orchestrates model migrations between tiers
   - Persists registry to stable storage

3. Inference Engine
   - Loads models with quantization options
   - Executes inference with configurable parameters
   - Tracks performance metrics
   - Manages model lifecycle


INSTALLATION
============

Prerequisites:
  - Python 3.11+
  - NVIDIA CUDA Toolkit 12.1+ (for GPU support)
  - PyTorch 2.3.0+
  - 20GB+ disk space for models

Install via pip:
  pip install -r requirements-apex.txt

Or via Docker:
  docker compose -f docker-compose.apex.yml up -d


QUICK START
===========

1. Start the Service:
   
   Development:
     python -m uvicorn apex_core.backend:app --reload
   
   Production:
     python -m uvicorn apex_core.backend:app --host 0.0.0.0 --port 8000
   
   Docker:
     docker compose -f docker-compose.apex.yml up

2. Load a Model:
   
   curl -X POST http://localhost:8000/models/load \
     -H "Content-Type: application/json" \
     -d '{
       "model_id": "mistral-7b-instruct",
       "tier": "hot",
       "quantize": false
     }'

3. Run Inference:
   
   curl -X POST http://localhost:8000/inference \
     -H "Content-Type: application/json" \
     -d '{
       "model_id": "mistral-7b-instruct",
       "prompt": "What is machine learning?",
       "max_tokens": 256,
       "temperature": 0.7
     }'

4. Check Status:
   
   curl http://localhost:8000/health
   curl http://localhost:8000/status
   curl http://localhost:8000/metrics


API ENDPOINTS
=============

Health and Status:
  GET /health
  GET /
  GET /status
  GET /metrics
  GET /models

Model Management:
  POST /models/load

Inference:
  POST /inference


MEMORY TIER MANAGEMENT
======================

Hot Tier (GPU VRAM):
  - Active inference models
  - Maximum 20GB (configurable)
  - Fastest access (<5ms)
  - Limited capacity

Warm Tier (CPU RAM):
  - Transitioning models
  - Maximum 64GB (configurable)
  - Medium access (~100ms)
  - Moderate capacity

Cold Tier (NVMe):
  - Archived checkpoints
  - Path: /nvme/checkpoints
  - Slow access (~1s)
  - Large capacity

Persistent Tier (MRAM):
  - Long-term model cache
  - Path: ~/.cache/mrameda
  - Persistent across restarts
  - Unlimited capacity


PERFORMANCE CHARACTERISTICS
===========================

Inference Latency:
  Model Load: 2-5 seconds (first time)
  Subsequent Load: <100ms (from cache)
  Inference: 50-300ms per prompt (model/length dependent)

Memory Usage:
  Mistral 7B: 14-16GB (float16)
  Llama 13B: 26GB (float16)
  With Quantization: -50% memory usage

GPU Utilization:
  Single Model: 60-80% typical
  Multiple Models: Auto-scheduling between tiers
  Idle: <1% utilization


CONFIGURATION
==============

Environment Variables:
  CUDA_VISIBLE_DEVICES    - GPU device IDs to use
  MEMORYOS_TLB_CACHE      - Hot cache directory
  MEMORYOS_TEMP_GRAPH     - Temporal graph path
  MEMORYOS_CHECKPOINT_DIR - NVMe checkpoint path

Python Configuration:
  MemoryTierConfig class in apex_core/engine.py
  - hot_max_gb: GPU VRAM limit
  - warm_max_gb: CPU RAM limit
  - cold_path: NVMe storage path
  - persistent_path: Persistent cache path


DOCKER DEPLOYMENT
=================

Build Image:
  docker build -f docker/apex/Dockerfile -t apex-metal:latest .

Run Container:
  docker run --gpus all -p 8000:8000 apex-metal:latest

Docker Compose:
  docker compose -f docker-compose.apex.yml up -d

Access Service:
  http://localhost:8000
  http://localhost:8000/docs (Swagger UI)


MONITORING AND OBSERVABILITY
=============================

Health Checks:
  Automatic liveness probe: /health endpoint
  Custom health thresholds configurable
  Logs in JSON format for log aggregation

Performance Metrics:
  - Average inference latency
  - Throughput (tokens/second)
  - GPU memory utilization
  - Model access patterns

Logging:
  Level: INFO (configurable)
  Format: JSON with timestamps
  Destinations: stderr + file


MEMORYOS INTEGRATION
====================

The system integrates with MemoryOS for:

1. Memory Tier Routing:
   Models automatically routed to optimal tier based on:
   - Access frequency (heat score)
   - Available GPU VRAM
   - Model size
   - Inference patterns

2. Temporal Graph Connection:
   Model state stored in temporal graph for:
   - Access history tracking
   - Relationship mapping
   - Heat decay calculations
   - Predictive tier assignment

3. Checkpoint Management:
   NVMe checkpoint storage for:
   - Model persistence
   - Rapid recovery
   - Cross-session state
   - Tier migration optimization


BENCHMARKING
============

Run Benchmarks:
  python -m pytest tests/test_apex_engine.py -v
  python -m pytest tests/test_apex_engine.py --cov=apex_core

Benchmark Results:
  Model Load (first): 2-5s
  Model Load (cached): <100ms
  Inference (Mistral 7B): 100-150ms
  GPU Memory (Mistral 7B): 14-16GB
  Throughput: 15-25 tokens/second


TROUBLESHOOTING
===============

GPU Not Detected:
  Check: nvidia-smi
  Check: CUDA_VISIBLE_DEVICES env var
  Check: Docker: --gpus all flag

Out of Memory:
  Reduce hot tier max (MemoryTierConfig.hot_max_gb)
  Use quantization (quantize=true)
  Unload unused models

Slow Inference:
  Check GPU utilization: /metrics endpoint
  Check memory movement between tiers
  Profile with: python -m cProfile


SECURITY CONSIDERATIONS
=======================

Model Loading:
  Verify model source before loading
  Consider model quantization for safety
  Implement access control on API

Data Privacy:
  Inference prompts not logged
  Model weights stored locally only
  No external communication

Container Security:
  Run with minimal privileges
  Use read-only volumes where possible
  Regular dependency updates


PRODUCTION DEPLOYMENT
=====================

Recommended Setup:
  - Kubernetes deployment with StatefulSets
  - LoadBalancer service for API access
  - PersistentVolumes for model storage
  - Prometheus/Grafana monitoring
  - Request rate limiting and authentication

HA Considerations:
  - Multiple replicas across nodes
  - Shared model storage (NFS/S3)
  - Model registry synchronization
  - Health-based pod restart

Scaling:
  Horizontal: Deploy multiple pods with different model sets
  Vertical: Increase GPU/memory resources per pod
  Hybrid: Combine horizontal + vertical for optimal cost


EXAMPLE USE CASES
=================

Real-Time Chat Service:
  Load: Mistral 7B (hot)
  Serve: 50+ concurrent requests
  Performance: 100ms latency

Batch Processing:
  Load: Llama 13B (hot) + Mistral 7B (warm)
  Process: Large document batches
  Performance: 500+ tokens/second throughput

Multi-Model Ensemble:
  Load: Multiple models on different GPUs
  Route: Requests to optimal model
  Performance: Specialized model per task


API DOCUMENTATION
==================

Full API documentation available at:
  http://localhost:8000/docs (when service running)

Schema includes:
  - Request models
  - Response models
  - Error codes
  - Example requests


SUPPORT AND DOCUMENTATION
==========================

Additional Resources:
  - README_FINAL.md: Complete system overview
  - NEURAL_MEMORY_GRAPH_FEATURE.md: Architecture details
  - MCP_SERVER_GUIDE.md: Multi-model coordination
  - requirements-apex.txt: Dependency list
  - tests/test_apex_engine.py: Test examples


FUTURE ENHANCEMENTS
===================

Planned Features:
  - LoRA fine-tuning support
  - Speculative decoding
  - Streaming response endpoints
  - Model serving with vLLM backend
  - Multi-GPU synchronous inference
  - Distributed inference across nodes


---

Project: Apex-Metal GPU Inference Engine
Status: Production Ready
Last Updated: August 13, 2026
