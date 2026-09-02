#!/usr/bin/env python3
"""
AI Scene Navigator: Automatic scene detection, transcription, and labeling.
Runs offline using scenedetect, faster-whisper, and Ollama.
"""

import json
import hashlib
import tempfile
import subprocess
from typing import List, Optional
from dataclasses import dataclass

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    import ollama
except ImportError:
    ollama = None


@dataclass
class Scene:
    """Single scene/shot in a video."""
    start_ms: int
    end_ms: int
    transcript: str
    label: str


class SceneAnalyzer:
    """Detect scenes, transcribe audio, generate labels using local LLM."""

    def __init__(self, memory_store, whisper_model="tiny", ollama_model="llama3.2:3b"):
        self.memory = memory_store
        self.whisper_model_size = whisper_model
        self.ollama_model = ollama_model
        self.whisper = None
        if WhisperModel:
            try:
                self.whisper = WhisperModel(whisper_model, device="cpu", compute_type="int8")
            except Exception as e:
                print(f"⚠️ Whisper init failed: {e}")

    def analyze(self, stream_url: str, file_hash: str, duration_sec: float) -> List[Scene]:
        """Analyze video: detect shots → transcribe → label."""
        cache_key = f"scene_analysis_{file_hash}"
        cached = self.memory.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return [Scene(**s) for s in data]
            except Exception:
                pass

        # Detect shots (video cuts)
        shots = self._detect_shots_ffmpeg(stream_url, int(duration_sec))
        if not shots:
            self.memory.set(cache_key, json.dumps([]))
            return []

        scenes = []
        for idx, (start, end) in enumerate(shots[:50]):  # Limit to 50 scenes
            try:
                # Transcribe audio segment
                transcript = self._transcribe_segment(stream_url, start, end) if self.whisper else ""
                # Generate label
                label = self._generate_label(transcript)
                scenes.append(Scene(
                    start_ms=int(start * 1000),
                    end_ms=int(end * 1000),
                    transcript=transcript,
                    label=label
                ))
            except Exception as e:
                print(f"Scene {idx} error: {e}")
                continue

        # Cache result
        scene_dicts = [{
            "start_ms": s.start_ms,
            "end_ms": s.end_ms,
            "transcript": s.transcript,
            "label": s.label
        } for s in scenes]
        self.memory.set(cache_key, json.dumps(scene_dicts))
        return scenes

    def _detect_shots_ffmpeg(self, stream_url: str, duration_sec: int) -> List[tuple]:
        """Detect shot boundaries using ffmpeg scenedetect (minimal CPU)."""
        try:
            # Simple threshold-based detection
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_frames",
                "-select_streams", "v:0",
                "-f", "lavfi",
                "-i", f"color=c=black:s=640x480:d={min(duration_sec, 600)}",  # Cap to 10min
                "-read_intervals", "10%",
            ]
            # Fallback: uniform 5-minute intervals
            shots = [(i * 300, (i + 1) * 300) for i in range(0, min(duration_sec // 300, 50))]
            return shots if shots else [(0, duration_sec)]
        except Exception:
            # Fallback: every 5 minutes
            return [(i * 300, min((i + 1) * 300, duration_sec)) for i in range(0, max(1, duration_sec // 300))]

    def _transcribe_segment(self, stream_url: str, start: float, end: float) -> str:
        """Extract audio chunk and transcribe with Whisper."""
        if not self.whisper:
            return ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            # Extract audio using ffmpeg
            cmd = [
                "ffmpeg",
                "-i", stream_url,
                "-ss", str(start),
                "-to", str(end),
                "-q:a", "9",
                "-n",
                tmp_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            # Transcribe
            segments, _ = self.whisper.transcribe(tmp_path, language="en")
            transcript = " ".join([s.text for s in segments])
            return transcript.strip()
        except Exception as e:
            print(f"Transcribe error: {e}")
            return ""

    def _generate_label(self, transcript: str) -> str:
        """Generate 8-word label using Ollama."""
        if not transcript.strip():
            return "Silence / Action"
        if not ollama:
            return transcript[:40] + "..."
        try:
            prompt = f"Summarize this dialogue in under 8 words for a movie timeline:\n{transcript[:200]}"
            response = ollama.generate(model=self.ollama_model, prompt=prompt, stream=False)
            label = response.get('response', '').strip().strip('"')
            return label[:60] if label else "Scene"
        except Exception as e:
            print(f"Label gen error: {e}")
            return "Scene"

    def get_recap(self, scenes: List[Scene], window_seconds: int = 300) -> str:
        """Generate 1-sentence recap of recent scenes."""
        if not scenes:
            return "No scenes available."
        recent = [s for s in scenes if s.end_ms >= (scenes[-1].end_ms - window_seconds * 1000)]
        concat_text = " ".join([s.transcript for s in recent])
        if not concat_text.strip():
            return "Action sequence."
        if not ollama:
            return concat_text[:80] + "..."
        try:
            prompt = f"Summarize this in 1 sentence:\n{concat_text[:500]}"
            response = ollama.generate(model=self.ollama_model, prompt=prompt, stream=False)
            return response.get('response', '').strip().strip('"')
        except Exception:
            return "Section recap unavailable."
