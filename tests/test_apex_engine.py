"""
Apex-Metal Inference Engine Test Suite
======================================

Comprehensive tests for GPU routing, model loading, and inference.
"""

import pytest
import asyncio
from pathlib import Path
from apex_core.engine import (
    MemoryTierConfig,
    GPUContextManager,
    ModelRouter,
    InferenceEngine
)


@pytest.fixture
def memory_config():
    """Fixture for memory tier configuration."""
    return MemoryTierConfig(
        hot_max_gb=10.0,
        warm_max_gb=32.0,
        cold_path="/tmp/apex_checkpoints",
        persistent_path="/tmp/apex_cache"
    )


@pytest.fixture
async def inference_engine(memory_config):
    """Fixture for initialized inference engine."""
    engine = InferenceEngine(config=memory_config)
    yield engine


class TestGPUContextManager:
    """Test suite for GPU device management."""
    
    def test_gpu_detection(self):
        """Test GPU backend detection."""
        manager = GPUContextManager()
        assert manager.device_type in ["cuda", "mps", "cpu"]
    
    def test_device_count(self):
        """Test GPU device enumeration."""
        manager = GPUContextManager()
        assert manager.device_count >= 0
    
    def test_device_string_generation(self):
        """Test device string formatting."""
        manager = GPUContextManager()
        device = manager.get_device()
        assert isinstance(device, str)
        assert len(device) > 0


class TestModelRouter:
    """Test suite for memory tier routing."""
    
    def test_router_initialization(self, memory_config):
        """Test ModelRouter initialization."""
        router = ModelRouter(memory_config)
        assert router.config == memory_config
        assert isinstance(router.model_registry, dict)
    
    def test_model_registration(self, memory_config):
        """Test model registration."""
        router = ModelRouter(memory_config)
        model_id = "test-model"
        router._register_model(model_id, "hot")
        
        assert model_id in router.model_registry
        assert router.model_registry[model_id]["tier"] == "hot"
    
    @pytest.mark.asyncio
    async def test_model_routing(self, memory_config):
        """Test model routing to tiers."""
        router = ModelRouter(memory_config)
        model_id = "test-model"
        
        device = await router.route_model(model_id, "hot")
        assert isinstance(device, str)
        assert model_id in router.model_registry
    
    def test_access_pattern_tracking(self, memory_config):
        """Test access pattern heat calculation."""
        router = ModelRouter(memory_config)
        model_id = "test-model"
        router._register_model(model_id, "hot")
        
        initial_heat = router.model_registry[model_id]["heat_score"]
        
        # Update access (increase heat)
        router.update_access_pattern(model_id, accessed=True)
        updated_heat = router.model_registry[model_id]["heat_score"]
        
        assert updated_heat > initial_heat


class TestInferenceEngine:
    """Test suite for inference operations."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, memory_config):
        """Test InferenceEngine initialization."""
        engine = InferenceEngine(config=memory_config)
        assert engine.config == memory_config
        assert engine.router is not None
        assert isinstance(engine.loaded_models, dict)
    
    def test_tier_status_reporting(self, memory_config):
        """Test memory tier status reporting."""
        engine = InferenceEngine(config=memory_config)
        status = engine.get_tier_status()
        
        assert "hot_gpu" in status
        assert "warm_cpu" in status
        assert "cold_nvme" in status
        assert "persistent_mram" in status
    
    def test_metrics_summary_empty(self, memory_config):
        """Test metrics summary with no inferences."""
        engine = InferenceEngine(config=memory_config)
        metrics = engine.get_metrics_summary()
        
        assert "error" in metrics
    
    @pytest.mark.asyncio
    async def test_model_loading_error_handling(self, memory_config):
        """Test error handling for non-existent models."""
        engine = InferenceEngine(config=memory_config)
        
        # Try to load non-existent model
        success = await engine.load_model("non-existent-model", tier="hot")
        
        # Should fail gracefully
        assert success is False


class TestMemoryTierConfiguration:
    """Test suite for memory tier configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MemoryTierConfig()
        
        assert config.hot_max_gb == 20.0
        assert config.warm_max_gb == 64.0
        assert "/nvme/checkpoints" in config.cold_path
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = MemoryTierConfig(
            hot_max_gb=16.0,
            warm_max_gb=128.0,
            cold_path="/custom/path"
        )
        
        assert config.hot_max_gb == 16.0
        assert config.warm_max_gb == 128.0
        assert config.cold_path == "/custom/path"


@pytest.mark.asyncio
async def test_concurrent_operations(memory_config):
    """Test concurrent model operations."""
    engine = InferenceEngine(config=memory_config)
    
    # Simulate concurrent routing operations
    tasks = [
        engine.router.route_model(f"model-{i}", "hot")
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
    assert all(isinstance(r, str) for r in results)


def test_registry_persistence(memory_config, tmp_path):
    """Test model registry persistence."""
    config = MemoryTierConfig(
        persistent_path=str(tmp_path)
    )
    
    # Create router and register model
    router1 = ModelRouter(config)
    router1._register_model("test-model", "hot")
    router1.save_registry()
    
    # Create new router and verify registry loaded
    router2 = ModelRouter(config)
    assert "test-model" in router2.model_registry


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=apex_core"])
