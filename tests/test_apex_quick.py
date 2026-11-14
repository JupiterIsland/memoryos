#!/usr/bin/env python
"""
Quick Test Script for Apex-Metal Inference Engine
===================================================

Run this to verify all components work.
"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from apex_core.engine import (
    MemoryTierConfig,
    GPUContextManager,
    ModelRouter,
    InferenceEngine
)


async def test_gpu_manager():
    """Test GPU detection and device management."""
    print("\n[TEST 1] GPU Context Manager")
    print("=" * 50)
    
    manager = GPUContextManager()
    print(f"GPU Backend:        {manager.device_type}")
    print(f"Device Count:       {manager.device_count}")
    print(f"Current Device:     {manager.get_device()}")
    print(f"Total VRAM (MB):    {manager.get_device_memory():.0f}")
    print(f"Utilization (%):    {manager.get_device_utilization():.1f}")
    
    return manager.device_count > 0


async def test_model_router():
    """Test model routing and registry."""
    print("\n[TEST 2] Model Router")
    print("=" * 50)
    
    config = MemoryTierConfig(
        hot_max_gb=20.0,
        warm_max_gb=64.0,
        cold_path="./nvme_checkpoints",
        persistent_path="./.cache/mrameda"
    )
    
    router = ModelRouter(config)
    print(f"Config loaded:      hot={config.hot_max_gb}GB, warm={config.warm_max_gb}GB")
    print(f"Registry size:      {len(router.model_registry)}")
    
    # Route a test model
    device = await router.route_model("test-mistral-7b", "hot")
    print(f"Model routed to:    {device}")
    print(f"Registry updated:   {len(router.model_registry)} models")
    
    # Update access pattern
    router.update_access_pattern("test-mistral-7b", accessed=True)
    heat = router.model_registry["test-mistral-7b"]["heat_score"]
    print(f"Heat score:         {heat:.2f}")
    
    return True


async def test_inference_engine():
    """Test full inference engine."""
    print("\n[TEST 3] Inference Engine")
    print("=" * 50)
    
    config = MemoryTierConfig()
    engine = InferenceEngine(config=config)
    
    print(f"Engine initialized: {engine is not None}")
    print(f"Models loaded:      {len(engine.loaded_models)}")
    
    # Load a model
    print("\nLoading test model...")
    success = await engine.load_model("mistral-7b-instruct", tier="hot", quantize=False)
    print(f"Model loaded:       {success}")
    print(f"Models in cache:    {len(engine.loaded_models)}")
    
    # Run inference
    print("\nRunning inference...")
    prompt = "What is machine learning?"
    result, metrics = await engine.inference(
        "mistral-7b-instruct",
        prompt,
        max_tokens=100,
        temperature=0.7
    )
    
    print(f"Prompt:             {prompt[:50]}...")
    print(f"Result:             {result[:80]}...")
    print(f"Latency (ms):       {metrics.latency_ms:.1f}")
    print(f"Throughput (tok/s): {metrics.throughput_tokens_per_sec:.1f}")
    print(f"GPU Memory (MB):    {metrics.gpu_memory_mb:.0f}")
    print(f"Tier:               {metrics.tier}")
    
    # Get status
    status = engine.get_tier_status()
    print(f"\nTier Status:")
    print(f"  Hot GPU:          {status['hot_gpu']['models_loaded']} models")
    print(f"  GPU Util (%):     {status['hot_gpu']['utilization_percent']:.1f}")
    
    # Get metrics
    metrics_summary = engine.get_metrics_summary()
    print(f"\nMetrics Summary:")
    print(f"  Total inferences: {metrics_summary['total_inferences']}")
    print(f"  Avg latency (ms): {metrics_summary['avg_latency_ms']:.1f}")
    
    return success


async def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("APEX-METAL INFERENCE ENGINE TEST SUITE")
    print("=" * 50)
    
    try:
        # Test 1
        gpu_ok = await test_gpu_manager()
        
        # Test 2
        router_ok = await test_model_router()
        
        # Test 3
        engine_ok = await test_inference_engine()
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"GPU Manager:        {'PASS' if gpu_ok else 'WARN (CPU mode)'}")
        print(f"Model Router:       {'PASS' if router_ok else 'FAIL'}")
        print(f"Inference Engine:   {'PASS' if engine_ok else 'FAIL'}")
        
        if all([router_ok, engine_ok]):
            print("\nAll tests PASSED! System is operational.")
            return 0
        else:
            print("\nSome tests failed. Check output above.")
            return 1
            
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
