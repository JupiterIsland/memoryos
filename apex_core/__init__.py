"""
Apex Core Package
=================

GPU-aware inference engine with MemoryOS integration.
"""

__version__ = "0.2.0"
__author__ = "Gordon"

from .engine import (
    GPUContextManager,
    ModelRouter,
    InferenceEngine,
    MemoryTierConfig,
    InferenceMetrics
)

__all__ = [
    "GPUContextManager",
    "ModelRouter",
    "InferenceEngine",
    "MemoryTierConfig",
    "InferenceMetrics"
]
