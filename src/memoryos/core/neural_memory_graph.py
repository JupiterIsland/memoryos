"""
Neural Memory Graph v0.2.0
==========================
GPU-aware memory router with NVIDIA Riva voice interface.
Predicts memory access patterns and optimizes placement across GPU, CPU, NVMe.
Features voice narration, hands-free commands, and real-time GPU telemetry.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MemoryTier:
    """Memory tier placement strategy."""
    name: str
    bandwidth_gbps: float
    capacity_gb: float
    latency_ns: float
    persistence: bool
    
    def __repr__(self):
        return f"{self.name} ({self.capacity_gb}GB @ {self.bandwidth_gbps}GB/s, {self.latency_ns}ns)"


class GPUTelemetry:
    """NVIDIA GPU telemetry and memory management."""
    
    def __init__(self):
        """Initialize GPU telemetry."""
        self.gpu_id = 0
        self.vendor = "NVIDIA"
        self.try_import_nvidia()
    
    def try_import_nvidia(self):
        """Attempt to import NVIDIA GPU libraries."""
        try:
            import pynvml
            pynvml.nvmlInit()
            self.pynvml = pynvml
            self.available = True
            print(f"[GPU] NVIDIA GPU telemetry available (pynvml)")
        except ImportError:
            print(f"[GPU] pynvml not available. Using simulated GPU metrics.")
            self.available = False
    
    def get_gpu_memory_info(self) -> Dict:
        """Get current GPU memory utilization."""
        if self.available:
            try:
                handle = self.pynvml.nvmlDeviceGetHandleByIndex(self.gpu_id)
                meminfo = self.pynvml.nvmlDeviceGetMemoryInfo(handle)
                return {
                    'total_mb': meminfo.total / 1024 / 1024,
                    'used_mb': meminfo.used / 1024 / 1024,
                    'free_mb': meminfo.free / 1024 / 1024,
                    'utilization_pct': (meminfo.used / meminfo.total) * 100,
                }
            except Exception as e:
                print(f"[GPU] Error reading telemetry: {e}")
        
        # Simulated metrics
        return {
            'total_mb': 24000,  # RTX 4090 = 24GB
            'used_mb': 16000,
            'free_mb': 8000,
            'utilization_pct': 66.7,
        }
    
    def get_gpu_load(self) -> float:
        """Get GPU utilization 0-100."""
        if self.available:
            try:
                handle = self.pynvml.nvmlDeviceGetHandleByIndex(self.gpu_id)
                util = self.pynvml.nvmlDeviceGetUtilizationRates(handle)
                return util.gpu
            except Exception:
                pass
        
        return 50.0  # Simulated


class NeuralMemoryGraph:
    """
    GPU-aware memory router with predictive placement.
    Routes hot memories across GPU VRAM, CPU cache, and NVMe.
    Integrates NVIDIA Riva for voice interface.
    """
    
    def __init__(self, 
                 heat_stream,
                 riva_client=None):
        """
        Initialize Neural Memory Graph.
        
        Args:
            heat_stream: MemoryHeatStream instance
            riva_client: Optional RivaVoiceClient for voice interaction
        """
        self.heat_stream = heat_stream
        self.riva = riva_client
        self.gpu = GPUTelemetry()
        
        # Define memory tiers (NVIDIA RTX 4090 example)
        self.tiers = {
            'gpu_l1': MemoryTier('GPU L1 Cache', 20000, 0.192, 1, False),
            'gpu_l2': MemoryTier('GPU L2 Cache', 15000, 6.0, 5, False),
            'gpu_vram': MemoryTier('GPU VRAM', 900, 24, 100, False),
            'cpu_cache': MemoryTier('CPU L3 Cache', 100, 0.05, 1000, False),
            'cpu_ram': MemoryTier('System RAM', 100, 128, 100000, False),
            'nvme': MemoryTier('NVMe Checkpoint', 3, 1000, 10000000, True),
        }
        
        # Current memory placement
        self.memory_placement: Dict[str, str] = {}
        self.load_placement_cache()
        
        print("[NeuralMemoryGraph] Initialized with GPU telemetry")
        print(f"[NeuralMemoryGraph] Memory tiers: {len(self.tiers)}")
    
    def load_placement_cache(self):
        """Load memory placement decisions from cache."""
        cache_file = Path(self.heat_stream.temp_graph) / "memory_placement.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.memory_placement = json.load(f)
            except Exception:
                pass
    
    def save_placement_cache(self):
        """Save memory placement decisions to cache."""
        cache_file = Path(self.heat_stream.temp_graph) / "memory_placement.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.memory_placement, f, indent=2)
        except Exception:
            pass
    
    def predict_memory_tier(self, block_id: str, heat_score: float, access_frequency: int) -> str:
        """
        Predict optimal memory tier for a block.
        
        Args:
            block_id: Memory block ID
            heat_score: Heat score 0-1.0
            access_frequency: Recent access count
        
        Returns:
            Tier name: 'gpu_vram' | 'cpu_cache' | 'cpu_ram' | 'nvme'
        """
        gpu_mem = self.gpu.get_gpu_memory_info()
        gpu_utilization = gpu_mem['utilization_pct']
        
        # Decision logic
        if heat_score >= 0.8 and gpu_utilization < 70:
            # Hot + room in VRAM
            return 'gpu_vram'
        elif heat_score >= 0.7 and gpu_utilization < 85:
            # Very hot + some VRAM
            return 'gpu_vram'
        elif heat_score >= 0.5 and access_frequency > 5:
            # Moderately hot + frequently accessed
            return 'cpu_cache'
        elif heat_score >= 0.2:
            # Warm memory
            return 'cpu_ram'
        else:
            # Cold memory
            return 'nvme'
    
    def optimize_for_model(self, model_size_gb: float) -> Dict:
        """
        Optimize memory allocation for model loading.
        
        Args:
            model_size_gb: Size of model to load
        
        Returns:
            Optimization plan with tier allocations
        """
        gpu_mem = self.gpu.get_gpu_memory_info()
        available_vram = gpu_mem['free_mb'] / 1024
        
        plan = {
            'model_size_gb': model_size_gb,
            'timestamp': datetime.now().isoformat(),
            'gpu_vram_reserved_gb': min(available_vram, model_size_gb * 0.7),
            'memory_rebalance': {},
            'recommendation': ''
        }
        
        if available_vram >= model_size_gb:
            plan['recommendation'] = f"Load full model ({model_size_gb}GB) to GPU VRAM"
            plan['memory_rebalance']['gpu_vram'] = ['model_weights']
        elif available_vram >= model_size_gb * 0.5:
            plan['recommendation'] = f"Load model to GPU with quantization"
            plan['memory_rebalance']['gpu_vram'] = ['model_weights_quantized']
        else:
            plan['recommendation'] = f"Load model with offloading to CPU/NVMe"
            plan['memory_rebalance']['gpu_vram'] = ['active_context']
            plan['memory_rebalance']['cpu_ram'] = ['model_layers']
            plan['memory_rebalance']['nvme'] = ['cold_layers']
        
        # Speak recommendation if Riva available
        if self.riva:
            self.riva.text_to_speech(plan['recommendation'])
        
        return plan
    
    def get_prefetch_schedule(self, next_n_tokens: int, limit: int = 5) -> List[Dict]:
        """
        Predict which memories will be needed in next N tokens.
        Pre-fetch them to optimal tier.
        
        Args:
            next_n_tokens: Number of tokens to look ahead
            limit: Maximum memories to prefetch
        
        Returns:
            List of prefetch decisions with priorities
        """
        hot = self.heat_stream.scan_for_hot_memories()
        
        prefetch_plan = []
        for i, block in enumerate(hot[:limit]):
            tier = self.predict_memory_tier(block.id, block.heat_score, block.access_count)
            
            prefetch_plan.append({
                'block_id': block.id,
                'title': block.title,
                'current_tier': self.memory_placement.get(block.id, 'unknown'),
                'target_tier': tier,
                'priority': i + 1,
                'heat_score': block.heat_score,
                'reason': f"Token window {next_n_tokens}: rank #{i+1} by heat"
            })
            
            self.memory_placement[block.id] = tier
        
        self.save_placement_cache()
        
        # Narrate prefetch plan if Riva available
        if self.riva and prefetch_plan:
            narration = f"Prefetching {len(prefetch_plan)} memories for next {next_n_tokens} tokens"
            self.riva.text_to_speech(narration)
        
        return prefetch_plan
    
    def get_memory_status(self) -> Dict:
        """Get current memory graph status."""
        gpu_mem = self.gpu.get_gpu_memory_info()
        hot = self.heat_stream.scan_for_hot_memories()
        
        # Count blocks by tier
        tier_distribution = {}
        for block_id, tier in self.memory_placement.items():
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'gpu_memory': gpu_mem,
            'hot_memories': len(hot),
            'placement_distribution': tier_distribution,
            'total_blocks_tracked': len(self.memory_placement),
            'memory_tiers': {k: asdict(v) for k, v in self.tiers.items()},
        }
    
    def voice_status_report(self):
        """Generate and speak memory status report."""
        status = self.get_memory_status()
        gpu_mem = status['gpu_memory']
        
        report = f"Memory status: GPU VRAM {gpu_mem['utilization_pct']:.0f}% full. "
        report += f"Tracking {status['total_blocks_tracked']} memory blocks. "
        report += f"Hot memories: {status['hot_memories']}."
        
        if self.riva:
            self.riva.text_to_speech(report)
            print(f"[Voice] {report}")
        else:
            print(f"[Status] {report}")
        
        return report


# CLI Commands
def neural_route_command(model_name: str = "mistral-7b", predict_tokens: int = 256):
    """CLI: Get neural routing plan for model."""
    from memoryos.core.heat_stream import MemoryHeatStream
    
    heat_stream = MemoryHeatStream()
    graph = NeuralMemoryGraph(heat_stream)
    
    # Get model size (estimate)
    model_size_map = {
        'mistral-7b': 7,
        'mistral-13b': 13,
        'llama-7b': 7,
        'llama-13b': 13,
        'llama-70b': 70,
    }
    
    size_gb = model_size_map.get(model_name, 7)
    
    print(f"\n[Neural Route] Model: {model_name} ({size_gb}GB)")
    
    # Get optimization plan
    opt_plan = graph.optimize_for_model(size_gb)
    print(f"[Recommendation] {opt_plan['recommendation']}")
    
    # Get prefetch schedule
    prefetch = graph.get_prefetch_schedule(predict_tokens, limit=5)
    print(f"\n[Prefetch Schedule] Next {predict_tokens} tokens:")
    for item in prefetch:
        print(f"  {item['priority']}. {item['title']}")
        print(f"     {item['current_tier']} → {item['target_tier']}")
    
    # Status report
    status = graph.get_memory_status()
    print(f"\n[Memory Status] GPU: {status['gpu_memory']['utilization_pct']:.1f}% | Hot: {status['hot_memories']}")


def neural_prefetch_command(next_tokens: int = 256):
    """CLI: Prefetch memories for next N tokens."""
    from memoryos.core.heat_stream import MemoryHeatStream
    
    heat_stream = MemoryHeatStream()
    graph = NeuralMemoryGraph(heat_stream)
    
    prefetch = graph.get_prefetch_schedule(next_tokens, limit=5)
    
    print(f"\n[Prefetch] Planning for {next_tokens} tokens ahead:")
    for item in prefetch:
        print(f"  {item['block_id']}: {item['target_tier']}")
    
    print(f"\n[OK] Prefetch plan saved to memory graph cache")


def voice_memory_status():
    """CLI: Speak current memory status."""
    from memoryos.core.heat_stream import MemoryHeatStream
    from memoryos.integrations.riva_voice import RivaVoiceClient
    
    heat_stream = MemoryHeatStream()
    riva = RivaVoiceClient()
    graph = NeuralMemoryGraph(heat_stream, riva)
    
    graph.voice_status_report()
