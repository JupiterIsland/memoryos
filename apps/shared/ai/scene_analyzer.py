"""AI Scene Navigator powered by MemoryOS + Token Lab Gemma-4-31B-IT VLM."""

import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional

from apps.shared.memory_store import MemoryStore

from .models import FrameVisionResult, Scene
from .scene_detector import SceneDetector
from .visual_fx import analyze_frame_visually, compute_frame_metrics

try:
    import cv2
except ImportError:
    cv2 = None


def _file_cache_key(video_path_or_url: str) -> str:
    digest = hashlib.sha256(video_path_or_url.encode("utf-8")).hexdigest()[:16]
    return f"scene_nav_{digest}"


def _encode_jpeg_bytes(raw_bytes: bytes) -> str:
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _extract_frame_ffmpeg(video_path: str, timestamp_sec: float) -> Optional[str]:
    if not shutil.which("ffmpeg"):
        return None
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{max(0.0, timestamp_sec):.2f}",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-vf",
            "scale=640:-1",
            "-q:v",
            "5",
            str(tmp_path),
        ]
        subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        if tmp_path.exists() and tmp_path.stat().st_size > 0:
            return _encode_jpeg_bytes(tmp_path.read_bytes())
    except Exception:
        pass
    finally:
        tmp_path.unlink(missing_ok=True)
    return None


def _extract_frame_cv2(video_path: str, timestamp_sec: float) -> Optional[str]:
    if cv2 is None:
        return None
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp_sec) * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            return None
        h, w = frame.shape[:2]
        if w > 640:
            scale = 640.0 / w
            frame = cv2.resize(frame, (640, max(1, int(h * scale))))
        ok_enc, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ok_enc:
            return _encode_jpeg_bytes(buf.tobytes())
    except Exception:
        pass
    finally:
        cap.release()
    return None


class SceneAnalyzer:
    """Detect scenes, extract keyframes, label with Gemma-4-31B-IT, and cache in MemoryStore."""

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        threshold: float = 30.0,
        max_scenes: int = 10,
        advisor_db_path: Optional[Path] = None,
        user_id: str = "default",
    ):
        self.memory = memory_store or MemoryStore()
        self.detector = SceneDetector(threshold=threshold)
        self.max_scenes = max_scenes
        self.advisor_db_path = advisor_db_path
        self.user_id = user_id
        self.last_advisor_hint: Optional[dict] = None
        self._last_frame_metrics: Optional[dict] = None
        self._last_vlm_json: Optional[str] = None
        self.vlm_stats: dict = {"frames_evaluated": 0, "gemma_routed": 0, "d3_skipped": 0}

    def extract_keyframe(self, video_path_or_url: str, timestamp_sec: float) -> Optional[str]:
        """Extract a base64 JPEG data URL at timestamp_sec using ffmpeg or OpenCV."""
        return _extract_frame_ffmpeg(video_path_or_url, timestamp_sec) or _extract_frame_cv2(
            video_path_or_url, timestamp_sec
        )

    def _detect_duration_fallback(self, video_path_or_url: str) -> float:
        if cv2 is None:
            return 0.0
        cap = cv2.VideoCapture(video_path_or_url)
        if not cap.isOpened():
            return 0.0
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
            return float(frames / fps) if fps > 0 and frames > 0 else 0.0
        finally:
            cap.release()

    def _label_scene_with_vlm(
        self,
        scene: Scene,
        frame_data_url: Optional[str],
        idx: int,
        frame_metrics: Optional[dict] = None,
    ) -> Scene:
        from src.memoryos.router import compute_frame_delta, router_to_gemma

        start_s = scene.start_ms / 1000.0
        end_s = scene.end_ms / 1000.0
        prompt = (
            f"Scene {idx + 1} ({start_s:.1f}s to {end_s:.1f}s).\n"
            f"Transcript/Notes: {scene.transcript or 'N/A'}\n"
            'Return strict JSON with keys "label" (under 7 words) and "summary" (1 concise sentence).'
        )

        try:
            curr_metrics = frame_metrics or (compute_frame_metrics(frame_data_url) if frame_data_url else None)
            frame_delta = (
                compute_frame_delta(curr_metrics, self._last_frame_metrics)
                if curr_metrics is not None
                else None
            )
            raw = router_to_gemma(
                prompt,
                image_url=frame_data_url,
                max_tokens=160,
                user_id=self.user_id,
                session_id="jupiter-tv-scene-nav",
                db_path=self.advisor_db_path,
                frame_delta=frame_delta,
                previous_response=self._last_vlm_json,
            )
            self.vlm_stats["frames_evaluated"] += 1
            if curr_metrics is not None:
                self._last_frame_metrics = dict(curr_metrics)

            cleaned = raw.strip()
            if "{" in cleaned and "}" in cleaned:
                json_str = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
                parsed = json.loads(json_str)
                d3_skipped = bool(parsed.get("d3_skipped", False)) or (
                    frame_delta is not None and not frame_delta.get("significant_change", True)
                )
                if d3_skipped:
                    self.vlm_stats["d3_skipped"] += 1
                else:
                    self.vlm_stats["gemma_routed"] += 1
                    self._last_vlm_json = json_str
                scene.label = str(parsed.get("label") or scene.label or f"Scene {idx + 1}")[:80]
                scene.summary = str(parsed.get("summary") or "")[:300]
                return scene
            self.vlm_stats["gemma_routed"] += 1
            scene.label = cleaned.splitlines()[0][:60] or f"Scene {idx + 1}"
            scene.summary = cleaned[:300]
        except Exception:
            if not scene.label:
                scene.label = f"Scene {idx + 1}"
        return scene

    def analyze(
        self,
        video_path_or_url: str,
        use_ai: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Scene]:
        """Detect scenes, gatekeep frame deltas via d3, label with Token Lab VLM, and cache in MemoryStore."""
        cache_key = _file_cache_key(video_path_or_url)
        cached = self.memory.get(cache_key)
        if cached:
            try:
                return [Scene.from_dict(item) for item in json.loads(cached)]
            except Exception:
                pass

        scenes = self.detector.detect(video_path_or_url)
        if not scenes:
            duration = self._detect_duration_fallback(video_path_or_url)
            if duration > 0:
                scenes = self.detector._uniform_chunks(duration, chunk_size=max(30, int(duration / 6)))

        scenes = scenes[: self.max_scenes]

        if use_ai:
            for idx, scene in enumerate(scenes):
                if progress_callback:
                    progress_callback(f"Labeling scene {idx + 1}/{len(scenes)} (d3 Gatekeeper + Gemma-4-31B-IT)...")
                mid_sec = ((scene.start_ms + scene.end_ms) / 2.0) / 1000.0
                frame = self.extract_keyframe(video_path_or_url, mid_sec)
                metrics = None
                if frame:
                    scene.thumbnail_b64 = frame
                    metrics = compute_frame_metrics(frame)
                    scene.palette = metrics["palette"]
                    scene.intensity = metrics["intensity"]
                self._label_scene_with_vlm(scene, frame, idx, frame_metrics=metrics)
            self.evaluate_session_with_advisor()

        if scenes:
            self.memory.set(cache_key, json.dumps([s.to_dict() for s in scenes]))
        return scenes

    def evaluate_session_with_advisor(self) -> Optional[dict]:
        """Run Quiet Advisor detectors + d3 routing on Jupiter TV's logged inferences."""
        try:
            from apps.quiet_advisor_ui.api import run_detection_cycle

            res = run_detection_cycle(lookback_hours=24, seed_if_empty=False, db_path=self.advisor_db_path)
            cards = (res.get("state") or {}).get("active_cards") or []
            self.last_advisor_hint = cards[0] if cards else None
            return self.last_advisor_hint
        except Exception:
            return None

    def inspect_frame(self, image_input: str | bytes, context_hint: str = "") -> FrameVisionResult:
        """Run d3 delta gatekeeping + Gemma-4-31B-IT VLM visual inspection on a captured frame."""
        curr_metrics = compute_frame_metrics(image_input)
        res = analyze_frame_visually(
            image_input,
            context_hint=context_hint,
            user_id=self.user_id,
            db_path=self.advisor_db_path,
            previous_metrics=self._last_frame_metrics,
        )
        self._last_frame_metrics = dict(curr_metrics)
        self.vlm_stats["frames_evaluated"] += 1
        if "d3-gatekeeper" in (res.model or ""):
            self.vlm_stats["d3_skipped"] += 1
        else:
            self.vlm_stats["gemma_routed"] += 1
        self.evaluate_session_with_advisor()
        return res

    def search_scenes(self, scenes: List[Scene], query: str) -> List[Scene]:
        """Search scenes by keyword overlap first, falling back to Token Lab semantic match."""
        q = query.strip().lower()
        if not q or not scenes:
            return []

        tokens = [t for t in q.split() if len(t) > 1]
        scored = []
        for s in scenes:
            haystack = f"{s.label} {s.summary} {s.transcript}".lower()
            hits = sum(1 for tok in tokens if tok in haystack)
            if hits > 0:
                scored.append((hits, s))
        if scored:
            scored.sort(key=lambda pair: pair[0], reverse=True)
            return [pair[1] for pair in scored]

        try:
            from src.memoryos.router import route_task

            catalog = "\n".join(
                f"{i}: [{s.start_ms // 1000}s-{s.end_ms // 1000}s] {s.label} - {s.summary} {s.transcript}"
                for i, s in enumerate(scenes)
            )
            res = route_task(
                f"User query: {query}\nScenes:\n{catalog}\nReply with only the best matching 0-based scene index integer.",
                max_tokens=16,
                save_checkpoint=True,
                user_id=self.user_id,
                session_id="jupiter-tv-search",
                db_path=self.advisor_db_path,
            )
            idx = int("".join(ch for ch in res["content"] if ch.isdigit()) or "0")
            if 0 <= idx < len(scenes):
                return [scenes[idx]]
        except Exception:
            pass
        return []

    def recap(self, scenes: List[Scene], up_to_ms: Optional[int] = None) -> str:
        """Generate a concise AI recap of scenes up to up_to_ms."""
        if not scenes:
            return "No scenes analyzed yet."
        relevant = [s for s in scenes if up_to_ms is None or s.start_ms <= up_to_ms] or scenes[:1]
        timeline = "\n".join(
            f"- {s.start_ms // 1000}s-{s.end_ms // 1000}s | {s.label}: {s.summary or s.transcript or 'Visual segment'}"
            for s in relevant
        )
        try:
            from src.memoryos.router import route_to_gemma

            out = route_to_gemma(
                f"Give a crisp 2-sentence 'Previously on' recap of these scenes:\n{timeline}",
                max_tokens=200,
                user_id=self.user_id,
                session_id="jupiter-tv-recap",
                db_path=self.advisor_db_path,
            )
            self.evaluate_session_with_advisor()
            return out
        except Exception as e:
            return f"Scenes covered: {', '.join(s.label for s in relevant)} (AI recap error: {e})"
