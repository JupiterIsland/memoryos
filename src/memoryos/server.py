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
import json
import os
import re
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

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
    from fastapi import Body, FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

_tlb = MemTLB(max_hot=5)
_heat_stream = None
_qa_db: Optional[QuietAdvisorDB] = None
_override_db_path: Optional[Path] = None


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

    def _send_json(self, payload: Dict[str, Any], status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                from apps.quiet_advisor_ui.server import DASHBOARD_HTML

                body = DASHBOARD_HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
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
            self._send_json(
                apply_card_action(
                    card_id=card_id,
                    action=action,
                    user_id=user_id,
                    metadata=metadata,
                    db_path=target_db,
                )
            )
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
    args = parser.parse_args()

    global _override_db_path
    if args.db:
        _override_db_path = Path(args.db)
        os.environ["QUIET_ADVISOR_DB"] = str(_override_db_path)

    resolved = _init_services(db_path=_override_db_path)
    print(f"[Router] Starting MemoryOS Router on http://{args.host}:{args.port} (DB: {resolved})")

    if HAS_FASTAPI:
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
