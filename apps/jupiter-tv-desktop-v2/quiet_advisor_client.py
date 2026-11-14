"""
QuietAdvisor Client for Jupiter Desktop
========================================
HTTP client and CPU cv2 frame-delta bridge for communicating with MemoryOS Router.

Usage:
    from quiet_advisor_client import QuietAdvisorClient, compute_mse_delta, extract_cv2_frame

    client = QuietAdvisorClient(
        router_url="http://localhost:5000",
        session_id="jupiter-session-001",
        user_id="jupiter-desktop",
    )

    frame_bgr, frame_bytes = extract_cv2_frame("concert.mp4", position_ms=12500)
    delta = compute_mse_delta(frame_bgr, prev_frame_bgr)
    gate_result = client.check_frame_delta(
        mse=delta["mse"],
        mse_delta=delta["mse_delta"],
        brightness_delta=delta["brightness_delta"],
        contrast_delta=delta["contrast_delta"],
        intensity_delta=delta["intensity_delta"],
        palette_shift=delta["palette_shift"],
        context_hint="pause @ 00:12",
    )
    if not gate_result["skip_vision"]:
        inference = client.route_inference(
            prompt="Describe this frame",
            image_bytes=frame_bytes,
            task_type="vision_heavy",
        )
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def extract_cv2_frame(
    video_source: Optional[str],
    position_ms: int = 0,
    fallback_frame_bytes: bytes = b"",
) -> Tuple[Any, bytes]:
    """
    Extract the current video frame as a cv2 BGR ndarray and PNG bytes on CPU.

    1. If `fallback_frame_bytes` is already available (e.g., from PyQt6 QVideoSink),
       decodes the cv2 frame directly from those bytes in memory.
    2. Otherwise, if `video_source` is set and `cv2` is installed, seeks `cv2.VideoCapture`
       to `position_ms`, reads the frame, and encodes PNG bytes.
    3. Gracefully returns `(None, fallback_frame_bytes)` when `cv2` is unavailable.
    """
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np

        if fallback_frame_bytes:
            arr = np.frombuffer(fallback_frame_bytes, dtype=np.uint8)
            decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if decoded is not None:
                return decoded, fallback_frame_bytes

        if video_source and not video_source.startswith("magnet:"):
            cap = cv2.VideoCapture(video_source)
            try:
                if cap.isOpened():
                    if position_ms > 0:
                        cap.set(cv2.CAP_PROP_POS_MSEC, float(position_ms))
                    ok, frame = cap.read()
                    if ok and frame is not None:
                        ok_enc, buf = cv2.imencode(".png", frame)
                        png_bytes = bytes(buf.tobytes()) if ok_enc else fallback_frame_bytes
                        return frame, png_bytes
            finally:
                cap.release()
    except Exception as exc:
        logger.debug(f"cv2 frame extraction fallback engaged: {exc}")

    return None, fallback_frame_bytes


def compute_mse_delta(
    current_frame: Any,
    previous_frame: Any = None,
    threshold: float = 12.0,
) -> Dict[str, Any]:
    """
    Compute CPU Mean Squared Error (MSE) delta between two video frames.

    Accepts either `cv2`/`numpy` ndarrays OR encoded image `bytes` (PNG/JPEG).
    Uses headless OpenCV + NumPy on CPU when available, with a pure-Python
    byte-sampling fallback when `cv2`/`numpy` are not installed.
    """
    if current_frame is None or (isinstance(current_frame, (bytes, bytearray)) and len(current_frame) == 0):
        return {
            "mse": 0.0,
            "mse_delta": 0.0,
            "threshold": float(threshold),
            "brightness_delta": 0.0,
            "contrast_delta": 0.0,
            "intensity_delta": 0.0,
            "palette_shift": 0.0,
            "composite_delta": 0.0,
            "significant_change": False,
            "method": "empty",
        }

    if previous_frame is None or (isinstance(previous_frame, (bytes, bytearray)) and len(previous_frame) == 0):
        return {
            "mse": 1.0,
            "mse_delta": 999.0,
            "threshold": float(threshold),
            "brightness_delta": 1.0,
            "contrast_delta": 1.0,
            "intensity_delta": 1.0,
            "palette_shift": 1.0,
            "composite_delta": 1.0,
            "significant_change": True,
            "method": "initial_frame",
        }

    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np

        def _to_gray(inp: Any):
            if isinstance(inp, (bytes, bytearray)):
                arr = np.frombuffer(inp, dtype=np.uint8)
                bgr = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                return bgr
            if hasattr(inp, "ndim"):
                if inp.ndim == 3:
                    return cv2.cvtColor(inp, cv2.COLOR_BGR2GRAY)
                return inp
            return None

        img_cur = _to_gray(current_frame)
        img_prev = _to_gray(previous_frame)
        if img_cur is not None and img_prev is not None:
            cur_small = cv2.resize(img_cur, (160, 90)).astype(np.float32)
            prev_small = cv2.resize(img_prev, (160, 90)).astype(np.float32)
            mse_raw = float(np.mean((cur_small - prev_small) ** 2))
            mse_norm = round(min(1.0, mse_raw / (255.0 ** 2)), 6)
            brightness_delta = round(min(1.0, abs(float(np.mean(cur_small) - np.mean(prev_small))) / 255.0), 4)
            contrast_delta = round(min(1.0, abs(float(np.std(cur_small) - np.std(prev_small))) / 128.0), 4)
            composite_delta = round(min(1.0, mse_raw / max(threshold * 4.0, 1e-6)), 4)
            palette_shift = round(min(1.0, composite_delta * 0.6), 4)
            return {
                "mse": mse_norm,
                "mse_delta": round(mse_raw, 4),
                "threshold": float(threshold),
                "brightness_delta": brightness_delta,
                "contrast_delta": contrast_delta,
                "intensity_delta": composite_delta,
                "palette_shift": palette_shift,
                "composite_delta": composite_delta,
                "significant_change": mse_raw >= float(threshold),
                "method": "cv2_cpu_mse",
            }
    except Exception:
        pass

    cur_bytes = current_frame if isinstance(current_frame, (bytes, bytearray)) else bytes(str(current_frame), "utf-8")
    prev_bytes = previous_frame if isinstance(previous_frame, (bytes, bytearray)) else bytes(str(previous_frame), "utf-8")
    sample_len = min(len(cur_bytes), len(prev_bytes), 4096)
    if sample_len <= 0:
        return {
            "mse": 0.0,
            "mse_delta": 0.0,
            "threshold": float(threshold),
            "brightness_delta": 0.0,
            "contrast_delta": 0.0,
            "intensity_delta": 0.0,
            "palette_shift": 0.0,
            "composite_delta": 0.0,
            "significant_change": False,
            "method": "empty",
        }

    sq_sum = sum((cur_bytes[i] - prev_bytes[i]) ** 2 for i in range(sample_len))
    mse_raw = sq_sum / float(sample_len)
    mse_norm = round(min(1.0, mse_raw / (255.0 ** 2)), 6)
    mean_cur = sum(cur_bytes[:sample_len]) / float(sample_len)
    mean_prev = sum(prev_bytes[:sample_len]) / float(sample_len)
    brightness_delta = round(min(1.0, abs(mean_cur - mean_prev) / 255.0), 4)
    composite_delta = round(min(1.0, mse_raw / max(threshold * 4.0, 1e-6)), 4)
    return {
        "mse": mse_norm,
        "mse_delta": round(mse_raw, 4),
        "threshold": float(threshold),
        "brightness_delta": brightness_delta,
        "contrast_delta": round(min(1.0, composite_delta * 0.4), 4),
        "intensity_delta": composite_delta,
        "palette_shift": round(min(1.0, composite_delta * 0.6), 4),
        "composite_delta": composite_delta,
        "significant_change": mse_raw >= float(threshold),
        "method": "cpu_byte_mse",
    }


class QuietAdvisorClient:
    """
    HTTP client for MemoryOS Router.

    Handles all communication with /api/frame-delta, /api/route, /api/acknowledge-card.
    Includes error handling, timeouts, and safe fallback responses.
    """

    def __init__(
        self,
        router_url: Optional[str] = None,
        session_id: str = "jupiter-desktop-session",
        user_id: str = "default",
        timeout: float = 15.0,
        base_url: Optional[str] = None,
        check_health_on_init: bool = False,
    ):
        resolved_url = router_url or base_url or os.getenv("MEMORYOS_ROUTER_URL") or "http://127.0.0.1:5000"
        self.router_url = resolved_url.rstrip("/")
        self.base_url = self.router_url
        self.session_id = session_id
        self.user_id = user_id
        self.timeout = float(timeout)

        self._last_inference_result: Optional[Dict[str, Any]] = None
        self._last_frame_hash: Optional[str] = None
        self._router_health: Optional[bool] = None

        if check_health_on_init:
            self._check_router_health()

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.router_url}{path}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urllib.parse.urlencode(clean_params)}"

        if requests is not None:
            if method.upper() == "GET":
                resp = requests.get(url, timeout=self.timeout)
            else:
                resp = requests.post(url, json=payload or {}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json() if resp.text else {}

        headers = {"Accept": "application/json"}
        data: Optional[bytes] = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    def _check_router_health(self) -> bool:
        """Check if router is healthy."""
        try:
            res = self._request_json("GET", "/health")
            self._router_health = res.get("status") == "healthy"
            return bool(self._router_health)
        except Exception as exc:
            logger.debug(f"Router unreachable during health check: {exc}")
            self._router_health = False
            return False

    def health(self) -> Dict[str, Any]:
        return self._request_json("GET", "/health")

    def get_state(self) -> Dict[str, Any]:
        return self._request_json("GET", "/api/state")

    def check_frame_delta(
        self,
        mse: Optional[float] = None,
        brightness_delta: float = 0.0,
        contrast_delta: float = 0.0,
        intensity_delta: float = 0.0,
        palette_shift: float = 0.0,
        context_hint: Optional[str] = None,
        *,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        frame_delta: Optional[Dict[str, Any]] = None,
        mse_delta: Optional[float] = None,
        threshold: float = 12.0,
        previous_response: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST to /api/frame-delta to check if a video frame has changed significantly.

        Supports both normalized `mse` (0.0-1.0) and raw pixel `mse_delta` (0.0-65025.0)
        as well as full `frame_delta` dicts from `compute_mse_delta()`.
        """
        payload: Dict[str, Any] = {
            "session_id": session_id or self.session_id,
            "user_id": user_id or self.user_id,
            "context_hint": context_hint or "Jupiter Desktop frame analysis",
            "threshold": threshold,
        }
        if previous_response is not None:
            payload["previous_response"] = previous_response

        if isinstance(frame_delta, dict):
            payload["frame_delta"] = dict(frame_delta)
            if mse_delta is not None:
                payload["mse_delta"] = float(mse_delta)
        elif mse_delta is not None:
            payload["mse_delta"] = float(mse_delta)
            norm = min(1.0, float(mse_delta) / max(threshold * 4.0, 1e-6))
            payload["frame_delta"] = {
                "mse_delta": float(mse_delta),
                "threshold": float(threshold),
                "brightness": brightness_delta,
                "contrast": contrast_delta,
                "intensity": intensity_delta or norm,
                "palette_shift": palette_shift,
                "composite_delta": norm,
                "significant_change": float(mse_delta) >= float(threshold),
            }
        elif mse is not None:
            mse_val = float(mse)
            # Distinguish normalized [0, 1] MSE vs raw 0-255 pixel MSE (> 1.0)
            if mse_val > 1.0:
                norm = min(1.0, mse_val / max(threshold * 4.0, 1e-6))
                sig = mse_val >= float(threshold)
                payload["mse_delta"] = mse_val
                payload["frame_delta"] = {
                    "mse_delta": mse_val,
                    "threshold": float(threshold),
                    "brightness": brightness_delta,
                    "contrast": contrast_delta,
                    "intensity": intensity_delta or norm,
                    "palette_shift": palette_shift,
                    "composite_delta": norm,
                    "significant_change": sig,
                }
            else:
                norm_threshold = 0.08
                sig = mse_val >= norm_threshold
                payload["frame_delta"] = {
                    "brightness": brightness_delta,
                    "contrast": contrast_delta,
                    "intensity": intensity_delta,
                    "palette_shift": palette_shift,
                    "composite_delta": mse_val,
                    "threshold": norm_threshold,
                    "significant_change": sig,
                }

        try:
            result = self._request_json("POST", "/api/frame-delta", payload=payload)
            logger.debug(
                f"Frame delta: skip_vision={result.get('skip_vision', False)}, "
                f"latency={result.get('gate_latency_ms', 0)}ms"
            )
            return result
        except Exception as exc:
            logger.error(f"Frame delta request failed: {exc}")
            return self._fallback_frame_delta(error=str(exc))

    def route_inference(
        self,
        prompt: str,
        task_type: str = "balanced_code",
        image_url: Optional[str] = None,
        max_tokens: int = 1024,
        context_from_memory: bool = True,
        *,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        tlb_context: Optional[str] = None,
        frame_delta: Optional[Dict[str, Any]] = None,
        mse_delta: Optional[float] = None,
        prefer_local: bool = False,
        forced_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST to /api/route to execute an LLM/VLM request via MemoryOS Router."""
        resolved_img = image_url
        if not resolved_img and image_bytes:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            resolved_img = f"data:image/png;base64,{b64}"

        payload: Dict[str, Any] = {
            "session_id": session_id or self.session_id,
            "user_id": user_id or self.user_id,
            "prompt": prompt,
            "prompt_text": prompt,
            "task_type": task_type,
            "image_url": resolved_img,
            "max_tokens": int(max_tokens),
            "context_from_memory": bool(context_from_memory),
            "prefer_local": bool(prefer_local),
        }
        if tlb_context:
            payload["tlb_context"] = tlb_context
        if frame_delta is not None:
            payload["frame_delta"] = frame_delta
        if mse_delta is not None:
            payload["mse_delta"] = mse_delta
        if forced_model:
            payload["forced_model"] = forced_model

        try:
            result = self._request_json("POST", "/api/route", payload=payload)
            self._last_inference_result = result
            logger.info(
                f"Inference routed to {result.get('model', 'unknown')}: "
                f"{result.get('latency_ms', 0)}ms"
            )
            return result
        except Exception as exc:
            logger.error(f"Inference routing failed: {exc}")
            return self._fallback_inference(error=str(exc))

    # Alias for callers using client.route(...)
    route = route_inference

    def acknowledge_card(
        self,
        card_id: Optional[int] = None,
        action: str = "acknowledge",
        insight_type: Optional[str] = None,
        penalty_weight: Optional[float] = None,
        *,
        card_type: Optional[str] = None,
        user_id: Optional[str] = None,
        penalty: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        POST to /api/acknowledge-card when user clicks [Acknowledge & Apply].

        Closes the feedback loop: user preference -> DB update -> next routing respects it.
        """
        resolved_type = card_type or insight_type or "vram_thrashing"
        resolved_user = user_id or self.user_id
        resolved_penalty = penalty if penalty is not None else penalty_weight

        body: Dict[str, Any] = {
            "user_id": resolved_user,
            "card_type": resolved_type,
            "action": action,
        }
        if card_id is not None:
            body["card_id"] = int(card_id)
        if resolved_penalty is not None:
            body["penalty"] = float(resolved_penalty)

        try:
            result = self._request_json(
                "POST",
                "/api/acknowledge-card",
                payload=body,
                params={"user_id": resolved_user, "card_type": resolved_type, "action": action},
            )
            logger.info(
                f"Card acknowledged: {resolved_type}, penalty={result.get('penalty_applied', 'N/A')}"
            )
            return result
        except Exception as exc:
            logger.error(f"Card acknowledgment failed: {exc}")
            return self._fallback_acknowledge_card(error=str(exc))

    def get_hot_memories(self, limit: int = 5) -> Dict[str, Any]:
        try:
            return self._request_json("GET", "/api/memory/hot", params={"limit": limit})
        except Exception as exc:
            logger.error(f"Failed to get hot memories: {exc}")
            return {"status": "error", "memories": [], "total": 0, "error": str(exc)}

    def get_status(self) -> Dict[str, Any]:
        try:
            return self._request_json("GET", "/api/status")
        except Exception as exc:
            logger.error(f"Failed to get router status: {exc}")
            return {"error": str(exc)}

    def _fallback_frame_delta(
        self,
        timeout: bool = False,
        connection_error: bool = False,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "skip_vision": False,
            "d3_decision": {
                "choice": "surface_now",
                "confidence": 0.5,
                "probabilities": {"ignore": 0.2, "defer": 0.3, "surface_now": 0.5},
            },
            "gate_latency_ms": 0.0,
            "error": f"Router unavailable ({error or ('timeout' if timeout else 'connection error')})",
        }

    def _fallback_inference(
        self,
        timeout: bool = False,
        connection_error: bool = False,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self._last_inference_result:
            return {
                **self._last_inference_result,
                "cached": True,
                "error": "Router unavailable, returning cached result",
            }
        return {
            "content": "[Router unavailable. Unable to generate inference.]",
            "model": "fallback-cached",
            "route": "none",
            "task_type": "none",
            "latency_ms": 0.0,
            "error": f"Router unavailable ({error or ('timeout' if timeout else 'connection error')})",
        }

    def _fallback_acknowledge_card(
        self,
        timeout: bool = False,
        connection_error: bool = False,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "status": "error",
            "message": f"Router unavailable ({error or ('timeout' if timeout else 'connection error')})",
            "penalty_applied": 0.0,
            "timestamp": datetime.now().isoformat(),
            "error": "Preference not stored in DB",
        }


# Backwards-compatible alias
MemoryOSRouterClient = QuietAdvisorClient
