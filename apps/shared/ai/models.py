"""Data models for scene detection, AI Scene Navigator, and graphical visuals."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Scene:
    """Represents a detected scene in a video with optional visual metadata."""

    start_ms: int      # Start in milliseconds
    end_ms: int        # End in milliseconds
    label: str = ""    # AI-generated or default scene label
    summary: str = ""  # Optional 1-sentence visual/narrative summary
    transcript: str = ""  # Optional transcript snippet
    thumbnail_b64: str = ""  # Base64 JPEG/PNG data URL for keyframe preview
    palette: List[str] = field(default_factory=list)  # Dominant hex colors
    intensity: float = 0.5  # Visual energy/brightness score in [0.0, 1.0]

    @property
    def duration_ms(self):
        return self.end_ms - self.start_ms

    def to_dict(self) -> dict:
        return {
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "label": self.label,
            "summary": self.summary,
            "transcript": self.transcript,
            "thumbnail_b64": self.thumbnail_b64,
            "palette": list(self.palette),
            "intensity": float(self.intensity),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        return cls(
            start_ms=int(data["start_ms"]),
            end_ms=int(data["end_ms"]),
            label=data.get("label", ""),
            summary=data.get("summary", ""),
            transcript=data.get("transcript", ""),
            thumbnail_b64=data.get("thumbnail_b64", ""),
            palette=list(data.get("palette") or []),
            intensity=float(data.get("intensity", 0.5)),
        )

    def __repr__(self):
        label = f" - {self.label}" if self.label else ""
        return f"<Scene {self.start_ms}ms-{self.end_ms}ms{label}>"


@dataclass
class FrameVisionResult:
    """Structured visual inspection output for a single video frame."""

    caption: str
    objects: List[str] = field(default_factory=list)
    mood: str = "neutral"
    lighting: str = "balanced"
    palette: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    model: str = "local-heuristic"
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "caption": self.caption,
            "objects": list(self.objects),
            "mood": self.mood,
            "lighting": self.lighting,
            "palette": list(self.palette),
            "tags": list(self.tags),
            "model": self.model,
            "latency_ms": self.latency_ms,
        }
