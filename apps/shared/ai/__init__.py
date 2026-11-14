"""AI scene detection, navigation, and graphical visual functions."""

from .models import FrameVisionResult, Scene
from .scene_analyzer import SceneAnalyzer
from .scene_detector import SceneDetector
from .visual_fx import (
    SUPPORTED_FILTERS,
    analyze_frame_visually,
    apply_visual_filter,
    build_storyboard_sheet,
    compute_frame_metrics,
    export_interactive_visual_dashboard,
    extract_dominant_palette,
    render_hero_poster,
)

__all__ = [
    "Scene",
    "FrameVisionResult",
    "SceneDetector",
    "SceneAnalyzer",
    "SUPPORTED_FILTERS",
    "extract_dominant_palette",
    "compute_frame_metrics",
    "apply_visual_filter",
    "build_storyboard_sheet",
    "render_hero_poster",
    "analyze_frame_visually",
    "export_interactive_visual_dashboard",
]
