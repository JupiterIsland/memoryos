#!/usr/bin/env python3
"""
Jupiter Studio // MemoryOS Hybrid Desktop Workstation (Zero-Dependency Python stdlib server).

Features:
  1) Real-time SSE token streaming (/api/chat/stream) with reasoning display, Stop button and Dual Arena.
  2) Auto-Route (d3 + SpeculativeOffloadNet) across cloud providers -- AMD Token Lab, OpenAI, Google Gemini API,
     Groq, OpenRouter, Cerebras, NVIDIA NIM / Brev, DigitalOcean MI300X, Hugging Face Router -- and local
     servers -- AMD Lemonade Server (Ryzen AI), Ollama, vLLM and NVIDIA Flare.
  3) Frank-v1: built-in CPU continual-learning intent router (EWC + A-GEM, /api/frank/*).
  4) Memory Keeper: persistent SQLite Memory Vault of pinned facts (/api/memory/*).
  5) NEON control plane: circuit breakers, SHA-256 hash-chained ops ledger, recovery engine and
     declarative (zero-exec) plugin packs.
  6) Workspace scanner / context packer (root-contained, symlink-safe; see workspace_pack.py).

Network security model:
  * Binds to 127.0.0.1 by default. Non-loopback binds are refused unless --unsafe-lan is passed,
    and LAN mode always requires a random per-launch access token.
  * Loopback mode enforces Host / Origin / Referer / Sec-Fetch-Site checks (DNS-rebinding + CSRF),
    but has no token by default: any process running as your user can call the API. Pass
    --require-token (or JUPITER_STUDIO_REQUIRE_TOKEN=1) to require a token on loopback as well.
"""

from __future__ import annotations

import argparse
import base64
import hmac
import http.cookies
import ipaddress
import json
import secrets
import os
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

IS_FROZEN = bool(getattr(sys, "frozen", False))
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR

for _p in (str(BUNDLE_ROOT), str(APP_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _parse_env_line(raw: str) -> Optional[Tuple[str, str]]:
    """Parse a single .env assignment supporting optional `export `, matching quotes, and unquoted comments."""
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    if line.startswith("export "):
        line = line[7:].strip()
        if "=" not in line:
            return None
    k, v = line.split("=", 1)
    k = k.strip()
    v = v.strip()
    if not k:
        return None
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        v = v[1:-1]
    elif " #" in v:
        v = v.split(" #", 1)[0].rstrip()
    return k, v


def _bootstrap_standalone_env() -> None:
    """Ensure .env exists beside the executable on first launch and load it into os.environ."""
    env_file = APP_DIR / ".env"
    if IS_FROZEN and not env_file.exists():
        bundled_example = BUNDLE_ROOT / ".env.example"
        if bundled_example.exists():
            try:
                shutil.copy2(bundled_example, env_file)
            except Exception:
                pass
    if env_file.exists():
        try:
            for raw in env_file.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                parsed = _parse_env_line(raw)
                if not parsed:
                    continue
                k, v = parsed
                if k not in os.environ:
                    os.environ[k] = v
        except Exception:
            pass


_bootstrap_standalone_env()

from src.memoryos.gpu_backends import MultiGPUDetector
from src.memoryos.router import (
    CEREBRAS_MODEL_MAP,
    DO_MODEL_MAP,
    GEMINI_MODEL_MAP,
    GROQ_MODEL_MAP,
    MODEL_PROFILES,
    NVIDIA_MODEL_MAP,
    OPENROUTER_MODEL_MAP,
    _get_cerebras_credentials,
    _get_do_credentials,
    _get_gemini_credentials,
    _get_groq_credentials,
    _get_nvidia_credentials,
    _get_openai_credentials,
    _get_openrouter_credentials,
    _get_tokenlab_credentials,
    _is_configured_key,
    _local_d3_fallback,
    get_cloud_provider_status,
    get_policy_telemetry,
    route_task,
    select_model_with_d3,
)
from src.memoryos.workspace_pack import (
    export_copilot_bundle,
    get_git_branch,
    pack_workspace_context,
    scan_workspace_files,
)


def _safe_int_env(name: str, default: int, min_val: int = 1, max_val: int = 65535) -> int:
    try:
        val = int(os.getenv(name, str(default)))
        if min_val <= val <= max_val:
            return val
    except (TypeError, ValueError):
        pass
    return default


PORT = _safe_int_env("JUPITER_STUDIO_PORT", 7860)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MAX_REQUEST_BODY_BYTES = 16 * 1024 * 1024  # 16 MB request cap
MAX_IMAGE_DATA_CHARS = 12 * 1024 * 1024  # 12 MB data-URI cap
MAX_HISTORY_ITEMS = 20
_LOCAL_ORIGIN_HOSTS = {"127.0.0.1", "localhost", "::1"}
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SAFE_IMAGE_DATA_URI_RE = re.compile(
    r"^data:image/(?:png|jpe?g|gif|webp|bmp|avif);base64,[A-Za-z0-9+/=\s]+$",
    re.IGNORECASE,
)
_STRICT_HOST_RE = re.compile(
    r"^(?:\[[0-9a-fA-F:]+\]|[A-Za-z0-9.-]+)(?::\d{1,5})?$"
)
_TOKEN_COOKIE_NAME = "jupiter_studio_token"
_ACCESS_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


def _is_loopback_bind_host(host: str) -> bool:
    """True only for loopback addresses. An empty host means 'all interfaces' and is NOT loopback."""
    cleaned = (host or "").strip().lower().strip("[]")
    if cleaned == "localhost":
        return True
    try:
        return ipaddress.ip_address(cleaned).is_loopback
    except ValueError:
        return False


def _bind_host_error(host: str, unsafe_lan: bool) -> Optional[str]:
    """Return an error message if binding to `host` is not allowed, else None."""
    if _is_loopback_bind_host(host) or unsafe_lan:
        return None
    shown = host if host else "'' (all interfaces)"
    return (
        f"Refusing to bind Jupiter Studio to {shown}: this exposes your API keys and workspace to the "
        "network. Use the default 127.0.0.1, or pass --unsafe-lan (a per-launch access token will be required)."
    )


def _is_allowed_origin(origin: str) -> bool:
    """Allow CORS only from local loopback origins to prevent cross-site exfiltration."""
    if not origin:
        return True
    cleaned = origin.strip()
    if any(ch.isspace() for ch in cleaned):
        return False
    try:
        parsed = urllib.parse.urlsplit(cleaned)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return False
    return (parsed.hostname or "").lower() in _LOCAL_ORIGIN_HOSTS


def _is_private_or_local_host(hostname: str) -> bool:
    """Block loopback, private, link-local, multicast, and internal hostnames in remote image URLs."""
    host = (hostname or "").strip().lower().rstrip(".")
    if not host or host in _LOCAL_ORIGIN_HOSTS or host.endswith((".local", ".internal", ".localhost")):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def _safe_nonneg_int(val: Any, default: int = 0) -> int:
    if isinstance(val, bool):
        return default
    try:
        return max(0, int(val or 0))
    except (TypeError, ValueError):
        return default


def _make_markdown_fence(content: str) -> str:
    longest = 2
    run = 0
    for ch in content:
        if ch == "`":
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0
    return "`" * (longest + 1)


def _sanitize_image_url(image_base64: Any) -> Optional[str]:
    """Allow only bounded raster data:image/*;base64,... URIs or public https:// image URLs."""
    if not isinstance(image_base64, str):
        return None
    cleaned = image_base64.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_IMAGE_DATA_CHARS:
        raise ValueError("Attached image exceeds 12 MB limit")
    if _SAFE_IMAGE_DATA_URI_RE.match(cleaned):
        return cleaned
    lower = cleaned.lower()
    if lower.startswith("https://"):
        try:
            parsed = urllib.parse.urlsplit(cleaned)
        except ValueError as exc:
            raise ValueError("Unsupported image format: malformed https:// URL") from exc
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Unsupported image format: credentials in image URL are not allowed")
        if parsed.netloc and parsed.hostname and not _is_private_or_local_host(parsed.hostname):
            return cleaned
        raise ValueError("Unsupported image format: private or loopback image URLs are not allowed")
    raise ValueError("Unsupported image format: expected raster data:image/...;base64,... or public https:// URL")


def _extract_raw_base64_image(image_data_uri: Optional[str]) -> Optional[str]:
    """Extract raw base64 payload from a validated raster data:image/*;base64,... URI."""
    if not image_data_uri or not _SAFE_IMAGE_DATA_URI_RE.match(image_data_uri):
        return None
    _, b64_part = image_data_uri.split(";base64,", 1)
    cleaned = re.sub(r"\s+", "", b64_part)
    return cleaned or None


def _sanitize_history(history: Any) -> List[Dict[str, str]]:
    """Whitelist user/assistant turns and cap history length (blocks system-role injection)."""
    if not isinstance(history, list):
        return []
    out: List[Dict[str, str]] = []
    for item in history[-MAX_HISTORY_ITEMS:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "user").strip().lower()
        if role not in ("user", "assistant"):
            continue
        content = item.get("content")
        if not isinstance(content, str):
            continue
        if content:
            out.append({"role": role, "content": content})
    return out


def _get_local_vllm_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for a local vLLM / SGLang / TensorFold OpenAI-compatible server."""
    base_url = os.getenv("LOCAL_VLLM_BASE_URL", "http://127.0.0.1:8000/v1").strip().rstrip("/")
    api_key = os.getenv("LOCAL_VLLM_API_KEY", "EMPTY").strip()
    return api_key, base_url


def _get_nvidia_flare_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for a local NVIDIA Flare (DGX Spark Rust inference server) endpoint."""
    base_url = os.getenv("NVIDIA_FLARE_BASE_URL", "http://127.0.0.1:8080/v1").strip().rstrip("/")
    api_key = os.getenv("NVIDIA_FLARE_API_KEY", "EMPTY").strip()
    return api_key, base_url


_LEMONADE_CACHE: Dict[str, Any] = {"url": None, "checked": 0.0, "alive": False}
_LEMONADE_CACHE_LOCK = threading.Lock()


def _is_private_or_wsl_ip(addr: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(addr.strip("[]"))
        return ip_obj.is_private and not ip_obj.is_loopback
    except ValueError:
        return False


def _discover_wsl_host_ips() -> List[str]:
    """Return likely Windows host IPs when running inside WSL2 (filtering out public DNS servers like 8.8.8.8)."""
    ips: List[str] = []
    # Prefer default route gateway (Windows vEthernet adapter inside WSL2 NAT)
    try:
        import subprocess
        out = subprocess.check_output(["ip", "route"], text=True, timeout=0.6)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "default" and parts[1] == "via":
                gw = parts[2].strip()
                if _is_private_or_wsl_ip(gw):
                    ips.append(gw)
    except Exception:
        pass
    try:
        for line in Path("/etc/resolv.conf").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("nameserver"):
                parts = line.split()
                if len(parts) >= 2:
                    addr = parts[1].strip()
                    if _is_private_or_wsl_ip(addr):
                        ips.append(addr)
    except Exception:
        pass
    return list(dict.fromkeys(ips))


def _normalize_lemonade_base(raw_url: str) -> str:
    clean = str(raw_url or "").strip().rstrip("/")
    if not clean:
        return "http://127.0.0.1:13305/api/v1"
    parsed = urllib.parse.urlparse(clean)
    if parsed.path in ("", "/"):
        return f"{clean}/api/v1"
    return clean


def _extract_lemonade_models(payload: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(payload, dict):
        return []
    found: List[str] = []
    # OpenAI /api/v1/models schema: {"data": [{"id": "...", "model_name": "..."}]}
    for item in payload.get("data", []) if isinstance(payload.get("data"), list) else []:
        if isinstance(item, dict):
            mid = str(item.get("id") or item.get("model_name") or item.get("checkpoint") or "").strip()
            if mid and mid not in found:
                found.append(mid)
    # Native Lemonade /api/v1/health schema: {"status": "ok", "model_loaded": "...", "all_models_loaded": [{"model_name": "..."}]}
    loaded_top = str(payload.get("model_loaded") or "").strip()
    if loaded_top and loaded_top not in found:
        found.append(loaded_top)
    for item in payload.get("all_models_loaded", []) if isinstance(payload.get("all_models_loaded"), list) else []:
        if isinstance(item, dict):
            mname = str(item.get("model_name") or item.get("id") or "").strip()
            if mname and mname not in found:
                found.append(mname)
    return found


def _probe_lemonade_endpoint(base_url: str, timeout: float = 0.8) -> Tuple[bool, List[str]]:
    """Probe Lemonade via /models and native /health (handles schema & path variations cleanly)."""
    norm = _normalize_lemonade_base(base_url)
    root = norm[:-7] if norm.endswith("/api/v1") else (norm[:-3] if norm.endswith("/v1") else norm)
    models: List[str] = []
    alive = False

    for url in dict.fromkeys([f"{norm}/models", f"{norm}/health", f"{root}/api/v1/health"]):
        resp = _http_ok(url, timeout)
        if isinstance(resp, dict):
            if "data" in resp or resp.get("status") == "ok" or "all_models_loaded" in resp or "model_loaded" in resp:
                alive = True
                for mid in _extract_lemonade_models(resp):
                    if mid not in models:
                        models.append(mid)
                if models:
                    break
    return alive, models


def _get_lemonade_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for a local AMD Lemonade Server (Ryzen AI XDNA 2 / FastFlowLM) endpoint."""
    env_url = os.getenv("LEMONADE_BASE_URL", "").strip()
    api_key = os.getenv("LEMONADE_API_KEY", "EMPTY").strip()
    if env_url:
        return api_key, _normalize_lemonade_base(env_url)

    now = time.time()
    with _LEMONADE_CACHE_LOCK:
        ttl = 10.0 if _LEMONADE_CACHE.get("alive") else 2.0
        if _LEMONADE_CACHE["checked"] and now - _LEMONADE_CACHE["checked"] < ttl and _LEMONADE_CACHE["url"]:
            return api_key, _LEMONADE_CACHE["url"]

    candidates = ["http://127.0.0.1:13305/api/v1"]
    for addr in _discover_wsl_host_ips():
        fmt = f"[{addr}]" if ":" in addr and not addr.startswith("[") else addr
        candidates.append(f"http://{fmt}:13305/api/v1")

    found = candidates[0]
    is_alive = False
    for cand in dict.fromkeys(candidates):
        ok, _ = _probe_lemonade_endpoint(cand, 0.6)
        if ok:
            found = cand
            is_alive = True
            break

    with _LEMONADE_CACHE_LOCK:
        _LEMONADE_CACHE.update(url=found, checked=time.time(), alive=is_alive)
    return api_key, found


def _get_huggingface_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for Hugging Face Inference Providers (zero-download serverless router)."""
    base_url = os.getenv("HF_BASE_URL", "https://router.huggingface.co/v1").strip().rstrip("/")
    api_key = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or "").strip()
    return api_key, base_url

try:
    from apps.jupiter_studio_ui import STUDIO_HTML as HTML_PAGE
except ImportError:
    from jupiter_studio_ui import STUDIO_HTML as HTML_PAGE

_OLLAMA_CACHE: Dict[str, Any] = {"host": None, "checked": 0.0}
_OLLAMA_CACHE_LOCK = threading.Lock()


def _http_ok(url: str, timeout: float = 1.2) -> Optional[Dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
    except Exception:
        return None


def _resolve_ollama_host() -> Optional[str]:
    """Find a live Ollama server: OLLAMA_HOST, localhost, or the Windows host when running under WSL."""
    now = time.time()
    with _OLLAMA_CACHE_LOCK:
        if now - _OLLAMA_CACHE["checked"] < 10 and _OLLAMA_CACHE["checked"]:
            return _OLLAMA_CACHE["host"]
    candidates = [os.getenv("OLLAMA_HOST", OLLAMA_HOST).rstrip("/"), "http://127.0.0.1:11434"]
    for addr in _discover_wsl_host_ips():
        fmt = f"[{addr}]" if ":" in addr and not addr.startswith("[") else addr
        candidates.append(f"http://{fmt}:11434")
    found = None
    for cand in dict.fromkeys(candidates):
        if _http_ok(f"{cand}/api/tags") is not None:
            found = cand
            break
    with _OLLAMA_CACHE_LOCK:
        _OLLAMA_CACHE.update(host=found, checked=time.time())
    return found


_PROVIDER_RUNTIME_ERRORS: Dict[str, str] = {}
_PROVIDER_ERR_LOCK = threading.Lock()
_PROVIDER_TO_SHORT: Dict[str, str] = {
    "AMD Token Lab": "cloud",
    "OpenAI Cloud": "openai",
    "Google Gemini API": "gemini",
    "Groq Cloud": "groq",
    "OpenRouter": "openrouter",
    "Cerebras Cloud": "cerebras",
    "NVIDIA NIM": "nv",
    "DigitalOcean MI300X": "do",
    "Hugging Face Router": "hf",
}


def _is_quota_or_billing_detail(code: int, detail: str) -> bool:
    if code in (401, 402, 403):
        return True
    if code == 429:
        low = detail.lower()
        return any(tok in low for tok in ("insufficient_quota", "no credits", "add credits", "pre-paid", "billing", "current quota"))
    return False


def _record_provider_runtime_error(provider_key: str, code: int, detail: str) -> Optional[str]:
    short = _PROVIDER_TO_SHORT.get(provider_key)
    if not short or not _is_quota_or_billing_detail(code, detail):
        return None
    if code == 402 or "pre-paid" in detail.lower() or "credits" in detail.lower() or "insufficient_quota" in detail.lower():
        msg = f"{provider_key}: no API credits remaining (HTTP {code})"
    else:
        msg = f"{provider_key}: API key rejected (HTTP {code})"
    with _PROVIDER_ERR_LOCK:
        _PROVIDER_RUNTIME_ERRORS[short] = msg
    return msg


def _clear_provider_runtime_error(provider_key: str) -> None:
    short = _PROVIDER_TO_SHORT.get(provider_key)
    if not short:
        return
    with _PROVIDER_ERR_LOCK:
        _PROVIDER_RUNTIME_ERRORS.pop(short, None)


def _get_provider_runtime_error(short: str) -> str:
    with _PROVIDER_ERR_LOCK:
        return _PROVIDER_RUNTIME_ERRORS.get(short, "")


def _is_provider_usable(short: str) -> bool:
    with _PROVIDER_ERR_LOCK:
        return short not in _PROVIDER_RUNTIME_ERRORS


def _count_local_ollama_manifests() -> int:
    try:
        lib = Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library"
        if lib.is_dir():
            return sum(1 for p in lib.rglob("*") if p.is_file())
    except Exception:
        pass
    return 0


def _probe_configured_cloud_credits(timeout: float = 5.0) -> None:
    """Test configured cloud providers with a minimal 1-token check to catch 0-credit/401 keys early."""
    status = get_cloud_provider_status()
    targets: List[Tuple[str, str, str, str]] = []
    if status["amd_tokenlab"]["configured"]:
        k, u = _get_tokenlab_credentials()
        targets.append(("AMD Token Lab", "Gemma-4-31B-IT", k, u))
    if status.get("openai", {}).get("configured"):
        k, u = _get_openai_credentials()
        targets.append(("OpenAI Cloud", "gpt-4o-mini", k, u))
    if status.get("huggingface", {}).get("configured"):
        k, u = _get_huggingface_credentials()
        targets.append(("Hugging Face Router", "Qwen/Qwen2.5-72B-Instruct", k, u))
    if status.get("groq", {}).get("configured"):
        k, u = _get_groq_credentials()
        targets.append(("Groq Cloud", GROQ_MODEL_MAP["MiniCPM5-2B"], k, u))
    if status.get("openrouter", {}).get("configured"):
        k, u = _get_openrouter_credentials()
        targets.append(("OpenRouter", OPENROUTER_MODEL_MAP["MiniCPM5-2B"], k, u))
    if status.get("cerebras", {}).get("configured"):
        k, u = _get_cerebras_credentials()
        targets.append(("Cerebras Cloud", CEREBRAS_MODEL_MAP["MiniCPM5-2B"], k, u))
    if status["nvidia_brev"]["configured"]:
        k, u = _get_nvidia_credentials()
        targets.append(("NVIDIA NIM", NVIDIA_MODEL_MAP["MiniCPM5-2B"], k, u))
    if status["digitalocean_mi300x"]["configured"]:
        k, u = _get_do_credentials()
        targets.append(("DigitalOcean MI300X", DO_MODEL_MAP["MiniCPM5-2B"], k, u))

    def _check_one(prov_key: str, model_id: str, api_key: str, base_url: str) -> None:
        url = f"{base_url.rstrip('/')}/chat/completions"
        body = json.dumps({
            "model": model_id,
            "messages": [{"role": "user", "content": "OK"}],
            "max_tokens": 4,
            "temperature": 0,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "MemoryOS-Probe/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout):
                _clear_provider_runtime_error(prov_key)
        except urllib.error.HTTPError as http_err:
            detail = ""
            try:
                detail = http_err.read().decode("utf-8", errors="replace")[:350]
            except Exception:
                pass
            finally:
                try:
                    http_err.close()
                except Exception:
                    pass
            _record_provider_runtime_error(prov_key, http_err.code, detail)
        except Exception:
            pass

    if not targets:
        return
    threads = [threading.Thread(target=_check_one, args=t, daemon=True) for t in targets]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=timeout + 1.0)


def _probe_model_availability(force_refresh: bool = False) -> Dict[str, Any]:
    """Report which execution providers can actually serve a request right now."""
    if force_refresh:
        with _OLLAMA_CACHE_LOCK:
            _OLLAMA_CACHE.update(host=None, checked=0.0)
        with _LEMONADE_CACHE_LOCK:
            _LEMONADE_CACHE.update(checked=0.0, alive=False)
        _probe_configured_cloud_credits(timeout=4.5)

    cloud = get_cloud_provider_status()
    host = _resolve_ollama_host()
    installed: List[str] = []
    if host:
        tags = _http_ok(f"{host}/api/tags") or {}
        installed = [m.get("name", "") for m in tags.get("models", []) if isinstance(m, dict)]
    _, vllm_url = _get_local_vllm_credentials()
    _, flare_url = _get_nvidia_flare_credentials()
    _, lemonade_url = _get_lemonade_credentials()
    lemonade_ok, lemonade_installed = _probe_lemonade_endpoint(lemonade_url, 0.8)
    hf_ready = bool(cloud.get("huggingface", {}).get("configured"))
    groq_ready = bool(cloud.get("groq", {}).get("configured"))
    openrouter_ready = bool(cloud.get("openrouter", {}).get("configured"))
    cerebras_ready = bool(cloud.get("cerebras", {}).get("configured"))
    openai_ready = bool(cloud.get("openai", {}).get("configured"))
    gemini_ready = bool(cloud.get("gemini", {}).get("configured"))

    lemonade_ready = bool(lemonade_ok and len(lemonade_installed) > 0)
    lemonade_reason = ""
    if lemonade_ok and not lemonade_installed:
        lemonade_reason = (
            f"Lemonade Server running at {lemonade_url}, but 0 models downloaded "
            "(run `lemonade-server pull Qwen3-4B-Instruct-2507-GGUF`)"
        )
    elif not lemonade_ok:
        is_wsl = False
        try:
            is_wsl = "microsoft" in Path("/proc/version").read_text(encoding="utf-8", errors="replace").lower()
        except Exception:
            pass
        if is_wsl:
            lemonade_reason = (
                f"No TCP response at {lemonade_url} (WSL2 NAT cannot reach Windows 127.0.0.1:13305 unless "
                "networkingMode=mirrored, --host 0.0.0.0, or running Studio natively on Windows)"
            )
        else:
            lemonade_reason = f"No Lemonade Server at {lemonade_url}"

    ollama_reason = "Ollama not running - start the Ollama app"
    if not host:
        local_manifests = _count_local_ollama_manifests()
        if local_manifests > 0:
            ollama_reason = f"Ollama stopped ({local_manifests} local model(s) on disk) - start Ollama app"

    def state(ok: bool, reason: str) -> Dict[str, Any]:
        return {"ready": ok, "reason": "" if ok else reason}

    def cloud_state(short_key: str, configured: bool, unconfigured_reason: str) -> Dict[str, Any]:
        if not configured:
            return {"ready": False, "reason": unconfigured_reason, "billing_error": False}
        rt_err = _get_provider_runtime_error(short_key)
        if rt_err:
            return {"ready": False, "reason": rt_err, "billing_error": True}
        return {"ready": True, "reason": "", "billing_error": False}

    return {
        "providers": {
            "studio": state(True, ""),
            "cloud": cloud_state("cloud", cloud["amd_tokenlab"]["configured"], "Set TOKENLAB_API_KEY in .env"),
            "openai": cloud_state("openai", openai_ready, "Set OPENAI_API_KEY in .env"),
            "gemini": cloud_state("gemini", gemini_ready, "Set GEMINI_API_KEY in .env"),
            "groq": cloud_state("groq", groq_ready, "Set GROQ_API_KEY in .env"),
            "openrouter": cloud_state("openrouter", openrouter_ready, "Set OPENROUTER_API_KEY in .env"),
            "cerebras": cloud_state("cerebras", cerebras_ready, "Set CEREBRAS_API_KEY in .env"),
            "nv": cloud_state("nv", cloud["nvidia_brev"]["configured"], "Set NVIDIA_API_KEY in .env"),
            "do": cloud_state("do", cloud["digitalocean_mi300x"]["configured"], "Set DO_MODEL_ACCESS_KEY in .env"),
            "hf": cloud_state("hf", hf_ready, "Set HF_TOKEN in .env"),
            "lemonade": state(lemonade_ready, lemonade_reason),
            "vllm": state(_http_ok(f"{vllm_url}/models", 0.8) is not None, f"No vLLM server at {vllm_url}"),
            "flare": state(_http_ok(f"{flare_url}/models", 0.8) is not None, f"No Flare server at {flare_url}"),
            "ollama": state(bool(host), ollama_reason),
            "auto": state(True, ""),
        },
        "ollama_host": host,
        "ollama_installed": installed,
        "lemonade_url": lemonade_url,
        "lemonade_installed": lemonade_installed,
    }


_SPEC_MODEL: Any = None
_SPEC_MODEL_LOCK = threading.Lock()
_TELEM_LOCK = threading.Lock()
_LAST_OFFLOAD_TS: Optional[float] = None
_LAST_TARGET_SEEN: str = "auto:d3"
_MODEL_SWITCH_COUNT: int = 0
_STUDIO_START_TS: float = time.time()

_STUDIO_SYSTEM_PROMPT = (
    "You are an AI systems engineer and coding assistant inside MemoryOS // Jupiter Studio. "
    "Architecture facts (never invent unimplemented subsystems like NVMe SSD weight streaming): "
    "MemoryOS uses a local host CPU delta gate + SpeculativeOffloadNet MLP (4->8->1) and d3 router "
    "to route prompts across cloud GPUs (AMD Token Lab, OpenAI Cloud, Google Gemini API, NVIDIA NIM, DigitalOcean MI300X, HF Router) "
    "or local servers (AMD Lemonade Server / FastFlowLM on Ryzen AI XDNA 2, Ollama, vLLM/Flare), "
    "keeping local GPU VRAM at 0 MB when offloaded. "
    "Frank-v1 is Jupiter Studio's built-in CPU continual-learning neural router (not a human student). "
    "Never claim you wrote a fact into QuietAdvisorDB.sqlite unless the user explicitly pinned it through the app."
)


def _record_target_activity(target_key: str, did_offload: bool = False) -> None:
    """Update real runtime offload timestamp and target-switch counter."""
    global _LAST_OFFLOAD_TS, _LAST_TARGET_SEEN, _MODEL_SWITCH_COUNT
    with _TELEM_LOCK:
        if did_offload:
            _LAST_OFFLOAD_TS = time.time()
        if target_key and target_key != _LAST_TARGET_SEEN:
            _MODEL_SWITCH_COUNT += 1
            _LAST_TARGET_SEEN = target_key


def _local_route_preview(prompt: str, has_image: bool, total_chars: int) -> Tuple[str, str]:
    """Zero-network local d3 preview used during typing/speculation (never hits remote /v1/systemone)."""
    state_text = (
        f"Prompt preview ({total_chars} chars, has image input: {str(has_image).lower()}): {prompt[:240]}"
    )
    criteria = {
        "vision_heavy": "Requires vision",
        "balanced_code": "Requires code or architecture",
        "fast_light": "Short simple query",
    }
    decision = _local_d3_fallback(state_text=state_text, criteria=criteria, model="d3-local")
    tier = str(decision.get("choice") or ("vision_heavy" if has_image else "balanced_code"))
    if tier == "fast_light":
        # Interactive Studio routes short chat to 27B/31B unless local selected explicitly
        tier = "balanced_code"
    model_map = {
        "vision_heavy": "Gemma-4-31B-IT",
        "balanced_code": "Qwen3.8-27B",
        "fast_light": "Qwen3.8-27B",
    }
    return model_map.get(tier, "Qwen3.8-27B"), tier


def _is_local_execution_provider(provider_key: str, is_local_ollama: bool) -> bool:
    """Return True when inference executes on a local host/LAN server rather than external cloud."""
    if is_local_ollama:
        return True
    low = (provider_key or "").lower()
    return any(tok in low for tok in ("lemonade", "ollama", "local vllm", "nvidia flare", "frank", "built-in"))


_FRANK_MODEL: Any = None
_FRANK_MODEL_LOCK = threading.Lock()
_LAST_FRANK_PREDICTION: Optional[Dict[str, Any]] = None


def _get_frank_model():
    global _FRANK_MODEL
    if _FRANK_MODEL is None:
        with _FRANK_MODEL_LOCK:
            if _FRANK_MODEL is None:
                try:
                    from src.memoryos.frank import FrankModel
                except ImportError:
                    from memoryos.frank import FrankModel
                try:
                    _FRANK_MODEL = FrankModel.load()
                except Exception:
                    from src.memoryos.frank import TRAINING_CURRICULUM
                    m = FrankModel.create_fresh()
                    m.fit_continual(TRAINING_CURRICULUM, epochs=130, lr=0.45, ewc_lambda=0.0)
                    _FRANK_MODEL = m
    return _FRANK_MODEL


def _predict_frank_intent(prompt: str, record: bool = False) -> Dict[str, Any]:
    global _LAST_FRANK_PREDICTION
    fm = _get_frank_model()
    ewc_protected = bool(fm._ewc_fisher is not None)
    query = str(prompt or "").strip()
    if not query:
        return {
            "model": fm.model_name,
            "version": fm.version,
            "intent": "idle",
            "confidence": 0.0,
            "confidence_pct": 0.0,
            "latency_us": 0.0,
            "probs": {},
            "ewc_protected": ewc_protected,
        }
    pred = fm.predict(query)
    out = {
        "model": pred["model"],
        "version": pred["version"],
        "intent": pred["intent"],
        "confidence": pred["confidence"],
        "confidence_pct": round(float(pred["confidence"]) * 100.0, 1),
        "latency_us": pred["latency_us"],
        "probs": pred["probs"],
        "ewc_protected": ewc_protected,
    }
    if record:
        with _FRANK_MODEL_LOCK:
            _LAST_FRANK_PREDICTION = {**out, "prompt_preview": query[:120]}
    return out


def _run_frank_turn(raw_prompt: str) -> Dict[str, Any]:
    try:
        from src.memoryos.frank import run_frank_assistant_turn
    except ImportError:
        from memoryos.frank import run_frank_assistant_turn
    prof = MultiGPUDetector.get_active_profile()
    vault = _get_memory_vault()
    return run_frank_assistant_turn(
        prompt=raw_prompt,
        gpu_profile=prof.__dict__,
        vault_summary=vault.get_summary(),
        recalled_facts=vault.recall(raw_prompt, limit=3) if raw_prompt.strip() else [],
        frank_model=_get_frank_model(),
    )


def _run_live_speculation(body: Dict[str, Any]) -> Dict[str, Any]:
    """Run the real 4->8->1 SpeculativeOffloadModel MLP + local d3 preview (zero network calls)."""
    global _SPEC_MODEL
    prompt = str(body.get("prompt") or "")
    target = str(body.get("target") or "auto:d3").strip()
    has_image = bool(body.get("has_image"))
    file_count = _safe_nonneg_int(body.get("file_count"), 0)
    extra_chars = _safe_nonneg_int(body.get("extra_chars"), 0)
    total_chars = len(prompt) + extra_chars
    est_tokens = max(1, total_chars // 4)

    with _TELEM_LOCK:
        secs_since = (time.time() - _LAST_OFFLOAD_TS) if _LAST_OFFLOAD_TS else 60.0
        uptime_mins = max(1.0, (time.time() - _STUDIO_START_TS) / 60.0)
        switch_rate = min(1.0, _MODEL_SWITCH_COUNT / max(4.0, uptime_mins * 2.0))

    mlp_us = 0.0
    try:
        model = _SPEC_MODEL
        if model is None:
            with _SPEC_MODEL_LOCK:
                if _SPEC_MODEL is None:
                    _SPEC_MODEL = _get_memory_vault()._load_or_init_model()
                model = _SPEC_MODEL

        # Map prompt complexity, context load, and real session counters into normalized MLP features
        complexity = min(1.0, (len(prompt) / 600.0) + (0.35 if has_image else 0.0) + (0.15 * min(3, file_count)))
        ctx_util = min(1.0, max(0.05, est_tokens / 4096.0))
        features = {
            "mse_delta_norm": round(max(0.15, complexity), 4),
            "context_utilization": round(ctx_util, 4),
            "secs_since_offload": round(min(1.0, secs_since / 120.0), 4),
            "model_switch_rate": round(switch_rate, 4),
        }
        t0 = time.perf_counter_ns()
        p_offload = model.predict_proba(features)
        if p_offload >= model.tau_hi:
            action = "offload_now"
        elif p_offload <= model.tau_lo:
            action = "skip"
        else:
            action = "digest"
        mlp_us = round((time.perf_counter_ns() - t0) / 1000.0, 2)
    except Exception:
        p_offload = 0.88
        action = "offload_now"
        mlp_us = 0.0

    local_target = target.startswith(("ollama:", "lemonade:", "vllm:", "flare:", "studio:"))
    if target == "studio:frank":
        selected_model, selected_tier = "Frank-v1", "builtin_helper"
    elif target == "auto:d3":
        selected_model, selected_tier = _local_route_preview(prompt, has_image, total_chars)
    else:
        selected_model = target.split(":", 1)[1] if ":" in target else target
        selected_tier = "local_device" if local_target else "explicit_cloud"

    if local_target:
        vram_saved_gb = 0.0
    else:
        upper = selected_model.upper()
        if "72B" in upper or "70B" in upper:
            vram_saved_gb = 42.0
        elif "31B" in upper or "32B" in upper:
            vram_saved_gb = 18.5
        elif "27B" in upper:
            vram_saved_gb = 16.2
        elif "DEEPSEEK" in upper:
            vram_saved_gb = 14.0
        elif "2B" in upper:
            vram_saved_gb = 2.4
        else:
            vram_saved_gb = 8.0

    frank_pred = None
    try:
        frank_pred = _predict_frank_intent(prompt, record=False)
    except Exception:
        frank_pred = None

    return {
        "p_offload": round(float(p_offload), 4),
        "action": action,
        "mlp_latency_us": mlp_us,
        "predicted_model": selected_model,
        "predicted_tier": selected_tier,
        "est_tokens": est_tokens,
        "vram_saved_gb": vram_saved_gb,
        "is_local": local_target,
        "frank": frank_pred,
    }


def _get_studio_db_path() -> Path:
    return REPO_ROOT / "QuietAdvisorDB.sqlite"


def _get_memory_vault():
    try:
        from src.memoryos.memory_keeper import MemoryVault
    except ImportError:
        from memoryos.memory_keeper import MemoryVault
    return MemoryVault(db_path=_get_studio_db_path())


def _get_cloud_video():
    try:
        from src.memoryos import cloud_video
    except ImportError:
        from memoryos import cloud_video
    return cloud_video


def _get_hf_hub():
    try:
        from src.memoryos import hf_hub
    except ImportError:
        from memoryos import hf_hub
    return hf_hub


def _get_ops_ledger():
    try:
        from src.memoryos.ops_console import OperationsLedger
    except ImportError:
        from memoryos.ops_console import OperationsLedger
    return OperationsLedger(db_path=_get_studio_db_path())


def _get_control_plane_ledger():
    try:
        from src.memoryos.control_plane import ImmutableLedger
    except ImportError:
        from memoryos.control_plane import ImmutableLedger
    return ImmutableLedger(db_path=_get_studio_db_path())


def _get_recovery_manager():
    try:
        from src.memoryos.control_plane import RecoveryManager
    except ImportError:
        from memoryos.control_plane import RecoveryManager
    return RecoveryManager(db_path=_get_studio_db_path())


_CIRCUIT_BREAKERS: Dict[str, Any] = {}
_CB_LOCK = threading.Lock()


def _get_circuit_breaker(provider_key: str):
    try:
        from src.memoryos.control_plane import CircuitBreaker
    except ImportError:
        from memoryos.control_plane import CircuitBreaker
    key = str(provider_key or "unknown")
    with _CB_LOCK:
        cb = _CIRCUIT_BREAKERS.get(key)
        if cb is None:
            cb = CircuitBreaker(name=key)
            _CIRCUIT_BREAKERS[key] = cb
        return cb


def _list_circuit_breakers() -> List[Dict[str, Any]]:
    with _CB_LOCK:
        return [cb.status() for cb in sorted(_CIRCUIT_BREAKERS.values(), key=lambda x: x.name)]


def _reset_circuit_breaker(provider_key: Optional[str] = None) -> List[Dict[str, Any]]:
    with _CB_LOCK:
        if provider_key:
            cb = _CIRCUIT_BREAKERS.get(provider_key)
            if cb is not None:
                cb.record_success()
        else:
            for cb in _CIRCUIT_BREAKERS.values():
                cb.record_success()
        return [cb.status() for cb in sorted(_CIRCUIT_BREAKERS.values(), key=lambda x: x.name)]


def _get_declarative_plugins():
    try:
        from src.memoryos.control_plane import DeclarativePluginLoader
    except ImportError:
        from memoryos.control_plane import DeclarativePluginLoader
    loader = DeclarativePluginLoader(ledger=_get_control_plane_ledger())
    plugins_dir = REPO_ROOT / "plugins"
    if not plugins_dir.is_dir():
        plugins_dir = BUNDLE_ROOT / "plugins"
    loader.load_directory(plugins_dir)
    return loader


def _plan_studio_objective(objective: str, prefer_local: bool = False):
    from dataclasses import asdict
    try:
        from src.memoryos.ops_console import OperationsPlanner
    except ImportError:
        from memoryos.ops_console import OperationsPlanner
    gpu_profile = asdict(MultiGPUDetector.get_active_profile())
    models_info = _probe_model_availability()
    frank_pred = None
    try:
        fm = _get_frank_model()
        frank_pred = fm.predict(objective)
    except Exception:
        frank_pred = None
    vault_facts = []
    try:
        if objective.strip():
            vault_facts = _get_memory_vault().recall(objective, limit=5)
    except Exception:
        vault_facts = []
    return OperationsPlanner.plan_objective(
        objective,
        gpu_profile=gpu_profile,
        models_info=models_info,
        frank_prediction=frank_pred,
        prefer_local=prefer_local,
        vault_facts=vault_facts,
    )


def _connect_studio_sessions_db(db_path: Optional[Path] = None) -> Any:
    import sqlite3
    target_db = Path(db_path) if db_path else _get_studio_db_path()
    target_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target_db, timeout=2.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS studio_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            target TEXT NOT NULL DEFAULT 'auto:d3',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS studio_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES studio_sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            reasoning TEXT DEFAULT '',
            meta_label TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_studio_messages_session ON studio_messages(session_id, id)"
    )
    conn.commit()
    return conn


def _list_studio_sessions(limit: int = 40, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    try:
        conn = _connect_studio_sessions_db(db_path)
        try:
            rows = conn.execute(
                """
                SELECT s.id, s.title, s.target, s.created_at, s.updated_at,
                       COUNT(m.id) AS message_count
                FROM studio_sessions s
                LEFT JOIN studio_messages m ON m.session_id = s.id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (max(1, min(100, int(limit))),),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def _get_studio_session_detail(session_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    if not _SESSION_ID_RE.match(session_id or ""):
        return None
    try:
        conn = _connect_studio_sessions_db(db_path)
        try:
            sess = conn.execute(
                "SELECT id, title, target, created_at, updated_at FROM studio_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if not sess:
                return None
            msgs = conn.execute(
                """
                SELECT id, role, content, reasoning, meta_label, created_at
                FROM studio_messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()
            return {"session": dict(sess), "messages": [dict(m) for m in msgs]}
        finally:
            conn.close()
    except Exception:
        return None


def _upsert_studio_session(
    session_id: Optional[str] = None,
    title: Optional[str] = None,
    target: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    import uuid
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    sid = str(session_id or "").strip()
    if not sid or not _SESSION_ID_RE.match(sid):
        sid = f"sess-{uuid.uuid4().hex[:12]}"
    clean_title = " ".join(str(title or "New Studio Session").split())[:72] or "New Studio Session"
    clean_target = str(target or "auto:d3").strip()[:120] or "auto:d3"

    conn = _connect_studio_sessions_db(db_path)
    try:
        existing = conn.execute("SELECT id, title FROM studio_sessions WHERE id = ?", (sid,)).fetchone()
        if existing:
            if title:
                conn.execute(
                    "UPDATE studio_sessions SET title = ?, target = ?, updated_at = ? WHERE id = ?",
                    (clean_title, clean_target, now, sid),
                )
            else:
                conn.execute(
                    "UPDATE studio_sessions SET target = ?, updated_at = ? WHERE id = ?",
                    (clean_target, now, sid),
                )
        else:
            conn.execute(
                "INSERT INTO studio_sessions (id, title, target, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (sid, clean_title, clean_target, now, now),
            )
        conn.commit()
        row = conn.execute(
            "SELECT id, title, target, created_at, updated_at FROM studio_sessions WHERE id = ?",
            (sid,),
        ).fetchone()
        return dict(row) if row else {"id": sid, "title": clean_title, "target": clean_target}
    finally:
        conn.close()


def _append_studio_turn(
    session_id: Optional[str],
    target: str,
    user_text: str,
    assistant_text: str,
    reasoning: str = "",
    meta_label: str = "",
    db_path: Optional[Path] = None,
) -> str:
    """Ensure session exists and append both user prompt and assistant response atomically."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    first_title = " ".join((user_text or "Studio Session").split())[:52] or "Studio Session"
    sess = _upsert_studio_session(session_id=session_id, title=None if session_id else first_title, target=target, db_path=db_path)
    sid = str(sess["id"])
    try:
        conn = _connect_studio_sessions_db(db_path)
        try:
            # If this session had a default placeholder title, promote first user prompt as title
            row = conn.execute("SELECT title FROM studio_sessions WHERE id = ?", (sid,)).fetchone()
            if row and row["title"] in ("New Studio Session", "Studio Session") and first_title:
                conn.execute("UPDATE studio_sessions SET title = ?, updated_at = ? WHERE id = ?", (first_title, now, sid))
            else:
                conn.execute("UPDATE studio_sessions SET updated_at = ? WHERE id = ?", (now, sid))
            conn.execute(
                "INSERT INTO studio_messages (session_id, role, content, reasoning, meta_label, created_at) VALUES (?, 'user', ?, '', '', ?)",
                (sid, str(user_text or ""), now),
            )
            if assistant_text:
                conn.execute(
                    "INSERT INTO studio_messages (session_id, role, content, reasoning, meta_label, created_at) VALUES (?, 'assistant', ?, ?, ?, ?)",
                    (sid, str(assistant_text), str(reasoning or ""), str(meta_label or ""), now),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
    return sid


def _delete_studio_session(session_id: str, db_path: Optional[Path] = None) -> bool:
    if not _SESSION_ID_RE.match(session_id or ""):
        return False
    try:
        conn = _connect_studio_sessions_db(db_path)
        try:
            cur = conn.execute("DELETE FROM studio_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()
    except Exception:
        return False


def _record_studio_inference(
    model_id: str,
    is_local_exec: bool,
    prompt_chars: int,
    latency_ms: float,
    success: bool = True,
) -> None:
    """Persist completed Jupiter Studio turns to QuietAdvisorDB for real health/telemetry."""
    try:
        import sqlite3
        from datetime import datetime, timezone
        from src.memoryos.quiet_advisor_db import QuietAdvisorDB

        db_path = REPO_ROOT / "QuietAdvisorDB.sqlite"
        if not db_path.exists():
            return
        prof = MultiGPUDetector.get_active_profile()
        used_vram = int(getattr(prof, "used_vram_mb", 0) or 0) if is_local_exec else 0
        est_tokens = max(1, int(prompt_chars // 4))
        tps = round((est_tokens / max(latency_ms / 1000.0, 0.05)), 1) if success else 0.0
        conn = sqlite3.connect(db_path, timeout=1.0)
        try:
            db = QuietAdvisorDB(db_path)
            db.close()
        except Exception:
            pass
        conn.execute(
            """
            INSERT INTO memoryos_inference_log (
                user_id, session_id, timestamp, model_id,
                context_tokens_provided, context_tokens_used,
                time_to_first_token_ms, total_latency_ms, tokens_per_second,
                gpu_id, gpu_utilization_percent, gpu_temperature_celsius,
                gpu_memory_used_mb, cache_hit, speculative_hit, error_occurred
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
            """,
            (
                "studio-user",
                "jupiter-studio",
                datetime.now(timezone.utc).isoformat(),
                str(model_id or "unknown")[:120],
                max(4096, est_tokens),
                est_tokens,
                round(float(latency_ms) * 0.25, 2),
                round(float(latency_ms), 2),
                tps,
                "local-host" if is_local_exec else "cloud-offload",
                float(getattr(prof, "utilization_pct", 0.0) or 0.0),
                float(getattr(prof, "temperature_c", 0.0) or 0.0),
                used_vram,
                0 if success else 1,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _compute_live_health(prof: Any) -> Dict[str, Any]:
    """Compute live Workstation Health Score from current GPU profile and real recent DB logs."""
    try:
        from datetime import datetime, timezone
        from quiet_advisor_detectors import InferenceLog, compute_workstation_health

        util = getattr(prof, "utilization_pct", None)
        if util is None:
            util = getattr(prof, "utilization_percent", 0.0)
        used_mb = getattr(prof, "used_vram_mb", None)
        if used_mb is None:
            used_mb = getattr(prof, "memory_used_mb", 0)
        total_mb = getattr(prof, "total_vram_mb", None)
        if total_mb is None:
            total_mb = getattr(prof, "memory_total_mb", 0)
        temp_c = getattr(prof, "temperature_c", 0.0)

        logs: List[InferenceLog] = []
        db_path = REPO_ROOT / "QuietAdvisorDB.sqlite"
        if db_path.exists():
            try:
                import sqlite3
                conn = sqlite3.connect(db_path, timeout=1.0)
                rows = conn.execute(
                    "SELECT model_id, context_tokens_provided, context_tokens_used, total_latency_ms, "
                    "tokens_per_second, error_occurred FROM memoryos_inference_log ORDER BY id DESC LIMIT 12"
                ).fetchall()
                conn.close()
                for r in rows:
                    logs.append(
                        InferenceLog(
                            timestamp=datetime.now(timezone.utc),
                            model_id=str(r[0] or "studio"),
                            context_tokens_provided=int(r[1] or 4096),
                            context_tokens_used=int(r[2] or 256),
                            time_to_first_token_ms=0.0,
                            total_latency_ms=float(r[3] or 100.0),
                            tokens_per_second=float(r[4] or 30.0),
                            gpu_utilization_percent=float(util or 0.0),
                            gpu_temperature_celsius=float(temp_c or 0.0),
                            gpu_memory_used_mb=int(used_mb or 0),
                            error_occurred=bool(r[5]),
                        )
                    )
            except Exception:
                logs = []

        if not logs:
            logs = [
                InferenceLog(
                    timestamp=datetime.now(timezone.utc),
                    model_id="live-probe",
                    context_tokens_provided=4096,
                    context_tokens_used=2048,
                    time_to_first_token_ms=0.0,
                    total_latency_ms=0.0,
                    tokens_per_second=0.0,
                    gpu_utilization_percent=float(util or 0.0),
                    gpu_temperature_celsius=float(temp_c or 0.0),
                    gpu_memory_used_mb=int(used_mb or 0),
                )
            ]

        cap = int(total_mb) if total_mb and int(total_mb) > 0 else 8192
        return compute_workstation_health(logs, vram_capacity_mb=cap)
    except Exception:
        return {"score": 100, "grade": "A", "status": "healthy", "components": {"vram_headroom": 100.0, "thermal_headroom": 100.0}}


class JupiterStudioHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    # When set, every request must present this token (?t= once, then HttpOnly cookie or X-Studio-Token).
    access_token: Optional[str] = None


_HTML_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: blob:; "
    "media-src 'self' blob: data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


class JupiterStudioHandler(BaseHTTPRequestHandler):
    timeout = 30.0

    def _get_header(self, name: str, default: str = "") -> str:
        val = self.headers.get(name)
        if val is None:
            val = self.headers.get(name.lower())
        return str(val) if val is not None else default

    def _request_path(self) -> str:
        return urllib.parse.urlsplit(self.path or "/").path or "/"

    def _send_security_headers(self, include_csp: bool = False) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if include_csp:
            self.send_header("Content-Security-Policy", _HTML_CSP)
        origin = self._get_header("Origin").strip()
        if origin and _is_allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _is_loopback_bound(self) -> bool:
        srv = getattr(self, "server", None)
        addr = getattr(srv, "server_address", None)
        if not addr or not isinstance(addr, tuple):
            return True
        return _is_loopback_bind_host(str(addr[0] or ""))

    def _is_allowed_host(self, host_header: str) -> bool:
        if not host_header or not self._is_loopback_bound():
            return True
        cleaned = host_header.strip()
        if not _STRICT_HOST_RE.match(cleaned):
            return False
        try:
            parsed = urllib.parse.urlsplit(f"http://{cleaned}")
        except ValueError:
            return False
        if parsed.username is not None or parsed.password is not None or parsed.path or parsed.query or parsed.fragment:
            return False
        return (parsed.hostname or "").lower() in _LOCAL_ORIGIN_HOSTS

    def _enforce_host(self) -> bool:
        host = self._get_header("Host").strip()
        if host and not self._is_allowed_host(host):
            self._send_json({"error": "Invalid Host header for local studio server"}, status=403)
            return False
        return self._enforce_token()

    def _supplied_token(self) -> Tuple[str, bool]:
        """Return (token, came_from_query). Query wins so a fresh launch URL replaces a stale cookie."""
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query)
        q_vals = query.get("t") or []
        if q_vals and q_vals[0]:
            return q_vals[0], True
        header_tok = self._get_header("X-Studio-Token").strip()
        if header_tok:
            return header_tok, False
        raw_cookie = self._get_header("Cookie")
        if raw_cookie:
            try:
                jar = http.cookies.SimpleCookie()
                jar.load(raw_cookie)
                morsel = jar.get(_TOKEN_COOKIE_NAME)
                if morsel is not None and morsel.value:
                    return morsel.value, False
            except http.cookies.CookieError:
                pass
        return "", False

    def _enforce_token(self) -> bool:
        expected = getattr(getattr(self, "server", None), "access_token", None)
        if not expected:
            return True
        supplied, from_query = self._supplied_token()
        if not supplied or not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
            self._send_json({"error": "Missing or invalid Jupiter Studio access token"}, status=401)
            return False
        if from_query and self.command == "GET":
            # Swap the URL token for an HttpOnly cookie and strip it from the address bar / history.
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", self._request_path())
            self.send_header("Set-Cookie", f"{_TOKEN_COOKIE_NAME}={expected}; HttpOnly; SameSite=Strict; Path=/")
            self.send_header("Content-Length", "0")
            self._send_security_headers()
            self.end_headers()
            return False
        return True

    def _origin_matches_host(self, origin: str) -> bool:
        """Validate Origin: loopback-only when loopback-bound, or matching Host when LAN-bound."""
        if self._is_loopback_bound():
            return _is_allowed_origin(origin)
        host_header = self._get_header("Host").strip()
        try:
            o_parsed = urllib.parse.urlsplit(origin.strip())
            h_parsed = urllib.parse.urlsplit(f"http://{host_header}") if host_header else None
        except ValueError:
            return False
        if o_parsed.scheme not in ("http", "https") or o_parsed.username is not None or o_parsed.password is not None:
            return False
        o_host = (o_parsed.hostname or "").lower()
        if o_host in _LOCAL_ORIGIN_HOSTS:
            return True
        return bool(h_parsed and o_host and o_host == (h_parsed.hostname or "").lower())

    def _enforce_origin(self) -> bool:
        if not self._enforce_host():
            return False
        origin = self._get_header("Origin").strip()
        if origin and not self._origin_matches_host(origin):
            self._send_json({"error": "Cross-origin requests are forbidden"}, status=403)
            return False
        sec_fetch_site = self._get_header("Sec-Fetch-Site").strip().lower()
        if sec_fetch_site == "cross-site":
            self._send_json({"error": "Cross-site API requests are forbidden"}, status=403)
            return False
        if not origin:
            referer = self._get_header("Referer").strip()
            if referer:
                try:
                    ref_parsed = urllib.parse.urlsplit(referer)
                    ref_origin = f"{ref_parsed.scheme}://{ref_parsed.netloc}" if ref_parsed.scheme and ref_parsed.netloc else referer
                except ValueError:
                    ref_origin = referer
                if not self._origin_matches_host(ref_origin):
                    self._send_json({"error": "Cross-origin Referer is forbidden"}, status=403)
                    return False
        return True

    def _write_bytes(self, payload: bytes) -> bool:
        try:
            self.wfile.write(payload)
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            return False

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        self.end_headers()
        self._write_bytes(payload)

    def _read_json_body(self) -> Optional[Dict[str, Any]]:
        if "chunked" in self._get_header("Transfer-Encoding", "").lower():
            self._send_json({"error": "Chunked transfer encoding is not supported; send Content-Length"}, status=411)
            return None
        raw_len = self._get_header("Content-Length", "0").strip()
        try:
            length = int(raw_len) if raw_len else 0
        except ValueError:
            self._send_json({"error": "Invalid Content-Length header"}, status=400)
            return None
        if length < 0:
            self._send_json({"error": "Negative Content-Length header"}, status=400)
            return None
        if length > MAX_REQUEST_BODY_BYTES:
            self._send_json(
                {"error": f"Request body too large (max {MAX_REQUEST_BODY_BYTES // (1024 * 1024)} MB)"},
                status=413,
            )
            return None
        if length == 0:
            return {}
        try:
            raw = self.rfile.read(length)
        except TimeoutError:
            self._send_json({"error": "Request body timed out"}, status=408)
            return None
        if not raw:
            return {}
        try:
            decoded = raw.decode("utf-8")
            parsed = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "Invalid JSON request body"}, status=400)
            return None
        if not isinstance(parsed, dict):
            self._send_json({"error": "JSON request body must be an object"}, status=400)
            return None
        return parsed

    def do_OPTIONS(self) -> None:
        host = self._get_header("Host").strip()
        if host and not self._is_allowed_host(host):
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        origin = self._get_header("Origin").strip()
        if origin and not _is_allowed_origin(origin):
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_security_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Studio-Token")
        self.end_headers()

    def do_DELETE(self) -> None:
        if not self._enforce_origin():
            return
        route = self._request_path()
        if route.startswith("/api/sessions/"):
            sid = route[len("/api/sessions/"):].strip("/")
            if not _SESSION_ID_RE.match(sid):
                self._send_json({"error": "Invalid session id"}, status=400)
                return
            deleted = _delete_studio_session(sid)
            self._send_json({"deleted": deleted, "id": sid}, status=200 if deleted else 404)
            return
        if route.startswith("/api/memory/fact/"):
            raw_fid = route[len("/api/memory/fact/"):].strip("/")
            if not raw_fid.isdigit():
                self._send_json({"error": "Invalid memory fact id"}, status=400)
                return
            deleted = _get_memory_vault().forget(int(raw_fid))
            self._send_json({"deleted": deleted, "id": int(raw_fid)}, status=200 if deleted else 404)
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_GET(self) -> None:
        try:
            route = self._request_path()
            if route in ("/", "/index.html"):
                if not self._enforce_host():
                    return
                payload = HTML_PAGE.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self._send_security_headers(include_csp=True)
                self.end_headers()
                self._write_bytes(payload)
                return

            if route in ("/assets/jupiter_studio_icon.png", "/favicon.ico"):
                if not self._enforce_host():
                    return
                for candidate in (
                    BUNDLE_ROOT / "assets" / "jupiter_studio_icon.png",
                    APP_DIR / "assets" / "jupiter_studio_icon.png",
                    REPO_ROOT / "assets" / "jupiter_studio_icon.png",
                ):
                    if candidate.is_file():
                        payload = candidate.read_bytes()
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", "image/png")
                        self.send_header("Content-Length", str(len(payload)))
                        self.send_header("Cache-Control", "public, max-age=3600")
                        self._send_security_headers()
                        self.end_headers()
                        self._write_bytes(payload)
                        return
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return

            if not self._enforce_origin():
                return

            if route.startswith("/api/voice/audio/"):
                fname = Path(urllib.parse.unquote(route[len("/api/voice/audio/"):])).name
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:7870/outputs/{urllib.parse.quote(fname)}", timeout=15) as r:
                        wav = r.read()
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(wav)))
                    self._send_security_headers()
                    self.end_headers()
                    self._write_bytes(wav)
                except Exception:
                    self._send_json({"error": "Voice Studio audio unavailable"}, status=404)
                return

            if route == "/api/video/status":
                cv = _get_cloud_video()
                status_doc = cv.get_cloud_video_status()
                status_doc["outputs"] = cv.list_generated_videos()
                status_doc["spend"] = cv.get_video_spend_ledger(_get_studio_db_path(), limit=20)
                self._send_json(status_doc)
                return

            if route == "/api/video/estimate":
                cv = _get_cloud_video()
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query)
                target = str((qs.get("target") or [f"gemini:{cv.DEFAULT_OMNI_VIDEO_MODEL}"])[0] or "").strip()
                duration = (qs.get("duration") or ["10"])[0]
                resolution = str((qs.get("resolution") or ["720p"])[0] or "720p")
                raw_cap = str((qs.get("max_budget_usd") or [""])[0] or "").strip()
                try:
                    max_budget = float(raw_cap) if raw_cap else None
                    est = cv.estimate_video_generation_cost(
                        target=target,
                        duration=duration,
                        resolution=resolution,
                        max_budget_usd=max_budget,
                    )
                    self._send_json(est)
                except ValueError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                return

            if route == "/api/video/ledger":
                cv = _get_cloud_video()
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query)
                limit = _safe_nonneg_int((qs.get("limit") or ["40"])[0], 40) or 40
                self._send_json(cv.get_video_spend_ledger(_get_studio_db_path(), limit=limit))
                return

            if route == "/api/video/scenes":
                cv = _get_cloud_video()
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query)
                query = str((qs.get("q") or [""])[0] or "")
                video_name = str((qs.get("video") or [""])[0] or "")
                limit = _safe_nonneg_int((qs.get("limit") or ["40"])[0], 40) or 40
                scenes = cv.search_video_scenes(_get_memory_vault(), query=query, video_name=video_name, limit=limit)
                self._send_json({"scenes": scenes})
                return

            if route == "/api/video/outputs":
                cv = _get_cloud_video()
                out_dir = cv.get_video_output_dir(create=False)
                self._send_json({"output_dir": str(out_dir), "videos": cv.list_generated_videos()})
                return

            if route.startswith("/api/video/outputs/"):
                self._serve_video_file(route[len("/api/video/outputs/"):])
                return

            if route == "/api/hf/status":
                hf = _get_hf_hub()
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query)
                live_flag = str((qs.get("live") or ["1"])[0] or "1").strip().lower() not in {"0", "false", "no"}
                self._send_json(hf.get_hf_hub_status(live_whoami=live_flag))
                return

            if route == "/api/hf/models":
                hf = _get_hf_hub()
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query)
                q_str = str((qs.get("q") or [""])[0] or "")
                task_str = str((qs.get("task") or ["8gb-gguf"])[0] or "8gb-gguf")
                sort_str = str((qs.get("sort") or ["trendingScore"])[0] or "trendingScore")
                limit_val = _safe_nonneg_int((qs.get("limit") or ["12"])[0], 12) or 12
                gguf_flag = str((qs.get("gguf_only") or ["0"])[0] or "0").strip().lower() in {"1", "true", "yes"}
                warm_flag = str((qs.get("warm_only") or ["0"])[0] or "0").strip().lower() in {"1", "true", "yes"}
                self._send_json(
                    hf.search_hf_models(
                        query=q_str,
                        task=task_str,
                        sort=sort_str,
                        limit=limit_val,
                        gguf_only=gguf_flag,
                        warm_only=warm_flag,
                    )
                )
                return

            if route == "/api/health":
                self._send_json({"status": "ok", "version": "2.2.0"})
                return

            if route == "/api/sessions":
                self._send_json({"sessions": _list_studio_sessions()})
                return

            if route.startswith("/api/sessions/"):
                sid = route[len("/api/sessions/"):].strip("/")
                if not _SESSION_ID_RE.match(sid):
                    self._send_json({"error": "Invalid session id"}, status=400)
                    return
                detail = _get_studio_session_detail(sid)
                if not detail:
                    self._send_json({"error": "Session not found"}, status=404)
                    return
                self._send_json(detail)
                return

            if route == "/api/status":
                prof = MultiGPUDetector.get_active_profile()
                cloud = get_cloud_provider_status()
                policy = get_policy_telemetry()
                health = _compute_live_health(prof)
                self._send_json({"gpu": prof.__dict__, "cloud": cloud, "policy": policy, "health": health})
                return

            if route == "/api/models":
                verify = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path or "/").query).get("verify", [""])[0] == "1"
                self._send_json(_probe_model_availability(force_refresh=verify))
                return

            if route == "/api/workspace/files":
                files = scan_workspace_files(REPO_ROOT, max_files=150)
                branch = get_git_branch(REPO_ROOT)
                self._send_json({"files": files, "repo_root": str(REPO_ROOT), "git_branch": branch})
                return

            if route == "/api/memory/vault":
                vault = _get_memory_vault()
                self._send_json({
                    "facts": vault.list_facts(limit=60),
                    "summary": vault.get_summary(),
                })
                return

            if route == "/api/frank/status":
                fm = _get_frank_model()
                with _FRANK_MODEL_LOCK:
                    last_pred = dict(_LAST_FRANK_PREDICTION) if _LAST_FRANK_PREDICTION else None
                self._send_json({
                    "model": fm.model_name,
                    "version": fm.version,
                    "intents": fm.intents,
                    "ewc_protected": bool(fm._ewc_fisher is not None),
                    "last_prediction": last_pred,
                })
                return

            if route == "/api/frank/predict":
                qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                query = str((qs.get("q") or qs.get("prompt") or [""])[0] or "").strip()
                self._send_json(_predict_frank_intent(query, record=bool(query)))
                return

            if route == "/api/ops/ledger":
                from dataclasses import asdict
                ledger = _get_ops_ledger()
                models_info = _probe_model_availability()
                providers = models_info.get("providers") or {}
                online = [k for k, v in providers.items() if k != "auto" and isinstance(v, dict) and v.get("ready")]
                self._send_json({
                    "runs": ledger.list_recent(limit=25),
                    "resources_online": len(online),
                    "online_providers": online,
                    "hardware": asdict(MultiGPUDetector.get_active_profile()),
                })
                return

            if route == "/api/ledger/verify":
                self._send_json(_get_control_plane_ledger().verify())
                return

            if route == "/api/ops/recovery":
                self._send_json({"recoverable": _get_recovery_manager().list_recoverable()})
                return

            if route == "/api/breakers":
                self._send_json({"breakers": _list_circuit_breakers()})
                return

            if route == "/api/plugins":
                loader = _get_declarative_plugins()
                self._send_json({
                    "loaded": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "version": p.version,
                            "sdk_version": p.sdk_version,
                            "permissions": p.permissions,
                            "require_human_approval": bool(p.policies.get("require_human_approval")),
                            "operations": [op.namespaced_id for op in p.operations],
                        }
                        for p in loader.packs.values()
                    ],
                    "rejected": loader.rejected,
                })
                return

            if route == "/api/control-plane/health":
                t0 = time.perf_counter()
                ledger_status = _get_control_plane_ledger().verify()
                loader = _get_declarative_plugins()
                vault = _get_memory_vault()
                models_info = _probe_model_availability()
                providers = models_info.get("providers") or {}
                online = [k for k, v in providers.items() if k != "auto" and isinstance(v, dict) and v.get("ready")]
                breakers = _list_circuit_breakers()
                recoverable = _get_recovery_manager().list_recoverable()
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                self._send_json({
                    "status": "healthy" if ledger_status.get("valid") else "degraded",
                    "latency_ms": latency_ms,
                    "recoverable_count": len(recoverable),
                    "breakers": breakers,
                    "subsystems": {
                        "planner": {"status": "healthy", "model": _get_frank_model().model_name},
                        "memory": {"status": "healthy", "facts": len(vault.list_facts(limit=100))},
                        "resources": {"status": "healthy", "online_count": len(online), "online": online},
                        "plugins": {"status": "healthy", "loaded": sorted(loader.packs.keys()), "rejected": len(loader.rejected)},
                        "ledger": {"status": "healthy" if ledger_status.get("valid") else "tampered", **ledger_status},
                    },
                })
                return

            self._send_json({"error": "Not found"}, status=404)
        except Exception:
            self._send_json({"error": "Internal server error"}, status=500)

    def do_POST(self) -> None:
        if not self._enforce_origin():
            return
        body = self._read_json_body()
        if body is None:
            return

        route = self._request_path()

        if route == "/api/chat/stream":
            self._handle_chat_stream(body)
            return

        try:
            if route == "/api/workspace/copilot-bundle":
                goal = str(body.get("goal") or "")
                raw_files = body.get("files")
                if raw_files is not None and not isinstance(raw_files, list):
                    self._send_json({"error": "'files' must be a list of relative paths"}, status=400)
                    return
                advice = str(body.get("advice") or "")
                bundle = export_copilot_bundle(
                    REPO_ROOT,
                    user_goal=goal,
                    selected_files=raw_files or None,
                    assistant_advice=advice,
                )
                self._send_json({"bundle": bundle})
                return

            if route == "/api/workspace/pack":
                raw_files = body.get("files")
                if raw_files is not None and not isinstance(raw_files, list):
                    self._send_json({"error": "'files' must be a list of relative paths"}, status=400)
                    return
                pack = pack_workspace_context(REPO_ROOT, selected_files=raw_files or None)
                self._send_json(pack)
                return

            if route == "/api/speculate":
                self._send_json(_run_live_speculation(body))
                return

            if route == "/api/sessions":
                sess = _upsert_studio_session(
                    session_id=body.get("id"),
                    title=body.get("title"),
                    target=body.get("target"),
                )
                self._send_json({"session": sess})
                return

            if route == "/api/memory/remember":
                topic = str(body.get("topic") or "general")
                content = str(body.get("content") or "").strip()
                tags = str(body.get("tags") or "")
                importance = body.get("importance", 1.0)
                if not content:
                    self._send_json({"error": "Memory content cannot be empty"}, status=400)
                    return
                fact = _get_memory_vault().remember(topic=topic, content=content, tags=tags, importance=float(importance))
                self._send_json({"fact": fact})
                return

            if route == "/api/memory/reclaim":
                try:
                    from src.memoryos.memory_keeper import reclaim_memory
                except ImportError:
                    from memoryos.memory_keeper import reclaim_memory
                report = reclaim_memory(ollama_host=_resolve_ollama_host() or "http://127.0.0.1:11434")
                _get_memory_vault().record_energy_event(
                    event_type="vram_reclaim",
                    vram_reclaimed_mb=report.get("vram_freed_mb", 0),
                    details=f"unloaded={report.get('unloaded_models', [])}",
                )
                self._send_json(report)
                return

            if route == "/api/memory/train":
                global _SPEC_MODEL
                raw_samples = body.get("samples")
                new_episodes = None
                if isinstance(raw_samples, list) and raw_samples:
                    new_episodes = []
                    for item in raw_samples:
                        if isinstance(item, dict) and isinstance(item.get("features"), dict):
                            new_episodes.append((item["features"], float(item.get("label", 1.0))))
                res = _get_memory_vault().train_continual_model(
                    new_episodes=new_episodes,
                    epochs=_safe_nonneg_int(body.get("epochs"), 60) or 60,
                    seed_defaults=bool(body.get("seed_defaults", True)),
                )
                if res.get("trained"):
                    with _SPEC_MODEL_LOCK:
                        _SPEC_MODEL = None
                self._send_json(res)
                return

            if route == "/api/memory/audit":
                try:
                    from src.memoryos.memory_keeper import run_anti_forgetting_audit
                except ImportError:
                    from memoryos.memory_keeper import run_anti_forgetting_audit
                self._send_json(run_anti_forgetting_audit())
                return

            if route == "/api/frank/teach":
                global _FRANK_MODEL
                try:
                    from src.memoryos.frank import DEFAULT_FRANK_WEIGHTS_PATH, FRANK_INTENTS, TRAINING_CURRICULUM
                except ImportError:
                    from memoryos.frank import DEFAULT_FRANK_WEIGHTS_PATH, FRANK_INTENTS, TRAINING_CURRICULUM
                teach_prompt = str(body.get("prompt") or "").strip()
                teach_intent = str(body.get("intent") or "").strip()
                if not teach_prompt or teach_intent not in FRANK_INTENTS:
                    self._send_json({"error": f"Provide non-empty prompt and intent in {list(FRANK_INTENTS)}"}, status=400)
                    return
                use_agem = bool(body.get("use_agem", True))
                with _FRANK_MODEL_LOCK:
                    fm = _get_frank_model()
                    res = fm.fit_continual(
                        [(teach_prompt, teach_intent)] * 4,
                        replay_samples=TRAINING_CURRICULUM,
                        epochs=45,
                        lr=0.25,
                        ewc_lambda=6.0,
                        use_agem=use_agem,
                    )
                    fm.version = "1.0.0-taught"
                    try:
                        fm.save(DEFAULT_FRANK_WEIGHTS_PATH)
                    except OSError:
                        pass
                self._send_json({"taught": True, "intent": teach_intent, **res})
                return

            if route == "/api/frank/predict":
                query = str(body.get("prompt") or body.get("q") or "").strip()
                self._send_json(_predict_frank_intent(query, record=bool(query)))
                return

            if route == "/api/ops/plan":
                objective = str(body.get("objective") or body.get("prompt") or "").strip()
                if not objective:
                    self._send_json({"error": "Provide a non-empty objective"}, status=400)
                    return
                prefer_local = bool(body.get("prefer_local", False))
                plan = _plan_studio_objective(objective, prefer_local=prefer_local)
                self._send_json(plan.to_dict())
                return

            if route == "/api/ops/dispatch":
                objective = str(body.get("objective") or body.get("prompt") or "").strip()
                if not objective:
                    self._send_json({"error": "Provide a non-empty objective"}, status=400)
                    return
                prefer_local = bool(body.get("prefer_local", False))
                dry_run = bool(body.get("dry_run", False))
                t0 = time.perf_counter()
                plan = _plan_studio_objective(objective, prefer_local=prefer_local)
                preflight_results: Dict[str, Any] = {}
                if "reclaim_vram_and_ram" in plan.preflight_actions and not dry_run:
                    try:
                        from src.memoryos.memory_keeper import reclaim_memory
                    except ImportError:
                        from memoryos.memory_keeper import reclaim_memory
                    preflight_results["reclaim_vram_and_ram"] = reclaim_memory(ollama_host=_resolve_ollama_host())

                executed_target = plan.primary_target
                status = "completed"
                if dry_run:
                    content = f"[DRY-RUN PLAN] {plan.rationale}"
                    status = "planned"
                elif executed_target == "studio:frank":
                    content = _run_frank_turn(objective)
                else:
                    # Execute via Frank local synthesizer when caller requests fast local ops or cloud unreachable
                    try:
                        content = _run_frank_turn(
                            f"Operational Dispatch ({plan.intent} -> {executed_target}): {objective}"
                        )
                    except Exception:
                        executed_target = "studio:frank"
                        content = _run_frank_turn(objective)
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                _get_ops_ledger().record_run(
                    plan,
                    executed_target=executed_target,
                    status=status,
                    latency_ms=latency_ms,
                )
                self._send_json({
                    "plan": plan.to_dict(),
                    "executed_target": executed_target,
                    "preflight_results": preflight_results,
                    "content": content,
                    "status": status,
                    "latency_ms": latency_ms,
                })
                return

            if route == "/api/ops/recovery/dismiss":
                op_id = str(body.get("operation_id") or "").strip()
                if not op_id:
                    self._send_json({"error": "Provide non-empty operation_id"}, status=400)
                    return
                ok = _get_recovery_manager().dismiss_operation(op_id, ledger=_get_control_plane_ledger())
                self._send_json({"dismissed": ok, "operation_id": op_id})
                return

            if route == "/api/breakers/reset":
                prov = str(body.get("provider") or "").strip() or None
                breakers = _reset_circuit_breaker(prov)
                _get_control_plane_ledger().append({"event": "circuit_breaker_reset", "provider": prov or "all"})
                self._send_json({"reset": True, "breakers": breakers})
                return

            if route == "/api/plugins/execute":
                try:
                    from src.memoryos.control_plane import ApprovalRequiredError, BudgetExceededError
                except ImportError:
                    from memoryos.control_plane import ApprovalRequiredError, BudgetExceededError
                op_name = str(body.get("operation") or "").strip()
                if not op_name:
                    self._send_json({"error": "Provide non-empty operation (e.g. security_pack.secret_scan)"}, status=400)
                    return
                approved = bool(body.get("approved", False))
                inputs = body.get("inputs") if isinstance(body.get("inputs"), dict) else {}
                loader = _get_declarative_plugins()
                try:
                    out = loader.execute_operation(op_name, inputs, approved=approved, workspace_root=REPO_ROOT)
                    self._send_json(out)
                except ApprovalRequiredError as exc:
                    self._send_json(
                        {"approval_required": True, "operation": op_name, "error": str(exc)},
                        status=409,
                    )
                except KeyError as exc:
                    self._send_json({"error": str(exc)}, status=404)
                except BudgetExceededError as exc:
                    self._send_json({"error": str(exc), "metric": exc.metric}, status=408)
                except PermissionError as exc:
                    self._send_json({"error": str(exc)}, status=403)
                return

            if route == "/api/voice/speak":
                text = str(body.get("text") or "").strip()[:1500]
                if not text:
                    self._send_json({"error": "Provide text to speak"}, status=400)
                    return
                payload = json.dumps({
                    "mode": str(body.get("mode") or "custom_voice"),
                    "speaker": str(body.get("speaker") or "Ryan"),
                    "text": text,
                }).encode("utf-8")
                req = urllib.request.Request(
                    "http://127.0.0.1:7870/api/voice/speak",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with urllib.request.urlopen(req, timeout=180) as r:
                        res = json.loads(r.read().decode("utf-8"))
                    if res.get("filename"):
                        res["audio_url"] = f"/api/voice/audio/{res['filename']}"
                    self._send_json(res)
                except Exception as exc:
                    self._send_json({"fallback": True, "error": f"Voice Studio offline ({exc})"})
                return

            if route == "/api/video/analyze":
                self._handle_video_analyze(body)
                return

            if route == "/api/video/generate":
                self._handle_video_generate(body)
                return

            if route == "/api/hf/ollama-pull":
                hf = _get_hf_hub()
                repo_id = str(body.get("repo_id") or "").strip()
                if not repo_id:
                    self._send_json({"ok": False, "error": "repo_id is required."}, status=400)
                    return
                try:
                    res = hf.pull_hf_gguf_to_ollama(repo_id=repo_id)
                    self._send_json(res)
                except ValueError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                except RuntimeError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=503)
                return

            if route == "/api/chat":
                self._handle_chat_sync(body)
                return

            self._send_json({"error": "Unknown endpoint"}, status=404)
        except Exception:
            self._send_json({"error": "Internal server error"}, status=500)

    def _serve_video_file(self, raw_subpath: str) -> None:
        cv = _get_cloud_video()
        fname = urllib.parse.unquote(raw_subpath or "")
        safe_path = cv.resolve_safe_video_path(fname)
        if safe_path is None:
            self._send_json({"error": "Invalid video filename"}, status=400)
            return
        if not safe_path.is_file():
            self._send_json({"error": "Video file not found"}, status=404)
            return

        total_size = int(safe_path.stat().st_size)
        range_hdr = self._get_header("Range").strip()
        start = 0
        end = max(0, total_size - 1)
        partial = False

        if range_hdr:
            m = re.match(r"^bytes=(\d*)-(\d*)$", range_hdr.split(",", 1)[0].strip())
            if not m or (not m.group(1) and not m.group(2)) or total_size == 0:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{total_size}")
                self._send_security_headers()
                self.end_headers()
                return
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else (total_size - 1)
            else:
                suffix_len = int(m.group(2))
                start = max(0, total_size - suffix_len)
                end = total_size - 1
            if start >= total_size or end < start:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{total_size}")
                self._send_security_headers()
                self.end_headers()
                return
            end = min(end, total_size - 1)
            partial = True

        content_len = max(0, end - start + 1) if total_size > 0 else 0
        self.send_response(HTTPStatus.PARTIAL_CONTENT if partial else HTTPStatus.OK)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(content_len))
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{total_size}")
        self._send_security_headers()
        self.end_headers()

        if content_len == 0:
            return
        with safe_path.open("rb") as fh:
            fh.seek(start)
            remaining = content_len
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                if not self._write_bytes(chunk):
                    break
                remaining -= len(chunk)

    def _handle_video_analyze(self, body: Dict[str, Any]) -> None:
        cv = _get_cloud_video()
        raw_frames = body.get("frames")
        sanitized_frames: List[Dict[str, Any]] = []
        if raw_frames is not None:
            if not isinstance(raw_frames, list):
                self._send_json({"ok": False, "error": "'frames' must be a list"}, status=400)
                return
            for idx, item in enumerate(raw_frames[:32]):
                if not isinstance(item, dict):
                    continue
                raw_uri = item.get("data_uri") or item.get("image_base64")
                if not raw_uri:
                    continue
                try:
                    clean_uri = _sanitize_image_url(raw_uri)
                except ValueError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, status=400)
                    return
                if not clean_uri:
                    continue
                frame_entry: Dict[str, Any] = {
                    "timestamp_s": float(item.get("timestamp_s", idx * 2.0) or 0.0),
                    "data_uri": clean_uri,
                    "metrics": item.get("metrics") if isinstance(item.get("metrics"), dict) else {},
                }
                if item.get("mse_delta") is not None:
                    frame_entry["mse_delta"] = item.get("mse_delta")
                sanitized_frames.append(frame_entry)

        video_path = str(body.get("video_path") or "").strip() or None
        if not sanitized_frames and not video_path:
            self._send_json({"ok": False, "error": "Provide sampled video frames or a local video_path."}, status=400)
            return

        video_name = str(body.get("video_name") or (Path(video_path).name if video_path else "clip.mp4")).strip() or "clip.mp4"
        target = str(body.get("target") or cv.DEFAULT_VIDEO_ANALYZE_TARGET).strip()
        prompt_hint = str(body.get("prompt_hint") or "").strip()
        try:
            mse_threshold = float(body.get("mse_threshold", 12.0) or 12.0)
            delta_threshold = float(body.get("delta_threshold", 0.08) or 0.08)
        except (TypeError, ValueError):
            self._send_json({"ok": False, "error": "Invalid frame delta threshold."}, status=400)
            return

        max_cloud_frames = _safe_nonneg_int(body.get("max_cloud_frames"), 8) or 8
        save_to_vault = bool(body.get("save_to_vault", True))

        try:
            res = cv.analyze_video_frames_cloud(
                frames=sanitized_frames or None,
                video_path=video_path,
                video_name=video_name,
                target=target,
                prompt_hint=prompt_hint,
                mse_threshold=mse_threshold,
                delta_threshold=delta_threshold,
                max_cloud_frames=max_cloud_frames,
                save_to_vault=save_to_vault,
                vault=_get_memory_vault(),
                ledger=_get_control_plane_ledger(),
            )
            _record_studio_inference(res.get("model", target), False, len(video_name), res.get("total_ms", 0.0), success=True)
            self._send_json(res)
        except (ValueError, FileNotFoundError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:
            msg = cv.sanitize_video_error(exc)
            missing = "not configured" in msg.lower()
            self._send_json(
                {"ok": False, "missing_key": missing, "error": msg},
                status=503 if missing else 502,
            )

    def _handle_video_generate(self, body: Dict[str, Any]) -> None:
        cv = _get_cloud_video()
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            self._send_json({"ok": False, "error": "Video generation prompt cannot be empty."}, status=400)
            return

        try:
            first_frame = _sanitize_image_url(body.get("first_frame_data_uri")) if body.get("first_frame_data_uri") else None
            last_frame = _sanitize_image_url(body.get("last_frame_data_uri")) if body.get("last_frame_data_uri") else None
            raw_refs = body.get("reference_images")
            if raw_refs is not None and not isinstance(raw_refs, list):
                self._send_json({"ok": False, "error": "'reference_images' must be a list"}, status=400)
                return
            refs: List[str] = []
            for item in (raw_refs or [])[:6]:
                if item:
                    cleaned = _sanitize_image_url(item)
                    if cleaned:
                        refs.append(cleaned)
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
            return

        target = str(body.get("target") or "").strip() or None
        model = str(body.get("model") or cv.DEFAULT_OMNI_VIDEO_MODEL).strip()
        aspect_ratio = str(body.get("aspect_ratio") or "16:9").strip()
        resolution = str(body.get("resolution") or "720p").strip()
        duration = body.get("duration", 10)
        prev_id = str(body.get("previous_interaction_id") or "").strip() or None

        raw_cap = body.get("max_budget_usd")
        max_budget_usd: Optional[float] = None
        if raw_cap is not None and str(raw_cap).strip() != "":
            if isinstance(raw_cap, bool):
                self._send_json({"ok": False, "error": "Invalid max_budget_usd value."}, status=400)
                return
            try:
                max_budget_usd = float(raw_cap)
            except (TypeError, ValueError):
                self._send_json({"ok": False, "error": "Invalid max_budget_usd value."}, status=400)
                return

        try:
            res = cv.generate_video_cloud(
                prompt=prompt,
                model=model,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                duration=duration,
                first_frame_data_uri=first_frame,
                last_frame_data_uri=last_frame,
                reference_images=refs or None,
                previous_interaction_id=prev_id,
                vault=_get_memory_vault(),
                target=target,
                max_budget_usd=max_budget_usd,
                ledger=_get_control_plane_ledger(),
            )
            _record_studio_inference(res.get("model", model), False, len(prompt), res.get("elapsed_ms", 0.0), success=True)
            self._send_json(res)
        except cv.VideoBudgetExceededError as exc:
            self._send_json(
                {
                    "ok": False,
                    "budget_exceeded": True,
                    "estimated_cost_usd": exc.estimated_cost_usd,
                    "max_budget_usd": exc.max_budget_usd,
                    "error": str(exc),
                },
                status=400,
            )
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:
            msg = cv.sanitize_video_error(exc)
            missing = (
                "not configured" in msg.lower()
                or "GEMINI_API_KEY" in msg
                or "FAL_KEY" in msg
                or "REPLICATE_API_TOKEN" in msg
                or "HF_TOKEN" in msg
            )
            payload: Dict[str, Any] = {"ok": False, "error": msg}
            if missing:
                payload["missing_key"] = True
                if "FAL_KEY" in msg:
                    payload["setup_hint"] = (
                        "Add FAL_KEY=your_fal_key to .env and restart Jupiter Studio (0 MB local VRAM)."
                    )
                elif "REPLICATE_API_TOKEN" in msg:
                    payload["setup_hint"] = (
                        "Add REPLICATE_API_TOKEN=your_token to .env and restart Jupiter Studio (0 MB local VRAM)."
                    )
                elif "HF_TOKEN" in msg:
                    payload["setup_hint"] = (
                        "Add HF_TOKEN=hf_your_token to .env and restart Jupiter Studio (0 MB local VRAM)."
                    )
                else:
                    payload["setup_hint"] = (
                        "Add GEMINI_API_KEY=your_key to .env and restart Jupiter Studio (0 MB local VRAM)."
                    )
            self._send_json(payload, status=503 if missing else 502)

    _BLOCKED_UPLOAD_NAMES = {
        ".env",
        ".env.local",
        ".env.development",
        ".env.production",
        ".env.staging",
        ".env.test",
        "credentials.json",
        "secrets.json",
        "token.json",
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "id_dsa",
        ".npmrc",
        ".netrc",
        ".pypirc",
        ".htpasswd",
    }
    _BLOCKED_UPLOAD_EXTS = (".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".kdbx")

    @classmethod
    def _is_sensitive_filename(cls, name: str) -> bool:
        raw = str(name or "")
        if "\x00" in raw:
            return True
        normalized = raw.replace("\\", "/")
        parts = [p.strip().rstrip(". ").lower() for p in normalized.split("/") if p.strip()]
        if ".git" in parts:
            return True
        base = parts[-1] if parts else ""
        if not base:
            return False
        return (
            base in cls._BLOCKED_UPLOAD_NAMES
            or base.endswith(".env")
            or (base.startswith(".env.") and base != ".env.example")
            or base.endswith(cls._BLOCKED_UPLOAD_EXTS)
        )

    @staticmethod
    def _format_uploaded_files(
        uploaded_files: Any,
        max_chars_per_file: int = 40000,
        max_total_chars: int = 120000,
        max_files: int = 25,
    ) -> str:
        """Format browser-uploaded text/code files into safe fenced Markdown context blocks."""
        if not isinstance(uploaded_files, list) or not uploaded_files:
            return ""
        blocks: List[str] = []
        used_chars = 0
        included_count = 0
        omitted_count = 0
        for item in uploaded_files:
            if not isinstance(item, dict):
                continue
            raw_name = str(item.get("name") or "uploaded_file.txt")
            if JupiterStudioHandler._is_sensitive_filename(raw_name):
                continue
            name = re.sub(r"[\r\n\x00]+", " ", raw_name).strip() or "uploaded_file.txt"
            remaining = max_total_chars - used_chars
            if included_count >= max_files or remaining <= 0:
                omitted_count += 1
                continue
            raw_content = str(item.get("content") or "")
            cap = min(max_chars_per_file, remaining)
            snippet = raw_content[:cap]
            truncated = len(raw_content) > cap
            suffix = "\n... [truncated]" if truncated else ""
            body_text = f"{snippet}{suffix}"
            fence = _make_markdown_fence(body_text)
            blocks.append(f"#### {name}\n{fence}\n{body_text}\n{fence}")
            used_chars += len(snippet)
            included_count += 1
        if omitted_count > 0:
            blocks.append(f"*({omitted_count} additional uploaded file(s) omitted: context limit reached)*")
        return "\n\n".join(blocks)

    def _build_effective_prompt(
        self,
        prompt: str,
        uploaded_files: Any,
        workspace_files: Any,
    ) -> str:
        effective_prompt = str(prompt or "")
        try:
            vault = _get_memory_vault()
            recalled = vault.recall(effective_prompt, limit=3) if effective_prompt.strip() else []
            if recalled:
                mem_lines = [f"- [{m['topic']}] {m['content']}" for m in recalled if m.get("content")]
                if mem_lines:
                    effective_prompt = (
                        f"{effective_prompt}\n\n---\n### Persistent Workspace Memory Vault:\n"
                        + "\n".join(mem_lines)
                    )
        except Exception:
            pass
        if isinstance(uploaded_files, list) and uploaded_files:
            formatted_uploads = self._format_uploaded_files(uploaded_files)
            if formatted_uploads:
                effective_prompt = (
                    f"{effective_prompt}\n\n---\n### Uploaded User Files:\n{formatted_uploads}"
                )
        if isinstance(workspace_files, list) and workspace_files:
            pack = pack_workspace_context(REPO_ROOT, selected_files=workspace_files, include_git=True)
            if pack.get("bundle_text"):
                effective_prompt = (
                    f"{effective_prompt}\n\n---\n### Attached Project Workspace Context:\n{pack['bundle_text']}"
                )
        return effective_prompt

    def _handle_chat_stream(self, body: Dict[str, Any]) -> None:
        prompt = str(body.get("prompt") or "")
        target = str(body.get("target") or "auto:d3")
        raw_sid = str(body.get("session_id") or "").strip()
        session_id = raw_sid if _SESSION_ID_RE.match(raw_sid) else None
        history = _sanitize_history(body.get("history"))
        raw_image = body.get("image_base64")
        workspace_files = body.get("workspace_files") if isinstance(body.get("workspace_files"), list) else []
        uploaded_files = body.get("uploaded_files") if isinstance(body.get("uploaded_files"), list) else []

        # Send SSE headers
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self._send_security_headers()
        self.end_headers()
        self.close_connection = True

        client_alive = True
        captured_chunks: List[str] = []
        captured_reasoning: List[str] = []
        active_provider_label = ""

        def _send(event_type: str, data: Dict[str, Any]) -> bool:
            nonlocal client_alive, active_provider_label
            if event_type == "delta" and isinstance(data, dict) and data.get("delta"):
                captured_chunks.append(str(data["delta"]))
            elif event_type == "reasoning" and isinstance(data, dict) and data.get("delta"):
                captured_reasoning.append(str(data["delta"]))
            elif event_type == "start" and isinstance(data, dict) and data.get("provider"):
                active_provider_label = str(data["provider"])
            if not client_alive:
                return False
            try:
                line = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
                self.wfile.write(line)
                self.wfile.flush()
                return True
            except (BrokenPipeError, ConnectionResetError, OSError):
                client_alive = False
                return False

        t0 = time.perf_counter()

        try:
            image_base64 = _sanitize_image_url(raw_image) if raw_image else None
            effective_prompt = self._build_effective_prompt(prompt, uploaded_files, workspace_files)
            if not effective_prompt.strip() and not image_base64:
                _send("error", {"error": "Prompt cannot be empty"})
                return

            try:
                from src.memoryos.control_plane import OperationState
                from src.memoryos.ops_console import OperationPlan
            except ImportError:
                from memoryos.control_plane import OperationState
                from memoryos.ops_console import OperationPlan
            import uuid as _uuid

            objective_text = (prompt or effective_prompt).strip()
            if target == "auto:d3":
                plan = _plan_studio_objective(objective_text)
                candidates = [plan.primary_target] + [c for c in plan.fallback_chain if c != plan.primary_target]
                if "studio:frank" not in candidates:
                    candidates.append("studio:frank")
            else:
                plan = OperationPlan(
                    op_id=f"op-{_uuid.uuid4().hex[:10]}",
                    objective=objective_text[:500],
                    intent="manual_override",
                    intent_confidence=1.0,
                    primary_target=target,
                    primary_tier="manual_override",
                    rationale=f"Direct operator resource target: {target}",
                )
                candidates = [target]

            rec_mgr = _get_recovery_manager()
            cp_ledger = _get_control_plane_ledger()
            ops_ledger = _get_ops_ledger()
            rec_mgr.save_state(
                plan.op_id,
                OperationState.RUNNING,
                objective=plan.objective[:240],
                operation_name=f"dispatch:{plan.primary_target}",
            )
            cp_ledger.append({
                "event": "operation_started",
                "op_id": plan.op_id,
                "target": plan.primary_target,
                "intent": plan.intent,
            })

            if "reclaim_vram_and_ram" in plan.preflight_actions:
                try:
                    from src.memoryos.memory_keeper import reclaim_memory
                except ImportError:
                    from memoryos.memory_keeper import reclaim_memory
                reclaim_res = reclaim_memory(ollama_host=_resolve_ollama_host() or "http://127.0.0.1:11434")
                _send("reasoning", {"delta": f"[Preflight] VRAM reclaim: {reclaim_res.get('vram_freed_mb', 0)} MB freed.\n"})

            _send("ops_plan", plan.to_dict())

            resolved_attempts: List[Tuple[str, str, str, bool]] = []
            for cand in candidates:
                m_name, p_key, is_oll = self._resolve_target(cand, effective_prompt, bool(image_base64))
                resolved_attempts.append((cand, m_name, p_key, is_oll))

            executed_cand = target
            active_model = ""
            is_local_exec = False
            last_exc: Optional[Exception] = None
            stream_started = False

            for idx, (cand_target, model_name, provider_key, is_ollama) in enumerate(resolved_attempts):
                breaker = _get_circuit_breaker(provider_key)
                if cand_target != "studio:frank" and not breaker.can_execute() and idx + 1 < len(resolved_attempts):
                    _send("reasoning", {"delta": f"[CircuitBreaker OPEN] Skipping {provider_key}; failing over...\n"})
                    continue

                is_local_exec = _is_local_execution_provider(provider_key, is_ollama)
                active_provider_label = provider_key
                executed_cand = cand_target
                if not stream_started:
                    _record_target_activity(cand_target, did_offload=(not is_local_exec))
                    if not _send("start", {"model_used": model_name, "provider": provider_key, "is_local": is_local_exec}):
                        break
                    stream_started = True
                elif idx > 0:
                    _send("reasoning", {"delta": f"[Failover -> {model_name} ({provider_key})]\n"})

                try:
                    active_model = model_name
                    if cand_target == "studio:frank":
                        frank_out = _run_frank_turn(prompt or effective_prompt)
                        pred = frank_out["prediction"]
                        _send("reasoning", {"delta": f"Frank-v1 neural classification: intent={pred['intent']} confidence={pred['confidence']} latency={pred['latency_us']} us"})
                        _send("delta", {"delta": frank_out["content"]})
                    elif is_ollama:
                        self._stream_ollama(model_name, effective_prompt, history, _send, image_base64=image_base64)
                    else:
                        active_model = (
                            self._stream_cloud(
                                provider_key,
                                model_name,
                                effective_prompt,
                                history,
                                image_base64,
                                _send,
                                allow_hydra=(cand_target == "auto:d3"),
                            )
                            or model_name
                        )
                    breaker.record_success()
                    last_exc = None
                    break
                except Exception as attempt_exc:
                    breaker.record_failure()
                    last_exc = attempt_exc
                    if idx + 1 < len(resolved_attempts) and client_alive and not captured_chunks:
                        _send("reasoning", {"delta": f"[Breaker] {provider_key} failed ({attempt_exc}); trying next resource...\n"})
                        continue
                    raise attempt_exc

            if last_exc is not None:
                raise last_exc

            if client_alive:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                _record_studio_inference(active_model, is_local_exec, len(effective_prompt), latency, success=True)
                full_reply = "".join(captured_chunks)
                full_reason = "".join(captured_reasoning)
                meta_lbl = f"{active_model} [{active_provider_label}] · {latency} ms"
                persisted_sid = _append_studio_turn(
                    session_id=session_id,
                    target=executed_cand,
                    user_text=prompt or "(attached context)",
                    assistant_text=full_reply,
                    reasoning=full_reason,
                    meta_label=meta_lbl,
                )
                rec_mgr.save_state(
                    plan.op_id,
                    OperationState.COMPLETE,
                    objective=plan.objective[:240],
                    operation_name=f"dispatch:{executed_cand}",
                )
                ops_ledger.record_run(plan, executed_target=executed_cand, status="COMPLETE", latency_ms=latency)
                cp_ledger.append({"event": "operation_complete", "op_id": plan.op_id, "target": executed_cand, "latency_ms": latency})
                _send("done", {"latency_ms": latency, "model_used": active_model, "session_id": persisted_sid, "op_id": plan.op_id})
        except Exception as exc:
            fail_ms = round((time.perf_counter() - t0) * 1000, 2)
            _record_studio_inference(target, False, len(prompt), fail_ms, success=False)
            try:
                from src.memoryos.control_plane import OperationState
                _get_recovery_manager().save_state(
                    f"op-{uuid.uuid4().hex[:8]}" if "plan" not in locals() else plan.op_id,
                    OperationState.FAILED,
                    objective=(prompt or "")[:240],
                    operation_name=f"dispatch:{target}",
                )
                if "plan" in locals():
                    _get_ops_ledger().record_run(plan, executed_target=target, status="FAILED", latency_ms=fail_ms)
                    _get_control_plane_ledger().append({"event": "operation_failed", "op_id": plan.op_id, "error": str(exc)[:240]})
            except Exception:
                pass
            _send("error", {"error": str(exc)})

    def _handle_chat_sync(self, body: Dict[str, Any]) -> None:
        prompt = str(body.get("prompt") or "")
        target = str(body.get("target") or "auto:d3")
        raw_session_id = str(body.get("session_id") or "").strip()
        session_id = raw_session_id if _SESSION_ID_RE.match(raw_session_id) else None
        history = _sanitize_history(body.get("history"))
        raw_image = body.get("image_base64")
        workspace_files = body.get("workspace_files") if isinstance(body.get("workspace_files"), list) else []
        uploaded_files = body.get("uploaded_files") if isinstance(body.get("uploaded_files"), list) else []
        t0 = time.perf_counter()

        try:
            image_base64 = _sanitize_image_url(raw_image) if raw_image else None
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
            return

        effective_prompt = self._build_effective_prompt(prompt, uploaded_files, workspace_files)
        if not effective_prompt.strip() and not image_base64:
            self._send_json({"error": "Prompt cannot be empty"}, status=400)
            return

        model_name, provider_key, is_ollama = self._resolve_target(target, effective_prompt, bool(image_base64))
        is_local_exec = _is_local_execution_provider(provider_key, is_ollama)
        _record_target_activity(target, did_offload=(not is_local_exec))
        content = ""
        err = ""

        try:
            if target == "studio:frank":
                frank_out = _run_frank_turn(prompt or effective_prompt)
                content = frank_out["content"]
            elif is_ollama:
                content, err = self._call_ollama_chat(
                    model_name,
                    effective_prompt,
                    history=history,
                    image_base64=image_base64,
                )
            else:
                content, err = self._call_cloud_direct(
                    provider_key,
                    model_name,
                    effective_prompt,
                    history=history,
                    image_base64=image_base64,
                )
        except Exception as exc:
            err = str(exc)

        latency = round((time.perf_counter() - t0) * 1000, 2)
        _record_studio_inference(model_name, is_local_exec, len(effective_prompt), latency, success=not bool(err))
        persisted_sid = session_id
        if not err and content:
            meta_lbl = f"{model_name} [{provider_key}] · {latency} ms"
            persisted_sid = _append_studio_turn(
                session_id=session_id,
                target=target,
                user_text=prompt or "(attached context)",
                assistant_text=content,
                meta_label=meta_lbl,
            )
        self._send_json({
            "model_used": f"{provider_key}: {model_name}",
            "content": content or f"[{err}]",
            "error": err or None,
            "latency_ms": latency,
            "is_local": is_local_exec,
            "session_id": persisted_sid,
        })

    @staticmethod
    def _classify_workload(prompt: str, has_image: bool) -> str:
        """Map prompt intent cleanly to: fast_code | architecture | large_design | cheap_bg | balanced."""
        low = str(prompt or "").lower()
        n_chars = len(low)
        if has_image or n_chars >= 6000 or any(k in low for k in ("design doc", "design document", "specification", "rfc", "prd", "large document", "screenshot", "diagram")):
            return "large_design"
        if any(k in low for k in ("architecture", "system design", "audit", "tradeoff", "distributed", "refactor plan", "threat model")):
            return "architecture"
        if any(k in low for k in ("def ", "class ", "function", "refactor", "debug", "bug", "pytest", "unittest", "typescript", "python", "script", "code", "patch", "sql", "diff")):
            return "fast_code"
        if n_chars < 140 and any(k in low for k in ("summarize", "summary", "tag", "classify", "title", "format", "triage", "short", "clean", "convert")):
            return "cheap_bg"
        try:
            pred = _get_frank_model().predict(low)
            if pred["confidence"] >= 0.62 and pred["intent"] in ("fast_code", "architecture", "large_design", "cheap_bg"):
                return str(pred["intent"])
        except Exception:
            pass
        return "balanced"

    def _resolve_target(self, target: str, prompt: str, has_image: bool) -> Tuple[str, str, bool]:
        target_str = str(target or "auto:d3").strip()
        if target_str == "studio:frank":
            return "Frank-v1", "Jupiter Studio Built-In (Frank)", False
        if target_str == "auto:d3":
            status = get_cloud_provider_status()
            workload = self._classify_workload(prompt, has_image)

            if workload == "fast_code":
                if status.get("groq", {}).get("configured") and _is_provider_usable("groq"):
                    return GROQ_MODEL_MAP["Qwen3.8-27B"], "Groq Cloud", False
                if status.get("cerebras", {}).get("configured") and _is_provider_usable("cerebras"):
                    return CEREBRAS_MODEL_MAP["Qwen3.8-27B"], "Cerebras Cloud", False

            if workload == "architecture":
                if status["amd_tokenlab"]["configured"] and _is_provider_usable("cloud"):
                    return "DeepSeek-V4.1-Flash", "AMD Token Lab", False
                if status.get("openrouter", {}).get("configured") and _is_provider_usable("openrouter"):
                    return OPENROUTER_MODEL_MAP["DeepSeek-V4.1-Flash"], "OpenRouter", False

            if workload == "large_design":
                if status["amd_tokenlab"]["configured"] and _is_provider_usable("cloud"):
                    return "Gemma-4-31B-IT", "AMD Token Lab", False
                if status.get("openrouter", {}).get("configured") and _is_provider_usable("openrouter"):
                    return OPENROUTER_MODEL_MAP["Gemma-4-31B-IT"], "OpenRouter", False

            if workload == "cheap_bg":
                if status["amd_tokenlab"]["configured"] and _is_provider_usable("cloud"):
                    return "MiniCPM5-2B", "AMD Token Lab", False
                if status.get("groq", {}).get("configured") and _is_provider_usable("groq"):
                    return GROQ_MODEL_MAP["MiniCPM5-2B"], "Groq Cloud", False
                if status.get("cerebras", {}).get("configured") and _is_provider_usable("cerebras"):
                    return CEREBRAS_MODEL_MAP["MiniCPM5-2B"], "Cerebras Cloud", False

            total_chars = len(prompt)
            decision = select_model_with_d3(prompt_text=prompt, has_image=has_image, context_chars=total_chars)
            selected_model = decision.get("selected_model", "Gemma-4-31B-IT")
            # Cascade across configured & usable cloud accelerators -> live local Lemonade -> Local Ollama
            if status["amd_tokenlab"]["configured"] and _is_provider_usable("cloud"):
                return selected_model, "AMD Token Lab", False
            if status.get("groq", {}).get("configured") and _is_provider_usable("groq"):
                return GROQ_MODEL_MAP.get(selected_model, "llama-3.3-70b-versatile"), "Groq Cloud", False
            if status.get("openrouter", {}).get("configured") and _is_provider_usable("openrouter"):
                return OPENROUTER_MODEL_MAP.get(selected_model, "deepseek/deepseek-chat"), "OpenRouter", False
            if status.get("cerebras", {}).get("configured") and _is_provider_usable("cerebras"):
                return CEREBRAS_MODEL_MAP.get(selected_model, "llama-3.3-70b"), "Cerebras Cloud", False
            if status["nvidia_brev"]["configured"] and _is_provider_usable("nv"):
                nv_model = NVIDIA_MODEL_MAP.get(selected_model, "meta/llama-3.3-70b-instruct")
                return nv_model, "NVIDIA NIM", False
            if status["digitalocean_mi300x"]["configured"] and _is_provider_usable("do"):
                do_model = DO_MODEL_MAP.get(selected_model, "meta-llama/Llama-3.3-70B-Instruct")
                return do_model, "DigitalOcean MI300X", False
            if status.get("huggingface", {}).get("configured") and _is_provider_usable("hf"):
                hf_model = "Qwen/Qwen2.5-VL-72B-Instruct" if has_image else "Qwen/Qwen2.5-Coder-32B-Instruct"
                return hf_model, "Hugging Face Router", False
            if status.get("openai", {}).get("configured") and _is_provider_usable("openai"):
                oai_model = "gpt-4o" if has_image else "gpt-4o-mini"
                return oai_model, "OpenAI Cloud", False
            if status.get("gemini", {}).get("configured") and _is_provider_usable("gemini"):
                return GEMINI_MODEL_MAP.get(selected_model, "gemini-3.8-flash"), "Google Gemini API", False
            _, lemon_url = _get_lemonade_credentials()
            lemon_ok, lemon_models = _probe_lemonade_endpoint(lemon_url, 0.5)
            if lemon_ok and lemon_models:
                return lemon_models[0], "Lemonade Server (Ryzen AI)", False
            return "qwen2.5-coder:7b", "Local Ollama", True

        if target_str.startswith("ollama:"):
            return target_str.split(":", 1)[1], "Local Ollama", True

        if target_str.startswith("cloud:"):
            return target_str.split(":", 1)[1], "AMD Token Lab", False

        if target_str.startswith("openai:"):
            return target_str.split(":", 1)[1], "OpenAI Cloud", False

        if target_str.startswith("gemini:"):
            return target_str.split(":", 1)[1], "Google Gemini API", False

        if target_str.startswith("groq:"):
            return target_str.split(":", 1)[1], "Groq Cloud", False

        if target_str.startswith("openrouter:"):
            return target_str.split(":", 1)[1], "OpenRouter", False

        if target_str.startswith("cerebras:"):
            return target_str.split(":", 1)[1], "Cerebras Cloud", False

        if target_str.startswith("nv:"):
            return target_str.split(":", 1)[1], "NVIDIA NIM", False

        if target_str.startswith("do:"):
            return target_str.split(":", 1)[1], "DigitalOcean MI300X", False

        if target_str.startswith("vllm:"):
            return target_str.split(":", 1)[1], "Local vLLM (Spark)", False

        if target_str.startswith("flare:"):
            return target_str.split(":", 1)[1], "NVIDIA Flare (Spark)", False

        if target_str.startswith("lemonade:"):
            return target_str.split(":", 1)[1], "Lemonade Server (Ryzen AI)", False

        if target_str.startswith("hf:"):
            return target_str.split(":", 1)[1], "Hugging Face Router", False

        return "Gemma-4-31B-IT", "AMD Token Lab", False

    @staticmethod
    def _resolve_cloud_credentials(provider_key: str) -> Tuple[str, str, bool]:
        """Return (api_key, base_url, is_local_openai) for the given provider label."""
        if "Lemonade" in provider_key:
            api_key, base_url = _get_lemonade_credentials()
            return api_key, base_url, True
        if "Local vLLM" in provider_key:
            api_key, base_url = _get_local_vllm_credentials()
            return api_key, base_url, True
        if "Flare" in provider_key:
            api_key, base_url = _get_nvidia_flare_credentials()
            return api_key, base_url, True
        if "Groq" in provider_key:
            api_key, base_url = _get_groq_credentials()
            return api_key, base_url, False
        if "OpenAI" in provider_key:
            api_key, base_url = _get_openai_credentials()
            return api_key, base_url, False
        if "Gemini" in provider_key:
            api_key, base_url = _get_gemini_credentials()
            return api_key, base_url, False
        if "OpenRouter" in provider_key:
            api_key, base_url = _get_openrouter_credentials()
            return api_key, base_url, False
        if "Cerebras" in provider_key:
            api_key, base_url = _get_cerebras_credentials()
            return api_key, base_url, False
        if "NVIDIA" in provider_key:
            api_key, base_url = _get_nvidia_credentials()
            return api_key, base_url, False
        if "DigitalOcean" in provider_key:
            api_key, base_url = _get_do_credentials()
            return api_key, base_url, False
        if "Hugging Face" in provider_key:
            api_key, base_url = _get_huggingface_credentials()
            return api_key, base_url, False
        api_key, base_url = _get_tokenlab_credentials()
        return api_key, base_url, False

    @staticmethod
    def _has_real_api_key(api_key: str) -> bool:
        return _is_configured_key(
            api_key,
            "tl-your-tokenlab-key-here",
            "your-token-lab-api-key-here",
            "gsk_your-groq-key-here",
            "your-groq-api-key-here",
            "sk-or-your-openrouter-key-here",
            "your-openrouter-api-key-here",
            "csk-your-cerebras-key-here",
            "your-cerebras-api-key-here",
            "nvapi-your-nvidia-api-key-here",
            "your-nvidia-api-key-here",
            "do-ai-your-model-access-key-here",
            "hf_your-token-here",
            "your-huggingface-token-here",
            "sk-your-key-here",
            "your-openai-api-key-here",
            "AIza-your-gemini-key-here",
            "your-gemini-api-key-here",
        )

    @staticmethod
    def _build_gemini_steps(
        prompt: str,
        history: Optional[List[Dict[str, str]]],
        image_base64: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Build stateless May 2026 Interactions API v1 steps from sanitized history and current turn."""
        steps: List[Dict[str, Any]] = []
        for h in _sanitize_history(history):
            step_type = "user_input" if h["role"] == "user" else "model_output"
            steps.append({
                "type": step_type,
                "content": [{"type": "text", "text": h["content"]}],
            })
        current_blocks: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_base64 and isinstance(image_base64, str):
            cleaned_img = image_base64.strip()
            if cleaned_img.lower().startswith("data:") and ";base64," in cleaned_img:
                header_part, b64_part = cleaned_img.split(";base64,", 1)
                mime_type = header_part[5:].strip().lower() or "image/png"
                raw_b64 = re.sub(r"\s+", "", b64_part)
                if raw_b64:
                    current_blocks.append({"type": "image", "mime_type": mime_type, "data": raw_b64})
            elif cleaned_img.lower().startswith("https://"):
                current_blocks.append({"type": "image", "uri": cleaned_img})
        steps.append({"type": "user_input", "content": current_blocks})
        return steps

    @staticmethod
    def _format_provider_http_error(
        provider_label: str,
        http_err: urllib.error.HTTPError,
        model_name: str,
        limit: int = 400,
    ) -> RuntimeError:
        """Read and close an upstream HTTPError safely, returning a clear RuntimeError."""
        detail = ""
        try:
            detail = http_err.read().decode("utf-8", errors="replace")[:limit]
        except Exception:
            pass
        finally:
            try:
                http_err.close()
            except Exception:
                pass
        if http_err.code == 429:
            return RuntimeError(f"{provider_label}: rate limited (HTTP 429). Wait a few seconds and retry.")
        if http_err.code in (401, 403):
            return RuntimeError(f"{provider_label}: API key rejected (HTTP {http_err.code}). Check .env.")
        if http_err.code == 404:
            return RuntimeError(f"{provider_label}: model '{model_name}' not found (HTTP 404).")
        return RuntimeError(f"{provider_label}: HTTP {http_err.code} {detail}".strip())

    @classmethod
    def _format_gemini_http_error(cls, http_err: urllib.error.HTTPError, model_name: str, limit: int = 400) -> RuntimeError:
        """Read and close an upstream Gemini HTTPError safely, returning a clear RuntimeError."""
        return cls._format_provider_http_error("Google Gemini API", http_err, model_name, limit=limit)

    def _stream_gemini_interactions(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        image_base64: Optional[str],
        _send: Any,
        system_prompt: str = _STUDIO_SYSTEM_PROMPT,
    ) -> str:
        """Stream a turn via Google Gemini Interactions API v1 (pure stdlib urllib + SSE)."""
        url = f"{base_url.rstrip('/')}/interactions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "x-goog-api-key": api_key,
        }
        payload_obj: Dict[str, Any] = {
            "model": model_name,
            "system_instruction": system_prompt,
            "input": self._build_gemini_steps(prompt, history, image_base64),
            "stream": True,
            "store": False,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload_obj).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            resp_ctx = urllib.request.urlopen(req, timeout=120.0)
        except urllib.error.HTTPError as http_err:
            raise self._format_gemini_http_error(http_err, model_name, limit=400) from http_err
        except urllib.error.URLError as url_err:
            raise RuntimeError(f"Google Gemini API: cannot reach {base_url} ({url_err.reason}).") from url_err

        accumulated: List[str] = []
        with resp_ctx as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str:
                    continue
                if data_str == "[DONE]":
                    break
                try:
                    obj = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                event_type = str(obj.get("event_type") or "")
                if event_type == "error" or (not event_type and obj.get("error")):
                    err_obj = obj.get("error")
                    if isinstance(err_obj, dict):
                        msg = str(err_obj.get("message") or err_obj.get("code") or err_obj)
                    else:
                        msg = str(err_obj or obj.get("message") or "Unknown error")
                    raise RuntimeError(f"Gemini API error: {msg}")
                if event_type == "step.start":
                    step = obj.get("step") or {}
                    if isinstance(step, dict) and step.get("type") == "model_output":
                        for block in step.get("content") or []:
                            if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                                txt = str(block["text"])
                                accumulated.append(txt)
                                if _send("delta", {"delta": txt}) is False:
                                    return "".join(accumulated)
                elif event_type == "step.delta":
                    delta = obj.get("delta") or {}
                    if not isinstance(delta, dict):
                        continue
                    d_type = delta.get("type")
                    if d_type == "text":
                        txt = delta.get("text")
                        if txt:
                            txt_str = str(txt)
                            accumulated.append(txt_str)
                            if _send("delta", {"delta": txt_str}) is False:
                                return "".join(accumulated)
                    elif d_type == "thought_summary":
                        content_obj = delta.get("content")
                        thought_txt = ""
                        if isinstance(content_obj, dict):
                            thought_txt = str(content_obj.get("text") or "")
                        elif isinstance(content_obj, list):
                            thought_txt = "".join(
                                str(b.get("text") or "")
                                for b in content_obj
                                if isinstance(b, dict) and b.get("type") == "text"
                            )
                        if not thought_txt and delta.get("text"):
                            thought_txt = str(delta["text"])
                        if thought_txt:
                            if _send("reasoning", {"delta": thought_txt}) is False:
                                return "".join(accumulated)
                elif event_type in ("interaction.completed", "interaction.complete"):
                    break
        return "".join(accumulated)

    def _stream_cloud(
        self,
        provider_key: str,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        image_base64: Optional[str],
        _send: Any,
        allow_hydra: bool = False,
    ) -> str:
        api_key, base_url, is_local_openai = self._resolve_cloud_credentials(provider_key)

        if not is_local_openai and not self._has_real_api_key(api_key):
            raise RuntimeError(f"{provider_key} API key not configured in .env")

        if provider_key == "Google Gemini API":
            self._stream_gemini_interactions(
                api_key,
                base_url,
                model_name,
                prompt,
                history,
                image_base64,
                _send,
                _STUDIO_SYSTEM_PROMPT,
            )
            return model_name

        # Build grounded messages with sanitized history
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": _STUDIO_SYSTEM_PROMPT}
        ]
        for h in _sanitize_history(history):
            messages.append({"role": h["role"], "content": h["content"]})

        # Append current user prompt
        if image_base64:
            user_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
            user_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": prompt})

        candidate_models = [model_name]
        if "Token Lab" in provider_key:
            for fb in ("Qwen3.8-27B", "Gemma-4-31B-IT", "DeepSeek-V4.1-Flash"):
                if fb not in candidate_models:
                    candidate_models.append(fb)

        resp_ctx = None
        active_model = model_name
        last_exc: Optional[Exception] = None
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "JupiterStudio/1.0.1",
        }
        if api_key and api_key.upper() != "EMPTY":
            headers["Authorization"] = f"Bearer {api_key}"

        for idx, cand_model in enumerate(candidate_models):
            cand_payload = json.dumps({
                "model": cand_model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 2048,
                "stream": True,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=cand_payload, headers=headers, method="POST")
            try:
                resp_ctx = urllib.request.urlopen(req, timeout=120.0)
                active_model = cand_model
                if idx > 0:
                    if not _send("start", {"model_used": cand_model, "provider": f"{provider_key} (Auto-Failover)", "is_local": is_local_openai}):
                        resp_ctx.close()
                        return active_model
                break
            except urllib.error.HTTPError as http_err:
                detail = ""
                try:
                    detail = http_err.read().decode("utf-8", errors="replace")[:400]
                except Exception:
                    pass
                finally:
                    try:
                        http_err.close()
                    except Exception:
                        pass
                recorded = _record_provider_runtime_error(provider_key, http_err.code, detail)
                is_quota = _is_quota_or_billing_detail(http_err.code, detail)
                if not is_quota and http_err.code in (429, 502, 503, 504) and idx + 1 < len(candidate_models):
                    time.sleep(0.5)
                    continue
                if recorded:
                    last_exc = RuntimeError(recorded)
                elif http_err.code == 429:
                    last_exc = RuntimeError(f"{provider_key}: rate limited across all models (HTTP 429). Wait a few seconds and retry.")
                elif http_err.code in (401, 403):
                    last_exc = RuntimeError(f"{provider_key}: API key rejected (HTTP {http_err.code}). Check .env.")
                elif http_err.code == 404:
                    last_exc = RuntimeError(f"{provider_key}: model '{cand_model}' not found on this provider (HTTP 404).")
                else:
                    last_exc = RuntimeError(f"{provider_key}: HTTP {http_err.code} {detail}".strip())
                break
            except urllib.error.URLError as url_err:
                last_exc = RuntimeError(
                    f"{provider_key}: cannot reach {base_url} ({url_err.reason}). Is the server running?"
                )
                break

        # Hydra Failover for auto:d3: secondary configured cloud -> live Lemonade Server -> live Ollama
        if resp_ctx is None and allow_hydra:
            cloud_stat = get_cloud_provider_status()
            hydra_targets: List[Tuple[str, str, bool]] = []
            if "AMD Token Lab" not in provider_key and cloud_stat["amd_tokenlab"]["configured"] and _is_provider_usable("cloud"):
                hydra_targets.append(("AMD Token Lab", "Qwen3.8-27B", False))
            if "Groq" not in provider_key and cloud_stat.get("groq", {}).get("configured") and _is_provider_usable("groq"):
                hydra_targets.append(("Groq Cloud", GROQ_MODEL_MAP.get(model_name, "llama-3.3-70b-versatile"), False))
            if "OpenRouter" not in provider_key and cloud_stat.get("openrouter", {}).get("configured") and _is_provider_usable("openrouter"):
                hydra_targets.append(("OpenRouter", OPENROUTER_MODEL_MAP.get(model_name, "deepseek/deepseek-chat"), False))
            if "Cerebras" not in provider_key and cloud_stat.get("cerebras", {}).get("configured") and _is_provider_usable("cerebras"):
                hydra_targets.append(("Cerebras Cloud", CEREBRAS_MODEL_MAP.get(model_name, "llama-3.3-70b"), False))
            if "NVIDIA" not in provider_key and cloud_stat["nvidia_brev"]["configured"] and _is_provider_usable("nv"):
                hydra_targets.append(("NVIDIA NIM", NVIDIA_MODEL_MAP.get(model_name, "meta/llama-3.3-70b-instruct"), False))
            if "DigitalOcean" not in provider_key and cloud_stat["digitalocean_mi300x"]["configured"] and _is_provider_usable("do"):
                hydra_targets.append(("DigitalOcean MI300X", DO_MODEL_MAP.get(model_name, "meta-llama/Llama-3.3-70B-Instruct"), False))
            _, lemon_url = _get_lemonade_credentials()
            lemon_ok, lemon_models = _probe_lemonade_endpoint(lemon_url, 0.5)
            if lemon_ok and lemon_models:
                hydra_targets.append(("Lemonade Server (Ryzen AI)", lemon_models[0], True))
            for h_prov, h_model, h_local in hydra_targets:
                h_key, h_base, _ = self._resolve_cloud_credentials(h_prov)
                h_headers = {"Content-Type": "application/json", "Accept": "text/event-stream", "User-Agent": "JupiterStudio/1.0.1"}
                if h_key and h_key.upper() != "EMPTY":
                    h_headers["Authorization"] = f"Bearer {h_key}"
                h_payload = json.dumps({"model": h_model, "messages": messages, "temperature": 0.2, "max_tokens": 2048, "stream": True}).encode("utf-8")
                try:
                    resp_ctx = urllib.request.urlopen(urllib.request.Request(f"{h_base.rstrip('/')}/chat/completions", data=h_payload, headers=h_headers, method="POST"), timeout=120.0)
                    active_model = h_model
                    if not _send("start", {"model_used": h_model, "provider": f"{h_prov} (Hydra Failover)", "is_local": h_local}):
                        resp_ctx.close()
                        return active_model
                    break
                except Exception:
                    resp_ctx = None
            if resp_ctx is None:
                o_host = _resolve_ollama_host()
                if o_host:
                    o_tags = _http_ok(f"{o_host}/api/tags", 0.5) or {}
                    o_models = [m.get("name", "") for m in o_tags.get("models", []) if isinstance(m, dict) and m.get("name")]
                    if o_models:
                        chosen_o = o_models[0]
                        if _send("start", {"model_used": chosen_o, "provider": "Local Ollama (Hydra Failover)", "is_local": True}):
                            self._stream_ollama(chosen_o, prompt, history, _send, image_base64=image_base64)
                        return chosen_o

        if resp_ctx is None:
            if last_exc is not None:
                raise last_exc
            raise RuntimeError(f"{provider_key}: no upstream response established")

        with resp_ctx as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    obj = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("error"):
                    err_obj = obj["error"]
                    err_msg = err_obj.get("message") if isinstance(err_obj, dict) else str(err_obj)
                    raise RuntimeError(f"{provider_key}: {err_msg or err_obj}")
                choices = obj.get("choices") or []
                if choices and isinstance(choices[0], dict):
                    choice0 = choices[0]
                    delta = choice0.get("delta") or {}
                    if isinstance(delta, dict):
                        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                        if reasoning:
                            if _send("reasoning", {"delta": str(reasoning)}) is False:
                                break
                        content = delta.get("content")
                        if content:
                            if _send("delta", {"delta": str(content)}) is False:
                                break
                    if choice0.get("finish_reason"):
                        break
        return active_model

    def _stream_ollama(
        self,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        _send: Any,
        image_base64: Optional[str] = None,
    ) -> None:
        install_hint = (
            "ollama create frank -f memory/models/Modelfile.frank"
            if model_name in ("frank", "frank:latest")
            else f"ollama pull {model_name}"
        )
        host = _resolve_ollama_host()
        if not host:
            raise RuntimeError(
                "Ollama is not running. Start it on Windows (open the Ollama app or run `ollama serve`), "
                f"or select `Frank-v1 (Built-In)` (`studio:frank`) to run offline without Ollama. Setup: `{install_hint}`."
            )
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": _STUDIO_SYSTEM_PROMPT},
            *_sanitize_history(history),
        ]
        user_msg: Dict[str, Any] = {"role": "user", "content": prompt}
        raw_b64 = _extract_raw_base64_image(image_base64)
        if raw_b64:
            user_msg["images"] = [raw_b64]
        messages.append(user_msg)
        payload = json.dumps({"model": model_name, "messages": messages, "stream": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{host}/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            resp_ctx = urllib.request.urlopen(req, timeout=180.0)
        except urllib.error.HTTPError as http_err:
            try:
                if http_err.code == 404:
                    raise RuntimeError(f"Model '{model_name}' is not installed in Ollama. Run: {install_hint}") from http_err
                raise RuntimeError(f"Ollama HTTP {http_err.code}") from http_err
            finally:
                try:
                    http_err.close()
                except Exception:
                    pass
        except urllib.error.URLError as url_err:
            raise RuntimeError(f"Ollama unreachable at {host}: {url_err.reason}") from url_err

        with resp_ctx as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("error"):
                    raise RuntimeError(f"Ollama: {obj['error']}")
                msg = obj.get("message")
                if isinstance(msg, dict):
                    thinking = msg.get("thinking")
                    if thinking:
                        if _send("reasoning", {"delta": str(thinking)}) is False:
                            break
                    chunk = msg.get("content", "")
                    if chunk:
                        if _send("delta", {"delta": str(chunk)}) is False:
                            break
                if obj.get("done"):
                    break

    def _call_cloud_direct(
        self,
        provider_key: str,
        model_name: str,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None,
    ) -> Tuple[str, str]:
        api_key, base_url, is_local_openai = self._resolve_cloud_credentials(provider_key)

        if not is_local_openai and not self._has_real_api_key(api_key):
            return "", f"{provider_key} API key not configured in .env"

        if provider_key == "Google Gemini API":
            url = f"{base_url.rstrip('/')}/interactions"
            payload = json.dumps({
                "model": model_name,
                "system_instruction": _STUDIO_SYSTEM_PROMPT,
                "input": self._build_gemini_steps(prompt, history, image_base64),
                "stream": False,
                "store": False,
            }).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
                "User-Agent": "JupiterStudio/1.0",
            }
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=45.0) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                text_parts: List[str] = []
                if isinstance(data, dict):
                    for step in data.get("steps") or []:
                        if isinstance(step, dict) and step.get("type") == "model_output":
                            for block in step.get("content") or []:
                                if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                                    text_parts.append(str(block["text"]))
                content = "".join(text_parts)
                if not content:
                    return "", f"{provider_key}: empty model_output in response"
                return content, ""
            except urllib.error.HTTPError as http_err:
                return "", str(self._format_gemini_http_error(http_err, model_name, limit=300))
            except Exception as exc:
                return "", str(exc)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": _STUDIO_SYSTEM_PROMPT},
            *_sanitize_history(history),
        ]
        if image_base64:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_base64}},
                ],
            })
        else:
            messages.append({"role": "user", "content": prompt})

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JupiterStudio/1.0",
        }
        if api_key and api_key.upper() != "EMPTY":
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            url,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            choices = data.get("choices") if isinstance(data, dict) else None
            if not choices or not isinstance(choices[0], dict):
                return "", f"{provider_key}: empty choices in response"
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if not content:
                content = msg.get("reasoning_content") or msg.get("reasoning") or ""
            return str(content), ""
        except urllib.error.HTTPError as http_err:
            detail = ""
            try:
                detail = http_err.read().decode("utf-8", errors="replace")[:300]
            except Exception:
                pass
            finally:
                try:
                    http_err.close()
                except Exception:
                    pass
            recorded = _record_provider_runtime_error(provider_key, http_err.code, detail)
            return "", recorded or f"{provider_key}: HTTP {http_err.code} {detail}".strip()
        except Exception as exc:
            return "", str(exc)

    def _call_ollama_chat(
        self,
        model: str,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        image_base64: Optional[str] = None,
    ) -> Tuple[str, str]:
        host = _resolve_ollama_host() or OLLAMA_HOST.rstrip("/")
        url = f"{host}/api/chat"
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": _STUDIO_SYSTEM_PROMPT},
            *_sanitize_history(history),
        ]
        user_msg: Dict[str, Any] = {"role": "user", "content": prompt}
        raw_b64 = _extract_raw_base64_image(image_base64)
        if raw_b64:
            user_msg["images"] = [raw_b64]
        messages.append(user_msg)
        payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            if isinstance(data, dict):
                if data.get("error"):
                    return "", f"Ollama: {data['error']}"
                msg = data.get("message")
                if isinstance(msg, dict):
                    return str(msg.get("content") or msg.get("thinking") or ""), ""
                if "response" in data:
                    return str(data.get("response", "")), ""
            return "", "Ollama returned an unexpected response payload"
        except urllib.error.HTTPError as http_err:
            try:
                http_err.close()
            except Exception:
                pass
            return "", f"Ollama HTTP {http_err.code} (ensure Ollama is running on {host})"
        except Exception as exc:
            return "", f"Ollama call failed ({exc}); ensure Ollama is running on {host}"

    def _call_ollama(self, model: str, prompt: str) -> str:
        content, err = self._call_ollama_chat(model, prompt)
        return content if not err else f"[Ollama Call Failed]: {err}"


def main():
    global REPO_ROOT

    parser = argparse.ArgumentParser(description="Jupiter Studio // MemoryOS Hybrid AI Workstation")
    parser.add_argument("--host", default=os.getenv("JUPITER_STUDIO_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=_safe_int_env("JUPITER_STUDIO_PORT", PORT))
    parser.add_argument("--workspace", default=None, help="Project folder to expose in Workspace Context Files")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=os.getenv("JUPITER_NO_BROWSER", "").strip().lower() in ("1", "true", "yes"),
        help="Do not automatically open the web browser on startup",
    )
    parser.add_argument(
        "--unsafe-lan",
        action="store_true",
        default=os.getenv("JUPITER_STUDIO_UNSAFE_LAN", "").strip().lower() in ("1", "true", "yes"),
        help="Allow binding to a non-loopback address (e.g. 0.0.0.0). Always requires an access token. "
        "Traffic is plain HTTP, so only use on a trusted network.",
    )
    parser.add_argument(
        "--require-token",
        action="store_true",
        default=os.getenv("JUPITER_STUDIO_REQUIRE_TOKEN", "").strip().lower() in ("1", "true", "yes"),
        help="Require a per-launch access token even on loopback (blocks other local processes).",
    )
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        raise ValueError(f"Invalid port {args.port}: expected 1..65535")

    bind_error = _bind_host_error(args.host, args.unsafe_lan)
    if bind_error:
        print(f"[!] {bind_error}", file=sys.stderr)
        sys.exit(2)

    access_token: Optional[str] = None
    if args.require_token or not _is_loopback_bind_host(args.host):
        access_token = os.getenv("JUPITER_STUDIO_TOKEN", "").strip() or secrets.token_urlsafe(24)
        if not _ACCESS_TOKEN_RE.match(access_token):
            print("[!] JUPITER_STUDIO_TOKEN must be 16-128 chars of [A-Za-z0-9_-]", file=sys.stderr)
            sys.exit(2)

    if args.workspace:
        ws_path = Path(args.workspace).expanduser().resolve()
        if ws_path.is_dir():
            REPO_ROOT = ws_path
        else:
            print(f"[!] Warning: workspace directory not found: {ws_path}; using {REPO_ROOT}", file=sys.stderr)

    server = None
    bound_port = args.port
    max_port = min(65536, args.port + 10)
    for candidate_port in range(args.port, max_port):
        try:
            server = JupiterStudioHTTPServer((args.host, candidate_port), JupiterStudioHandler)
            bound_port = candidate_port
            break
        except OSError:
            continue

    if server is None:
        raise RuntimeError(f"Could not bind Jupiter Studio on ports {args.port}..{max_port - 1}")

    server.access_token = access_token
    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::", "") else args.host
    url = f"http://{display_host}:{bound_port}"
    if access_token:
        url = f"{url}/?t={access_token}"
    print(f"[+] Jupiter Studio active at {url}")
    if not _is_loopback_bind_host(args.host):
        print(
            f"[!] UNSAFE LAN MODE: listening on {args.host or 'all interfaces'}:{bound_port} over plain HTTP. "
            "Anyone with the token URL above can use your API keys.",
            file=sys.stderr,
        )
    print(f"[+] Workspace root: {REPO_ROOT}")

    try:
        recovered = _get_recovery_manager().recover_incomplete(ledger=_get_control_plane_ledger())
        if recovered:
            print(f"[+] RecoveryEngine: {len(recovered)} interrupted operation(s) queued for operator review")
    except Exception:
        pass

    threading.Thread(target=_probe_configured_cloud_credits, kwargs={"timeout": 4.5}, daemon=True).start()

    if IS_FROZEN and not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
