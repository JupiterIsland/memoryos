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
import json
import os
import shutil
import sys
import threading
import time
import urllib.error
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
            for raw in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
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
    pack_workspace_context,
    scan_workspace_files,
)

PORT = int(os.getenv("JUPITER_STUDIO_PORT", 7860))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


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


def _http_ok(url: str, timeout: float = 1.2) -> Optional[Dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except Exception:
        return None


def _resolve_ollama_host() -> Optional[str]:
    """Find a live Ollama server: OLLAMA_HOST, localhost, or the Windows host when running under WSL."""
    now = time.time()
    if now - _OLLAMA_CACHE["checked"] < 10 and _OLLAMA_CACHE["checked"]:
        return _OLLAMA_CACHE["host"]
    candidates = [OLLAMA_HOST.rstrip("/"), "http://127.0.0.1:11434"]
    try:
        for line in Path("/etc/resolv.conf").read_text().splitlines():
            if line.startswith("nameserver"):
                candidates.append(f"http://{line.split()[1]}:11434")
    except Exception:
        pass
    found = None
    for cand in dict.fromkeys(candidates):
        if _http_ok(f"{cand}/api/tags") is not None:
            found = cand
            break
    _OLLAMA_CACHE.update(host=found, checked=now)
    return found


def _probe_model_availability() -> Dict[str, Any]:
    """Report which execution providers can actually serve a request right now."""
    cloud = get_cloud_provider_status()
    host = _resolve_ollama_host()
    installed: List[str] = []
    if host:
        tags = _http_ok(f"{host}/api/tags") or {}
        installed = [m.get("name", "") for m in tags.get("models", [])]
    _, vllm_url = _get_local_vllm_credentials()
    _, flare_url = _get_nvidia_flare_credentials()

    def state(ok: bool, reason: str) -> Dict[str, Any]:
        return {"ready": ok, "reason": "" if ok else reason}

    return {
        "providers": {
            "cloud": state(cloud["amd_tokenlab"]["configured"], "Set TOKENLAB_API_KEY in .env"),
            "nv": state(cloud["nvidia_brev"]["configured"], "Set NVIDIA_API_KEY in .env"),
            "do": state(cloud["digitalocean_mi300x"]["configured"], "Set DO_MODEL_ACCESS_KEY in .env"),
            "vllm": state(_http_ok(f"{vllm_url}/models", 0.8) is not None, f"No vLLM server at {vllm_url}"),
            "flare": state(_http_ok(f"{flare_url}/models", 0.8) is not None, f"No Flare server at {flare_url}"),
            "ollama": state(bool(host), "Ollama not running - start the Ollama app"),
            "auto": state(True, ""),
        },
        "ollama_host": host,
        "ollama_installed": installed,
    }


_SPEC_MODEL: Any = None


def _run_live_speculation(body: Dict[str, Any]) -> Dict[str, Any]:
    """Run the real 4->8->1 SpeculativeOffloadModel MLP + d3 router preview on a draft prompt."""
    global _SPEC_MODEL
    prompt = str(body.get("prompt") or "")
    has_image = bool(body.get("has_image"))
    file_count = int(body.get("file_count") or 0)
    extra_chars = int(body.get("extra_chars") or 0)
    total_chars = len(prompt) + extra_chars
    est_tokens = max(1, total_chars // 4)

    t0 = time.perf_counter_ns()
    try:
        if _SPEC_MODEL is None:
            try:
                from src.memoryos.speculative_offload import SpeculativeOffloadModel
            except ImportError:
                from memoryos.speculative_offload import SpeculativeOffloadModel
            _SPEC_MODEL = SpeculativeOffloadModel.load()

        # Map prompt complexity, context load, and attachments into the 4 normalized MLP features
        complexity = min(1.0, (len(prompt) / 600.0) + (0.35 if has_image else 0.0) + (0.15 * min(3, file_count)))
        ctx_util = min(1.0, max(0.05, est_tokens / 4096.0))
        features = {
            "mse_delta_norm": round(max(0.15, complexity), 4),
            "context_utilization": round(ctx_util, 4),
            "secs_since_offload": 0.45,
            "model_switch_rate": 0.20,
        }
        p_offload = _SPEC_MODEL.predict_proba(features)
        action = _SPEC_MODEL.decide(features)
    except Exception:
        p_offload = 0.88
        action = "offload_now"
    mlp_us = round((time.perf_counter_ns() - t0) / 1000.0, 2)

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

        sample = InferenceLog(
            timestamp=datetime.now(timezone.utc),
            model_id="live-probe",
            context_tokens_provided=4096,
            context_tokens_used=3600,
            time_to_first_token_ms=0.0,
            total_latency_ms=0.091,
            tokens_per_second=64.5,
            gpu_utilization_percent=float(getattr(prof, "utilization_percent", 0.0) or 0.0),
            gpu_temperature_celsius=float(getattr(prof, "temperature_c", 0.0) or 0.0),
            gpu_memory_used_mb=int(getattr(prof, "memory_used_mb", 0) or 0),
        )
        cap = int(getattr(prof, "memory_total_mb", 8192) or 8192)
        return compute_workstation_health([sample], vram_capacity_mb=cap)
    except Exception:
        return {"score": 100, "grade": "A", "status": "healthy", "components": {"vram_headroom": 100.0, "thermal_headroom": 100.0}}


class JupiterStudioHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            payload = HTML_PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path in ("/assets/jupiter_studio_icon.png", "/favicon.ico"):
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
                    self.end_headers()
                    self.wfile.write(payload)
                    return
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        if self.path == "/api/status":
            prof = MultiGPUDetector.get_active_profile()
            cloud = get_cloud_provider_status()
            policy = get_policy_telemetry()
            health = _compute_live_health(prof)
            self._send_json({"gpu": prof.__dict__, "cloud": cloud, "policy": policy, "health": health})
            return

        if self.path == "/api/models":
            self._send_json(_probe_model_availability())
            return

        if self.path == "/api/workspace/files":
            files = scan_workspace_files(REPO_ROOT, max_files=150)
            self._send_json({"files": files, "repo_root": str(REPO_ROOT)})
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            body = {}

        if self.path == "/api/workspace/copilot-bundle":
            goal = body.get("goal", "")
            files = body.get("files") or None
            advice = body.get("advice", "")
            bundle = export_copilot_bundle(REPO_ROOT, user_goal=goal, selected_files=files, assistant_advice=advice)
            self._send_json({"bundle": bundle})
            return

        if self.path == "/api/workspace/pack":
            files = body.get("files") or None
            pack = pack_workspace_context(REPO_ROOT, selected_files=files)
            self._send_json(pack)
            return

        if self.path == "/api/speculate":
            self._send_json(_run_live_speculation(body))
            return

        if self.path == "/api/chat/stream":
            self._handle_chat_stream(body)
            return

        if self.path == "/api/chat":
            self._handle_chat_sync(body)
            return

        self._send_json({"error": "Unknown endpoint"}, status=404)

    _BLOCKED_UPLOAD_NAMES = {".env", ".env.local", ".env.production", "credentials.json", "id_rsa", "id_ed25519"}
    _BLOCKED_UPLOAD_EXTS = (".pem", ".key", ".p12", ".pfx")

    @classmethod
    def _is_sensitive_filename(cls, name: str) -> bool:
        base = Path(str(name or "")).name.lower()
        return (
            base in cls._BLOCKED_UPLOAD_NAMES
            or (base.startswith(".env.") and base != ".env.example")
            or base.endswith(cls._BLOCKED_UPLOAD_EXTS)
        )

    @staticmethod
    def _format_uploaded_files(
        uploaded_files: List[Dict[str, Any]],
        max_chars_per_file: int = 40000,
        max_total_chars: int = 120000,
    ) -> str:
        """Format browser-uploaded text/code files into safe fenced Markdown context blocks."""
        if not uploaded_files:
            return ""
        blocks: List[str] = []
        used_chars = 0
        for item in uploaded_files:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "uploaded_file.txt").strip()
            if JupiterStudioHandler._is_sensitive_filename(name):
                continue
            raw_content = str(item.get("content") or "")
            remaining = max_total_chars - used_chars
            if remaining <= 0:
                blocks.append(f"#### {name}\n*(omitted: total upload context limit reached)*")
                continue
            cap = min(max_chars_per_file, remaining)
            snippet = raw_content[:cap]
            truncated = len(raw_content) > cap
            suffix = "\n... [truncated]" if truncated else ""
            blocks.append(f"#### {name}\n```\n{snippet}{suffix}\n```")
            used_chars += len(snippet)
        return "\n\n".join(blocks)

    def _handle_chat_stream(self, body: Dict[str, Any]) -> None:
        prompt = body.get("prompt", "")
        target = body.get("target", "auto:d3")
        history = body.get("history") or []
        image_base64 = body.get("image_base64")
        workspace_files = body.get("workspace_files") or []
        uploaded_files = body.get("uploaded_files") or []

        # Send SSE headers
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.close_connection = True

        def _send(event_type: str, data: Dict[str, Any]) -> None:
            try:
                line = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
                self.wfile.write(line)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        t0 = time.perf_counter()

        # Build context if workspace or uploaded files were attached
        effective_prompt = prompt
        if uploaded_files:
            formatted_uploads = self._format_uploaded_files(uploaded_files)
            if formatted_uploads:
                effective_prompt = (
                    f"{effective_prompt}\n\n---\n### Uploaded User Files:\n{formatted_uploads}"
                )
        if workspace_files:
            pack = pack_workspace_context(REPO_ROOT, selected_files=workspace_files, include_git=True)
            effective_prompt = (
                f"{effective_prompt}\n\n---\n### Attached Project Workspace Context:\n{pack['bundle_text']}"
            )

        # Resolve model and provider
        model_name, provider_key, is_local = self._resolve_target(target, effective_prompt, bool(image_base64))
        _send("start", {"model_used": model_name, "provider": provider_key, "is_local": is_local})

        # Stream execution
        try:
            if is_local:
                self._stream_ollama(model_name, effective_prompt, history, _send)
            else:
                self._stream_cloud(provider_key, model_name, effective_prompt, history, image_base64, _send)

            latency = round((time.perf_counter() - t0) * 1000, 2)
            _send("done", {"latency_ms": latency, "model_used": model_name})
        except Exception as exc:
            _send("error", {"error": str(exc)})

    def _handle_chat_sync(self, body: Dict[str, Any]) -> None:
        prompt = body.get("prompt", "")
        target = body.get("target", "auto:d3")
        image_base64 = body.get("image_base64")
        uploaded_files = body.get("uploaded_files") or []
        t0 = time.perf_counter()

        effective_prompt = prompt
        if uploaded_files:
            formatted_uploads = self._format_uploaded_files(uploaded_files)
            if formatted_uploads:
                effective_prompt = (
                    f"{effective_prompt}\n\n---\n### Uploaded User Files:\n{formatted_uploads}"
                )

        model_name, provider_key, is_local = self._resolve_target(target, effective_prompt, bool(image_base64))
        content = ""
        err = ""

        try:
            if is_local:
                content = self._call_ollama(model_name, effective_prompt)
            else:
                content, err = self._call_cloud_direct(provider_key, model_name, effective_prompt)
        except Exception as exc:
            err = str(exc)

        latency = round((time.perf_counter() - t0) * 1000, 2)
        self._send_json({
            "model_used": f"{provider_key}: {model_name}",
            "content": content or f"[{err}]",
            "latency_ms": latency,
            "is_local": is_local,
        })

    def _resolve_target(self, target: str, prompt: str, has_image: bool) -> Tuple[str, str, bool]:
        if target == "auto:d3":
            total_chars = len(prompt)
            decision = select_model_with_d3(prompt_text=prompt, has_image=has_image, context_chars=total_chars)
            selected_model = decision.get("selected_model", "Gemma-4-31B-IT")
            tier = decision.get("selected_tier", "balanced_code")
            # Never downgrade interactive studio chat to the 2B triage model unless explicitly chosen
            if selected_model == "MiniCPM5-2B":
                selected_model = "Gemma-4-31B-IT" if has_image else "Qwen3.8-27B"
                tier = "vision_heavy" if has_image else "balanced_code"
            # If AMD Token Lab is ready, use it; otherwise NIM or DO
            status = get_cloud_provider_status()
            if status["amd_tokenlab"]["configured"]:
                return selected_model, "AMD Token Lab", False
            if status["nvidia_brev"]["configured"]:
                nv_model = NVIDIA_MODEL_MAP.get(selected_model, "meta/llama-3.3-70b-instruct")
                return nv_model, "NVIDIA NIM", False
            if status["digitalocean_mi300x"]["configured"]:
                do_model = DO_MODEL_MAP.get(selected_model, "meta-llama/Llama-3.3-70B-Instruct")
                return do_model, "DigitalOcean MI300X", False
            return "qwen2.5-coder:7b", "Local Ollama", True

        if target.startswith("ollama:"):
            return target.split(":", 1)[1], "Local Ollama", True

        if target.startswith("cloud:"):
            return target.split(":", 1)[1], "AMD Token Lab", False

        if target.startswith("nv:"):
            return target.split(":", 1)[1], "NVIDIA NIM", False

        if target.startswith("do:"):
            return target.split(":", 1)[1], "DigitalOcean MI300X", False

        if target.startswith("vllm:"):
            return target.split(":", 1)[1], "Local vLLM (Spark)", False

        if target.startswith("flare:"):
            return target.split(":", 1)[1], "NVIDIA Flare (Spark)", False

        if target.startswith("hf:"):
            return target.split(":", 1)[1], "Hugging Face Router", False

        return "Gemma-4-31B-IT", "AMD Token Lab", False

    def _stream_cloud(
        self,
        provider_key: str,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        image_base64: Optional[str],
        _send: Any,
    ) -> None:
        is_local_openai = False
        if "Local vLLM" in provider_key:
            api_key, base_url = _get_local_vllm_credentials()
            is_local_openai = True
        elif "Flare" in provider_key:
            api_key, base_url = _get_nvidia_flare_credentials()
            is_local_openai = True
        elif "NVIDIA" in provider_key:
            api_key, base_url = _get_nvidia_credentials()
        elif "DigitalOcean" in provider_key:
            api_key, base_url = _get_do_credentials()
        elif "Hugging Face" in provider_key:
            api_key, base_url = _get_huggingface_credentials()
        else:
            api_key, base_url = _get_tokenlab_credentials()

        if not is_local_openai and not api_key:
            raise RuntimeError(f"{provider_key} API key not configured in .env")

        # Build messages with history
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a world-class AI software architect and coding engineer in Jupiter Studio."}
        ]
        for h in history:
            role = h.get("role", "user")
            content = h.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

        # Append current user prompt
        if image_base64:
            user_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
            user_content.append({"type": "image_url", "image_url": {"url": image_base64}})
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": prompt})

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2048,
            "stream": True,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "JupiterStudio/0.2",
        }
        if api_key and api_key.upper() != "EMPTY":
            headers["Authorization"] = f"Bearer {api_key}"

        candidate_models = [model_name]
        if "Token Lab" in provider_key:
            for fb in ("Qwen3.8-27B", "Gemma-4-31B-IT", "DeepSeek-V4.1-Flash"):
                if fb not in candidate_models:
                    candidate_models.append(fb)

        resp_ctx = None
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
                if idx > 0:
                    _send("start", {"model_used": cand_model, "provider": f"{provider_key} (Auto-Failover)", "is_local": False})
                break
            except urllib.error.HTTPError as http_err:
                if http_err.code == 429 and idx + 1 < len(candidate_models):
                    time.sleep(1.0)
                    continue
                detail = ""
                try:
                    detail = http_err.read().decode("utf-8", errors="replace")[:400]
                except Exception:
                    pass
                if http_err.code == 429:
                    raise RuntimeError(f"{provider_key}: rate limited across all models (HTTP 429). Wait a few seconds and retry.") from http_err
                if http_err.code in (401, 403):
                    raise RuntimeError(f"{provider_key}: API key rejected (HTTP {http_err.code}). Check .env.") from http_err
                if http_err.code == 404:
                    raise RuntimeError(f"{provider_key}: model '{model_name}' not found on this provider (HTTP 404).") from http_err
                raise RuntimeError(f"{provider_key}: HTTP {http_err.code} {detail}".strip()) from http_err
            except urllib.error.URLError as url_err:
                raise RuntimeError(
                    f"{provider_key}: cannot reach {base_url} ({url_err.reason}). Is the server running?"
                ) from url_err

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
                    choices = obj.get("choices") or []
                    if choices:
                        choice0 = choices[0]
                        delta = choice0.get("delta") or {}
                        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                        if reasoning:
                            _send("reasoning", {"delta": reasoning})
                        content = delta.get("content")
                        if content:
                            _send("delta", {"delta": content})
                        if choice0.get("finish_reason"):
                            break
                except json.JSONDecodeError:
                    continue

    def _stream_ollama(
        self,
        model_name: str,
        prompt: str,
        history: List[Dict[str, str]],
        _send: Any,
    ) -> None:
        host = _resolve_ollama_host()
        if not host:
            raise RuntimeError(
                "Ollama is not running. Start it on Windows (open the Ollama app or run `ollama serve`), "
                f"then `ollama pull {model_name}`."
            )
        messages: List[Dict[str, str]] = [
            {"role": h.get("role", "user"), "content": h.get("content", "")}
            for h in history
            if h.get("content")
        ]
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({"model": model_name, "messages": messages, "stream": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{host}/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            resp_ctx = urllib.request.urlopen(req, timeout=180.0)
        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                raise RuntimeError(f"Model '{model_name}' is not installed. Run: ollama pull {model_name}") from http_err
            raise RuntimeError(f"Ollama HTTP {http_err.code}") from http_err
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
                if obj.get("error"):
                    raise RuntimeError(f"Ollama: {obj['error']}")
                chunk = (obj.get("message") or {}).get("content", "")
                if chunk:
                    _send("delta", {"delta": chunk})
                if obj.get("done"):
                    break

    def _call_cloud_direct(self, provider_key: str, model_name: str, prompt: str) -> Tuple[str, str]:
        is_local_openai = False
        if "Local vLLM" in provider_key:
            api_key, base_url = _get_local_vllm_credentials()
            is_local_openai = True
        elif "Flare" in provider_key:
            api_key, base_url = _get_nvidia_flare_credentials()
            is_local_openai = True
        elif "NVIDIA" in provider_key:
            api_key, base_url = _get_nvidia_credentials()
        elif "DigitalOcean" in provider_key:
            api_key, base_url = _get_do_credentials()
        elif "Hugging Face" in provider_key:
            api_key, base_url = _get_huggingface_credentials()
        else:
            api_key, base_url = _get_tokenlab_credentials()

        if not is_local_openai and not api_key:
            return "", f"{provider_key} API key not configured in .env"

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JupiterStudio/0.2",
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
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"], ""
        except Exception as exc:
            return "", str(exc)

    def _call_ollama(self, model: str, prompt: str) -> str:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")
        except Exception as exc:
            return f"[Ollama Call Failed]: {exc}\nEnsure Ollama is running on host ({OLLAMA_HOST})."


def main():
    global REPO_ROOT

    parser = argparse.ArgumentParser(description="Jupiter Studio // MemoryOS Hybrid AI Workstation")
    parser.add_argument("--host", default=os.getenv("JUPITER_STUDIO_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("JUPITER_STUDIO_PORT", PORT)))
    parser.add_argument("--workspace", default=None, help="Project folder to expose in Workspace Context Files")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=os.getenv("JUPITER_NO_BROWSER", "").strip().lower() in ("1", "true", "yes"),
        help="Do not automatically open the web browser on startup",
    )
    args = parser.parse_args()

    if args.workspace:
        ws_path = Path(args.workspace).expanduser().resolve()
        if ws_path.is_dir():
            REPO_ROOT = ws_path

    server = None
    bound_port = args.port
    for candidate_port in range(args.port, args.port + 10):
        try:
            server = ThreadingHTTPServer((args.host, candidate_port), JupiterStudioHandler)
            bound_port = candidate_port
            break
        except OSError:
            continue

    if server is None:
        raise RuntimeError(f"Could not bind Jupiter Studio on ports {args.port}..{args.port + 9}")

    url = f"http://127.0.0.1:{bound_port}"
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
