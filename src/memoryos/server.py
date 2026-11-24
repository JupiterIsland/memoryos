"""
MemoryOS Router Server v0.4.0
=============================
Standalone FastAPI (with automatic stdlib HTTP fallback) backend for the hybrid
Jupiter Desktop + MemoryOS system.

Endpoints:
  - GET  /                   Quiet Advisor Web Dashboard (when UI module is present)
  - GET  /health             Service health & backend status
  - POST /api/frame-delta    CPU MSE/delta pre-inference gatekeeping via Token Lab d3
  - POST /api/route          Auto-route inference/code prompts via d3 + preference penalties
  - POST /api/acknowledge-card  Apply [Acknowledge & Apply] feedback to SQLite preferences
  - GET  /api/state          Quiet Advisor dashboard state
  - POST /api/detect         Run Quiet Advisor pattern detectors
  - POST /api/cards/{id}/action  Apply card action
  - GET  /api/memory/hot     Hot TLB/HeatStream memory blocks
  - GET  /api/status         Router & active session status
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memoryos.core.tlb import MemTLB
from src.memoryos.quiet_advisor_db import QUIET_ADVISOR_SQLITE_PATH, QuietAdvisorDB
from src.memoryos.router_service import (
    process_acknowledge_card,
    process_frame_delta,
    process_route_request,
    resolve_db_path,
)

try:
    from src.memoryos.core.heat_stream import MemoryHeatStream
except Exception:
    MemoryHeatStream = None  # type: ignore[assignment]

try:
    from fastapi import Body, FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

_tlb = MemTLB(max_hot=5)
_heat_stream = None
_qa_db: Optional[QuietAdvisorDB] = None
_override_db_path: Optional[Path] = None
_LOCAL_ORIGIN_HOSTS = {"127.0.0.1", "localhost", "::1"}
_STRICT_HOST_RE = re.compile(
    r"^(?:\[[0-9a-fA-F:]+\]|[A-Za-z0-9.-]+)(?::\d{1,5})?$"
)


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
        f"Refusing to bind MemoryOS Router to {shown}: this exposes your local router and memory DB to the "
        "network. Use the default 127.0.0.1, or pass --unsafe-lan (or set ROUTER_UNSAFE_LAN=1)."
    )


def _is_allowed_origin(origin: str, extra_local_hosts: Sequence[str] = ()) -> bool:
    """Allow CORS only from local loopback origins when loopback-bound."""
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
    allowed = _LOCAL_ORIGIN_HOSTS | {h.lower() for h in extra_local_hosts}
    return (parsed.hostname or "").lower() in allowed


def _is_allowed_host(
    host_header: str,
    loopback_bound: bool,
    extra_local_hosts: Sequence[str] = (),
) -> bool:
    if not host_header or not loopback_bound:
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
    allowed = _LOCAL_ORIGIN_HOSTS | {h.lower() for h in extra_local_hosts}
    return (parsed.hostname or "").lower() in allowed


def _origin_matches_host(
    origin: str,
    host_header: str,
    loopback_bound: bool,
    extra_local_hosts: Sequence[str] = (),
) -> bool:
    """Validate Origin: loopback-only when loopback-bound, or matching Host when LAN-bound."""
    if loopback_bound:
        return _is_allowed_origin(origin, extra_local_hosts=extra_local_hosts)
    cleaned = origin.strip()
    if any(ch.isspace() for ch in cleaned):
        return False
    h_cleaned = (host_header or "").strip()
    if h_cleaned and not _STRICT_HOST_RE.match(h_cleaned):
        return False
    try:
        o_parsed = urllib.parse.urlsplit(cleaned)
        h_parsed = urllib.parse.urlsplit(f"http://{h_cleaned}") if h_cleaned else None
    except ValueError:
        return False
    if o_parsed.scheme not in ("http", "https") or o_parsed.username is not None or o_parsed.password is not None:
        return False
    if o_parsed.path not in ("", "/") or o_parsed.query or o_parsed.fragment:
        return False
    o_host = (o_parsed.hostname or "").lower()
    allowed = _LOCAL_ORIGIN_HOSTS | {h.lower() for h in extra_local_hosts}
    if o_host in allowed:
        return True
    return bool(h_parsed and o_host and o_host == (h_parsed.hostname or "").lower())


def _validate_local_request(
    *,
    host: str,
    origin: str,
    sec_fetch_site: str,
    referer: str,
    loopback_bound: bool,
    extra_local_hosts: Sequence[str] = (),
) -> Optional[str]:
    """Return an error reason if Host/Origin/Sec-Fetch-Site/Referer violates local-origin policy, else None."""
    if host and not _is_allowed_host(host, loopback_bound=loopback_bound, extra_local_hosts=extra_local_hosts):
        return "Invalid Host header for local router server"
    if origin and not _origin_matches_host(
        origin, host, loopback_bound=loopback_bound, extra_local_hosts=extra_local_hosts
    ):
        return "Cross-origin requests are forbidden"
    if sec_fetch_site.strip().lower() == "cross-site":
        return "Cross-site API requests are forbidden"
    if not origin and referer:
        try:
            ref_parsed = urllib.parse.urlsplit(referer)
            ref_origin = (
                f"{ref_parsed.scheme}://{ref_parsed.netloc}"
                if ref_parsed.scheme and ref_parsed.netloc
                else referer
            )
        except ValueError:
            ref_origin = referer
        if not _origin_matches_host(
            ref_origin, host, loopback_bound=loopback_bound, extra_local_hosts=extra_local_hosts
        ):
            return "Cross-origin Referer is forbidden"
    return None


def _init_services(db_path: Optional[Path] = None) -> Path:
    global _heat_stream, _qa_db
    memory_dir = Path(os.getenv("MEMORYOS_DIR", str(REPO_ROOT / "memory")))
    target_db = resolve_db_path(db_path or _override_db_path or QUIET_ADVISOR_SQLITE_PATH)

    if MemoryHeatStream is not None and _heat_stream is None:
        try:
            _heat_stream = MemoryHeatStream(
                tlb_cache_dir=str(memory_dir / "tlb_hot_cache"),
                temp_graph_path=str(memory_dir / "graph"),
            )
        except Exception as exc:
            print(f"[Router] HeatStream init warning: {exc}")

    try:
        _qa_db = QuietAdvisorDB(db_path=target_db)
        return _qa_db.db_path
    except Exception as exc:
        print(f"[Router] Quiet Advisor DB init warning: {exc}")
        return target_db


def _hot_memories_payload(limit: int = 5) -> Dict[str, Any]:
    if not _heat_stream:
        return {"status": "success", "total": 0, "memories": []}
    try:
        hot = _heat_stream.scan_for_hot_memories()
        results = [
            {
                "id": b.id,
                "title": b.title,
                "content": b.content[:500],
                "heat_score": b.heat_score,
                "access_count": b.access_count,
            }
            for b in hot[:limit]
        ]
        return {"status": "success", "total": len(results), "memories": results}
    except Exception as exc:
        return {"status": "warning", "total": 0, "memories": [], "detail": str(exc)}


if HAS_FASTAPI:
    class FrameDeltaRequest(BaseModel):
        session_id: str = "jupiter-desktop"
        frame_delta: Optional[Dict[str, Any]] = None
        mse_delta: Optional[float] = None
        threshold: Optional[float] = None
        context_hint: Optional[str] = None
        previous_response: Optional[str] = None
        user_id: str = "default"
        log_skip: bool = True

    class RoutingRequest(BaseModel):
        session_id: str = "api-route"
        prompt: Optional[str] = None
        prompt_text: Optional[str] = None
        task_type: Optional[str] = None
        image_url: Optional[str] = None
        tlb_context: Optional[str] = None
        frame_delta: Optional[Dict[str, Any]] = None
        mse_delta: Optional[float] = None
        threshold: Optional[float] = None
        forced_model: Optional[str] = None
        prefer_local: bool = False
        max_tokens: int = 1024
        user_id: str = "default"
        context_from_memory: bool = True

    class AcknowledgeCardRequest(BaseModel):
        user_id: Optional[str] = None
        card_id: Optional[int] = None
        card_type: str = "vram_thrashing"
        detector_type: Optional[str] = None
        action: str = "acknowledge"
        penalty: Optional[float] = None

    app = FastAPI(
        title="MemoryOS Router",
        description="Lightweight routing engine for hybrid Jupiter Desktop + MemoryOS Quiet Advisor",
        version="0.4.0",
    )
    app.state.bound_host = "127.0.0.1"

    @app.middleware("http")
    async def _enforce_origin_middleware(request: Request, call_next: Any):
        host = request.headers.get("host", "").strip()
        origin = request.headers.get("origin", "").strip()
        sec_fetch_site = request.headers.get("sec-fetch-site", "").strip()
        referer = request.headers.get("referer", "").strip()
        bound_host = getattr(app.state, "bound_host", "127.0.0.1")
        loopback_bound = _is_loopback_bind_host(bound_host)
        client_host = getattr(getattr(request, "client", None), "host", None)
        extra_hosts = ("testserver",) if client_host == "testclient" else ()
        err = _validate_local_request(
            host=host,
            origin=origin,
            sec_fetch_site=sec_fetch_site,
            referer=referer,
            loopback_bound=loopback_bound,
            extra_local_hosts=extra_hosts,
        )
        if err:
            resp = JSONResponse({"error": err}, status_code=HTTPStatus.FORBIDDEN)
            resp.headers["X-Content-Type-Options"] = "nosniff"
            resp.headers["X-Frame-Options"] = "DENY"
            resp.headers["Referrer-Policy"] = "no-referrer"
            return resp
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if origin and _origin_matches_host(
            origin, host, loopback_bound=loopback_bound, extra_local_hosts=extra_hosts
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response

    @app.on_event("startup")
    async def _on_startup() -> None:
        _init_services()

    @app.get("/")
    async def index_page():
        try:
            from apps.quiet_advisor_ui.server import DASHBOARD_HTML

            return HTMLResponse(content=DASHBOARD_HTML)
        except Exception:
            return {"service": "memoryos-router", "status": "running", "docs": "/docs"}

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        target_db = resolve_db_path(_override_db_path or QUIET_ADVISOR_SQLITE_PATH)
        return {
            "status": "healthy",
            "backend": "fastapi",
            "db_path": str(_qa_db.db_path if _qa_db else target_db),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "heat_stream": _heat_stream is not None,
                "quiet_advisor_db": _qa_db is not None,
                "tlb": _tlb is not None,
            },
        }

    @app.post("/api/frame-delta")
    async def frame_delta_check(req: FrameDeltaRequest) -> Dict[str, Any]:
        return process_frame_delta(req.model_dump(), default_db_path=_override_db_path or QUIET_ADVISOR_SQLITE_PATH)

    @app.post("/api/route")
    async def route_inference(req: RoutingRequest) -> Dict[str, Any]:
        try:
            return process_route_request(
                req.model_dump(),
                heat_stream=_heat_stream,
                default_db_path=_override_db_path or QUIET_ADVISOR_SQLITE_PATH,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/acknowledge-card")
    async def acknowledge_card(
        req: Optional[AcknowledgeCardRequest] = Body(default=None),
        user_id: Optional[str] = None,
        card_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = req.model_dump() if req is not None else {}
        if user_id:
            payload.setdefault("user_id", user_id)
        if card_type:
            payload["card_type"] = card_type
        if action:
            payload["action"] = action
        return process_acknowledge_card(payload, default_db_path=_override_db_path or QUIET_ADVISOR_SQLITE_PATH)

    @app.get("/api/state")
    async def api_state() -> Dict[str, Any]:
        from apps.quiet_advisor_ui.api import get_dashboard_state

        return get_dashboard_state(_override_db_path or QUIET_ADVISOR_SQLITE_PATH)

    @app.post("/api/detect")
    async def api_detect(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
        from apps.quiet_advisor_ui.api import run_detection_cycle

        return run_detection_cycle(
            lookback_hours=int(payload.get("lookback_hours") or 24),
            seed_if_empty=bool(payload.get("seed_if_empty", False)),
            db_path=_override_db_path or QUIET_ADVISOR_SQLITE_PATH,
        )

    @app.post("/api/cards/{card_id}/action")
    async def api_card_action(card_id: int, payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
        from apps.quiet_advisor_ui.api import apply_card_action

        return apply_card_action(
            card_id=card_id,
            action=str(payload.get("action") or "view"),
            user_id=payload.get("user_id"),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
            db_path=_override_db_path or QUIET_ADVISOR_SQLITE_PATH,
        )

    @app.get("/api/memory/hot")
    async def get_hot_memories(limit: int = 5) -> Dict[str, Any]:
        return _hot_memories_payload(limit=limit)

    @app.get("/api/status")
    async def get_status() -> Dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "heat_stream": _heat_stream is not None,
                "quiet_advisor_db": _qa_db is not None,
            },
            "db_path": str(_qa_db.db_path if _qa_db else resolve_db_path(_override_db_path)),
        }
else:
    app = None


class FallbackRouterHTTPHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP server fallback matching FastAPI routes."""

    db_path: Optional[Path] = None

    def _get_header(self, name: str, default: str = "") -> str:
        val = self.headers.get(name) if self.headers else None
        return val if isinstance(val, str) else default

    def _is_loopback_bound(self) -> bool:
        srv = getattr(self, "server", None)
        addr = getattr(srv, "server_address", None)
        if not addr or not isinstance(addr, tuple):
            return True
        return _is_loopback_bind_host(str(addr[0] or ""))

    def _origin_matches_host(self, origin: str) -> bool:
        return _origin_matches_host(
            origin,
            self._get_header("Host").strip(),
            loopback_bound=self._is_loopback_bound(),
        )

    def _send_security_headers(self, include_cors: bool = True) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if include_cors:
            origin = self._get_header("Origin").strip()
            if origin and self._origin_matches_host(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")

    def _enforce_origin(self) -> bool:
        err = _validate_local_request(
            host=self._get_header("Host").strip(),
            origin=self._get_header("Origin").strip(),
            sec_fetch_site=self._get_header("Sec-Fetch-Site").strip(),
            referer=self._get_header("Referer").strip(),
            loopback_bound=self._is_loopback_bound(),
        )
        if err:
            self._send_json({"error": err}, status=HTTPStatus.FORBIDDEN)
            return False
        return True

    def _send_json(self, payload: Dict[str, Any], status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self._send_security_headers(include_cors=(status != HTTPStatus.FORBIDDEN))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            return {}
        if length <= 0 or length > 2 * 1024 * 1024:
            return {}
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_OPTIONS(self) -> None:
        if not self._enforce_origin():
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_security_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        if not self._enforce_origin():
            return
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                from apps.quiet_advisor_ui.server import DASHBOARD_HTML

                body = DASHBOARD_HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_security_headers()
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception:
                self._send_json({"service": "memoryos-router", "status": "running"})
                return

        if path == "/health":
            target_db = resolve_db_path(self.db_path or QUIET_ADVISOR_SQLITE_PATH)
            self._send_json(
                {
                    "status": "healthy",
                    "backend": "stdlib-http",
                    "db_path": str(_qa_db.db_path if _qa_db else target_db),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "services": {
                        "heat_stream": _heat_stream is not None,
                        "quiet_advisor_db": _qa_db is not None,
                        "tlb": _tlb is not None,
                    },
                }
            )
            return

        if path == "/api/state":
            from apps.quiet_advisor_ui.api import get_dashboard_state

            self._send_json(get_dashboard_state(self.db_path or QUIET_ADVISOR_SQLITE_PATH))
            return

        if path == "/api/memory/hot":
            self._send_json(_hot_memories_payload())
            return

        if path == "/api/status":
            target_db = resolve_db_path(self.db_path or QUIET_ADVISOR_SQLITE_PATH)
            self._send_json(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "db_path": str(_qa_db.db_path if _qa_db else target_db),
                    "services": {
                        "heat_stream": _heat_stream is not None,
                        "quiet_advisor_db": _qa_db is not None,
                    },
                }
            )
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if not self._enforce_origin():
            return
        path = self.path.split("?", 1)[0]
        body = self._read_json_body()
        target_db = self.db_path or QUIET_ADVISOR_SQLITE_PATH

        if path == "/api/frame-delta":
            self._send_json(process_frame_delta(body, default_db_path=target_db))
            return

        if path == "/api/route":
            try:
                self._send_json(process_route_request(body, heat_stream=_heat_stream, default_db_path=target_db))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/acknowledge-card":
            self._send_json(process_acknowledge_card(body, default_db_path=target_db))
            return

        if path == "/api/detect":
            from apps.quiet_advisor_ui.api import run_detection_cycle

            self._send_json(
                run_detection_cycle(
                    lookback_hours=int(body.get("lookback_hours") or 24),
                    seed_if_empty=bool(body.get("seed_if_empty", False)),
                    db_path=target_db,
                )
            )
            return

        match = re.match(r"^/api/cards/(\d+)/action$", path)
        if match:
            from apps.quiet_advisor_ui.api import apply_card_action

            card_id = int(match.group(1))
            action = str(body.get("action") or "view")
            user_id = str(body["user_id"]) if body.get("user_id") else None
            metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else None
            try:
                self._send_json(
                    apply_card_action(
                        card_id=card_id,
                        action=action,
                        user_id=user_id,
                        metadata=metadata,
                        db_path=target_db,
                    )
                )
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def create_fallback_server(
    host: str = "127.0.0.1",
    port: int = 5000,
    db_path: Optional[Path] = None,
) -> ThreadingHTTPServer:
    _init_services(db_path=db_path)

    class _BoundHandler(FallbackRouterHTTPHandler):
        pass

    _BoundHandler.db_path = db_path
    return ThreadingHTTPServer((host, port), _BoundHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Start MemoryOS Router Server")
    parser.add_argument("--host", default=os.getenv("ROUTER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("ROUTER_PORT", "5000")))
    parser.add_argument("--db", default=None, help="Optional SQLite DB path")
    parser.add_argument(
        "--unsafe-lan",
        action="store_true",
        default=os.getenv("ROUTER_UNSAFE_LAN", "").strip().lower() in ("1", "true", "yes"),
        help="Allow binding to a non-loopback address (e.g. 0.0.0.0). Traffic is plain HTTP; use only on a trusted network.",
    )
    args = parser.parse_args()

    bind_error = _bind_host_error(args.host, args.unsafe_lan)
    if bind_error:
        print(f"[!] {bind_error}", file=sys.stderr)
        sys.exit(2)

    global _override_db_path
    if args.db:
        _override_db_path = Path(args.db)
        os.environ["QUIET_ADVISOR_DB"] = str(_override_db_path)

    resolved = _init_services(db_path=_override_db_path)
    print(f"[Router] Starting MemoryOS Router on http://{args.host}:{args.port} (DB: {resolved})")

    if HAS_FASTAPI:
        if app is not None:
            app.state.bound_host = args.host
        try:
            import uvicorn

            uvicorn.run(app, host=args.host, port=args.port, workers=1)
            return
        except ImportError:
            pass

    server = create_fallback_server(host=args.host, port=args.port, db_path=_override_db_path)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
