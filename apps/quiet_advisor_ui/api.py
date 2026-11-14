"""Backend data and action service for the Quiet Advisor UI."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quiet_advisor_detectors import (
    DEFAULT_EXPORT_PATH,
    NVMeCheckpointDetector,
    QuietAdvisorEngine,
    ingest_tokenlab_export,
    parse_tokenlab_export,
)
from quiet_advisor_scheduler import CardActionHandler, InferenceLogger, QuietAdvisorScheduler
from src.memoryos.quiet_advisor_db import DEFAULT_DB_PATH, QuietAdvisorDB


def _safe_json_load(raw: Any, fallback: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    if not raw:
        return fallback
    try:
        return json.loads(str(raw))
    except Exception:
        return fallback


def _parse_card(row: Dict[str, Any]) -> Dict[str, Any]:
    action_val = _safe_json_load(row.get("action_value"), {})
    if not isinstance(action_val, dict):
        action_val = {"value": action_val}
    d3_routing = action_val.get("d3_routing") or {}
    experiments = _safe_json_load(row.get("suggested_experiments"), [])
    if not isinstance(experiments, list):
        experiments = []

    metrics = [m for m in (row.get("metric_1"), row.get("metric_2"), row.get("metric_3")) if m not in (None, "")]
    conf = float(d3_routing.get("confidence") or 0.0)
    if conf <= 0.0:
        conf = 0.88
    probs = d3_routing.get("probabilities") or {"surface_now": conf, "defer": round(max(0.0, 1.0 - conf - 0.02), 2), "ignore": 0.02}
    return {
        "id": row["id"],
        "user_id": row.get("user_id", "default"),
        "detector_type": row.get("detector_type", "unknown"),
        "insight_rank": round(float(row.get("insight_rank") or 0.0), 4),
        "title": row.get("title") or "Untitled Insight",
        "subtitle": row.get("subtitle") or "",
        "description": row.get("description") or "",
        "metrics": [str(m) for m in metrics],
        "recommended_action": row.get("recommended_action") or "review",
        "action_value": action_val,
        "d3_routing": {
            "choice": d3_routing.get("choice", "surface_now"),
            "confidence": conf,
            "probabilities": probs,
            "model": d3_routing.get("model", "d3"),
        },
        "time_savings_seconds": int(row.get("time_savings_seconds") or 0),
        "quality_improvement_percent": float(row.get("quality_improvement_percent") or 0.0),
        "suggested_experiments": [str(e) for e in experiments],
        "user_dismissed": bool(row.get("user_dismissed")),
        "user_archived": bool(row.get("user_archived")),
        "user_actioned": bool(row.get("user_actioned")),
        "created_at": row.get("created_at") or "",
        "expires_at": row.get("expires_at") or "",
    }


def _scan_checkpoints(limit: int = 8) -> Dict[str, Any]:
    cp_dir = REPO_ROOT / "memory" / "checkpoints"
    if not cp_dir.exists():
        return {"count": 0, "recent": []}
    files = sorted(cp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    recent: List[Dict[str, Any]] = []
    for fp in files[:limit]:
        data = _safe_json_load(fp.read_text(encoding="utf-8", errors="ignore"), {})
        if not isinstance(data, dict):
            data = {}
        recent.append(
            {
                "name": fp.name,
                "timestamp": data.get("timestamp", ""),
                "route": data.get("route", "unknown"),
                "model": data.get("model", "unknown"),
                "latency_ms": float(data.get("latency_ms") or 0.0),
            }
        )
    return {"count": len(files), "recent": recent}


def get_dashboard_state(
    db_path: Optional[Path] = None,
    auto_ingest_export: bool = True,
) -> Dict[str, Any]:
    """Read cards, telemetry metrics, preferences, Token Lab grant summary, and NVMe checkpoints."""
    target_db = Path(db_path) if db_path else DEFAULT_DB_PATH
    db = QuietAdvisorDB(target_db)
    try:
        if auto_ingest_export and (DEFAULT_EXPORT_PATH.exists() or Path("/tmp/tokenlab_export.json").exists()):
            ingest_tokenlab_export(db)

        raw_active = [
            dict(r)
            for r in db.conn.execute(
                """
                SELECT * FROM quiet_advisor_cards
                WHERE COALESCE(user_dismissed, 0) = 0
                  AND COALESCE(user_archived, 0) = 0
                  AND COALESCE(user_actioned, 0) = 0
                ORDER BY id DESC
                LIMIT 50
                """
            ).fetchall()
        ]
        seen_titles = set()
        active_rows = []
        for r in raw_active:
            key = (r.get("detector_type"), r.get("title"))
            if key not in seen_titles:
                seen_titles.add(key)
                active_rows.append(r)
        archive_rows = [
            dict(r)
            for r in db.conn.execute(
                """
                SELECT * FROM quiet_advisor_cards
                WHERE COALESCE(user_dismissed, 0) = 1
                   OR COALESCE(user_archived, 0) = 1
                   OR COALESCE(user_actioned, 0) = 1
                ORDER BY id DESC
                LIMIT 50
                """
            ).fetchall()
        ]

        inf_rows = [
            dict(r)
            for r in db.conn.execute(
                """
                SELECT id, user_id, model_id, context_tokens_provided, context_tokens_used,
                       total_latency_ms, tokens_per_second, gpu_id, gpu_memory_used_mb,
                       output_quality_score, timestamp
                FROM memoryos_inference_log
                ORDER BY id DESC
                LIMIT 100
                """
            ).fetchall()
        ]

        pref_rows = [
            dict(r)
            for r in db.conn.execute(
                "SELECT user_id, card_type_preferences FROM quiet_advisor_user_preferences"
            ).fetchall()
        ]
        action_rows = [
            dict(r)
            for r in db.conn.execute(
                """
                SELECT user_id, card_id, action_type, action_result, created_at
                FROM quiet_advisor_card_actions
                ORDER BY id DESC
                LIMIT 25
                """
            ).fetchall()
        ]
    finally:
        db.close()

    total_inf = len(inf_rows)
    remote_inf = sum(1 for r in inf_rows if str(r.get("gpu_id") or "") == "tokenlab-remote" or int(r.get("gpu_memory_used_mb") or 0) == 0)
    avg_latency = (sum(float(r.get("total_latency_ms") or 0.0) for r in inf_rows) / total_inf) if total_inf else 0.0

    util_vals = [
        min(1.0, (float(r.get("context_tokens_used") or 0) / float(r["context_tokens_provided"])))
        for r in inf_rows
        if (r.get("context_tokens_provided") or 0) > 0
    ]
    avg_ctx_util = (sum(util_vals) / len(util_vals)) if util_vals else 0.0

    by_model: Dict[str, Dict[str, Any]] = {}
    for r in inf_rows:
        mid = str(r.get("model_id") or "unknown")
        bucket = by_model.setdefault(mid, {"count": 0, "latency_sum": 0.0})
        bucket["count"] += 1
        bucket["latency_sum"] += float(r.get("total_latency_ms") or 0.0)
    model_stats = [
        {
            "model_id": mid,
            "count": b["count"],
            "avg_latency_ms": round(b["latency_sum"] / max(1, b["count"]), 1),
        }
        for mid, b in sorted(by_model.items(), key=lambda kv: kv[1]["count"], reverse=True)
    ]

    preferences: Dict[str, float] = {}
    for pr in pref_rows:
        parsed = _safe_json_load(pr.get("card_type_preferences"), {})
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                try:
                    preferences[str(k)] = round(float(v), 3)
                except (TypeError, ValueError):
                    pass

    return {
        "db_path": str(target_db),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active_cards": [_parse_card(r) for r in active_rows],
        "archived_cards": [_parse_card(r) for r in archive_rows],
        "telemetry": {
            "total_inferences": total_inf,
            "remote_offload_count": remote_inf,
            "local_vram_saved_pct": round((remote_inf / total_inf) * 100.0, 1) if total_inf else 100.0,
            "avg_latency_ms": round(avg_latency, 1),
            "avg_context_utilization_pct": round(avg_ctx_util * 100.0, 1),
            "model_stats": model_stats,
            "latency_series": [round(float(r.get("total_latency_ms") or 0.0), 1) for r in reversed(inf_rows[:24])],
        },
        "preferences": preferences,
        "recent_actions": action_rows,
        "checkpoints": _scan_checkpoints(),
        "tokenlab": parse_tokenlab_export(),
    }


def _run_coro_sync(coro_fn) -> None:
    """Execute an async callable safely from either sync or running-event-loop contexts."""
    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False

    if not loop_running:
        asyncio.run(coro_fn())
    else:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(lambda: asyncio.run(coro_fn())).result()


def apply_card_action(
    card_id: int,
    action: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute a card interaction (action, dismiss, archive, view, learn_more)."""
    allowed = {"view", "dismiss", "archive", "learn_more", "action", "acknowledge"}
    if action not in allowed:
        raise ValueError(f"Unsupported action '{action}'. Expected one of {sorted(allowed)}")

    target_db = Path(db_path) if db_path else DEFAULT_DB_PATH
    db = QuietAdvisorDB(target_db)
    try:
        resolved_user = user_id
        if not resolved_user:
            row = db.conn.execute("SELECT user_id FROM quiet_advisor_cards WHERE id = ?", (card_id,)).fetchone()
            resolved_user = str(row["user_id"]) if row else "default"
        handler = CardActionHandler(db)
        _run_coro_sync(lambda: handler.handle_action(user_id=resolved_user, card_id=str(card_id), action=action, metadata=metadata))
    finally:
        db.close()

    return {"ok": True, "card_id": card_id, "action": action, "state": get_dashboard_state(target_db)}


async def _seed_sample_inferences(db: QuietAdvisorDB, user_id: str = "default") -> int:
    logger = InferenceLogger(db)
    now = datetime.utcnow()
    samples = [
        ("Gemma-4-31B-IT", 32768, 1950, 740.0, 46.0),
        ("Gemma-4-31B-IT", 32768, 2240, 680.0, 51.0),
        ("DeepSeek-V4.1-Flash", 65536, 4100, 390.0, 82.0),
        ("Qwen3.8-27B", 32768, 2800, 510.0, 64.0),
        ("MiniCPM5-2B", 16384, 920, 145.0, 128.0),
        ("Gemma-4-31B-IT", 32768, 2050, 710.0, 48.0),
    ]
    for idx, (model_id, ctx_prov, ctx_used, lat_ms, tps) in enumerate(samples):
        ts = (now - timedelta(minutes=(len(samples) - idx) * 12)).isoformat()
        await db.insert(
            "memoryos.inference_log",
            {
                "user_id": user_id,
                "session_id": "quiet-advisor-seed",
                "timestamp": ts,
                "model_id": model_id,
                "context_tokens_provided": ctx_prov,
                "context_tokens_used": ctx_used,
                "time_to_first_token_ms": round(lat_ms * 0.22, 1),
                "total_latency_ms": lat_ms,
                "tokens_per_second": tps,
                "gpu_id": "tokenlab-remote",
                "gpu_utilization_percent": 0.0,
                "gpu_temperature_celsius": 0.0,
                "gpu_memory_used_mb": 0,
                "output_quality_score": 0.91,
                "error_flag": False,
            },
        )
    return len(samples)


def run_detection_cycle(
    lookback_hours: int = 24,
    seed_if_empty: bool = False,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run QuietAdvisorScheduler detection against SQLite and return refreshed state."""
    target_db = Path(db_path) if db_path else DEFAULT_DB_PATH
    db = QuietAdvisorDB(target_db)
    seeded = 0
    try:
        async def _run():
            nonlocal seeded
            existing = await db.query("SELECT COUNT(*) AS cnt FROM memoryos.inference_log")
            cnt = int(existing[0]["cnt"]) if existing else 0
            if seed_if_empty and cnt < 5:
                seeded = await _seed_sample_inferences(db)
            scheduler = QuietAdvisorScheduler(db, QuietAdvisorEngine())
            await scheduler.run_daily_detection(lookback_hours=lookback_hours)

        _run_coro_sync(_run)
    finally:
        db.close()

    return {
        "ok": True,
        "seeded_inferences": seeded,
        "state": get_dashboard_state(target_db),
    }
