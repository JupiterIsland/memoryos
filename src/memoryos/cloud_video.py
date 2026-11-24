"""Cloud-offloaded Video Analysis & Generation for MemoryOS // Jupiter Studio.

Two zero-local-VRAM video workflows that run strictly in Python 3.11+ stdlib:
1. Cloud Video Analyzer & Scene Indexer:
   - Samples keyframes on CPU (browser canvas or optional lazy cv2) and runs
     MemoryOS's CPU frame-delta gate (mse_to_frame_delta / compute_frame_delta)
     to skip static/duplicate frames before any cloud network call.
   - Offloads only significant scene-change keyframes to AMD Token Lab
     multimodal models (default: MiniCPM-V-4.7-35B-A3B, MiniCPM-V-4.7-1B,
     Gemma-4-31B-IT) or Gemini / OpenAI vision endpoints.
   - Persists timestamped scene markers to MemoryVault (QuietAdvisorDB.sqlite)
     for instant search and documentary / archive recall.
2. Cloud Video Generator (Google Gemini Omni 1.2 Flash):
   - Offloads text-to-video, image-to-video (first frame / first+last frame),
     and turn-by-turn edits/extensions to Gemini Omni 1.2 Flash via the
     Interactions REST API, saving finished .mp4 files to I:\\video-outputs\\.
   - Keeps local RTX / host GPU VRAM at 0 MB.
"""

from __future__ import annotations

import base64
import ipaddress
import json
import math
import os
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from src.memoryos.control_plane import ImmutableLedger
    from src.memoryos.router import (
        _get_gemini_credentials,
        _get_openai_credentials,
        _get_tokenlab_credentials,
        _is_configured_key,
        compute_frame_delta,
        get_cloud_provider_status,
        mse_to_frame_delta,
    )
except ImportError:
    from memoryos.control_plane import ImmutableLedger
    from memoryos.router import (
        _get_gemini_credentials,
        _get_openai_credentials,
        _get_tokenlab_credentials,
        _is_configured_key,
        compute_frame_delta,
        get_cloud_provider_status,
        mse_to_frame_delta,
    )

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VIDEO_OUTPUT_DIR_WIN = Path("I:/video-outputs")
DEFAULT_VIDEO_ANALYZE_TARGET = "cloud:MiniCPM-V-4.7-35B-A3B"
DEFAULT_OMNI_VIDEO_MODEL = "gemini-omni-1.2-flash"
DEFAULT_OMNI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_FAL_QUEUE_BASE_URL = "https://queue.fal.run"
DEFAULT_REPLICATE_BASE_URL = "https://api.replicate.com/v1"
DEFAULT_HF_INFERENCE_BASE_URL = "https://router.huggingface.co/hf-inference/models"
DEFAULT_HF_ROUTER_CHAT_URL = "https://router.huggingface.co/v1"
DEFAULT_OLLAMA_OPENAI_URL = "http://127.0.0.1:11434/v1"

# Reference per-second USD estimates (Glass Box estimator — verify against provider billing)
VIDEO_GENERATOR_CATALOG: Tuple[Dict[str, Any], ...] = (
    {
        "target": "gemini:gemini-omni-1.2-flash",
        "provider": "gemini",
        "provider_label": "Google Gemini Omni Cloud",
        "model": "gemini-omni-1.2-flash",
        "label": "Gemini Omni 1.2 Flash (Google Cloud)",
        "env_var": "GEMINI_API_KEY",
        "rates": {"360p": 0.05, "720p": 0.10, "1080p": 0.15, "4k": 0.30},
        "default_rate": 0.10,
        "tier": "hero",
    },
    {
        "target": "fal:fal-ai/wan-25-preview/text-to-video",
        "provider": "fal",
        "provider_label": "fal.ai Cloud",
        "model": "fal-ai/wan-25-preview/text-to-video",
        "label": "Wan 2.5 Preview (fal.ai Draft)",
        "env_var": "FAL_KEY",
        "rates": {"360p": 0.05, "480p": 0.05, "720p": 0.10, "1080p": 0.15},
        "default_rate": 0.05,
        "tier": "draft",
    },
    {
        "target": "fal:fal-ai/pika/v2.2/text-to-video",
        "provider": "fal",
        "provider_label": "fal.ai Cloud",
        "model": "fal-ai/pika/v2.2/text-to-video",
        "label": "Pika 2.2 (fal.ai Fast Draft)",
        "env_var": "FAL_KEY",
        "rates": {"360p": 0.04, "720p": 0.04, "1080p": 0.08},
        "default_rate": 0.04,
        "tier": "draft",
    },
    {
        "target": "fal:fal-ai/kling-video/v2.1/standard/text-to-video",
        "provider": "fal",
        "provider_label": "fal.ai Cloud",
        "model": "fal-ai/kling-video/v2.1/standard/text-to-video",
        "label": "Kling 2.1 Standard (fal.ai Studio)",
        "env_var": "FAL_KEY",
        "rates": {"720p": 0.11, "1080p": 0.17},
        "default_rate": 0.11,
        "tier": "studio",
    },
    {
        "target": "replicate:wan-video/wan-2.5-t2v",
        "provider": "replicate",
        "provider_label": "Replicate Cloud",
        "model": "wan-video/wan-2.5-t2v",
        "label": "Wan 2.5 T2V (Replicate Open-Weight)",
        "env_var": "REPLICATE_API_TOKEN",
        "rates": {"360p": 0.05, "480p": 0.05, "720p": 0.10, "1080p": 0.15},
        "default_rate": 0.05,
        "tier": "draft",
    },
    {
        "target": "replicate:runwayml/gen4-turbo",
        "provider": "replicate",
        "provider_label": "Replicate Cloud",
        "model": "runwayml/gen4-turbo",
        "label": "Runway Gen-4 Turbo (Replicate)",
        "env_var": "REPLICATE_API_TOKEN",
        "rates": {"720p": 0.08, "1080p": 0.12},
        "default_rate": 0.12,
        "tier": "hero",
    },
    {
        "target": "replicate:luma/ray-2",
        "provider": "replicate",
        "provider_label": "Replicate Cloud",
        "model": "luma/ray-2",
        "label": "Luma Ray 2 (Replicate)",
        "env_var": "REPLICATE_API_TOKEN",
        "rates": {"720p": 0.18, "1080p": 0.24},
        "default_rate": 0.24,
        "tier": "hero",
    },
    {
        "target": "hf:Wan-AI/Wan2.2-TI2V-5B",
        "provider": "hf",
        "provider_label": "Hugging Face Router",
        "model": "Wan-AI/Wan2.2-TI2V-5B",
        "label": "Wan 2.2 TI2V 5B (Hugging Face Open-Weight)",
        "env_var": "HF_TOKEN",
        "rates": {"360p": 0.04, "480p": 0.04, "720p": 0.06, "1080p": 0.10},
        "default_rate": 0.05,
        "tier": "draft",
    },
    {
        "target": "hf:Wan-AI/Wan2.2-T2V-A14B",
        "provider": "hf",
        "provider_label": "Hugging Face Router",
        "model": "Wan-AI/Wan2.2-T2V-A14B",
        "label": "Wan 2.2 T2V A14B MoE (Hugging Face Open-Weight)",
        "env_var": "HF_TOKEN",
        "rates": {"360p": 0.06, "480p": 0.06, "720p": 0.08, "1080p": 0.14},
        "default_rate": 0.08,
        "tier": "hero",
    },
)

_GENERATOR_CATALOG_BY_TARGET: Dict[str, Dict[str, Any]] = {
    entry["target"]: entry for entry in VIDEO_GENERATOR_CATALOG
}


class VideoBudgetExceededError(ValueError):
    """Raised before dispatch when estimated cloud video cost exceeds the hard spend cap."""

    def __init__(self, message: str, estimated_cost_usd: float, max_budget_usd: float) -> None:
        super().__init__(message)
        self.estimated_cost_usd = float(estimated_cost_usd)
        self.max_budget_usd = float(max_budget_usd)

SUPPORTED_ANALYZE_TARGETS: Tuple[Dict[str, str], ...] = (
    {
        "target": "cloud:MiniCPM-V-4.7-35B-A3B",
        "label": "MiniCPM-V-4.7-35B-A3B (AMD Token Lab · Vision MoE)",
        "provider": "amd_tokenlab",
    },
    {
        "target": "cloud:MiniCPM-V-4.7-1B",
        "label": "MiniCPM-V-4.7-1B (AMD Token Lab · Fast Edge Vision)",
        "provider": "amd_tokenlab",
    },
    {
        "target": "cloud:Gemma-4-31B-IT",
        "label": "Gemma-4-31B-IT (AMD Token Lab · Deep Scene Analysis)",
        "provider": "amd_tokenlab",
    },
    {
        "target": "gemini:gemini-3.8-flash",
        "label": "Gemini 3.8 Flash (Google Gemini API · Multimodal)",
        "provider": "gemini",
    },
    {
        "target": "gemini:gemma-4-31b-it",
        "label": "Gemma 4 31B IT (Google Gemini API)",
        "provider": "gemini",
    },
    {
        "target": "openai:gpt-4o-mini",
        "label": "gpt-4o-mini (OpenAI Cloud · Vision)",
        "provider": "openai",
    },
    {
        "target": "openai:gpt-4o",
        "label": "gpt-4o (OpenAI Cloud · Flagship Vision)",
        "provider": "openai",
    },
    {
        "target": "ollama:hf.co/unsloth/gemma-4-E2B-it-GGUF",
        "label": "Gemma 4 E2B GGUF (Hugging Face Local · $0.00 Free)",
        "provider": "ollama",
    },
    {
        "target": "ollama:gemma4:26b",
        "label": "gemma4:26b (Local Ollama Vision · $0.00 Free)",
        "provider": "ollama",
    },
    {
        "target": "hf:Qwen/Qwen3.8-27B",
        "label": "Qwen 3.8 27B Vision (Hugging Face Router)",
        "provider": "huggingface",
    },
)

VALID_OMNI_ASPECT_RATIOS = {"16:9", "9:16"}
VALID_OMNI_RESOLUTIONS = {"360p", "720p", "1080p", "4k"}
MIN_OMNI_DURATION_S = 3
MAX_OMNI_DURATION_S = 15
MAX_OMNI_TWO_FRAME_OR_EXTEND_S = 10
MAX_OMNI_REFERENCE_IMAGES = 6
MAX_ANALYZE_FRAMES_INPUT = 32
MAX_CLOUD_FRAMES_CAP = 16

_SAFE_VIDEO_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,120}\.mp4$", re.IGNORECASE)
_IMAGE_DATA_URI_RE = re.compile(
    r"^data:(image/(?:png|jpe?g|gif|webp|bmp|avif));base64,([A-Za-z0-9+/=\s]+)$",
    re.IGNORECASE,
)
_SCENE_CONTENT_TS_RE = re.compile(r"^\[(\d{2}:\d{2}(?::\d{2})?)\]\s*(.+)$")


def get_video_output_dir(create: bool = True) -> Path:
    """Resolve cloud video output directory (./outputs/video default; auto-uses existing I:\\video-outputs)."""
    override = os.getenv("MEMORYOS_VIDEO_OUTPUT_DIR", "").strip()
    if override:
        out_dir = Path(override).expanduser()
    elif os.name == "nt" and DEFAULT_VIDEO_OUTPUT_DIR_WIN.is_dir():
        out_dir = DEFAULT_VIDEO_OUTPUT_DIR_WIN
    else:
        out_dir = REPO_ROOT / "outputs" / "video"
    if create:
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            out_dir = REPO_ROOT / "outputs" / "video"
            out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


_WIN_RESERVED_STEMS = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})


def resolve_safe_video_path(filename: str, output_dir: Optional[Path] = None) -> Optional[Path]:
    """Validate an .mp4 basename and confine resolution strictly within output_dir."""
    raw = str(filename or "").strip()
    if not raw or "/" in raw or "\\" in raw or ".." in raw or "\x00" in raw:
        return None
    if not _SAFE_VIDEO_FILENAME_RE.match(raw):
        return None
    stem = raw.rsplit(".", 1)[0].split(".")[0].upper()
    if stem in _WIN_RESERVED_STEMS:
        return None
    base = Path(output_dir) if output_dir is not None else get_video_output_dir(create=False)
    try:
        base_resolved = base.resolve()
        candidate = (base_resolved / raw).resolve()
    except OSError:
        return None
    if candidate.parent != base_resolved or candidate.name != raw:
        return None
    return candidate


def _get_fal_credentials() -> Tuple[str, str]:
    """Return (api_key, queue_base_url) for fal.ai asynchronous queue inference."""
    key = os.getenv("FAL_KEY", "").strip() or os.getenv("FAL_API_KEY", "").strip()
    base_url = os.getenv("FAL_QUEUE_BASE_URL", "").strip().rstrip("/") or DEFAULT_FAL_QUEUE_BASE_URL
    return key, base_url


def _get_replicate_credentials() -> Tuple[str, str]:
    """Return (api_token, base_url) for Replicate REST API predictions."""
    key = os.getenv("REPLICATE_API_TOKEN", "").strip() or os.getenv("REPLICATE_API_KEY", "").strip()
    base_url = os.getenv("REPLICATE_BASE_URL", "").strip().rstrip("/") or DEFAULT_REPLICATE_BASE_URL
    return key, base_url


def _get_hf_video_credentials() -> Tuple[str, str]:
    """Return (api_token, inference_base_url) for Hugging Face Router open-weight video."""
    key = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or "").strip()
    base_url = os.getenv("HF_INFERENCE_BASE_URL", "").strip().rstrip("/") or DEFAULT_HF_INFERENCE_BASE_URL
    return key, base_url


def _is_safe_public_https_url(url: str) -> bool:
    """Allow only public https:// URLs without credentials or private/loopback hosts (SSRF guard)."""
    cleaned = str(url or "").strip()
    if not cleaned or any(ch.isspace() for ch in cleaned) or "\x00" in cleaned:
        return False
    try:
        parsed = urllib.parse.urlsplit(cleaned)
    except ValueError:
        return False
    if (parsed.scheme or "").lower() != "https":
        return False
    if parsed.username is not None or parsed.password is not None or not parsed.netloc:
        return False
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host or host in {"localhost", "127.0.0.1", "::1"}:
        return False
    if host.endswith((".local", ".internal", ".localhost")):
        return False
    try:
        ip = ipaddress.ip_address(host)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    except ValueError:
        pass
    return True


def _is_generator_provider_configured(provider: str) -> bool:
    if provider == "gemini":
        key, _ = _get_gemini_credentials()
        return _is_configured_key(key, "AIza-your-gemini-key-here", "your-gemini-api-key-here")
    if provider == "fal":
        key, _ = _get_fal_credentials()
        return _is_configured_key(key, "fal-your-key-here", "your-fal-key-here")
    if provider == "replicate":
        key, _ = _get_replicate_credentials()
        return _is_configured_key(key, "r8_your-replicate-token-here", "your-replicate-token-here")
    if provider == "hf":
        key, _ = _get_hf_video_credentials()
        return _is_configured_key(key, "hf_your-token-here", "your-huggingface-token-here")
    return False


def _resolve_generator_target(target: Optional[str] = None, model: Optional[str] = None) -> Tuple[str, str, str]:
    """Normalize a generator selector into (canonical_target, provider_key, model_id)."""
    raw = str(target or "").strip()
    if not raw:
        m = str(model or DEFAULT_OMNI_VIDEO_MODEL).strip() or DEFAULT_OMNI_VIDEO_MODEL
        raw = m if ":" in m else f"gemini:{m}"
    if ":" not in raw:
        raw = f"gemini:{raw}"
    provider, model_id = raw.split(":", 1)
    provider = provider.strip().lower()
    model_id = model_id.strip()
    if provider not in {"gemini", "fal", "replicate", "hf"}:
        raise ValueError(f"Unsupported cloud video provider '{provider}'. Expected gemini, fal, replicate, or hf.")
    if not model_id:
        raise ValueError("Cloud video model id cannot be empty.")
    return f"{provider}:{model_id}", provider, model_id


def _parse_video_duration_seconds(duration: Any) -> int:
    if duration is None or str(duration).strip().lower() in ("", "none"):
        return 10
    raw_dur = str(duration).strip().lower()
    if raw_dur.endswith("s"):
        raw_dur = raw_dur[:-1]
    try:
        dur_f = float(raw_dur)
    except ValueError as exc:
        raise ValueError(f"Invalid duration '{duration}': expected integer seconds (3..15).") from exc
    if not math.isfinite(dur_f) or not dur_f.is_integer():
        raise ValueError(f"Duration must be an integer number of seconds (got {duration}).")
    dur_int = int(dur_f)
    if dur_int < MIN_OMNI_DURATION_S or dur_int > MAX_OMNI_DURATION_S:
        raise ValueError(
            f"Duration must be between {MIN_OMNI_DURATION_S} and {MAX_OMNI_DURATION_S} seconds (got {dur_int})."
        )
    return dur_int


def estimate_video_generation_cost(
    target: str = f"gemini:{DEFAULT_OMNI_VIDEO_MODEL}",
    duration: Any = 10,
    resolution: str = "720p",
    rate_override: Optional[float] = None,
    max_budget_usd: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute transparent pre-flight USD estimate and budget guard for a cloud video job."""
    norm_target, provider, model_id = _resolve_generator_target(target=target)
    dur_int = _parse_video_duration_seconds(duration)
    res = str(resolution or "720p").strip().lower()
    if res not in VALID_OMNI_RESOLUTIONS and res != "480p":
        raise ValueError(
            f"Unsupported resolution '{res}'. Expected one of {sorted(VALID_OMNI_RESOLUTIONS)}."
        )

    entry = _GENERATOR_CATALOG_BY_TARGET.get(norm_target)
    if entry:
        rates = entry["rates"]
        default_rate = float(entry["default_rate"])
        env_var = entry["env_var"]
        label = entry["label"]
        tier = entry["tier"]
        provider_label = entry["provider_label"]
    else:
        default_rate = 0.05 if provider in ("fal", "hf") else 0.10
        rates = {"360p": round(default_rate * 0.6, 4), "720p": default_rate, "1080p": round(default_rate * 1.5, 4)}
        env_var = {
            "gemini": "GEMINI_API_KEY",
            "fal": "FAL_KEY",
            "replicate": "REPLICATE_API_TOKEN",
            "hf": "HF_TOKEN",
        }[provider]
        label = f"{model_id} ({provider})"
        tier = "custom"
        provider_label = {
            "gemini": "Google Gemini Omni Cloud",
            "fal": "fal.ai Cloud",
            "replicate": "Replicate Cloud",
            "hf": "Hugging Face Router",
        }[provider]

    if rate_override is not None and not isinstance(rate_override, bool):
        r_val = float(rate_override)
        if not math.isfinite(r_val) or r_val < 0:
            raise ValueError("rate_override must be a finite non-negative number.")
        rate = r_val
    else:
        rate = float(rates.get(res, default_rate))

    est_cost = round(rate * dur_int, 4)

    caps: List[float] = []
    if max_budget_usd is not None and not isinstance(max_budget_usd, bool):
        cap_val = float(max_budget_usd)
        if not math.isfinite(cap_val) or cap_val < 0:
            raise ValueError("max_budget_usd must be a finite non-negative USD amount.")
        caps.append(cap_val)
    env_cap_raw = os.getenv("MEMORYOS_VIDEO_MAX_JOB_USD", "").strip()
    if env_cap_raw:
        try:
            env_cap = float(env_cap_raw)
            if not math.isfinite(env_cap) or env_cap < 0:
                caps.append(0.0)
            else:
                caps.append(env_cap)
        except ValueError:
            # Fail closed to $0.00 if an operator mistypes MEMORYOS_VIDEO_MAX_JOB_USD
            caps.append(0.0)
    eff_cap = round(min(caps), 4) if caps else None
    within_budget = True if eff_cap is None else (est_cost <= eff_cap + 1e-9)

    return {
        "target": norm_target,
        "provider": provider,
        "provider_label": provider_label,
        "model": model_id,
        "label": label,
        "tier": tier,
        "env_var": env_var,
        "configured": _is_generator_provider_configured(provider),
        "duration_s": dur_int,
        "resolution": res,
        "rate_per_sec_usd": round(rate, 4),
        "estimated_cost_usd": est_cost,
        "max_budget_usd": eff_cap,
        "within_budget": within_budget,
        "draft_baseline_usd": round(0.05 * 5, 4),
        "estimate_note": "Reference per-second estimate — verify exact billing on your provider dashboard.",
    }


def sanitize_video_error(err: Any) -> str:
    """Redact API keys, bearer/fal tokens, and URL key parameters from error messages."""
    text = str(err or "").strip()
    if not text:
        return ""
    for env_name in (
        "GEMINI_API_KEY",
        "TOKENLAB_API_KEY",
        "OPENAI_API_KEY",
        "FAL_KEY",
        "FAL_API_KEY",
        "REPLICATE_API_TOKEN",
        "REPLICATE_API_KEY",
        "HF_TOKEN",
        "HUGGINGFACE_API_KEY",
    ):
        secret = os.getenv(env_name, "").strip()
        if secret and len(secret) >= 6:
            text = text.replace(secret, "[REDACTED_KEY]")
    text = re.sub(r"AIza[0-9A-Za-z_\-]{20,}", "[REDACTED_KEY]", text)
    text = re.sub(r"AQ\.[0-9A-Za-z_\-]{12,}", "[REDACTED_KEY]", text)
    text = re.sub(r"ya29\.[0-9A-Za-z_\-]+", "[REDACTED_TOKEN]", text)
    text = re.sub(r"r8_[A-Za-z0-9_\-]{8,}", "[REDACTED_TOKEN]", text)
    text = re.sub(r"\bhf_[A-Za-z0-9]{10,}\b", "[REDACTED_KEY]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED_TOKEN]", text, flags=re.IGNORECASE)
    text = re.sub(r"\bKey\s+[A-Za-z0-9_\-:.]{6,}", "Key [REDACTED_KEY]", text)
    text = re.sub(
        r"([?&](?:key|api_key|apiKey|access_token|token|auth|signature)=)[^&\s\"'<>()]+",
        r"\1[REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text[:497] + "..." if len(text) > 500 else text


def list_generated_videos(output_dir: Optional[Path] = None, limit: int = 40) -> List[Dict[str, Any]]:
    """List saved .mp4 outputs sorted newest-first without external dependencies."""
    target_dir = Path(output_dir) if output_dir is not None else get_video_output_dir(create=False)
    if not target_dir.is_dir():
        return []
    cap = max(1, min(200, int(limit)))
    entries: List[Tuple[float, Dict[str, Any]]] = []
    try:
        for item in target_dir.iterdir():
            if not item.is_file() or item.suffix.lower() != ".mp4":
                continue
            if not _SAFE_VIDEO_FILENAME_RE.match(item.name):
                continue
            try:
                st = item.stat()
            except OSError:
                continue
            mtime = float(st.st_mtime)
            size_b = int(st.st_size)
            entries.append((
                mtime,
                {
                    "filename": item.name,
                    "size_bytes": size_b,
                    "size_mb": round(size_b / (1024.0 * 1024.0), 2),
                    "modified_at": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                    "video_url": f"/api/video/outputs/{urllib.parse.quote(item.name)}",
                    "path": str(item),
                },
            ))
    except OSError:
        return []
    entries.sort(key=lambda pair: pair[0], reverse=True)
    return [row for _, row in entries[:cap]]


def _format_timestamp(seconds: float) -> str:
    total = max(0, int(round(float(seconds or 0.0))))
    hrs, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def _parse_timestamp_label(label: str) -> float:
    parts = [p for p in str(label or "").split(":") if p.isdigit()]
    if len(parts) == 2:
        return float(int(parts[0]) * 60 + int(parts[1]))
    if len(parts) == 3:
        return float(int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]))
    return 0.0


def _slugify_video_name(name: str) -> str:
    stem = Path(str(name or "clip")).stem.lower()
    slug = re.sub(r"[^a-z0-9_-]+", "_", stem).strip("_")
    return slug[:48] or "clip"


def _parse_image_data_uri(data_uri: str) -> Optional[Tuple[str, str]]:
    cleaned = str(data_uri or "").strip()
    m = _IMAGE_DATA_URI_RE.match(cleaned)
    if not m:
        return None
    mime_type = m.group(1).lower()
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    raw_b64 = re.sub(r"\s+", "", m.group(2))
    if not raw_b64:
        return None
    return mime_type, raw_b64


def extract_video_keyframes_local(
    video_path: str,
    sample_interval_s: float = 3.0,
    max_frames: int = 24,
    max_width: int = 480,
) -> List[Dict[str, Any]]:
    """Extract sampled video frames on CPU using optional OpenCV + NumPy (no GPU VRAM)."""
    src = Path(str(video_path or "")).expanduser()
    if not src.is_file():
        raise FileNotFoundError(f"Video file not found: {src}")
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Local file decoding requires opencv-python/numpy, or upload the video in Jupiter Studio UI "
            "where your browser extracts keyframes natively with zero Python dependencies."
        ) from exc

    interval = max(0.5, min(60.0, float(sample_interval_s or 3.0)))
    cap_frames = max(1, min(MAX_ANALYZE_FRAMES_INPUT, int(max_frames or 24)))
    target_w = max(160, min(960, int(max_width or 480)))

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Unable to open video file: {src.name}")

    results: List[Dict[str, Any]] = []
    prev_small: Any = None
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0.0 or fps > 240.0:
            fps = 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_s = (total_frames / fps) if total_frames > 0 else 0.0

        timestamps: List[float] = []
        if duration_s > 0.0:
            t = 0.0
            while t < duration_s and len(timestamps) < cap_frames:
                timestamps.append(round(t, 2))
                t += interval
        else:
            timestamps = [round(i * interval, 2) for i in range(cap_frames)]

        for ts in timestamps:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            h, w = frame.shape[:2]
            if w > target_w and h > 0:
                new_h = max(2, int(round(h * (target_w / float(w)))))
                resized = cv2.resize(frame, (target_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                resized = frame

            small_gray = cv2.cvtColor(
                cv2.resize(resized, (64, 36), interpolation=cv2.INTER_AREA),
                cv2.COLOR_BGR2GRAY,
            ).astype(np.float32)

            if prev_small is None:
                mse_val = 255.0
            else:
                diff = small_gray - prev_small
                mse_val = float(np.mean(diff * diff))
            prev_small = small_gray

            brightness = round(float(np.mean(small_gray)) / 255.0, 4)
            contrast = round(min(1.0, float(np.std(small_gray)) / 128.0), 4)
            metrics = {
                "brightness": brightness,
                "contrast": contrast,
                "intensity": round(min(1.0, float(np.max(small_gray)) / 255.0), 4),
            }

            ok_enc, buf = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
            if not ok_enc:
                continue
            b64 = base64.b64encode(buf.tobytes()).decode("ascii")
            results.append({
                "timestamp_s": ts,
                "data_uri": f"data:image/jpeg;base64,{b64}",
                "metrics": metrics,
                "mse_delta": round(mse_val, 4),
            })
    finally:
        cap.release()

    if not results:
        raise RuntimeError(f"Could not decode any video frames from {src.name}")
    return results


def gate_video_frames(
    frames: Sequence[Dict[str, Any]],
    mse_threshold: float = 12.0,
    delta_threshold: float = 0.08,
    max_cloud_frames: int = 8,
) -> Dict[str, Any]:
    """Filter redundant static frames on CPU before cloud vision offload."""
    t0 = time.perf_counter()
    max_keep = max(1, min(MAX_CLOUD_FRAMES_CAP, int(max_cloud_frames or 8)))
    selected: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    prev_metrics: Optional[Dict[str, Any]] = None

    for idx, raw in enumerate(frames):
        if not isinstance(raw, dict):
            continue
        data_uri = str(raw.get("data_uri") or raw.get("image_base64") or "").strip()
        if not data_uri:
            continue
        ts = float(raw.get("timestamp_s", idx * 2.0) or 0.0)
        metrics = raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {}
        mse_raw = raw.get("mse_delta")

        if mse_raw is not None and not isinstance(mse_raw, bool):
            delta = mse_to_frame_delta(float(mse_raw), threshold=float(mse_threshold))
        else:
            delta = compute_frame_delta(metrics, prev_metrics, threshold=float(delta_threshold))

        is_first = len(selected) == 0
        significant = True if is_first else bool(delta.get("significant_change"))

        item = {
            "index": idx,
            "timestamp_s": round(ts, 2),
            "timestamp_label": _format_timestamp(ts),
            "data_uri": data_uri,
            "metrics": metrics,
            "delta": delta,
        }

        if significant and len(selected) < max_keep:
            selected.append(item)
            prev_metrics = metrics or prev_metrics
        else:
            reason = "cap_reached" if significant else "static_frame_skipped"
            item["skip_reason"] = reason
            skipped.append(item)

    total = len(selected) + len(skipped)
    skipped_cnt = len(skipped)
    skipped_pct = round((skipped_cnt / total) * 100.0, 1) if total > 0 else 0.0
    gate_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    return {
        "selected": selected,
        "skipped": skipped,
        "frames_total": total,
        "frames_offloaded": len(selected),
        "frames_skipped": skipped_cnt,
        "frames_skipped_pct": skipped_pct,
        "gate_ms": gate_ms,
    }


def _http_json_request(
    url: str,
    headers: Dict[str, str],
    payload: Optional[Dict[str, Any]] = None,
    method: str = "POST",
    timeout: float = 45.0,
) -> Dict[str, Any]:
    scheme = (urllib.parse.urlsplit(str(url or "")).scheme or "").lower()
    if scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme '{scheme}': only http and https are allowed.")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req_headers = dict(headers)
    if payload is not None and "Content-Type" not in req_headers:
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        finally:
            try:
                exc.close()
            except Exception:
                pass
        raise RuntimeError(f"HTTP {exc.code}: {sanitize_video_error(detail or exc.reason)}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {sanitize_video_error(exc.reason)}") from exc


def _extract_openai_chat_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        parts = [
            str(b.get("text") or "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        content = "\n".join(p for p in parts if p)
    text = str(content or "").strip()
    if not text:
        text = str(msg.get("reasoning_content") or msg.get("reasoning") or "").strip()
    return text


def _call_vision_provider(
    target: str,
    data_uri: str,
    prompt_text: str,
    timeout: float = 45.0,
) -> Tuple[str, str, str]:
    """Send one keyframe + prompt to an external cloud vision model (0 MB local VRAM)."""
    target_str = str(target or DEFAULT_VIDEO_ANALYZE_TARGET).strip()
    if ":" in target_str:
        prefix, model_name = target_str.split(":", 1)
    else:
        prefix, model_name = "cloud", target_str

    if prefix == "gemini":
        api_key, base_url = _get_gemini_credentials()
        if not _is_configured_key(api_key, "AIza-your-gemini-key-here", "your-gemini-api-key-here"):
            raise RuntimeError("Google Gemini API key not configured in .env (set GEMINI_API_KEY).")
        parsed_img = _parse_image_data_uri(data_uri)
        img_block: Dict[str, Any]
        if parsed_img:
            img_block = {"type": "image", "mime_type": parsed_img[0], "data": parsed_img[1]}
        else:
            img_block = {"type": "image", "uri": data_uri}
        resp = _http_json_request(
            f"{base_url.rstrip('/')}/interactions",
            headers={"x-goog-api-key": api_key, "User-Agent": "MemoryOS-CloudVideo/1.0"},
            payload={
                "model": model_name,
                "input": [
                    {
                        "type": "user_input",
                        "content": [{"type": "text", "text": prompt_text}, img_block],
                    }
                ],
                "stream": False,
                "store": False,
            },
            timeout=timeout,
        )
        parts: List[str] = []
        for step in resp.get("steps") or []:
            if isinstance(step, dict) and step.get("type") == "model_output":
                for block in step.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                        parts.append(str(block["text"]))
        text = "".join(parts).strip()
        if not text:
            raise RuntimeError(f"Google Gemini API ({model_name}) returned empty vision output")
        return text, "Google Gemini API", model_name

    if prefix == "openai":
        api_key, base_url = _get_openai_credentials()
        if not _is_configured_key(api_key, "sk-your-key-here", "your-openai-api-key-here"):
            raise RuntimeError("OpenAI API key not configured in .env (set OPENAI_API_KEY).")
        provider_label = "OpenAI Cloud"
        candidates = [model_name]
    elif prefix == "hf":
        api_key, _ = _get_hf_video_credentials()
        base_url = os.getenv("HF_BASE_URL", DEFAULT_HF_ROUTER_CHAT_URL).strip().rstrip("/")
        if not _is_configured_key(api_key, "hf_your-token-here", "your-huggingface-token-here"):
            raise RuntimeError("Hugging Face token not configured in .env (set HF_TOKEN).")
        provider_label = "Hugging Face Router"
        candidates = [model_name]
    elif prefix == "ollama":
        ollama_root = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip().rstrip("/")
        if "://" not in ollama_root:
            ollama_root = f"http://{ollama_root}"
        parsed_ol = urllib.parse.urlsplit(ollama_root)
        if (parsed_ol.scheme or "").lower() not in {"http", "https"}:
            raise ValueError("OLLAMA_HOST must use http or https.")
        ol_host = (parsed_ol.hostname or "").strip().lower()
        if ol_host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Refusing non-loopback OLLAMA_HOST for local video analysis.")
        api_key = "ollama"
        base_url = f"{ollama_root}/v1"
        provider_label = "Local Ollama ($0.00)"
        candidates = [model_name]
    else:
        api_key, base_url = _get_tokenlab_credentials()
        if not _is_configured_key(api_key, "tl-your-tokenlab-key-here", "your-token-lab-api-key-here"):
            raise RuntimeError("AMD Token Lab API key not configured in .env (set TOKENLAB_API_KEY).")
        provider_label = "AMD Token Lab"
        candidates = [model_name]
        if "Gemma-4-31B-IT" not in candidates:
            candidates.append("Gemma-4-31B-IT")

    last_err: Optional[Exception] = None
    for idx, cand_model in enumerate(candidates):
        try:
            data = _http_json_request(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "MemoryOS-CloudVideo/1.0",
                },
                payload={
                    "model": cand_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": data_uri}},
                            ],
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 220,
                },
                timeout=timeout,
            )
            text = _extract_openai_chat_text(data)
            if not text:
                raise RuntimeError(f"{provider_label} ({cand_model}) returned empty content")
            return text, provider_label, cand_model
        except Exception as exc:
            last_err = exc
            msg_low = str(exc).lower()
            if "http 401" in msg_low or "http 403" in msg_low:
                raise
            if idx + 1 < len(candidates) and any(
                code in msg_low for code in ("http 404", "http 429", "http 502", "http 503", "http 504")
            ):
                continue
            raise

    raise last_err if last_err is not None else RuntimeError(f"{provider_label}: cloud vision call failed")


def _parse_scene_json(raw_text: str, timestamp_s: float) -> Dict[str, Any]:
    cleaned = str(raw_text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[A-Za-z0-9_-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()

    parsed: Optional[Dict[str, Any]] = None
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            parsed = obj
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                obj = json.loads(m.group(0))
                if isinstance(obj, dict):
                    parsed = obj
            except json.JSONDecodeError:
                parsed = None

    ts_label = _format_timestamp(timestamp_s)
    if parsed:
        label = " ".join(str(parsed.get("label") or parsed.get("title") or "Scene Marker").split())[:72]
        summary = " ".join(str(parsed.get("summary") or parsed.get("caption") or "").split())[:260]
        raw_tags = parsed.get("tags")
        tags = (
            [str(t).strip().lower() for t in raw_tags[:5] if str(t).strip()]
            if isinstance(raw_tags, list)
            else []
        )
        mood = " ".join(str(parsed.get("mood") or "neutral").split())[:32]
    else:
        first_line = next((ln.strip() for ln in cleaned.splitlines() if ln.strip()), "Scene Marker")
        label = first_line[:64]
        summary = " ".join(cleaned.split())[:260] or f"Visual scene captured at {ts_label}."
        tags = []
        mood = "observed"

    return {
        "timestamp_s": round(float(timestamp_s or 0.0), 2),
        "timestamp_label": ts_label,
        "label": label or f"Scene at {ts_label}",
        "summary": summary or f"Visual scene captured at {ts_label}.",
        "tags": tags,
        "mood": mood or "neutral",
    }


def analyze_video_frames_cloud(
    frames: Optional[Sequence[Dict[str, Any]]] = None,
    video_path: Optional[str] = None,
    video_name: str = "clip.mp4",
    target: str = DEFAULT_VIDEO_ANALYZE_TARGET,
    prompt_hint: str = "",
    mse_threshold: float = 12.0,
    delta_threshold: float = 0.08,
    max_cloud_frames: int = 8,
    save_to_vault: bool = True,
    vault: Any = None,
    timeout: float = 45.0,
    ledger: Any = None,
) -> Dict[str, Any]:
    """Gate keyframes on CPU and offload scene indexing to AMD Token Lab / cloud vision."""
    t_start = time.perf_counter()
    clean_name = Path(str(video_name or (video_path or "clip.mp4"))).name or "clip.mp4"

    if frames and len(frames) > 0:
        working_frames = list(frames)[:MAX_ANALYZE_FRAMES_INPUT]
    elif video_path:
        working_frames = extract_video_keyframes_local(video_path, max_frames=MAX_ANALYZE_FRAMES_INPUT)
    else:
        raise ValueError("Provide sampled video frames or a valid local video_path.")

    gated = gate_video_frames(
        working_frames,
        mse_threshold=mse_threshold,
        delta_threshold=delta_threshold,
        max_cloud_frames=max_cloud_frames,
    )
    if gated["frames_total"] == 0:
        raise ValueError("No valid video frames with image data were found.")

    slug = _slugify_video_name(clean_name)
    hint_line = f" Operator focus: {prompt_hint.strip()[:240]}." if prompt_hint and prompt_hint.strip() else ""

    scenes: List[Dict[str, Any]] = []
    provider_used = ""
    model_used = ""

    for kf in gated["selected"]:
        ts_lbl = kf["timestamp_label"]
        delta_val = float(kf["delta"].get("composite_delta", 1.0))
        vlm_prompt = (
            f"Analyze this video frame from '{clean_name}' at timestamp {ts_lbl}.{hint_line} "
            "Respond ONLY with valid JSON: "
            '{"label": "3-6 word scene title", "summary": "concise 1-2 sentence visual description", '
            '"tags": ["tag1", "tag2", "tag3"], "mood": "one word"}.'
        )
        raw_reply, prov, mod = _call_vision_provider(
            target=target,
            data_uri=kf["data_uri"],
            prompt_text=vlm_prompt,
            timeout=timeout,
        )
        provider_used = prov
        model_used = mod
        parsed = _parse_scene_json(raw_reply, kf["timestamp_s"])
        parsed["composite_delta"] = round(delta_val, 4)
        parsed["mse_delta"] = kf["delta"].get("mse_delta")
        parsed["video_name"] = clean_name

        if save_to_vault and vault is not None:
            tag_str = ",".join(
                dict.fromkeys(["video_scene", slug] + [re.sub(r"[^a-z0-9_-]", "", t) for t in parsed["tags"] if t])
            )[:200]
            content = f"[{parsed['timestamp_label']}] {parsed['label']} — {parsed['summary']}"
            try:
                saved = vault.remember(
                    topic=f"video:{slug}",
                    content=content,
                    tags=tag_str,
                    importance=1.5,
                )
                parsed["fact_id"] = saved.get("id")
            except Exception:
                pass
        scenes.append(parsed)

    if save_to_vault and vault is not None:
        try:
            vault.record_energy_event(
                event_type="cloud_video_analyze",
                vram_saved_mb=6500.0,
                calls_skipped=int(gated["frames_skipped"]),
                offloaded_calls=int(gated["frames_offloaded"]),
                details=f"video={clean_name};model={model_used};skipped={gated['frames_skipped']}/{gated['frames_total']}",
            )
        except Exception:
            pass

    ledger_event_id: Optional[str] = None
    if ledger is not None:
        try:
            evt = ledger.append({
                "event": "cloud_video_analyze",
                "video_name": clean_name,
                "provider": provider_used or "AMD Token Lab",
                "model": model_used or target.split(":", 1)[-1],
                "frames_total": int(gated["frames_total"]),
                "frames_offloaded": int(gated["frames_offloaded"]),
                "frames_skipped": int(gated["frames_skipped"]),
                "frames_skipped_pct": float(gated["frames_skipped_pct"]),
                "est_cost_usd": 0.0,
                "local_vram_mb": 0,
            })
            ledger_event_id = evt.get("event_id")
        except Exception:
            ledger_event_id = None

    total_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
    return {
        "ok": True,
        "video_name": clean_name,
        "provider": provider_used or "AMD Token Lab",
        "model": model_used or target.split(":", 1)[-1],
        "local_vram_mb": 0,
        "frames_total": gated["frames_total"],
        "frames_offloaded": gated["frames_offloaded"],
        "frames_skipped": gated["frames_skipped"],
        "frames_skipped_pct": gated["frames_skipped_pct"],
        "gate_ms": gated["gate_ms"],
        "total_ms": total_ms,
        "scenes": scenes,
        "saved_to_vault": bool(save_to_vault and vault is not None),
        "ledger_event_id": ledger_event_id,
    }


def search_video_scenes(
    vault: Any,
    query: str = "",
    video_name: str = "",
    limit: int = 40,
) -> List[Dict[str, Any]]:
    """Query indexed video scene markers stored in MemoryVault."""
    if vault is None:
        return []
    cap = max(1, min(200, int(limit or 40)))
    q_terms = [tok.lower() for tok in re.split(r"\s+", str(query or "").strip()) if len(tok) >= 2]
    vid_filter = _slugify_video_name(video_name) if str(video_name or "").strip() else ""

    rows = vault.list_facts(limit=200)
    matches: List[Dict[str, Any]] = []
    for row in rows:
        topic = str(row.get("topic") or "")
        tags = str(row.get("tags") or "")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if "video_scene" not in tag_list and not topic.startswith("video:"):
            continue
        vid_slug = topic[len("video:"):] if topic.startswith("video:") else (tag_list[1] if len(tag_list) > 1 else "clip")
        if vid_filter and vid_filter not in vid_slug and vid_filter not in tags.lower():
            continue

        content = str(row.get("content") or "").strip()
        hay = f"{topic} {tags} {content}".lower()
        if q_terms and not all(term in hay for term in q_terms):
            continue

        ts_label = "00:00"
        rest = content
        ts_m = _SCENE_CONTENT_TS_RE.match(content)
        if ts_m:
            ts_label = ts_m.group(1)
            rest = ts_m.group(2).strip()

        if " — " in rest:
            label, summary = rest.split(" — ", 1)
        elif " - " in rest:
            label, summary = rest.split(" - ", 1)
        else:
            label, summary = rest[:64], rest

        matches.append({
            "id": row.get("id"),
            "video_slug": vid_slug,
            "timestamp_label": ts_label,
            "timestamp_s": _parse_timestamp_label(ts_label),
            "label": label.strip(),
            "summary": summary.strip(),
            "tags": [t for t in tag_list if t != "video_scene"],
            "created_at": row.get("created_at"),
        })
        if len(matches) >= cap:
            break
    return matches


def validate_omni_video_params(
    prompt: str,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration: Any = 10,
    first_frame_data_uri: Optional[str] = None,
    last_frame_data_uri: Optional[str] = None,
    reference_images: Optional[Sequence[str]] = None,
    previous_interaction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate Gemini Omni 1.2 Flash request parameters strictly before API dispatch."""
    clean_prompt = str(prompt or "").strip()
    if not clean_prompt:
        raise ValueError("Video generation prompt cannot be empty.")

    aspect = str(aspect_ratio or "16:9").strip()
    if aspect not in VALID_OMNI_ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect_ratio '{aspect}'. Expected one of {sorted(VALID_OMNI_ASPECT_RATIOS)}.")

    res = str(resolution or "720p").strip().lower()
    if res not in VALID_OMNI_RESOLUTIONS:
        raise ValueError(f"Unsupported resolution '{res}'. Expected one of {sorted(VALID_OMNI_RESOLUTIONS)}.")

    if duration is None or str(duration).strip().lower() in ("", "none"):
        dur_int = 10
    else:
        raw_dur = str(duration).strip().lower()
        if raw_dur.endswith("s"):
            raw_dur = raw_dur[:-1]
        try:
            dur_f = float(raw_dur)
        except ValueError as exc:
            raise ValueError(f"Invalid duration '{duration}': expected integer seconds (3..15).") from exc
        if not dur_f.is_integer():
            raise ValueError(f"Duration must be an integer number of seconds (got {duration}).")
        dur_int = int(dur_f)

    if dur_int < MIN_OMNI_DURATION_S or dur_int > MAX_OMNI_DURATION_S:
        raise ValueError(
            f"Duration must be between {MIN_OMNI_DURATION_S} and {MAX_OMNI_DURATION_S} seconds (got {dur_int})."
        )

    has_first = bool(first_frame_data_uri and str(first_frame_data_uri).strip())
    has_last = bool(last_frame_data_uri and str(last_frame_data_uri).strip())
    if has_last and not has_first:
        raise ValueError("last_frame requires first_frame as the starting keyframe.")

    prev_id = str(previous_interaction_id or "").strip() or None
    if dur_int > MAX_OMNI_TWO_FRAME_OR_EXTEND_S:
        if has_first and has_last:
            raise ValueError(
                f"First-and-last-frame transitions support {MIN_OMNI_DURATION_S}-{MAX_OMNI_TWO_FRAME_OR_EXTEND_S}s max (got {dur_int}s)."
            )
        if prev_id:
            raise ValueError(
                f"Video extensions/edits via previous_interaction_id support {MIN_OMNI_DURATION_S}-{MAX_OMNI_TWO_FRAME_OR_EXTEND_S}s max per turn (got {dur_int}s)."
            )

    refs = [str(r).strip() for r in (reference_images or []) if str(r or "").strip()]
    if len(refs) > MAX_OMNI_REFERENCE_IMAGES:
        raise ValueError(f"Up to {MAX_OMNI_REFERENCE_IMAGES} reference images are supported (got {len(refs)}).")

    return {
        "prompt": clean_prompt,
        "aspect_ratio": aspect,
        "resolution": res,
        "duration_s": dur_int,
        "first_frame": str(first_frame_data_uri).strip() if has_first else None,
        "last_frame": str(last_frame_data_uri).strip() if has_last else None,
        "reference_images": refs,
        "previous_interaction_id": prev_id,
    }


def _append_role_sentence(prompt_text: str, sentence: str) -> str:
    clean = prompt_text.strip()
    if not clean:
        return sentence
    sep = "" if clean[-1] in ".!?" else "."
    return f"{clean}{sep} {sentence}"


def _build_omni_image_block(img_str: str) -> Dict[str, Any]:
    parsed = _parse_image_data_uri(img_str)
    if parsed:
        return {"type": "image", "mime_type": parsed[0], "data": parsed[1]}
    if img_str.lower().startswith("https://"):
        return {"type": "image", "uri": img_str}
    raise ValueError("Reference image must be a base64 image data URI or public https:// URL.")


def _extract_omni_video_output(resp: Dict[str, Any]) -> Dict[str, Any]:
    out_vid = resp.get("output_video")
    if isinstance(out_vid, dict) and (out_vid.get("uri") or out_vid.get("data")):
        return out_vid
    for step in reversed(resp.get("steps") or []):
        if isinstance(step, dict) and step.get("type") == "model_output":
            for block in step.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "video" and (block.get("uri") or block.get("data")):
                    return block
    outputs = resp.get("outputs")
    if isinstance(outputs, list):
        for block in outputs:
            if isinstance(block, dict) and block.get("type") == "video" and (block.get("uri") or block.get("data")):
                return block
    return {}


def _download_omni_file_bytes(
    file_uri: str,
    api_key: str,
    base_url: str,
    poll_interval_s: float = 4.0,
    timeout: float = 600.0,
) -> bytes:
    """Poll Gemini Files API until ACTIVE, then download raw .mp4 bytes via x-goog-api-key header."""
    m = re.search(r"files/([A-Za-z0-9_-]+)", str(file_uri or ""))
    if not m:
        raise RuntimeError(f"Unrecognized Gemini Files URI in video response: {sanitize_video_error(file_uri)}")
    file_id = m.group(1)
    api_base = base_url.rstrip("/")
    headers = {"x-goog-api-key": api_key, "User-Agent": "MemoryOS-CloudVideo/1.0"}

    deadline = time.monotonic() + max(5.0, float(timeout or 600.0))
    while True:
        status_obj = _http_json_request(
            f"{api_base}/files/{file_id}",
            headers=headers,
            payload=None,
            method="GET",
            timeout=30.0,
        )
        state = str(status_obj.get("state") or "").upper()
        if state == "ACTIVE" or not state:
            break
        if state == "FAILED":
            err_msg = status_obj.get("error") or "Cloud video file processing failed."
            raise RuntimeError(f"Gemini Omni video failed: {sanitize_video_error(err_msg)}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Gemini Omni file '{file_id}' to become ACTIVE.")
        time.sleep(max(0.01, float(poll_interval_s)))

    dl_url = f"{api_base}/files/{file_id}:download?alt=media"
    req = urllib.request.Request(dl_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=max(30.0, float(timeout or 600.0))) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            err_body = ""
        finally:
            try:
                exc.close()
            except Exception:
                pass
        raise RuntimeError(f"Video download HTTP {exc.code}: {sanitize_video_error(err_body or exc.reason)}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Video download network error: {sanitize_video_error(exc.reason)}") from exc


def _download_public_https_bytes(url: str, timeout: float = 120.0) -> bytes:
    """Download video asset bytes strictly from a validated public https:// URL without auth headers."""
    if not _is_safe_public_https_url(url):
        raise ValueError(f"Blocked unsafe or non-HTTPS video URL: {sanitize_video_error(url)}")
    req = urllib.request.Request(url, headers={"User-Agent": "MemoryOS-CloudVideo/1.0"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=max(30.0, float(timeout or 120.0))) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            err_body = ""
        finally:
            try:
                exc.close()
            except Exception:
                pass
        raise RuntimeError(f"Video download HTTP {exc.code}: {sanitize_video_error(err_body or exc.reason)}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Video download network error: {sanitize_video_error(exc.reason)}") from exc


def _generate_video_gemini(
    model_id: str,
    params: Dict[str, Any],
    poll_interval_s: float = 4.0,
    timeout: float = 600.0,
) -> Tuple[bytes, Optional[str], str]:
    api_key, _ = _get_gemini_credentials()
    if not _is_configured_key(api_key, "AIza-your-gemini-key-here", "your-gemini-api-key-here"):
        raise RuntimeError(
            "GEMINI_API_KEY is not configured in .env. Add GEMINI_API_KEY=... and restart Jupiter Studio "
            "to generate cloud videos with Gemini Omni 1.2 Flash (0 MB local VRAM)."
        )

    base_url = (
        os.getenv("GEMINI_VIDEO_BASE_URL", "").strip().rstrip("/")
        or DEFAULT_OMNI_BASE_URL
    )
    final_prompt = params["prompt"]
    lower_p = final_prompt.lower()
    if params["first_frame"] and params["last_frame"]:
        if "starting frame" not in lower_p and "first frame" not in lower_p:
            final_prompt = _append_role_sentence(
                final_prompt,
                "Use the first image as the starting frame and the second image as the final frame.",
            )
    elif params["first_frame"]:
        if "starting frame" not in lower_p and "first frame" not in lower_p:
            ref_phrase = "the first image" if params["reference_images"] else "this image"
            final_prompt = _append_role_sentence(final_prompt, f"Use {ref_phrase} as the starting frame.")

    input_blocks: List[Dict[str, Any]] = []
    if params["first_frame"]:
        input_blocks.append(_build_omni_image_block(params["first_frame"]))
    if params["last_frame"]:
        input_blocks.append(_build_omni_image_block(params["last_frame"]))
    for ref_img in params["reference_images"]:
        input_blocks.append(_build_omni_image_block(ref_img))

    if input_blocks:
        input_blocks.append({"type": "text", "text": final_prompt})
        request_input: Any = input_blocks
    else:
        request_input = final_prompt

    req_payload: Dict[str, Any] = {
        "model": model_id or DEFAULT_OMNI_VIDEO_MODEL,
        "input": request_input,
        "response_format": {
            "type": "video",
            "delivery": "uri",
            "aspect_ratio": params["aspect_ratio"],
            "duration": f"{params['duration_s']}s",
            "resolution": params["resolution"],
        },
    }
    if params["previous_interaction_id"]:
        req_payload["previous_interaction_id"] = params["previous_interaction_id"]

    resp = _http_json_request(
        f"{base_url}/interactions",
        headers={"x-goog-api-key": api_key, "User-Agent": "MemoryOS-CloudVideo/1.0"},
        payload=req_payload,
        method="POST",
        timeout=max(30.0, float(timeout or 600.0)),
    )

    video_block = _extract_omni_video_output(resp)
    if not video_block:
        note = ""
        if params["previous_interaction_id"]:
            note = " Note: video-upload edits/extensions are restricted in the UK, EEA, and Switzerland."
        raise RuntimeError(f"Gemini Omni 1.2 Flash returned no video content.{note}")

    if video_block.get("data"):
        video_bytes = base64.b64decode(str(video_block["data"]))
    elif video_block.get("uri"):
        video_bytes = _download_omni_file_bytes(
            file_uri=str(video_block["uri"]),
            api_key=api_key,
            base_url=base_url,
            poll_interval_s=poll_interval_s,
            timeout=timeout,
        )
    else:
        raise RuntimeError("Gemini Omni response contained neither video data nor a download URI.")

    interaction_id = str(resp.get("id") or "").strip() or None
    return video_bytes, interaction_id, "omni"


def _extract_fal_video_url(resp: Dict[str, Any]) -> str:
    if not isinstance(resp, dict):
        return ""
    for candidate in (
        resp.get("video"),
        (resp.get("data") or {}).get("video") if isinstance(resp.get("data"), dict) else None,
        resp.get("output"),
    ):
        if isinstance(candidate, dict) and candidate.get("url"):
            return str(candidate["url"]).strip()
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    if resp.get("video_url"):
        return str(resp["video_url"]).strip()
    if resp.get("url"):
        return str(resp["url"]).strip()
    return ""


def _generate_video_fal(
    model_id: str,
    params: Dict[str, Any],
    poll_interval_s: float = 3.0,
    timeout: float = 600.0,
) -> Tuple[bytes, Optional[str], str]:
    fal_key, fal_base = _get_fal_credentials()
    if not _is_configured_key(fal_key, "fal-your-key-here", "your-fal-key-here"):
        raise RuntimeError(
            "FAL_KEY is not configured in .env. Add FAL_KEY=your_fal_key to .env and restart Jupiter Studio "
            "to generate cloud videos on fal.ai (0 MB local VRAM)."
        )
    clean_model = str(model_id or "").strip().strip("/")
    if not re.match(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+$", clean_model) or ".." in clean_model:
        raise ValueError(f"Invalid fal.ai model path '{clean_model}'.")

    submit_url = f"{fal_base}/{clean_model}"
    if not _is_safe_public_https_url(submit_url):
        raise ValueError(f"Blocked unsafe fal.ai endpoint URL: {sanitize_video_error(submit_url)}")

    headers = {"Authorization": f"Key {fal_key}", "User-Agent": "MemoryOS-CloudVideo/1.0"}
    payload: Dict[str, Any] = {
        "prompt": params["prompt"],
        "aspect_ratio": params["aspect_ratio"],
        "duration": str(params["duration_s"]),
        "resolution": params["resolution"],
    }
    if params["first_frame"]:
        payload["image_url"] = params["first_frame"]
    if params["last_frame"]:
        payload["end_image_url"] = params["last_frame"]

    sub = _http_json_request(submit_url, headers=headers, payload=payload, method="POST", timeout=45.0)
    req_id = str(sub.get("request_id") or "").strip() or None
    immediate_url = _extract_fal_video_url(sub)
    if immediate_url and str(sub.get("status") or "").upper() in ("", "COMPLETED"):
        return _download_public_https_bytes(immediate_url, timeout=timeout), req_id, "fal"

    status_url = str(sub.get("status_url") or "").strip()
    response_url = str(sub.get("response_url") or "").strip()
    if req_id:
        if not status_url:
            status_url = f"{fal_base}/{clean_model}/requests/{req_id}/status"
        if not response_url:
            response_url = f"{fal_base}/{clean_model}/requests/{req_id}"

    if not status_url or not response_url:
        raise RuntimeError("fal.ai queue response did not include status_url/response_url.")
    if not _is_safe_public_https_url(status_url) or not _is_safe_public_https_url(response_url):
        raise ValueError("Blocked unsafe or non-HTTPS URL returned by fal.ai queue.")

    deadline = time.monotonic() + max(5.0, float(timeout or 600.0))
    while True:
        st_obj = _http_json_request(status_url, headers=headers, payload=None, method="GET", timeout=30.0)
        st = str(st_obj.get("status") or "").upper()
        if st == "COMPLETED":
            break
        if st in ("FAILED", "CANCELLED", "ERROR"):
            err_detail = st_obj.get("error") or st_obj.get("logs") or "fal.ai video generation failed."
            raise RuntimeError(f"fal.ai job failed: {sanitize_video_error(err_detail)}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for fal.ai request '{req_id or clean_model}'.")
        time.sleep(max(0.01, float(poll_interval_s)))

    res_obj = _http_json_request(response_url, headers=headers, payload=None, method="GET", timeout=45.0)
    video_url = _extract_fal_video_url(res_obj)
    if not video_url:
        raise RuntimeError("fal.ai completed job contained no downloadable video URL.")
    return _download_public_https_bytes(video_url, timeout=timeout), req_id, "fal"


def _extract_replicate_video_url(output: Any) -> str:
    if isinstance(output, str):
        return output.strip()
    if isinstance(output, list):
        for item in output:
            found = _extract_replicate_video_url(item)
            if found:
                return found
    if isinstance(output, dict):
        for key in ("video", "url", "mp4"):
            val = output.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ""


def _generate_video_replicate(
    model_id: str,
    params: Dict[str, Any],
    poll_interval_s: float = 3.0,
    timeout: float = 600.0,
) -> Tuple[bytes, Optional[str], str]:
    rep_token, rep_base = _get_replicate_credentials()
    if not _is_configured_key(rep_token, "r8_your-replicate-token-here", "your-replicate-token-here"):
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured in .env. Add REPLICATE_API_TOKEN=your_token to .env "
            "and restart Jupiter Studio to generate cloud videos on Replicate (0 MB local VRAM)."
        )
    clean_model = str(model_id or "").strip().strip("/")
    if not re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", clean_model) or ".." in clean_model:
        raise ValueError(f"Invalid Replicate model slug '{clean_model}'. Expected owner/name.")

    submit_url = f"{rep_base}/models/{clean_model}/predictions"
    if not _is_safe_public_https_url(submit_url):
        raise ValueError(f"Blocked unsafe Replicate endpoint URL: {sanitize_video_error(submit_url)}")

    headers = {
        "Authorization": f"Bearer {rep_token}",
        "Prefer": "wait=60",
        "User-Agent": "MemoryOS-CloudVideo/1.0",
    }
    input_obj: Dict[str, Any] = {
        "prompt": params["prompt"],
        "aspect_ratio": params["aspect_ratio"],
        "duration": params["duration_s"],
        "resolution": params["resolution"],
    }
    if params["first_frame"]:
        input_obj["image"] = params["first_frame"]

    pred = _http_json_request(submit_url, headers=headers, payload={"input": input_obj}, method="POST", timeout=90.0)
    pred_id = str(pred.get("id") or "").strip() or None
    poll_headers = {"Authorization": f"Bearer {rep_token}", "User-Agent": "MemoryOS-CloudVideo/1.0"}

    deadline = time.monotonic() + max(5.0, float(timeout or 600.0))
    while True:
        status = str(pred.get("status") or "").lower()
        if status == "succeeded" or (pred.get("output") is not None and status not in ("starting", "processing", "queued")):
            break
        if status in ("failed", "canceled"):
            raise RuntimeError(f"Replicate job failed: {sanitize_video_error(pred.get('error') or status)}")
        urls = pred.get("urls") if isinstance(pred.get("urls"), dict) else {}
        poll_url = str(urls.get("get") or (f"{rep_base}/predictions/{pred_id}" if pred_id else "")).strip()
        if not poll_url:
            raise RuntimeError("Replicate response contained no polling URL.")
        if not _is_safe_public_https_url(poll_url):
            raise ValueError("Blocked unsafe or non-HTTPS Replicate polling URL.")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out waiting for Replicate prediction '{pred_id or clean_model}'.")
        time.sleep(max(0.01, float(poll_interval_s)))
        pred = _http_json_request(poll_url, headers=poll_headers, payload=None, method="GET", timeout=30.0)

    video_url = _extract_replicate_video_url(pred.get("output"))
    if not video_url:
        raise RuntimeError("Replicate prediction succeeded without a downloadable video URL.")
    return _download_public_https_bytes(video_url, timeout=timeout), pred_id, "rep"


def _generate_video_hf(
    model_id: str,
    params: Dict[str, Any],
    timeout: float,
) -> Tuple[bytes, Optional[str], str]:
    """Execute open-weight text-to-video via Hugging Face Inference Router."""
    hf_token, hf_base = _get_hf_video_credentials()
    if not _is_configured_key(hf_token, "hf_your-token-here", "your-huggingface-token-here"):
        raise RuntimeError(
            "Hugging Face token is not configured in .env (set HF_TOKEN to generate open-weight video)."
        )
    clean_model = model_id.strip("/")
    if not re.match(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$", clean_model):
        raise ValueError(f"Invalid Hugging Face video model identifier '{model_id}'.")

    submit_url = f"{hf_base}/{clean_model}"
    payload = json.dumps({
        "inputs": params["prompt"],
        "parameters": {
            "num_inference_steps": 25,
            "guidance_scale": 5.0,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        submit_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json",
            "User-Agent": "MemoryOS-CloudVideo/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(10.0, float(timeout or 300.0))) as resp:
            ctype = str(resp.headers.get("Content-Type") or "").lower()
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:320]
        except Exception:
            pass
        finally:
            try:
                exc.close()
            except Exception:
                pass
        if exc.code == 402:
            raise RuntimeError(
                "HTTP 402: Hugging Face Inference Providers has $0.00 credits on free tier (no card charged)."
            ) from exc
        raise RuntimeError(f"HTTP {exc.code}: {sanitize_video_error(detail or exc.reason)}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {sanitize_video_error(exc.reason)}") from exc

    if "application/json" in ctype or raw[:1] == b"{":
        doc = json.loads(raw.decode("utf-8", errors="replace"))
        vid_url = _extract_replicate_video_url(doc.get("video") or doc.get("url") or doc.get("output"))
        if not vid_url:
            raise RuntimeError(f"Hugging Face Router returned JSON without video URL: {sanitize_video_error(doc)}")
        return _download_public_https_bytes(vid_url, timeout=timeout), f"hf_{uuid.uuid4().hex[:8]}", "hf"

    return raw, f"hf_{uuid.uuid4().hex[:8]}", "hf"


def generate_video_cloud(
    prompt: str,
    model: str = DEFAULT_OMNI_VIDEO_MODEL,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration: Any = 10,
    first_frame_data_uri: Optional[str] = None,
    last_frame_data_uri: Optional[str] = None,
    reference_images: Optional[Sequence[str]] = None,
    previous_interaction_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
    vault: Any = None,
    poll_interval_s: float = 4.0,
    timeout: float = 600.0,
    target: Optional[str] = None,
    max_budget_usd: Optional[float] = None,
    rate_override: Optional[float] = None,
    ledger: Any = None,
) -> Dict[str, Any]:
    """Generate/edit/extend a cloud video with pre-flight cost estimate & hard spend cap (0 MB local VRAM)."""
    t0 = time.perf_counter()
    norm_target, provider_key, model_id = _resolve_generator_target(target=target, model=model)
    params = validate_omni_video_params(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        duration=duration,
        first_frame_data_uri=first_frame_data_uri,
        last_frame_data_uri=last_frame_data_uri,
        reference_images=reference_images,
        previous_interaction_id=previous_interaction_id,
    )

    estimate = estimate_video_generation_cost(
        target=norm_target,
        duration=params["duration_s"],
        resolution=params["resolution"],
        rate_override=rate_override,
        max_budget_usd=max_budget_usd,
    )
    if not estimate["within_budget"]:
        cap_val = float(estimate["max_budget_usd"] or 0.0)
        est_val = float(estimate["estimated_cost_usd"])
        raise VideoBudgetExceededError(
            f"Blocked before cloud dispatch: estimated ${est_val:.2f} USD exceeds hard spend cap ${cap_val:.2f} USD "
            f"({norm_target}, {params['duration_s']}s {params['resolution']}). Raise cap or switch to Draft preset.",
            estimated_cost_usd=est_val,
            max_budget_usd=cap_val,
        )

    if provider_key == "fal":
        video_bytes, interaction_id, file_prefix = _generate_video_fal(
            model_id=model_id,
            params=params,
            poll_interval_s=poll_interval_s,
            timeout=timeout,
        )
        provider_label = "fal.ai Cloud"
    elif provider_key == "replicate":
        video_bytes, interaction_id, file_prefix = _generate_video_replicate(
            model_id=model_id,
            params=params,
            poll_interval_s=poll_interval_s,
            timeout=timeout,
        )
        provider_label = "Replicate Cloud"
    elif provider_key == "hf":
        video_bytes, interaction_id, file_prefix = _generate_video_hf(
            model_id=model_id,
            params=params,
            timeout=timeout,
        )
        provider_label = "Hugging Face Router"
    else:
        video_bytes, interaction_id, file_prefix = _generate_video_gemini(
            model_id=model_id,
            params=params,
            poll_interval_s=poll_interval_s,
            timeout=timeout,
        )
        provider_label = "Google Gemini Omni Cloud"

    if not video_bytes:
        raise RuntimeError("Downloaded video file was empty (0 bytes).")

    target_dir = Path(output_dir) if output_dir is not None else get_video_output_dir(create=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "_", params["prompt"].lower()).strip("_")[:36] or "clip"
    filename = f"{file_prefix}_{stamp}_{slug}_{uuid.uuid4().hex[:6]}.mp4"
    out_path = resolve_safe_video_path(filename, output_dir=target_dir)
    if out_path is None:
        raise RuntimeError("Failed to construct safe output video filename.")

    tmp_path = target_dir / f".{filename}.tmp"
    tmp_path.write_bytes(video_bytes)
    os.replace(tmp_path, out_path)

    est_cost = float(estimate["estimated_cost_usd"])
    rate_s = float(estimate["rate_per_sec_usd"])

    if vault is not None:
        try:
            vault.record_energy_event(
                event_type="cloud_video_generate",
                vram_saved_mb=8192.0,
                calls_skipped=0,
                offloaded_calls=1,
                details=f"target={norm_target};file={filename};bytes={len(video_bytes)};est_usd={est_cost:.4f}",
            )
            vault.remember(
                topic=f"video_gen:{slug[:32]}",
                content=(
                    f"Generated cloud clip '{filename}' via {model_id} ({params['duration_s']}s {params['resolution']} "
                    f"{params['aspect_ratio']}, ~${est_cost:.2f} USD) from prompt: {params['prompt'][:200]}"
                    + (f" [interaction_id={interaction_id}]" if interaction_id else "")
                ),
                tags=f"video_gen,{provider_key},{params['resolution']},{params['aspect_ratio']}",
                importance=1.2,
            )
        except Exception:
            pass

    ledger_event_id: Optional[str] = None
    if ledger is not None:
        try:
            evt = ledger.append({
                "event": "cloud_video_generate",
                "filename": filename,
                "target": norm_target,
                "provider": provider_label,
                "model": model_id,
                "duration_s": params["duration_s"],
                "resolution": params["resolution"],
                "aspect_ratio": params["aspect_ratio"],
                "rate_per_sec_usd": rate_s,
                "est_cost_usd": est_cost,
                "interaction_id": interaction_id,
                "local_vram_mb": 0,
            })
            ledger_event_id = evt.get("event_id")
        except Exception:
            ledger_event_id = None

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "ok": True,
        "filename": filename,
        "video_url": f"/api/video/outputs/{urllib.parse.quote(filename)}",
        "path": str(out_path),
        "size_bytes": len(video_bytes),
        "interaction_id": interaction_id,
        "target": norm_target,
        "model": model_id,
        "provider": provider_label,
        "aspect_ratio": params["aspect_ratio"],
        "duration_s": params["duration_s"],
        "resolution": params["resolution"],
        "rate_per_sec_usd": rate_s,
        "estimated_cost_usd": est_cost,
        "ledger_event_id": ledger_event_id,
        "local_vram_mb": 0,
        "elapsed_ms": elapsed_ms,
    }


def get_video_spend_ledger(db_path: Path, limit: int = 40) -> Dict[str, Any]:
    """Read SHA-256 hash-chained video spend and CPU-gate savings entries."""
    db_file = Path(db_path)
    empty_summary = {
        "total_est_spend_usd": 0.0,
        "total_generated_seconds": 0,
        "total_generated_clips": 0,
        "total_analyzed_clips": 0,
        "total_frames_skipped": 0,
    }
    if not db_file.is_file():
        return {"ledger_valid": True, "event_count": 0, "entries": [], "summary": empty_summary}

    cap = max(1, min(200, int(limit or 40)))
    verification = ImmutableLedger(db_file).verify()

    rows: List[sqlite3.Row] = []
    conn = sqlite3.connect(str(db_file), timeout=5.0)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT seq, event_id, created_at, payload_json, event_hash "
            "FROM control_plane_ledger ORDER BY seq DESC LIMIT 500"
        ).fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        conn.close()

    entries: List[Dict[str, Any]] = []
    total_spend = 0.0
    total_gen_s = 0
    total_gen_clips = 0
    total_an_clips = 0
    total_skipped = 0

    for row in rows:
        try:
            payload = json.loads(str(row["payload_json"]))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        ev_type = str(payload.get("event") or "")
        if ev_type not in ("cloud_video_generate", "cloud_video_analyze"):
            continue

        if ev_type == "cloud_video_generate":
            total_gen_clips += 1
            total_gen_s += int(payload.get("duration_s") or 0)
            total_spend += float(payload.get("est_cost_usd") or 0.0)
        else:
            total_an_clips += 1
            total_skipped += int(payload.get("frames_skipped") or 0)

        if len(entries) < cap:
            entries.append({
                "seq": int(row["seq"]),
                "event_id": str(row["event_id"]),
                "created_at": str(row["created_at"]),
                "event": ev_type,
                "event_hash": str(row["event_hash"])[:16],
                "provider": payload.get("provider", ""),
                "model": payload.get("model", ""),
                "target": payload.get("target", ""),
                "filename": payload.get("filename") or payload.get("video_name") or "",
                "duration_s": payload.get("duration_s"),
                "resolution": payload.get("resolution"),
                "est_cost_usd": round(float(payload.get("est_cost_usd") or 0.0), 4),
                "frames_skipped": payload.get("frames_skipped"),
                "frames_total": payload.get("frames_total"),
                "local_vram_mb": int(payload.get("local_vram_mb") or 0),
            })

    return {
        "ledger_valid": bool(verification.get("valid", True)),
        "event_count": int(verification.get("event_count", 0)),
        "entries": entries,
        "summary": {
            "total_est_spend_usd": round(total_spend, 4),
            "total_generated_seconds": total_gen_s,
            "total_generated_clips": total_gen_clips,
            "total_analyzed_clips": total_an_clips,
            "total_frames_skipped": total_skipped,
        },
    }


def get_cloud_video_status() -> Dict[str, Any]:
    """Return live readiness status for both cloud video workflows without hitting external APIs."""
    cloud = get_cloud_provider_status()
    tl_ready = bool(cloud.get("amd_tokenlab", {}).get("configured"))
    gem_ready = bool(cloud.get("gemini", {}).get("configured"))
    oai_ready = bool(cloud.get("openai", {}).get("configured"))
    hf_ready = _is_generator_provider_configured("hf")
    fal_ready = _is_generator_provider_configured("fal")
    rep_ready = _is_generator_provider_configured("replicate")

    gen_providers = {
        "gemini": gem_ready,
        "fal": fal_ready,
        "replicate": rep_ready,
        "hf": hf_ready,
    }

    targets: List[Dict[str, Any]] = []
    for entry in SUPPORTED_ANALYZE_TARGETS:
        prov_key = entry["provider"]
        is_rdy = True if prov_key == "ollama" else bool(cloud.get(prov_key, {}).get("configured"))
        targets.append({
            **entry,
            "ready": is_rdy,
        })

    catalog: List[Dict[str, Any]] = []
    for entry in VIDEO_GENERATOR_CATALOG:
        catalog.append({
            **entry,
            "ready": bool(gen_providers.get(entry["provider"])),
        })

    out_dir = get_video_output_dir(create=True)
    return {
        "local_vram_mb": 0,
        "analyzer": {
            "ready": tl_ready or gem_ready or oai_ready,
            "default_target": DEFAULT_VIDEO_ANALYZE_TARGET if tl_ready else ("gemini:gemini-3.8-flash" if gem_ready else DEFAULT_VIDEO_ANALYZE_TARGET),
            "targets": targets,
            "providers": {
                "amd_tokenlab": tl_ready,
                "gemini": gem_ready,
                "openai": oai_ready,
            },
        },
        "generator": {
            "ready": any(gen_providers.values()),
            "model": DEFAULT_OMNI_VIDEO_MODEL,
            "providers": gen_providers,
            "catalog": catalog,
            "setup_hint": "Add GEMINI_API_KEY, FAL_KEY, or REPLICATE_API_TOKEN to .env and restart Jupiter Studio to generate cloud videos (0 MB local VRAM).",
            "output_dir": str(out_dir),
            "uk_eea_note": "Text-to-video and image-to-video run in cloud (0 MB VRAM); uploading source videos for video-to-video edits/extensions is restricted in the UK, EEA, and Switzerland.",
        },
    }
