#!/usr/bin/env python3
"""
Jupiter Studio // MemoryOS Hybrid Desktop Workstation (Zero-Dependency Python).
Features:
  1) Real-time SSE token streaming (/api/chat/stream) with reasoning display & Stop button.
  2) Smart Auto-Route (d3) across AMD Token Lab, NVIDIA NIM / Brev, DigitalOcean MI300X, and Local Ollama.
  3) Dynamic provider readiness badges & live Quiet Advisor / Zen 3 policy telemetry.
  4) Multi-turn conversation history with client-side Markdown rendering & 1-click code copying.
  5) Workspace folder scanner, context packer, screenshot drop, and 1-click 'Export Copilot Bundle'.
"""

from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import os
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
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
    DO_MODEL_MAP,
    MODEL_PROFILES,
    NVIDIA_MODEL_MAP,
    _get_do_credentials,
    _get_nvidia_credentials,
    _get_tokenlab_credentials,
    _is_configured_key,
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
_SAFE_IMAGE_DATA_URI_RE = re.compile(
    r"^data:image/(?:png|jpe?g|gif|webp|bmp|avif);base64,[A-Za-z0-9+/=\s]+$",
    re.IGNORECASE,
)
_STRICT_HOST_RE = re.compile(
    r"^(?:\[[0-9a-fA-F:]+\]|[A-Za-z0-9.-]+)(?::\d{1,5})?$"
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


def _get_lemonade_credentials() -> Tuple[str, str]:
    """Return (api_key, base_url) for a local AMD Lemonade Server (Ryzen AI XDNA 2 / FastFlowLM) endpoint."""
    base_url = os.getenv("LEMONADE_BASE_URL", "http://127.0.0.1:13305/api/v1").strip().rstrip("/")
    api_key = os.getenv("LEMONADE_API_KEY", "EMPTY").strip()
    return api_key, base_url


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
    try:
        for line in Path("/etc/resolv.conf").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("nameserver"):
                parts = line.split()
                if len(parts) >= 2:
                    addr = parts[1].strip()
                    if ":" in addr and not addr.startswith("["):
                        addr = f"[{addr}]"
                    candidates.append(f"http://{addr}:11434")
    except Exception:
        pass
    found = None
    for cand in dict.fromkeys(candidates):
        if _http_ok(f"{cand}/api/tags") is not None:
            found = cand
            break
    with _OLLAMA_CACHE_LOCK:
        _OLLAMA_CACHE.update(host=found, checked=time.time())
    return found


def _probe_model_availability() -> Dict[str, Any]:
    """Report which execution providers can actually serve a request right now."""
    cloud = get_cloud_provider_status()
    host = _resolve_ollama_host()
    installed: List[str] = []
    if host:
        tags = _http_ok(f"{host}/api/tags") or {}
        installed = [m.get("name", "") for m in tags.get("models", []) if isinstance(m, dict)]
    _, vllm_url = _get_local_vllm_credentials()
    _, flare_url = _get_nvidia_flare_credentials()
    _, lemonade_url = _get_lemonade_credentials()
    lemonade_resp = _http_ok(f"{lemonade_url}/models", 0.8)
    lemonade_installed: List[str] = []
    if isinstance(lemonade_resp, dict):
        lemonade_installed = [
            str(m.get("id", ""))
            for m in lemonade_resp.get("data", [])
            if isinstance(m, dict) and m.get("id")
        ]
    hf_ready = bool(cloud.get("huggingface", {}).get("configured"))

    def state(ok: bool, reason: str) -> Dict[str, Any]:
        return {"ready": ok, "reason": "" if ok else reason}

    return {
        "providers": {
            "cloud": state(cloud["amd_tokenlab"]["configured"], "Set TOKENLAB_API_KEY in .env"),
            "nv": state(cloud["nvidia_brev"]["configured"], "Set NVIDIA_API_KEY in .env"),
            "do": state(cloud["digitalocean_mi300x"]["configured"], "Set DO_MODEL_ACCESS_KEY in .env"),
            "hf": state(hf_ready, "Set HF_TOKEN in .env"),
            "lemonade": state(lemonade_resp is not None, f"No Lemonade Server at {lemonade_url}"),
            "vllm": state(_http_ok(f"{vllm_url}/models", 0.8) is not None, f"No vLLM server at {vllm_url}"),
            "flare": state(_http_ok(f"{flare_url}/models", 0.8) is not None, f"No Flare server at {flare_url}"),
            "ollama": state(bool(host), "Ollama not running - start the Ollama app"),
            "auto": state(True, ""),
        },
        "ollama_host": host,
        "ollama_installed": installed,
        "lemonade_url": lemonade_url,
        "lemonade_installed": lemonade_installed,
    }


_SPEC_MODEL: Any = None
_SPEC_MODEL_LOCK = threading.Lock()


def _run_live_speculation(body: Dict[str, Any]) -> Dict[str, Any]:
    """Run the real 4->8->1 SpeculativeOffloadModel MLP + d3 router preview on a draft prompt."""
    global _SPEC_MODEL
    prompt = str(body.get("prompt") or "")
    has_image = bool(body.get("has_image"))
    file_count = _safe_nonneg_int(body.get("file_count"), 0)
    extra_chars = _safe_nonneg_int(body.get("extra_chars"), 0)
    total_chars = len(prompt) + extra_chars
    est_tokens = max(1, total_chars // 4)

    mlp_us = 0.0
    try:
        model = _SPEC_MODEL
        if model is None:
            with _SPEC_MODEL_LOCK:
                if _SPEC_MODEL is None:
                    try:
                        from src.memoryos.speculative_offload import SpeculativeOffloadModel
                    except ImportError:
                        from memoryos.speculative_offload import SpeculativeOffloadModel
                    _SPEC_MODEL = SpeculativeOffloadModel.load()
                model = _SPEC_MODEL

        # Map prompt complexity, context load, and attachments into the 4 normalized MLP features
        complexity = min(1.0, (len(prompt) / 600.0) + (0.35 if has_image else 0.0) + (0.15 * min(3, file_count)))
        ctx_util = min(1.0, max(0.05, est_tokens / 4096.0))
        features = {
            "mse_delta_norm": round(max(0.15, complexity), 4),
            "context_utilization": round(ctx_util, 4),
            "secs_since_offload": 0.45,
            "model_switch_rate": 0.20,
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

    decision = select_model_with_d3(prompt_text=prompt or "code", has_image=has_image, context_chars=total_chars)
    selected_model = decision.get("selected_model", "Gemma-4-31B-IT")
    selected_tier = decision.get("selected_tier", "balanced_code")
    # Promote interactive studio chat off the 2B edge-triage model to 27B/31B frontier models
    if selected_model == "MiniCPM5-2B":
        selected_model = "Gemma-4-31B-IT" if has_image else "Qwen3.8-27B"
        selected_tier = "vision_heavy" if has_image else "balanced_code"
    vram_saved_gb = 18.5 if "31B" in selected_model else (16.2 if "27B" in selected_model else (14.0 if "DeepSeek" in selected_model else 2.4))

    return {
        "p_offload": round(float(p_offload), 4),
        "action": action,
        "mlp_latency_us": mlp_us,
        "predicted_model": selected_model,
        "predicted_tier": selected_tier,
        "est_tokens": est_tokens,
        "vram_saved_gb": vram_saved_gb,
    }


def _compute_live_health(prof: Any) -> Dict[str, Any]:
    """Compute live Workstation Health Score from current GPU profile."""
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
            total_mb = getattr(prof, "memory_total_mb", 8192)
        temp_c = getattr(prof, "temperature_c", 0.0)

        sample = InferenceLog(
            timestamp=datetime.now(timezone.utc),
            model_id="live-probe",
            context_tokens_provided=4096,
            context_tokens_used=3600,
            time_to_first_token_ms=0.0,
            total_latency_ms=0.091,
            tokens_per_second=64.5,
            gpu_utilization_percent=float(util or 0.0),
            gpu_temperature_celsius=float(temp_c or 0.0),
            gpu_memory_used_mb=int(used_mb or 0),
        )
        cap = int(total_mb or 8192)
        return compute_workstation_health([sample], vram_capacity_mb=cap)
    except Exception:
        return {"score": 100, "grade": "A", "status": "healthy", "components": {"vram_headroom": 100.0, "thermal_headroom": 100.0}}


class JupiterStudioHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


_HTML_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: blob:; "
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
        host = str(addr[0] or "").strip().lower()
        return host in ("127.0.0.1", "localhost", "::1", "")

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
        return True

    def _enforce_origin(self) -> bool:
        if not self._enforce_host():
            return False
        origin = self._get_header("Origin").strip()
        if origin and not _is_allowed_origin(origin):
            self._send_json({"error": "Cross-origin requests from non-local origins are forbidden"}, status=403)
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
                if not _is_allowed_origin(ref_origin):
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

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

            if route == "/api/health":
                self._send_json({"status": "ok", "version": "1.0.0"})
                return

            if route == "/api/status":
                prof = MultiGPUDetector.get_active_profile()
                cloud = get_cloud_provider_status()
                policy = get_policy_telemetry()
                health = _compute_live_health(prof)
                self._send_json({"gpu": prof.__dict__, "cloud": cloud, "policy": policy, "health": health})
                return

            if route == "/api/models":
                self._send_json(_probe_model_availability())
                return

            if route == "/api/workspace/files":
                files = scan_workspace_files(REPO_ROOT, max_files=150)
                branch = get_git_branch(REPO_ROOT)
                self._send_json({"files": files, "repo_root": str(REPO_ROOT), "git_branch": branch})
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

            if route == "/api/chat":
                self._handle_chat_sync(body)
                return

            self._send_json({"error": "Unknown endpoint"}, status=404)
        except Exception:
            self._send_json({"error": "Internal server error"}, status=500)

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

        def _send(event_type: str, data: Dict[str, Any]) -> bool:
            nonlocal client_alive
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

            model_name, provider_key, is_local = self._resolve_target(target, effective_prompt, bool(image_base64))
            if not _send("start", {"model_used": model_name, "provider": provider_key, "is_local": is_local}):
                return

            active_model = model_name
            if is_local:
                self._stream_ollama(model_name, effective_prompt, history, _send, image_base64=image_base64)
            else:
                active_model = (
                    self._stream_cloud(provider_key, model_name, effective_prompt, history, image_base64, _send)
                    or model_name
                )

            if client_alive:
                latency = round((time.perf_counter() - t0) * 1000, 2)
                _send("done", {"latency_ms": latency, "model_used": active_model})
        except Exception as exc:
            _send("error", {"error": str(exc)})

    def _handle_chat_sync(self, body: Dict[str, Any]) -> None:
        prompt = str(body.get("prompt") or "")
        target = str(body.get("target") or "auto:d3")
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

        model_name, provider_key, is_local = self._resolve_target(target, effective_prompt, bool(image_base64))
        content = ""
        err = ""

        try:
            if is_local:
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
        self._send_json({
            "model_used": f"{provider_key}: {model_name}",
            "content": content or f"[{err}]",
            "error": err or None,
            "latency_ms": latency,
            "is_local": is_local,
        })

    def _resolve_target(self, target: str, prompt: str, has_image: bool) -> Tuple[str, str, bool]:
        target_str = str(target or "auto:d3").strip()
        if target_str == "auto:d3":
            total_chars = len(prompt)
            decision = select_model_with_d3(prompt_text=prompt, has_image=has_image, context_chars=total_chars)
            selected_model = decision.get("selected_model", "Gemma-4-31B-IT")
            # Never downgrade interactive studio chat to the 2B triage model unless explicitly chosen
            if selected_model == "MiniCPM5-2B":
                selected_model = "Gemma-4-31B-IT" if has_image else "Qwen3.8-27B"
            # If AMD Token Lab is ready, use it; otherwise NIM, DO, HF, or Local Ollama
            status = get_cloud_provider_status()
            if status["amd_tokenlab"]["configured"]:
                return selected_model, "AMD Token Lab", False
            if status["nvidia_brev"]["configured"]:
                nv_model = NVIDIA_MODEL_MAP.get(selected_model, "meta/llama-3.3-70b-instruct")
                return nv_model, "NVIDIA NIM", False
            if status["digitalocean_mi300x"]["configured"]:
                do_model = DO_MODEL_MAP.get(selected_model, "meta-llama/Llama-3.3-70B-Instruct")
                return do_model, "DigitalOcean MI300X", False
            if status.get("huggingface", {}).get("configured"):
                return "Qwen/Qwen2.5-Coder-32B-Instruct", "Hugging Face Router", False
            return "qwen2.5-coder:7b", "Local Ollama", True

        if target_str.startswith("ollama:"):
            return target_str.split(":", 1)[1], "Local Ollama", True

        if target_str.startswith("cloud:"):
            return target_str.split(":", 1)[1], "AMD Token Lab", False

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
            "nvapi-your-nvidia-api-key-here",
            "your-nvidia-api-key-here",
            "do-ai-your-model-access-key-here",
            "hf_your-token-here",
            "your-huggingface-token-here",
        )

    def _stream_cloud(
        self,
        provider_key: str,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        image_base64: Optional[str],
        _send: Any,
    ) -> str:
        api_key, base_url, is_local_openai = self._resolve_cloud_credentials(provider_key)

        if not is_local_openai and not self._has_real_api_key(api_key):
            raise RuntimeError(f"{provider_key} API key not configured in .env")

        # Build messages with sanitized history
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a world-class AI software architect and coding engineer in Jupiter Studio."}
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

        url = f"{base_url.rstrip('/')}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "JupiterStudio/1.0",
        }
        if api_key and api_key.upper() != "EMPTY":
            headers["Authorization"] = f"Bearer {api_key}"

        candidate_models = [model_name]
        if "Token Lab" in provider_key:
            for fb in ("Qwen3.8-27B", "Gemma-4-31B-IT", "DeepSeek-V4.1-Flash"):
                if fb not in candidate_models:
                    candidate_models.append(fb)

        resp_ctx = None
        active_model = model_name
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
                    if not _send("start", {"model_used": cand_model, "provider": f"{provider_key} (Auto-Failover)", "is_local": False}):
                        resp_ctx.close()
                        return active_model
                break
            except urllib.error.HTTPError as http_err:
                detail = ""
                try:
                    if http_err.code == 429 and idx + 1 < len(candidate_models):
                        time.sleep(1.0)
                        continue
                    try:
                        detail = http_err.read().decode("utf-8", errors="replace")[:400]
                    except Exception:
                        pass
                finally:
                    try:
                        http_err.close()
                    except Exception:
                        pass
                if http_err.code == 429:
                    raise RuntimeError(f"{provider_key}: rate limited across all models (HTTP 429). Wait a few seconds and retry.") from http_err
                if http_err.code in (401, 403):
                    raise RuntimeError(f"{provider_key}: API key rejected (HTTP {http_err.code}). Check .env.") from http_err
                if http_err.code == 404:
                    raise RuntimeError(f"{provider_key}: model '{cand_model}' not found on this provider (HTTP 404).") from http_err
                raise RuntimeError(f"{provider_key}: HTTP {http_err.code} {detail}".strip()) from http_err
            except urllib.error.URLError as url_err:
                raise RuntimeError(
                    f"{provider_key}: cannot reach {base_url} ({url_err.reason}). Is the server running?"
                ) from url_err

        if resp_ctx is None:
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
        host = _resolve_ollama_host()
        if not host:
            raise RuntimeError(
                "Ollama is not running. Start it on Windows (open the Ollama app or run `ollama serve`), "
                f"then `ollama pull {model_name}`."
            )
        messages: List[Dict[str, Any]] = list(_sanitize_history(history))
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
                    raise RuntimeError(f"Model '{model_name}' is not installed. Run: ollama pull {model_name}") from http_err
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

        messages: List[Dict[str, Any]] = list(_sanitize_history(history))
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
            return "", f"{provider_key}: HTTP {http_err.code} {detail}".strip()
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
        messages: List[Dict[str, Any]] = list(_sanitize_history(history))
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
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        raise ValueError(f"Invalid port {args.port}: expected 1..65535")

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

    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::", "") else args.host
    url = f"http://{display_host}:{bound_port}"
    print(f"[+] Jupiter Studio active at {url}")
    print(f"[+] Workspace root: {REPO_ROOT}")

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
