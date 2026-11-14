"""
Apex-Metal GPU Inference Engine
Core module with memory tier routing
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import torch
    import numpy as np
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryTierConfig:
    """Configuration for memory tier placement."""
    hot_max_gb: float = 20.0
    warm_max_gb: float = 64.0
    cold_path: str = "/nvme/checkpoints"
    persistent_path: str = "~/.cache/mrameda"


@dataclass
class InferenceMetrics:
    """Performance metrics for inference operations."""
    model_id: str
    tier: str
    latency_ms: float
    throughput_tokens_per_sec: float
    gpu_memory_mb: float
    timestamp: datetime


class GPUContextManager:
    """Manages GPU device context and CUDA/ROCm routing."""
    
    def __init__(self):
        self.device_type = self._detect_gpu_type()
        self.device_count = self._get_device_count()
        self.current_device = 0
        
        logger.info(f"GPU Backend: {self.device_type}")
        logger.info(f"Device Count: {self.device_count}")
    
    def _detect_gpu_type(self) -> str:
        """Detect available GPU backend."""
        if not TORCH_AVAILABLE:
            return "cpu"
        
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _get_device_count(self) -> int:
        """Get number of available GPU devices."""
        if not TORCH_AVAILABLE:
            return 0
            
        if self.device_type == "cuda":
            return torch.cuda.device_count()
        else:
            return 1
    
    def get_device(self) -> str:
        """Get current device string for model placement."""
        if self.device_type == "cuda":
            return f"cuda:{self.current_device}"
        elif self.device_type == "mps":
            return "mps"
        else:
            return "cpu"
    
    def get_device_memory(self) -> float:
        """Get available GPU memory in MB."""
        if not TORCH_AVAILABLE or self.device_type != "cuda":
            return 0.0
        
        try:
            return torch.cuda.get_device_properties(self.current_device).total_memory / 1024 / 1024
        except:
            return 0.0
    
    def get_device_utilization(self) -> float:
        """Get GPU utilization percentage."""
        if not TORCH_AVAILABLE or self.device_type != "cuda":
            return 0.0
        
        try:
            allocated = torch.cuda.memory_allocated(self.current_device)
            reserved = torch.cuda.memory_reserved(self.current_device)
            return (allocated / reserved * 100) if reserved > 0 else 0.0
        except:
            return 0.0


class ModelRouter:
    """Routes models between memory tiers based on access patterns."""
    
    def __init__(self, config: MemoryTierConfig):
        self.config = config
        self.gpu_manager = GPUContextManager()
        
        # Ensure storage directories exist
        Path(self.config.cold_path).mkdir(parents=True, exist_ok=True)
        Path(self.config.persistent_path).expanduser().mkdir(parents=True, exist_ok=True)
        
        # Model registry
        self.model_registry: Dict[str, Dict] = {}
        self.load_registry()
    
    def load_registry(self):
        """Load model registry from persistent storage."""
        registry_file = Path(self.config.persistent_path).expanduser() / "model_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    self.model_registry = json.load(f)
                logger.info(f"Loaded {len(self.model_registry)} models from registry")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
    
    def save_registry(self):
        """Persist model registry to stable storage."""
        registry_file = Path(self.config.persistent_path).expanduser() / "model_registry.json"
        try:
            with open(registry_file, 'w') as f:
                json.dump(self.model_registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    async def route_model(self, model_id: str, desired_tier: str = "hot") -> str:
        """Route model to appropriate memory tier."""
        if model_id not in self.model_registry:
            self._register_model(model_id, desired_tier)
        
        registry_entry = self.model_registry[model_id]
        current_tier = registry_entry.get("tier", "cold")
        
        if current_tier == desired_tier:
            return self._get_tier_device(desired_tier)
        
        logger.info(f"Migrating {model_id} from {current_tier} to {desired_tier}")
        await self._migrate_model(model_id, current_tier, desired_tier)
        
        self.model_registry[model_id]["tier"] = desired_tier
        self.save_registry()
        
        return self._get_tier_device(desired_tier)
    
    def _register_model(self, model_id: str, tier: str):
        """Register a new model in the registry."""
        self.model_registry[model_id] = {
            "id": model_id,
            "tier": tier,
            "registered_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": None,
            "heat_score": 0.0
        }
    
    async def _migrate_model(self, model_id: str, from_tier: str, to_tier: str):
        """Migrate model between tiers (async operation)."""
        await asyncio.sleep(0.1)
        logger.info(f"Migration complete: {model_id} {from_tier} -> {to_tier}")
    
    def _get_tier_device(self, tier: str) -> str:
        """Get device string for given tier."""
        if tier == "hot":
            return self.gpu_manager.get_device()
        else:
            return "cpu"
    
    def update_access_pattern(self, model_id: str, accessed: bool = True):
        """Update model access statistics for heat calculation."""
        if model_id in self.model_registry:
            entry = self.model_registry[model_id]
            if accessed:
                entry["access_count"] += 1
                entry["last_accessed"] = datetime.now().isoformat()
                entry["heat_score"] = min(1.0, entry["heat_score"] + 0.1)
            else:
                entry["heat_score"] = max(0.0, entry["heat_score"] - 0.05)


class InferenceEngine:
    """Main inference engine with MemoryOS tier integration."""
    
    def __init__(self, 
                 config: Optional[MemoryTierConfig] = None,
                 memoryos_path: Optional[str] = None):
        """Initialize inference engine."""
        self.config = config or MemoryTierConfig()
        self.router = ModelRouter(self.config)
        self.gpu_manager = GPUContextManager()
        self.memoryos_path = memoryos_path
        
        # Model cache
        self.loaded_models: Dict[str, Dict] = {}
        self.metrics_history: List[InferenceMetrics] = []
        
        logger.info("Inference Engine initialized")
    
    async def load_model(self, 
                        model_id: str, 
                        tier: str = "hot",
                        quantize: bool = False) -> bool:
        """Load model and place on appropriate tier."""
        try:
            device = await self.router.route_model(model_id, tier)
            
            logger.info(f"Loading {model_id} on {device}")
            
            # Simulate model loading (real version would use transformers)
            self.loaded_models[model_id] = {
                "model": f"mock_{model_id}",
                "tokenizer": f"mock_tokenizer_{model_id}",
                "device": device,
                "loaded_at": datetime.now(),
                "tier": tier,
                "quantized": quantize
            }
            
            logger.info(f"Model {model_id} loaded successfully on {device}")
            self.router.update_access_pattern(model_id, accessed=True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    async def inference(self,
                       model_id: str,
                       prompt: str,
                       max_tokens: int = 256,
                       temperature: float = 0.7) -> Tuple[str, InferenceMetrics]:
        """Run inference on loaded model."""
        import time
        
        if model_id not in self.loaded_models:
            logger.error(f"Model {model_id} not loaded")
            return "", InferenceMetrics(model_id, "error", 0, 0, 0, datetime.now())
        
        model_info = self.loaded_models[model_id]
        device = model_info["device"]
        
        start_time = time.time()
        
        try:
            # Simulate inference
            await asyncio.sleep(0.1)
            generated_text = f"{prompt}\n[Generated by {model_id} on {device}]"
            
            latency_ms = (time.time() - start_time) * 1000
            throughput = max_tokens / (latency_ms / 1000) if latency_ms > 0 else 0
            
            gpu_memory_mb = 0.0
            if device.startswith("cuda"):
                gpu_memory_mb = self.gpu_manager.get_device_memory()
            
            metrics = InferenceMetrics(
                model_id=model_id,
                tier=model_info["tier"],
                latency_ms=latency_ms,
                throughput_tokens_per_sec=throughput,
                gpu_memory_mb=gpu_memory_mb,
                timestamp=datetime.now()
            )
            
            self.metrics_history.append(metrics)
            self.router.update_access_pattern(model_id, accessed=True)
            
            logger.info(f"Inference complete: {latency_ms:.1f}ms, {throughput:.1f} tok/s")
            
            return generated_text, metrics
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return "", InferenceMetrics(model_id, "error", 0, 0, 0, datetime.now())
    
    def get_tier_status(self) -> Dict:
        """Get current status of all memory tiers."""
        return {
            "hot_gpu": {
                "device": self.gpu_manager.get_device(),
                "total_memory_mb": self.gpu_manager.get_device_memory(),
                "utilization_percent": self.gpu_manager.get_device_utilization(),
                "models_loaded": sum(1 for m in self.loaded_models.values() if m["tier"] == "hot")
            },
            "warm_cpu": {
                "models_loaded": sum(1 for m in self.loaded_models.values() if m["tier"] == "warm")
            },
            "cold_nvme": {
                "checkpoint_path": self.config.cold_path,
                "exists": Path(self.config.cold_path).exists()
            },
            "persistent_mram": {
                "cache_path": self.config.persistent_path,
                "registry_size": len(self.router.model_registry)
            }
        }
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of recent inference metrics."""
        if not self.metrics_history:
            return {"error": "No metrics recorded"}
        
        recent = self.metrics_history[-100:]
        
        try:
            avg_latency = sum(m.latency_ms for m in recent) / len(recent)
            avg_throughput = sum(m.throughput_tokens_per_sec for m in recent) / len(recent)
            avg_memory = sum(m.gpu_memory_mb for m in recent) / len(recent)
        except:
            avg_latency = avg_throughput = avg_memory = 0
        
        return {
            "total_inferences": len(self.metrics_history),
            "avg_latency_ms": avg_latency,
            "avg_throughput_tokens_per_sec": avg_throughput,
            "avg_gpu_memory_mb": avg_memory,
            "latest_inference": recent[-1].timestamp.isoformat() if recent else None
        }
