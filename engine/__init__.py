"""
Jupiter TV - Video AI Engine
Scene detection, upscaling, and video processing
"""

__version__ = "0.1.0"
__author__ = "Jupiter TV Team"

from .scene_detector import SceneDetector
from .upscaler import VideoUpscaler
from .pipeline import VideoProcessingPipeline

__all__ = [
    "SceneDetector",
    "VideoUpscaler",
    "VideoProcessingPipeline",
]
