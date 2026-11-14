"""Local SQLite persistence adapter and live loop helpers for The Quiet Advisor."""

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
QUIET_ADVISOR_SQLITE_PATH = REPO_ROOT / "QuietAdvisorDB.sqlite"
LEGACY_DB_PATH = REPO_ROOT / "memory" / "quiet_advisor.db"
DEFAULT_DB_PATH = QUIET_ADVISOR_SQLITE_PATH
SCHEMA_SQL_PATH = REPO_ROOT / "schema.sql"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS memoryos_inference_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    timestamp TEXT NOT NULL,
    model_id TEXT NOT NULL,
    context_tokens_provided INTEGER DEFAULT 0,
    context_tokens_used INTEGER DEFAULT 0,
    time_to_first_token_ms REAL DEFAULT 0,
    total_latency_ms REAL DEFAULT 0,
    tokens_per_second REAL DEFAULT 0,
    gpu_id TEXT,
    gpu_utilization_percent REAL DEFAULT 0,
    gpu_temperature_celsius REAL DEFAULT 0,
    gpu_memory_used_mb INTEGER DEFAULT 0,
    output_quality_score REAL,
    error_flag INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS quiet_advisor_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    detector_type TEXT NOT NULL,
    insight_rank REAL DEFAULT 0,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    metric_1 TEXT,
    metric_2 TEXT,
    metric_3 TEXT,
    recommended_action TEXT,
    action_value TEXT,
    time_savings_seconds INTEGER DEFAULT 0,
    quality_improvement_percent REAL DEFAULT 0,
    suggested_experiments TEXT,
    user_dismissed INTEGER DEFAULT 0,
    user_archived INTEGER DEFAULT 0,
    user_actioned INTEGER DEFAULT 0,
    created_at TEXT,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS quiet_advisor_card_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_result TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS quiet_advisor_user_preferences (
    user_id TEXT PRIMARY KEY,
    card_type_preferences TEXT NOT NULL
);
"""

_TABLE_MAP = {
    "memoryos.inference_log": "memoryos_inference_log",
    "quiet_advisor.cards": "quiet_advisor_cards",
    "quiet_advisor.card_actions": "quiet_advisor_card_actions",
    "quiet_advisor.user_preferences": "quiet_advisor_user_preferences",
}


def _normalize_sql(sql: str) -> str:
    """Translate schema-qualified Postgres-style SQL from scheduler into SQLite SQL."""
    out = sql
    for src, dst in _TABLE_MAP.items():
        out = out.replace(src, dst)
    out = re.sub(r"\bNOW\(\)", "datetime('now')", out, flags=re.IGNORECASE)
    out = re.sub(r"\btrue\b", "1", out, flags=re.IGNORECASE)
    out = re.sub(r"\bfalse\b", "0", out, flags=re.IGNORECASE)
    return out


class QuietAdvisorDB:
    """Async-compatible SQLite adapter matching QuietAdvisorScheduler's DB contract."""

    def __init__(self, db_path: Optional[Path] = None):
        target = Path(db_path) if db_path else DEFAULT_DB_PATH
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(target), check_same_thread=False)
            self.db_path = target
            self.conn.row_factory = sqlite3.Row
            self._init_schema()
        except (sqlite3.OperationalError, OSError):
            fallback = Path("/tmp/QuietAdvisorDB.sqlite")
            fallback.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(fallback), check_same_thread=False)
            self.db_path = fallback
            self.conn.row_factory = sqlite3.Row
            self._init_schema()

    def _init_schema(self) -> None:
        ddl = SCHEMA_SQL_PATH.read_text(encoding="utf-8") if SCHEMA_SQL_PATH.exists() else SCHEMA_SQL
        self.conn.executescript(ddl)
        self.conn.commit()

    def insert_sync(self, table: str, record: Dict[str, Any]) -> int:
        table_name = _TABLE_MAP.get(table, table)
        clean_record = {
            k: (1 if v is True else 0 if v is False else v)
            for k, v in record.items()
        }
        if table_name == "memoryos_inference_log" and "user_id" in clean_record:
            self.conn.execute(
                "INSERT OR IGNORE INTO users (user_id, active) VALUES (?, 1)",
                (clean_record["user_id"],),
            )

        cols = ", ".join(clean_record.keys())
        placeholders = ", ".join("?" for _ in clean_record)
        cur = self.conn.execute(
            f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})",
            list(clean_record.values()),
        )
        self.conn.commit()
        return cur.lastrowid

    async def insert(self, table: str, record: Dict[str, Any]) -> int:
        return self.insert_sync(table, record)

    async def query(self, sql: str) -> List[Dict[str, Any]]:
        cur = self.conn.execute(_normalize_sql(sql))
        return [dict(row) for row in cur.fetchall()]

    async def query_one(self, sql: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute(_normalize_sql(sql))
        row = cur.fetchone()
        return dict(row) if row else None

    async def execute(self, sql: str) -> None:
        self.conn.execute(_normalize_sql(sql))
        self.conn.commit()

    def record_user_preference(
        self,
        user_id: str,
        card_type: str,
        penalty: float,
        action: str = "acknowledge",
        card_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update user preference weights for closed-loop routing feedback.

        Called when user clicks [Acknowledge & Apply] on a Quiet Advisor card.
        Stores penalty weight (e.g., vram_thrashing_penalty=1.5) in quiet_advisor_user_preferences.
        """
        existing = self.conn.execute(
            "SELECT card_type_preferences FROM quiet_advisor_user_preferences WHERE user_id = ? LIMIT 1",
            (user_id,),
        ).fetchone()

        prefs: Dict[str, Any] = {}
        if existing and existing[0]:
            try:
                parsed = json.loads(existing[0])
                if isinstance(parsed, dict):
                    prefs = parsed
            except Exception:
                prefs = {}

        penalty_key = f"{card_type}_penalty"
        prefs[penalty_key] = float(penalty)
        prefs[f"{card_type}_action"] = action
        prefs[f"{card_type}_updated_at"] = datetime.now(timezone.utc).isoformat()
        if card_type in ("vram_thrashing", "model_thrashing") and float(penalty) > 1.0:
            prefs["force_remote_offload"] = True
            prefs["preferred_vision_model"] = "Gemma-4-31B-IT"

        self.conn.execute(
            "INSERT OR REPLACE INTO quiet_advisor_user_preferences (user_id, card_type_preferences) VALUES (?, ?)",
            (user_id, json.dumps(prefs)),
        )

        if card_id is not None:
            self.conn.execute(
                "UPDATE quiet_advisor_cards SET user_actioned = 1 WHERE id = ?",
                (int(card_id),),
            )
            self.conn.execute(
                """
                INSERT INTO quiet_advisor_card_actions (user_id, card_id, action_type, action_result, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    str(card_id),
                    action,
                    json.dumps({"card_type": card_type, "penalty": float(penalty)}),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        self.conn.commit()
        return prefs

    def close(self) -> None:
        self.conn.close()


def row_to_inference_log(row: Dict[str, Any]):
    """Convert a SQLite inference_log dict row into quiet_advisor_detectors.InferenceLog."""
    from quiet_advisor_detectors import InferenceLog

    ts_raw = row["timestamp"]
    ts = datetime.fromisoformat(ts_raw) if isinstance(ts_raw, str) else ts_raw
    return InferenceLog(
        timestamp=ts,
        model_id=row["model_id"],
        context_tokens_provided=int(row.get("context_tokens_provided") or 0),
        context_tokens_used=int(row.get("context_tokens_used") or 0),
        time_to_first_token_ms=float(row.get("time_to_first_token_ms") or 0.0),
        total_latency_ms=float(row.get("total_latency_ms") or 0.0),
        tokens_per_second=float(row.get("tokens_per_second") or 0.0),
        gpu_utilization_percent=float(row.get("gpu_utilization_percent") or 0.0),
        gpu_temperature_celsius=float(row.get("gpu_temperature_celsius") or 0.0),
        gpu_memory_used_mb=int(row.get("gpu_memory_used_mb") or 0),
        output_quality_score=row.get("output_quality_score"),
        error_flag=bool(row.get("error_flag", False)),
        error_message=row.get("error_message"),
    )


async def log_routed_inference(
    inference_logger: Any,
    route_result: Dict[str, Any],
    user_id: str = "default",
    session_id: str = "router",
    context_tokens_provided: int = 8192,
) -> None:
    """Record a Token Lab route_task() execution into Quiet Advisor's InferenceLogger."""
    usage = route_result.get("usage", {})
    total_tokens = int(usage.get("total_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    latency_ms = float(route_result.get("latency_ms") or 1.0)
    tps = (completion_tokens / (latency_ms / 1000.0)) if latency_ms > 0 and completion_tokens > 0 else 0.0

    await inference_logger.log_inference(
        user_id=user_id,
        session_id=session_id,
        model_id=route_result.get("model", "unknown"),
        context_tokens_provided=context_tokens_provided,
        context_tokens_used=total_tokens or int(usage.get("prompt_tokens") or 0),
        time_to_first_token_ms=round(latency_ms * 0.2, 2),
        total_latency_ms=round(latency_ms, 2),
        tokens_per_second=round(tps, 2),
        gpu_state={
            "gpu_id": "tokenlab-remote",
            "utilization": 0.0,
            "temperature": 0.0,
            "memory_used_mb": 0,
        },
        output_quality_score=float(route_result.get("d3_decision", {}).get("confidence", 0.9)),
        error_flag=False,
    )


def record_routed_inference_sync(
    route_result: Dict[str, Any],
    user_id: str = "default",
    session_id: str = "jupiter-tv",
    context_tokens_provided: int = 8192,
    db_path: Optional[Path] = None,
) -> int:
    """Synchronously log a routed inference (e.g., from Jupiter TV or router.py) into SQLite."""
    usage = route_result.get("usage", {})
    total_tokens = int(usage.get("total_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    latency_ms = float(route_result.get("latency_ms") or 1.0)
    tps = (completion_tokens / (latency_ms / 1000.0)) if latency_ms > 0 and completion_tokens > 0 else 0.0
    conf = float((route_result.get("d3_decision") or {}).get("confidence") or 0.9)

    d3_skipped = bool(route_result.get("d3_skipped", False))
    tokens_used = 0 if d3_skipped else (total_tokens or prompt_tokens or 64)
    record_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "model_id": str(route_result.get("model") or "unknown"),
        "context_tokens_provided": 0 if d3_skipped else int(context_tokens_provided),
        "context_tokens_used": tokens_used,
        "time_to_first_token_ms": round(latency_ms * 0.2, 2),
        "total_latency_ms": round(latency_ms, 2),
        "tokens_per_second": round(tps, 2),
        "gpu_id": str(route_result.get("gpu_id") or "tokenlab-remote"),
        "gpu_utilization_percent": float(route_result.get("gpu_utilization_percent") or 0.0),
        "gpu_temperature_celsius": float(route_result.get("gpu_temperature_celsius") or 0.0),
        "gpu_memory_used_mb": int(route_result.get("gpu_memory_used_mb") or 0),
        "output_quality_score": conf,
        "error_flag": bool(route_result.get("error_flag", False)),
        "error_message": route_result.get("error_message"),
    }

    db = QuietAdvisorDB(db_path)
    try:
        row_id = db.insert_sync("memoryos.inference_log", record_payload)
    finally:
        db.close()

    live_ui_db = Path("/tmp/quiet_advisor_live.db")
    if db_path is None and live_ui_db.exists() and db.db_path != live_ui_db:
        try:
            mirror = QuietAdvisorDB(live_ui_db)
            try:
                mirror.insert_sync("memoryos.inference_log", record_payload)
            finally:
                mirror.close()
        except Exception:
            pass
    return row_id


def acknowledge_card_sync(
    user_id: Optional[str] = None,
    card_id: Optional[int] = None,
    card_type: str = "vram_thrashing",
    action: str = "acknowledge",
    penalty: Optional[float] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Acknowledge/apply a Quiet Advisor card and persist routing penalties in SQLite."""
    penalty_map = {
        "vram_thrashing": 1.5,
        "model_thrashing": 1.5,
        "cache_miss_spike": 1.3,
        "inference_stall": 1.2,
        "model_loading_slow": 1.4,
    }
    db = QuietAdvisorDB(db_path)
    try:
        resolved_user = user_id or "default"
        resolved_type = card_type
        resolved_penalty = penalty

        if card_id is not None:
            row = db.conn.execute(
                "SELECT user_id, detector_type, action_value FROM quiet_advisor_cards WHERE id = ?",
                (int(card_id),),
            ).fetchone()
            if row:
                if not user_id:
                    resolved_user = str(row["user_id"] or "default")
                if not card_type or card_type == "vram_thrashing":
                    resolved_type = str(row["detector_type"] or resolved_type)
                if resolved_penalty is None and row["action_value"]:
                    try:
                        av = json.loads(row["action_value"])
                        if isinstance(av, dict) and "vram_thrashing_penalty" in av:
                            resolved_penalty = float(av["vram_thrashing_penalty"])
                    except Exception:
                        pass

        final_penalty = float(
            resolved_penalty if resolved_penalty is not None else penalty_map.get(resolved_type, 1.5)
        )
        prefs = db.record_user_preference(
            user_id=resolved_user,
            card_type=resolved_type,
            penalty=final_penalty,
            action=action,
            card_id=card_id,
        )
        return {
            "status": "acknowledged",
            "user_id": resolved_user,
            "card_id": card_id,
            "card_type": resolved_type,
            "penalty_applied": final_penalty,
            "action": action,
            "preferences": prefs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


def get_routing_advice_sync(
    user_id: str = "default",
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Return active Quiet Advisor routing hints & learned preferences from SQLite."""
    db = QuietAdvisorDB(db_path)
    try:
        card_row = db.conn.execute(
            """
            SELECT id, detector_type, title, recommended_action, action_value
            FROM quiet_advisor_cards
            WHERE COALESCE(user_dismissed, 0) = 0
              AND COALESCE(user_archived, 0) = 0
            ORDER BY insight_rank DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        pref_row = db.conn.execute(
            "SELECT card_type_preferences FROM quiet_advisor_user_preferences WHERE user_id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
        if (not pref_row or not pref_row["card_type_preferences"]) and user_id in ("default", "jupiter-desktop"):
            alt_user = "jupiter-desktop" if user_id == "default" else "default"
            pref_row = db.conn.execute(
                "SELECT card_type_preferences FROM quiet_advisor_user_preferences WHERE user_id = ? LIMIT 1",
                (alt_user,),
            ).fetchone()
    finally:
        db.close()

    prefs: Dict[str, Any] = {}
    if pref_row and pref_row["card_type_preferences"]:
        try:
            prefs = json.loads(pref_row["card_type_preferences"])
        except Exception:
            prefs = {}

    vram_penalty = float(prefs.get("vram_thrashing_penalty") or prefs.get("model_thrashing_penalty") or 0.0)
    force_remote = bool(prefs.get("force_remote_offload")) or vram_penalty > 1.0
    cap = prefs.get("recommended_context_cap")

    hint: Dict[str, Any] = {
        "preferences": prefs,
        "vram_thrashing_penalty": vram_penalty,
        "force_remote_offload": force_remote,
        "preferred_vision_model": prefs.get("preferred_vision_model") or ("Gemma-4-31B-IT" if force_remote else None),
        "active_card": None,
        "recommended_context_cap": int(cap) if cap else None,
    }
    if card_row:
        act_val: Dict[str, Any] = {}
        try:
            act_val = json.loads(card_row["action_value"] or "{}")
        except Exception:
            act_val = {}
        hint["active_card"] = {
            "id": card_row["id"],
            "detector_type": card_row["detector_type"],
            "title": card_row["title"],
            "recommended_action": card_row["recommended_action"],
            "d3_routing": act_val.get("d3_routing") or {},
        }
        if hint["recommended_context_cap"] is None and "context_tokens" in act_val:
            hint["recommended_context_cap"] = int(act_val["context_tokens"])
    return hint
