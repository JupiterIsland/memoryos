"""Hugging Face Open-Weight Model Hub, 8GB Hardware-Fit Advisor & Local GGUF Bridge.

Pure Python 3.11+ stdlib integration with https://huggingface.co/models built for
MemoryOS // Jupiter Studio's Glass Box $0.00 zero-spend architecture:
1. Public Hub Search (https://huggingface.co/api/models — 100% $0.00, no billing):
   - Live search & task filtering across text-generation, GGUF, image-text-to-text,
     text-to-video, image-to-video, and text-to-speech models.
   - Automatic VRAM/RAM Hardware-Fit calculation calibrated for an 8 GB RTX 3070
     Laptop GPU + 16 GB system RAM ceiling.
2. Local Hugging Face Disk Cache Discovery ($0.00 already on disk):
   - Scans ~/.cache/huggingface/hub, HF_HOME, and I:\\voice-models\\hf to surface
     open-weight GGUF & safetensors repos already downloaded locally.
3. Account Zero-Spend Safety Inspector (whoami-v2):
   - Verifies whether the Hugging Face account has any payment method attached
     (canPay == False -> $0.00 hard ceiling guaranteed by upstream + local lock).
4. Loopback-Only Ollama GGUF Bridge (ollama pull hf.co/<org>/<repo> — $0.00 local):
   - Pulls any validated GGUF repository from huggingface.co/models into the local
     Ollama daemon (127.0.0.1:11434) with strict SSRF and repo-id validation.
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from src.memoryos.router import _is_configured_key
except ImportError:
    from memoryos.router import _is_configured_key

DEFAULT_HF_HUB_API_URL = "https://huggingface.co/api"
DEFAULT_HF_ROUTER_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_LOCAL_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_VOICE_HF_CACHE_WIN = Path("I:/voice-models/hf")

# Strict Hugging Face repo_id validation: org/model or org/model:quant
_SAFE_HF_REPO_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}/[A-Za-z0-9][A-Za-z0-9._-]{0,95}(?::[A-Za-z0-9._-]{1,40})?$"
)
_PARAM_SIZE_RE = re.compile(r"(?:^|[^A-Za-z0-9])(?:A)?(\d+(?:\.\d+)?)\s*[bB](?:[^A-Za-z0-9]|$)")

SUPPORTED_HF_TASKS: Tuple[Dict[str, str], ...] = (
    {"id": "8gb-gguf", "label": "8GB Local GGUF ($0.00)", "pipeline_tag": "", "gguf_only": "1"},
    {"id": "text-to-video", "label": "Text-to-Video (Open-Weight)", "pipeline_tag": "text-to-video", "gguf_only": "0"},
    {"id": "image-text-to-text", "label": "Vision / Video Frame VLM", "pipeline_tag": "image-text-to-text", "gguf_only": "0"},
    {"id": "text-generation", "label": "Coding & Reasoning LLMs", "pipeline_tag": "text-generation", "gguf_only": "0"},
    {"id": "text-to-speech", "label": "Voice & Audio TTS", "pipeline_tag": "text-to-speech", "gguf_only": "0"},
)

# Offline / degraded fallback catalog so UI stays usable without internet
FALLBACK_HF_MODELS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "unsloth/gemma-4-E2B-it-GGUF",
        "pipeline_tag": "image-text-to-text",
        "likes": 890,
        "downloads": 145000,
        "tags": ["gguf", "vision", "gemma4"],
        "params_total": 2_600_000_000,
        "live_providers": [],
    },
    {
        "id": "unsloth/Qwen3.5-4B-GGUF",
        "pipeline_tag": "text-generation",
        "likes": 740,
        "downloads": 210000,
        "tags": ["gguf", "qwen3", "coding"],
        "params_total": 4_000_000_000,
        "live_providers": [],
    },
    {
        "id": "prism-ml/Bonsai-4B-gguf",
        "pipeline_tag": "text-generation",
        "likes": 510,
        "downloads": 64000,
        "tags": ["gguf", "ternary", "low-vram"],
        "params_total": 4_000_000_000,
        "live_providers": [],
    },
    {
        "id": "Qwen/Qwen3.8-27B",
        "pipeline_tag": "image-text-to-text",
        "likes": 21700,
        "downloads": 6120000,
        "tags": ["safetensors", "vision", "multimodal"],
        "params_total": 27_781_427_952,
        "live_providers": ["deepinfra", "novita", "cerebras"],
    },
    {
        "id": "Wan-AI/Wan2.2-TI2V-5B",
        "pipeline_tag": "text-to-video",
        "likes": 1059,
        "downloads": 19961,
        "tags": ["diffusers", "text-to-video", "wan"],
        "params_total": 5_000_000_000,
        "live_providers": ["fal-ai", "wavespeed"],
    },
    {
        "id": "Wan-AI/Wan2.2-T2V-A14B",
        "pipeline_tag": "text-to-video",
        "likes": 641,
        "downloads": 5425,
        "tags": ["diffusers", "text-to-video", "moe"],
        "params_total": 14_000_000_000,
        "live_providers": ["fal-ai", "wavespeed"],
    },
)

_SEARCH_CACHE: Dict[Tuple[Any, ...], Tuple[float, Dict[str, Any]]] = {}
_WHOAMI_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_SEARCH_CACHE_TTL_S = 60.0
_WHOAMI_CACHE_TTL_S = 300.0


def get_hf_credentials() -> Tuple[str, str, str]:
    """Return (api_token, router_base_url, hub_api_url) from environment."""
    token = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or "").strip()
    router_url = os.getenv("HF_BASE_URL", DEFAULT_HF_ROUTER_BASE_URL).strip().rstrip("/")
    hub_url = os.getenv("HF_HUB_API_URL", DEFAULT_HF_HUB_API_URL).strip().rstrip("/")
    return token, router_url, hub_url


def is_hf_token_configured(token: Optional[str] = None) -> bool:
    raw = token if token is not None else get_hf_credentials()[0]
    return _is_configured_key(raw, "hf_your-token-here", "your-huggingface-token-here")


def sanitize_hf_error(err: Any) -> str:
    """Redact Hugging Face tokens and bearer credentials from any error text."""
    text = str(err or "").strip()
    if not text:
        return ""
    for env_name in ("HF_TOKEN", "HUGGINGFACE_API_KEY"):
        secret = os.getenv(env_name, "").strip()
        if secret and len(secret) >= 6:
            text = text.replace(secret, "[REDACTED_HF_TOKEN]")
    text = re.sub(r"\bhf_[A-Za-z0-9]{10,}\b", "[REDACTED_HF_TOKEN]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED_TOKEN]", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:397] + "..." if len(text) > 400 else text


def validate_safe_hf_repo_id(repo_id: str) -> str:
    """Validate Hugging Face <org>/<repo>[:quant] identifier; reject traversal or URLs."""
    cleaned = str(repo_id or "").strip()
    if cleaned.startswith("hf.co/"):
        cleaned = cleaned[len("hf.co/") :]
    if (
        not cleaned
        or ".." in cleaned
        or "//" in cleaned
        or "\\" in cleaned
        or "\x00" in cleaned
        or not _SAFE_HF_REPO_RE.match(cleaned)
    ):
        raise ValueError(f"Invalid Hugging Face repository id '{repo_id}'. Expected '<org>/<model>'.")
    return cleaned


def _infer_params_billions(
    repo_id: str,
    params_total: Optional[int] = None,
) -> Optional[float]:
    if isinstance(params_total, (int, float)) and params_total > 0:
        return round(float(params_total) / 1_000_000_000.0, 2)
    name = repo_id.split("/", 1)[-1]
    # Handle MoE patterns like 8x7B
    moe = re.search(r"(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[bB]", name)
    if moe:
        return round(float(moe.group(1)) * float(moe.group(2)) * 0.85, 2)
    matches = _PARAM_SIZE_RE.findall(name)
    if matches:
        try:
            return round(float(matches[-1]), 2)
        except ValueError:
            return None
    return None


def estimate_8gb_hardware_fit(
    repo_id: str,
    params_total: Optional[int] = None,
    tags: Optional[Sequence[str]] = None,
    pipeline_tag: str = "",
    vram_ceiling_gb: float = 8.0,
) -> Dict[str, Any]:
    """Estimate local VRAM fit against an 8 GB RTX 3070 + 16 GB RAM workstation."""
    tag_set = {str(t).lower() for t in (tags or ())}
    pipe = str(pipeline_tag or "").lower()
    lower_id = repo_id.lower()
    is_gguf = "gguf" in tag_set or lower_id.endswith("-gguf") or ".gguf" in lower_id
    is_video = pipe in {"text-to-video", "image-to-video", "video-text-to-text"} or "text-to-video" in tag_set

    params_b = _infer_params_billions(repo_id, params_total=params_total)

    if is_video:
        # Diffusion video transformers need heavier activation + VAE memory than LLM Q4 weights
        eff_b = params_b if params_b is not None else 5.0
        est_vram = round(eff_b * 1.65 + 2.2, 1)
        if est_vram <= vram_ceiling_gb - 0.5:
            tier = "fits_8gb_local"
            label = f"FITS 8GB DIFFUSION (~{est_vram} GB · $0 LOCAL)"
        elif est_vram <= 13.5:
            tier = "hybrid_cpu_gpu"
            label = f"CPU+GPU OFFLOAD (~{est_vram} GB · SLOW ON 8GB)"
        else:
            tier = "cloud_offload_only"
            label = f"CLOUD OFFLOAD ONLY (~{est_vram} GB · 0 MB LOCAL)"
        return {
            "params_b": params_b,
            "is_gguf": is_gguf,
            "est_q4_vram_gb": est_vram,
            "est_fp16_vram_gb": round(eff_b * 2.2 + 2.5, 1),
            "tier": tier,
            "label": label,
            "fits_8gb_vram": tier == "fits_8gb_local",
            "zero_cost_local_ready": False,
        }

    if params_b is None:
        if is_gguf:
            return {
                "params_b": None,
                "is_gguf": True,
                "est_q4_vram_gb": None,
                "est_fp16_vram_gb": None,
                "tier": "fits_8gb_local",
                "label": "GGUF QUANTIZED · CHECK SIZE ($0 LOCAL)",
                "fits_8gb_vram": True,
                "zero_cost_local_ready": True,
            }
        return {
            "params_b": None,
            "is_gguf": False,
            "est_q4_vram_gb": None,
            "est_fp16_vram_gb": None,
            "tier": "cloud_offload_only",
            "label": "CLOUD / HUB WEIGHTS (INSPECT SIZE)",
            "fits_8gb_vram": False,
            "zero_cost_local_ready": False,
        }

    q4_gb = round(params_b * 0.62 + 0.75, 1)
    fp16_gb = round(params_b * 2.05 + 1.0, 1)

    if q4_gb <= (vram_ceiling_gb - 1.0):
        tier = "fits_8gb_local"
        label = f"FITS 8GB RTX ({q4_gb} GB Q4 · $0.00 LOCAL)"
    elif q4_gb <= 11.5:
        tier = "hybrid_cpu_gpu"
        label = f"TIGHT 8GB+RAM SPLIT ({q4_gb} GB Q4)"
    else:
        tier = "cloud_offload_only"
        label = f"CLOUD OFFLOAD ({q4_gb} GB Q4 · 0 MB LOCAL)"

    return {
        "params_b": params_b,
        "is_gguf": is_gguf,
        "est_q4_vram_gb": q4_gb,
        "est_fp16_vram_gb": fp16_gb,
        "tier": tier,
        "label": label,
        "fits_8gb_vram": tier == "fits_8gb_local",
        "zero_cost_local_ready": bool(is_gguf and tier in {"fits_8gb_local", "hybrid_cpu_gpu"}),
    }


def _candidate_hf_cache_dirs() -> List[Path]:
    dirs: List[Path] = []
    override = os.getenv("MEMORYOS_HF_CACHE_DIR", "").strip()
    if override:
        dirs.append(Path(override).expanduser())
        return dirs

    hf_home = os.getenv("HF_HOME", "").strip()
    if hf_home:
        dirs.append(Path(hf_home).expanduser())
    if os.name == "nt" and DEFAULT_VOICE_HF_CACHE_WIN.exists():
        dirs.append(DEFAULT_VOICE_HF_CACHE_WIN)
    default_hub = Path.home() / ".cache" / "huggingface" / "hub"
    dirs.append(default_hub)
    return dirs


def scan_local_hf_cache(cache_dirs: Optional[Sequence[Path]] = None) -> List[Dict[str, Any]]:
    """Discover Hugging Face models--<org>--<repo> folders already cached on local disk ($0.00)."""
    roots = list(cache_dirs) if cache_dirs is not None else _candidate_hf_cache_dirs()
    by_repo: Dict[str, Dict[str, Any]] = {}

    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        # Check both root directly and root/hub (since HF_HOME stores repos inside hub/)
        scan_targets = [root]
        hub_sub = root / "hub"
        if hub_sub.is_dir():
            scan_targets.append(hub_sub)

        for base in scan_targets:
            try:
                children = list(base.iterdir())
            except OSError:
                continue
            for entry in children:
                if not entry.is_dir() or not entry.name.startswith("models--"):
                    continue
                parts = entry.name.split("--")
                if len(parts) < 3:
                    continue
                org = parts[1].strip()
                repo = "--".join(parts[2:]).strip()
                if not org or not repo:
                    continue
                repo_id = f"{org}/{repo}"
                total_bytes = 0
                has_gguf = False
                has_safetensors = False
                gguf_files: List[str] = []
                seen_realpaths: set[Path] = set()
                try:
                    for fp in entry.rglob("*"):
                        fname_low = fp.name.lower()
                        if fname_low.endswith(".gguf"):
                            has_gguf = True
                            if fp.name not in gguf_files:
                                gguf_files.append(fp.name)
                        elif fname_low.endswith(".safetensors"):
                            has_safetensors = True
                        if fp.is_file():
                            try:
                                real_fp = fp.resolve()
                                if real_fp not in seen_realpaths:
                                    seen_realpaths.add(real_fp)
                                    total_bytes += real_fp.stat().st_size
                            except OSError:
                                pass
                except OSError:
                    pass

                # Skip empty metadata-only cache stubs (< 1 KB with no weight files)
                if total_bytes < 1024 and not has_gguf and not has_safetensors:
                    continue
                if "gguf" in repo.lower():
                    has_gguf = True

                size_mb = round(total_bytes / (1024.0 * 1024.0), 1)
                fit = estimate_8gb_hardware_fit(
                    repo_id=repo_id,
                    tags=["gguf"] if has_gguf else (["safetensors"] if has_safetensors else []),
                )
                prev = by_repo.get(repo_id)
                if prev is None or size_mb > prev["size_mb"]:
                    by_repo[repo_id] = {
                        "id": repo_id,
                        "cache_dir": str(base),
                        "size_mb": size_mb,
                        "is_gguf": has_gguf,
                        "has_safetensors": has_safetensors,
                        "gguf_files": gguf_files[:4],
                        "cost_usd": 0.0,
                        "ollama_target": f"ollama:hf.co/{repo_id}" if has_gguf else None,
                        "hf_router_target": f"hf:{repo_id}",
                        "hardware_fit": fit,
                    }

    return sorted(by_repo.values(), key=lambda x: (-float(x["size_mb"]), x["id"]))


def get_hf_account_safety(live_check: bool = True, timeout: float = 6.0) -> Dict[str, Any]:
    """Verify Hugging Face token presence and zero-billing card status via whoami-v2."""
    token, router_url, hub_url = get_hf_credentials()
    configured = is_hf_token_configured(token)
    zero_lock_env = os.getenv("MEMORYOS_VIDEO_MAX_JOB_USD", "").strip()
    zero_spend_locked = False
    if zero_lock_env != "":
        try:
            zero_spend_locked = float(zero_lock_env) <= 0.0
        except ValueError:
            zero_spend_locked = False

    base_info: Dict[str, Any] = {
        "token_configured": configured,
        "router_base_url": router_url,
        "hub_api_url": hub_url,
        "authenticated": False,
        "is_pro": False,
        "can_pay": False,
        "zero_spend_locked": zero_spend_locked,
        "guaranteed_zero_cost": True,
        "billing_summary": (
            "Public Hub mode ($0.00) — no HF_TOKEN configured."
            if not configured
            else "HF_TOKEN configured — verifying account billing lock..."
        ),
    }
    if not configured or not live_check:
        if configured and zero_spend_locked:
            base_info["billing_summary"] = "Protected by local MEMORYOS_VIDEO_MAX_JOB_USD=0 hard zero-spend lock ($0.00)."
        return base_info

    cache_key = f"{hub_url}:{hash(token)}"
    now = time.monotonic()
    cached = _WHOAMI_CACHE.get(cache_key)
    if cached and (now - cached[0]) < _WHOAMI_CACHE_TTL_S:
        res = dict(cached[1])
        res["zero_spend_locked"] = zero_spend_locked
        res["guaranteed_zero_cost"] = (not res["can_pay"]) or zero_spend_locked
        return res

    req = urllib.request.Request(
        f"{hub_url}/whoami-v2",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "MemoryOS-JupiterStudio/2.1",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        is_pro = bool(data.get("isPro"))
        can_pay = bool(data.get("canPay"))
        guaranteed_zero = (not can_pay) or zero_spend_locked
        if not can_pay:
            summary = "NO PAYMENT CARD ON HUGGING FACE (canPay=false) · $0.00 HARD CEILING GUARANTEED"
        elif zero_spend_locked:
            summary = "Payment method on HF, but BLOCKED locally by MEMORYOS_VIDEO_MAX_JOB_USD=0 ($0.00)"
        else:
            summary = "HF payment method active — set Cap $0.00 to block paid router calls"
        result = {
            **base_info,
            "authenticated": True,
            "is_pro": is_pro,
            "can_pay": can_pay,
            "guaranteed_zero_cost": guaranteed_zero,
            "billing_summary": summary,
        }
        _WHOAMI_CACHE[cache_key] = (now, result)
        return result
    except Exception as exc:
        base_info["billing_summary"] = (
            f"Whoami check offline ({sanitize_hf_error(exc)[:80]}) · Local Cap $0.00 lock={'ACTIVE' if zero_spend_locked else 'OFF'}"
        )
        base_info["guaranteed_zero_cost"] = zero_spend_locked
        return base_info


def _normalize_hub_model_item(
    raw: Dict[str, Any],
    cached_ids: set[str],
) -> Optional[Dict[str, Any]]:
    repo_id = str(raw.get("id") or raw.get("modelId") or "").strip()
    if not repo_id or "/" not in repo_id:
        return None

    pipeline_tag = str(raw.get("pipeline_tag") or "").strip()
    tags = [str(t) for t in (raw.get("tags") or []) if isinstance(t, str)]
    likes = int(raw.get("likes") or 0)
    downloads = int(raw.get("downloads") or 0)

    params_total = raw.get("params_total")
    if params_total is None:
        st = raw.get("safetensors")
        gg = raw.get("gguf")
        if isinstance(st, dict) and isinstance(st.get("total"), (int, float)):
            params_total = int(st["total"])
        elif isinstance(gg, dict) and isinstance(gg.get("total"), (int, float)):
            params_total = int(gg["total"])

    live_providers: List[str] = list(raw.get("live_providers") or [])
    pm = raw.get("inferenceProviderMapping")
    if not live_providers and pm:
        if isinstance(pm, list):
            live_providers = [
                str(p.get("provider"))
                for p in pm
                if isinstance(p, dict) and p.get("status") == "live" and p.get("provider")
            ]
        elif isinstance(pm, dict):
            live_providers = [
                str(k)
                for k, v in pm.items()
                if isinstance(v, dict) and v.get("status") in (None, "live")
            ]

    fit = estimate_8gb_hardware_fit(
        repo_id=repo_id,
        params_total=params_total,
        tags=tags,
        pipeline_tag=pipeline_tag,
    )
    is_gguf = fit["is_gguf"]
    is_video = pipeline_tag in {"text-to-video", "image-to-video"} or "text-to-video" in {t.lower() for t in tags}
    is_vision = pipeline_tag == "image-text-to-text" or "vision" in {t.lower() for t in tags}

    return {
        "id": repo_id,
        "url": f"https://huggingface.co/{repo_id}",
        "pipeline_tag": pipeline_tag or ("text-generation" if is_gguf else "model"),
        "likes": likes,
        "downloads": downloads,
        "tags": tags[:8],
        "live_providers": live_providers[:6],
        "cached_locally": repo_id in cached_ids,
        "is_gguf": is_gguf,
        "is_video": is_video,
        "is_vision": is_vision,
        "hardware_fit": fit,
        "ollama_target": f"ollama:hf.co/{repo_id}" if is_gguf else None,
        "ollama_cli": f"ollama run hf.co/{repo_id}" if is_gguf else None,
        "hf_router_target": f"hf:{repo_id}",
        "video_target": f"hf:{repo_id}" if is_video else None,
        "cost_mode": "$0.00 Local Ollama / GGUF" if is_gguf else (
            "Cloud Video (Cap $0.00 Locked)" if is_video else "HF Router / Open-Weight"
        ),
    }


def search_hf_models(
    query: str = "",
    task: str = "8gb-gguf",
    sort: str = "trendingScore",
    limit: int = 12,
    gguf_only: bool = False,
    warm_only: bool = False,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Query public https://huggingface.co/api/models ($0.00) with 8GB RTX 3070 fit metadata."""
    q_clean = str(query or "").strip()[:120]
    task_clean = str(task or "all").strip().lower()
    sort_clean = sort if sort in {"trendingScore", "downloads", "likes"} else "trendingScore"
    lim = max(1, min(int(limit or 12), 24))

    effective_gguf = bool(gguf_only or task_clean == "8gb-gguf")
    pipeline_tag = ""
    if task_clean not in {"", "all", "8gb-gguf"}:
        pipeline_tag = task_clean

    local_cached = scan_local_hf_cache()
    cached_ids = {item["id"] for item in local_cached}

    _, _, hub_url = get_hf_credentials()
    cache_key = (hub_url, q_clean, pipeline_tag, sort_clean, lim, effective_gguf, bool(warm_only))
    now = time.monotonic()
    hit = _SEARCH_CACHE.get(cache_key)
    if hit and (now - hit[0]) < _SEARCH_CACHE_TTL_S:
        cached_payload = dict(hit[1])
        cached_payload["cached_count"] = len(local_cached)
        return cached_payload

    params: List[Tuple[str, str]] = [
        ("sort", sort_clean),
        ("direction", "-1"),
        ("limit", str(lim)),
        ("expand", "likes"),
        ("expand", "downloads"),
        ("expand", "pipeline_tag"),
        ("expand", "tags"),
        ("expand", "inferenceProviderMapping"),
        ("expand", "safetensors"),
        ("expand", "gguf"),
    ]
    if q_clean:
        params.append(("search", q_clean))
    if pipeline_tag:
        params.append(("pipeline_tag", pipeline_tag))
    if effective_gguf:
        params.append(("filter", "gguf"))
    if warm_only:
        params.append(("inference_provider", "all"))

    url = f"{hub_url}/models?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MemoryOS-JupiterStudio/2.1"},
        method="GET",
    )

    models: List[Dict[str, Any]] = []
    source = "huggingface_hub_live"
    warning = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_list = json.loads(resp.read().decode("utf-8", errors="replace"))
        if isinstance(raw_list, list):
            for entry in raw_list:
                if isinstance(entry, dict):
                    norm = _normalize_hub_model_item(entry, cached_ids)
                    if norm is not None:
                        models.append(norm)
    except Exception as exc:
        source = "offline_curated_fallback"
        warning = sanitize_hf_error(exc)
        for entry in FALLBACK_HF_MODELS:
            if effective_gguf and "gguf" not in entry.get("tags", []):
                continue
            if pipeline_tag and entry.get("pipeline_tag") != pipeline_tag:
                continue
            if q_clean and q_clean.lower() not in entry["id"].lower():
                continue
            norm = _normalize_hub_model_item(entry, cached_ids)
            if norm is not None:
                models.append(norm)

    result = {
        "ok": True,
        "source": source,
        "query": q_clean,
        "task": task_clean,
        "sort": sort_clean,
        "gguf_only": effective_gguf,
        "count": len(models),
        "cached_count": len(local_cached),
        "warning": warning,
        "models": models,
    }
    if source == "huggingface_hub_live":
        _SEARCH_CACHE[cache_key] = (now, result)
    return result


def _validate_loopback_ollama_url(ollama_host: Optional[str] = None) -> str:
    raw = (ollama_host or os.getenv("OLLAMA_HOST") or DEFAULT_LOCAL_OLLAMA_HOST).strip().rstrip("/")
    if "://" not in raw:
        raw = f"http://{raw}"
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Ollama host must use http or https.")
    host = (parsed.hostname or "").strip().lower()
    if host != "localhost":
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_loopback:
                raise ValueError("Refusing non-loopback Ollama host for Hugging Face pull.")
        except ValueError as exc:
            if "Refusing" in str(exc):
                raise
            raise ValueError("Refusing non-loopback Ollama host for Hugging Face pull.") from exc
    return raw


def list_local_ollama_models(ollama_host: Optional[str] = None, timeout: float = 2.0) -> List[str]:
    """List model tags currently installed in local loopback Ollama ($0.00)."""
    try:
        base = _validate_loopback_ollama_url(ollama_host)
        req = urllib.request.Request(f"{base}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return [str(m.get("name")) for m in (data.get("models") or []) if isinstance(m, dict) and m.get("name")]
    except Exception:
        return []


def pull_hf_gguf_to_ollama(
    repo_id: str,
    ollama_host: Optional[str] = None,
    timeout: float = 180.0,
) -> Dict[str, Any]:
    """Pull a validated hf.co/<org>/<repo> GGUF model into local loopback Ollama ($0.00)."""
    safe_repo = validate_safe_hf_repo_id(repo_id)
    base_url = _validate_loopback_ollama_url(ollama_host)
    ollama_model_ref = f"hf.co/{safe_repo}"
    payload = json.dumps({"model": ollama_model_ref, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/pull",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        status_str = str(data.get("status") or "success")
        return {
            "ok": True,
            "repo_id": safe_repo,
            "ollama_model": ollama_model_ref,
            "studio_target": f"ollama:{ollama_model_ref}",
            "status": status_str,
            "cost_usd": 0.0,
        }
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:260]
        except Exception:
            pass
        raise RuntimeError(f"Ollama pull failed (HTTP {exc.code}): {sanitize_hf_error(detail or exc.reason)}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Local Ollama daemon unreachable at {base_url} ({sanitize_hf_error(exc.reason)}). Start 'ollama serve' or run: ollama run {ollama_model_ref}"
        ) from exc


def get_hf_hub_status(live_whoami: bool = True) -> Dict[str, Any]:
    """Aggregate Hugging Face safety lock, local disk HF cache, and local Ollama readiness."""
    safety = get_hf_account_safety(live_check=live_whoami)
    local_cache = scan_local_hf_cache()
    ollama_models = list_local_ollama_models()
    total_cache_mb = round(sum(float(m["size_mb"]) for m in local_cache), 1)
    return {
        "ok": True,
        "safety": safety,
        "tasks": list(SUPPORTED_HF_TASKS),
        "local_cache": {
            "count": len(local_cache),
            "total_size_mb": total_cache_mb,
            "models": local_cache,
        },
        "ollama": {
            "live": len(ollama_models) > 0,
            "models": ollama_models,
        },
    }
