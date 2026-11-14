#!/usr/bin/env python
"""
Simple Apex-Metal API Server
=============================

Stripped down FastAPI server for testing without full dependencies.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from apex_core.engine import InferenceEngine, MemoryTierConfig


class SimpleApexServer:
    """Minimal test server."""
    
    def __init__(self):
        config = MemoryTierConfig(
            hot_max_gb=20.0,
            warm_max_gb=64.0,
            cold_path="./nvme_checkpoints",
            persistent_path="./.cache/mrameda"
        )
        self.engine = InferenceEngine(config=config)
    
    async def health(self) -> dict:
        """Health check."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "models_loaded": len(self.engine.loaded_models)
        }
    
    async def load_model(self, model_id: str, tier: str = "hot", quantize: bool = False) -> dict:
        """Load a model."""
        success = await self.engine.load_model(model_id, tier=tier, quantize=quantize)
        
        return {
            "success": success,
            "model_id": model_id,
            "tier": tier,
            "message": f"Model {model_id} loaded" if success else f"Failed to load {model_id}"
        }
    
    async def inference(self, model_id: str, prompt: str, max_tokens: int = 256) -> dict:
        """Run inference."""
        if model_id not in self.engine.loaded_models:
            return {"error": f"Model {model_id} not loaded"}
        
        result, metrics = await self.engine.inference(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        return {
            "model_id": model_id,
            "prompt": prompt[:100],
            "result": result[:200],
            "latency_ms": metrics.latency_ms,
            "throughput_tokens_per_sec": metrics.throughput_tokens_per_sec,
            "gpu_memory_mb": metrics.gpu_memory_mb,
            "tier": metrics.tier
        }
    
    async def status(self) -> dict:
        """Get tier status."""
        return self.engine.get_tier_status()
    
    async def metrics(self) -> dict:
        """Get metrics."""
        return self.engine.get_metrics_summary()


async def interactive_demo():
    """Run interactive demo."""
    server = SimpleApexServer()
    
    print("\n" + "=" * 60)
    print("APEX-METAL INTERACTIVE DEMO")
    print("=" * 60)
    
    while True:
        print("\nCommands:")
        print("  1. Health check")
        print("  2. Load model")
        print("  3. Run inference")
        print("  4. Check status")
        print("  5. View metrics")
        print("  0. Exit")
        
        choice = input("\nSelect command (0-5): ").strip()
        
        if choice == "0":
            print("Exiting...")
            break
        
        elif choice == "1":
            result = await server.health()
            print(f"\nHealth: {result}")
        
        elif choice == "2":
            model_id = input("Model ID (e.g., mistral-7b): ").strip()
            tier = input("Tier (hot/warm/cold) [hot]: ").strip() or "hot"
            result = await server.load_model(model_id, tier=tier)
            print(f"\nResult: {result}")
        
        elif choice == "3":
            model_id = input("Model ID: ").strip()
            prompt = input("Prompt: ").strip()
            result = await server.inference(model_id, prompt)
            print(f"\nResult: {result}")
        
        elif choice == "4":
            result = await server.status()
            print(f"\nStatus:")
            for tier, info in result.items():
                print(f"  {tier}: {info}")
        
        elif choice == "5":
            result = await server.metrics()
            print(f"\nMetrics: {result}")
        
        else:
            print("Invalid command")


if __name__ == "__main__":
    asyncio.run(interactive_demo())
