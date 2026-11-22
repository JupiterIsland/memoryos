"""
Memory Keeper, Continual Vault & Energy Reclaimer for MemoryOS.

Provides three concrete local capabilities for gamers and developers:
1. Live Memory Reclaimer (`reclaim_memory`): safely unloads idle local runner weights
   (e.g., Ollama /api/ps keep_alive=0) and collects unused buffers, returning measured
   before/after VRAM, host RAM, and GPU power telemetry.
2. Persistent Memory Vault (`MemoryVault`): SQLite-backed long-term memory facts and
   experience-replay episodes ("install memory" that survives restarts and model switches).
3. Never-Forget Continual Trainer (`train_continual_model`): trains SpeculativeOffloadModel
   on new workload episodes using Elastic Weight Consolidation (EWC) + Experience Replay so
   new patterns are learned without catastrophically forgetting prior operating regimes.
"""

from __future__ import annotations

import argparse
import gc
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from src.memoryos.gpu_backends import MultiGPUDetector
    from src.memoryos.speculative_offload import DEFAULT_WEIGHTS_PATH, SpeculativeOffloadModel
except ImportError:
    from memoryos.gpu_backends import MultiGPUDetector
    from memoryos.speculative_offload import DEFAULT_WEIGHTS_PATH, SpeculativeOffloadModel

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "QuietAdvisorDB.sqlite"
CONTINUAL_WEIGHTS_PATH = REPO_ROOT / "memory" / "models" / "speculative_offload_continual.json"
MAX_REPLAY_EPISODES = 2000
MAX_ENERGY_LEDGER_ROWS = 5000
TRUSTED_EPISODE_SOURCES = ("runtime", "explicit_train", "starter_curriculum")

# Conservative transparent energy model constants for local gaming/dev hardware vs heavy local LLM saturation:
# Typical laptop/desktop GPU incremental power above idle when executing heavy quantized 14B-32B inference (~45W for ~12s).
DEFAULT_INFERENCE_POWER_DELTA_W = 45.0
DEFAULT_SKIPPED_CALL_DURATION_S = 12.0


def _read_host_ram_mb(meminfo_path: Path = Path("/proc/meminfo")) -> Dict[str, int]:
    """Return total and available host RAM in MB cleanly without external deps."""
    if meminfo_path.exists():
        try:
            vals: Dict[str, int] = {}
            for line in meminfo_path.read_text(encoding="utf-8").splitlines():
                if ":" not in line:
                    continue
                k, rest = line.split(":", 1)
                toks = rest.strip().split()
                if toks and toks[0].isdigit():
                    vals[k.strip()] = int(toks[0])
            total_kb = vals.get("MemTotal", 0)
            avail_kb = vals.get("MemAvailable", vals.get("MemFree", 0))
            return {
                "total_mb": int(total_kb // 1024),
                "available_mb": int(avail_kb // 1024),
            }
        except Exception:
            pass
    return {"total_mb": 0, "available_mb": 0}


def _http_json(url: str, payload: Optional[Dict[str, Any]] = None, timeout: float = 1.5) -> Optional[Dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except Exception:
        return None


def _is_local_runner_url(url: str) -> bool:
    clean = str(url or "").strip().lower()
    return clean.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]"))


def reclaim_memory(ollama_host: Optional[str] = "http://127.0.0.1:11434") -> Dict[str, Any]:
    """Safely unload idle local Ollama runners + run GC, measuring VRAM & RAM reclaimed."""
    t0 = time.perf_counter()
    prof_before = MultiGPUDetector.get_active_profile()
    ram_before = _read_host_ram_mb()

    unloaded: List[str] = []
    if ollama_host and _is_local_runner_url(ollama_host):
        host = ollama_host.rstrip("/")
        ps_data = _http_json(f"{host}/api/ps", payload=None, timeout=1.2)
        models = ps_data.get("models", []) if isinstance(ps_data, dict) else []
        for entry in models:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or entry.get("model") or "").strip()
            if not name:
                continue
            resp = _http_json(
                f"{host}/api/generate",
                payload={"model": name, "prompt": "", "keep_alive": 0, "stream": False},
                timeout=3.0,
            )
            if resp is not None:
                unloaded.append(name)

    gc_collected = gc.collect()
    # Brief yield when an external GPU runner unloaded so nvidia-smi reflects freed allocations
    if unloaded:
        time.sleep(0.2)

    prof_after = MultiGPUDetector.get_active_profile()
    ram_after = _read_host_ram_mb()

    vram_before = int(getattr(prof_before, "used_vram_mb", 0) or 0)
    vram_after = int(getattr(prof_after, "used_vram_mb", 0) or 0)
    vram_freed = max(0, vram_before - vram_after)
    ram_freed = max(0, ram_after["available_mb"] - ram_before["available_mb"])

    return {
        "ok": True,
        "device_name": getattr(prof_after, "device_name", "CPU Mode"),
        "vram_before_mb": vram_before,
        "vram_after_mb": vram_after,
        "vram_total_mb": int(getattr(prof_after, "total_vram_mb", 0) or 0),
        "vram_freed_mb": vram_freed,
        "ram_avail_before_mb": ram_before["available_mb"],
        "ram_avail_after_mb": ram_after["available_mb"],
        "ram_freed_mb": ram_freed,
        "power_watts_before": getattr(prof_before, "power_watts", None),
        "power_watts_after": getattr(prof_after, "power_watts", None),
        "unloaded_models": unloaded,
        "gc_objects_collected": gc_collected,
        "duration_ms": round((time.perf_counter() - t0) * 1000.0, 2),
    }


class MemoryVault:
    """SQLite-backed continual memory vault, EWC replay buffer, and energy savings ledger."""

    def __init__(self, db_path: Optional[Path] = None, weights_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.weights_path = Path(weights_path) if weights_path is not None else CONTINUAL_WEIGHTS_PATH

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=3.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=3000")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS continual_memory_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '',
                importance REAL NOT NULL DEFAULT 1.0,
                recall_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_recalled_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS offload_training_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mse_delta_norm REAL NOT NULL,
                context_utilization REAL NOT NULL,
                secs_since_offload REAL NOT NULL,
                model_switch_rate REAL NOT NULL,
                label_offload REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'runtime',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS energy_savings_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                vram_saved_mb REAL NOT NULL DEFAULT 0.0,
                vram_reclaimed_mb REAL NOT NULL DEFAULT 0.0,
                avoided_watts REAL NOT NULL DEFAULT 0.0,
                estimated_wh_saved REAL NOT NULL DEFAULT 0.0,
                calls_skipped INTEGER NOT NULL DEFAULT 0,
                offloaded_calls INTEGER NOT NULL DEFAULT 0,
                details TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        return conn

    def remember(self, topic: str, content: str, tags: str = "", importance: float = 1.0) -> Dict[str, Any]:
        """Install or reinforce a persistent memory fact so future sessions never forget it."""
        clean_topic = " ".join(str(topic or "general").split())[:80] or "general"
        clean_content = str(content or "").strip()[:4000]
        clean_tags = ",".join(t.strip() for t in str(tags or "").split(",") if t.strip())[:200]
        if not clean_content:
            raise ValueError("Memory content cannot be empty")
        imp = max(0.1, min(5.0, float(importance)))
        now = datetime.now(timezone.utc).isoformat()

        conn = self._connect()
        try:
            existing = conn.execute(
                "SELECT id, recall_count FROM continual_memory_facts WHERE topic = ? AND content = ?",
                (clean_topic, clean_content),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE continual_memory_facts SET tags = ?, importance = ?, last_recalled_at = ? WHERE id = ?",
                    (clean_tags, imp, now, existing["id"]),
                )
                fact_id = int(existing["id"])
            else:
                cur = conn.execute(
                    "INSERT INTO continual_memory_facts (topic, content, tags, importance, created_at, last_recalled_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (clean_topic, clean_content, clean_tags, imp, now, now),
                )
                fact_id = int(cur.lastrowid)
            conn.commit()
            row = conn.execute("SELECT * FROM continual_memory_facts WHERE id = ?", (fact_id,)).fetchone()
            return dict(row)
        finally:
            conn.close()

    def recall(self, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant persisted facts ordered by lexical overlap, importance, and recency."""
        terms = {w.lower() for w in str(query or "").replace("/", " ").split() if len(w) >= 2}
        cap = max(1, min(50, int(limit)))
        now = datetime.now(timezone.utc).isoformat()

        conn = self._connect()
        try:
            rows = [dict(r) for r in conn.execute("SELECT * FROM continual_memory_facts ORDER BY id DESC LIMIT 250").fetchall()]
            if not rows:
                return []

            scored: List[Tuple[float, Dict[str, Any]]] = []
            for row in rows:
                hay = f"{row['topic']} {row['tags']} {row['content']}".lower()
                hits = sum(1 for t in terms if t in hay)
                if terms and hits == 0:
                    score = 0.05 * float(row.get("importance") or 1.0)
                else:
                    score = (1.0 + hits * 2.5) * float(row.get("importance") or 1.0)
                scored.append((score, row))

            scored.sort(key=lambda pair: (pair[0], pair[1]["id"]), reverse=True)
            chosen = [r for _, r in scored[:cap]]
            for item in chosen:
                conn.execute(
                    "UPDATE continual_memory_facts SET recall_count = recall_count + 1, last_recalled_at = ? WHERE id = ?",
                    (now, item["id"]),
                )
            conn.commit()
            return chosen
        finally:
            conn.close()

    def list_facts(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM continual_memory_facts ORDER BY importance DESC, id DESC LIMIT ?",
                (max(1, min(200, int(limit))),),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def forget(self, fact_id: int) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute("DELETE FROM continual_memory_facts WHERE id = ?", (int(fact_id),))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def record_episode(self, features: Dict[str, float], label_offload: float, source: str = "runtime") -> int:
        """Persist a labeled routing episode into the SQLite experience-replay buffer."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO offload_training_episodes
                (mse_delta_norm, context_utilization, secs_since_offload, model_switch_rate, label_offload, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    float(features.get("mse_delta_norm", 0.0)),
                    float(features.get("context_utilization", 0.0)),
                    float(features.get("secs_since_offload", 0.0)),
                    float(features.get("model_switch_rate", 0.0)),
                    1.0 if float(label_offload) >= 0.5 else 0.0,
                    str(source or "runtime")[:64],
                    now,
                ),
            )
            conn.execute(
                """
                DELETE FROM offload_training_episodes
                WHERE id NOT IN (
                    SELECT id FROM offload_training_episodes ORDER BY id DESC LIMIT ?
                )
                """,
                (MAX_REPLAY_EPISODES,),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def _load_or_init_model(self) -> SpeculativeOffloadModel:
        if self.weights_path.is_file():
            return SpeculativeOffloadModel.load(self.weights_path)
        return SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)

    def train_continual_model(
        self,
        new_episodes: Optional[Sequence[Tuple[Dict[str, float], float]]] = None,
        replay_limit: int = 200,
        lr: float = 0.08,
        epochs: int = 80,
        ewc_lambda: float = 15.0,
        seed_defaults: bool = False,
    ) -> Dict[str, Any]:
        """Train SpeculativeOffloadModel incrementally with EWC + replay and save checkpoint."""
        new_list: List[Tuple[Dict[str, float], float]] = []
        if new_episodes:
            for feats, lbl in new_episodes:
                self.record_episode(feats, float(lbl), source="explicit_train")
                new_list.append((feats, float(lbl)))

        conn = self._connect()
        try:
            placeholders = ",".join("?" for _ in TRUSTED_EPISODE_SOURCES)
            rows = conn.execute(
                f"SELECT mse_delta_norm, context_utilization, secs_since_offload, model_switch_rate, label_offload "
                f"FROM offload_training_episodes WHERE source IN ({placeholders}) ORDER BY id DESC LIMIT ?",
                (*TRUSTED_EPISODE_SOURCES, max(1, min(MAX_REPLAY_EPISODES, int(replay_limit)))),
            ).fetchall()
        finally:
            conn.close()

        replay_samples = [
            (
                {
                    "mse_delta_norm": float(r["mse_delta_norm"]),
                    "context_utilization": float(r["context_utilization"]),
                    "secs_since_offload": float(r["secs_since_offload"]),
                    "model_switch_rate": float(r["model_switch_rate"]),
                },
                float(r["label_offload"]),
            )
            for r in rows
        ]

        if not new_list and not replay_samples and seed_defaults:
            for feats, lbl in (build_gaming_curriculum() + build_coding_curriculum())[:8]:
                self.record_episode(feats, float(lbl), source="starter_curriculum")
                new_list.append((feats, float(lbl)))
            replay_samples = new_list[:]

        model = self._load_or_init_model()
        if not new_list and not replay_samples:
            return {
                "trained": False,
                "episodes_total": 0,
                "accuracy": None,
                "ewc_protected": bool(model.export_ewc_state() is not None),
                "weights_path": str(self.weights_path),
            }

        metrics = model.fit_continual(
            new_samples=new_list or replay_samples,
            replay_samples=replay_samples if new_list else (),
            lr=lr,
            epochs=epochs,
            ewc_lambda=ewc_lambda,
            consolidate_after=True,
        )
        model.version = "1.1.0-continual"
        model.save(self.weights_path)
        return {
            "trained": True,
            "episodes_total": len(replay_samples),
            "accuracy": metrics["accuracy"],
            "brier_loss": metrics["brier_loss"],
            "ewc_protected": bool(metrics.get("ewc_protected")),
            "weights_path": str(self.weights_path),
        }

    def record_energy_event(
        self,
        event_type: str,
        vram_saved_mb: float = 0.0,
        vram_reclaimed_mb: float = 0.0,
        calls_skipped: int = 0,
        offloaded_calls: int = 0,
        power_delta_w: float = DEFAULT_INFERENCE_POWER_DELTA_W,
        duration_s: float = DEFAULT_SKIPPED_CALL_DURATION_S,
        details: str = "",
    ) -> None:
        """Log verified hardware/inference savings with transparent watt-hour derivation."""
        events_saved = max(0, int(calls_skipped)) + max(0, int(offloaded_calls))
        wh_saved = round((events_saved * max(0.0, float(power_delta_w)) * max(0.0, float(duration_s))) / 3600.0, 4)
        avoided_watts = float(power_delta_w) if events_saved > 0 else 0.0
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO energy_savings_ledger
                (event_type, vram_saved_mb, vram_reclaimed_mb, avoided_watts, estimated_wh_saved, calls_skipped, offloaded_calls, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event_type)[:48],
                    float(vram_saved_mb),
                    float(vram_reclaimed_mb),
                    avoided_watts,
                    wh_saved,
                    int(calls_skipped),
                    int(offloaded_calls),
                    str(details or "")[:240],
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_summary(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            facts_count = int(conn.execute("SELECT COUNT(*) FROM continual_memory_facts").fetchone()[0])
            ep_count = int(conn.execute("SELECT COUNT(*) FROM offload_training_episodes").fetchone()[0])
            row = conn.execute(
                "SELECT COALESCE(SUM(calls_skipped), 0), COALESCE(SUM(offloaded_calls), 0), "
                "COALESCE(MAX(vram_saved_mb), 0.0), COALESCE(SUM(vram_reclaimed_mb), 0.0), "
                "COALESCE(SUM(estimated_wh_saved), 0.0) FROM energy_savings_ledger"
            ).fetchone()
            return {
                "facts_count": facts_count,
                "episodes_count": ep_count,
                "ewc_checkpoint_ready": self.weights_path.is_file(),
                "calls_skipped": int(row[0]),
                "offloaded_calls": int(row[1]),
                "peak_vram_saved_mb": round(float(row[2]), 1),
                "total_vram_reclaimed_mb": round(float(row[3]), 1),
                "estimated_wh_saved": round(float(row[4]), 4),
                "formula_note": f"{DEFAULT_INFERENCE_POWER_DELTA_W:.0f}W incremental GPU delta × {DEFAULT_SKIPPED_CALL_DURATION_S:.0f}s/event",
            }
        finally:
            conn.close()


def build_gaming_curriculum() -> List[Tuple[Dict[str, float], float]]:
    """Gaming workload curriculum: offload large visual scene cuts, skip steady UI frames."""
    return [
        ({"mse_delta_norm": 0.95, "context_utilization": 0.15, "secs_since_offload": 0.90, "model_switch_rate": 0.05}, 1.0),
        ({"mse_delta_norm": 0.88, "context_utilization": 0.20, "secs_since_offload": 0.80, "model_switch_rate": 0.05}, 1.0),
        ({"mse_delta_norm": 0.10, "context_utilization": 0.55, "secs_since_offload": 0.10, "model_switch_rate": 0.85}, 0.0),
        ({"mse_delta_norm": 0.12, "context_utilization": 0.50, "secs_since_offload": 0.15, "model_switch_rate": 0.80}, 0.0),
    ] * 6


def build_coding_curriculum() -> List[Tuple[Dict[str, float], float]]:
    """Shifted dev curriculum: offload high model-switch + context sessions, skip fresh motion bursts."""
    return [
        ({"mse_delta_norm": 0.10, "context_utilization": 0.65, "secs_since_offload": 0.25, "model_switch_rate": 0.90}, 1.0),
        ({"mse_delta_norm": 0.14, "context_utilization": 0.70, "secs_since_offload": 0.30, "model_switch_rate": 0.85}, 1.0),
        ({"mse_delta_norm": 0.85, "context_utilization": 0.10, "secs_since_offload": 0.05, "model_switch_rate": 0.05}, 0.0),
        ({"mse_delta_norm": 0.80, "context_utilization": 0.12, "secs_since_offload": 0.08, "model_switch_rate": 0.08}, 0.0),
    ] * 6


def _fresh_audit_mlp() -> SpeculativeOffloadModel:
    w1 = [
        [0.4, 0.2, 0.1, -0.1],
        [-0.2, 0.4, 0.2, 0.1],
        [0.3, -0.1, 0.3, 0.2],
        [0.1, 0.3, -0.1, 0.4],
        [-0.3, -0.2, 0.4, 0.1],
        [0.2, 0.1, 0.1, 0.3],
        [0.35, 0.25, -0.2, 0.1],
        [-0.1, 0.2, 0.3, -0.2],
    ]
    b1 = [0.05] * 8
    w2 = [0.25, -0.15, 0.2, 0.3, -0.1, 0.25, 0.2, -0.15]
    return SpeculativeOffloadModel(w1=w1, b1=b1, w2=w2, b2=0.0)


def build_telemetry_heavy_curriculum() -> List[Tuple[Dict[str, float], float]]:
    """Task C: multimodal high-context heavy vision regime testing 3-stage Fisher staleness."""
    return [
        ({"mse_delta_norm": 0.62, "context_utilization": 0.85, "secs_since_offload": 0.65, "model_switch_rate": 0.40}, 1.0),
        ({"mse_delta_norm": 0.70, "context_utilization": 0.78, "secs_since_offload": 0.55, "model_switch_rate": 0.35}, 1.0),
        ({"mse_delta_norm": 0.05, "context_utilization": 0.15, "secs_since_offload": 0.05, "model_switch_rate": 0.15}, 0.0),
        ({"mse_delta_norm": 0.08, "context_utilization": 0.12, "secs_since_offload": 0.08, "model_switch_rate": 0.12}, 0.0),
    ] * 6


def run_anti_forgetting_audit() -> Dict[str, Any]:
    """Run live Naive-SGD vs EWC+Replay (2-stage + 3-stage Task A->B->C staleness) and MLP latency check."""
    t0 = time.perf_counter()
    task_a = build_gaming_curriculum()
    task_b = build_coding_curriculum()
    task_c = build_telemetry_heavy_curriculum()

    naive = _fresh_audit_mlp()
    naive.fit_continual(task_a, lr=0.22, epochs=120, ewc_lambda=0.0, consolidate_after=False)
    naive.fit_continual(task_b, replay_samples=(), lr=0.30, epochs=180, ewc_lambda=0.0, consolidate_after=False)
    naive_a_after = naive.evaluate(task_a)["accuracy"]
    naive_b_after = naive.evaluate(task_b)["accuracy"]

    ewc = _fresh_audit_mlp()
    ewc.fit_continual(task_a, lr=0.22, epochs=120, ewc_lambda=0.0, consolidate_after=True)
    ewc_a_before = ewc.evaluate(task_a)["accuracy"]
    ewc.fit_continual(task_b, replay_samples=task_a, lr=0.22, epochs=150, ewc_lambda=8.0, consolidate_after=True)
    ewc_a_after = ewc.evaluate(task_a)["accuracy"]
    ewc_b_after = ewc.evaluate(task_b)["accuracy"]

    # 3-stage Fisher staleness check: learn Task C with replay + consolidated A+B Fisher
    ewc.fit_continual(task_c, replay_samples=task_a[:8] + task_b[:8], lr=0.20, epochs=120, ewc_lambda=8.0, consolidate_after=True)
    ewc_a_after_abc = ewc.evaluate(task_a)["accuracy"]
    ewc_c_after = ewc.evaluate(task_c)["accuracy"]
    ewc_state = ewc.export_ewc_state() or {}
    max_fisher = max(
        [v for row in ewc_state.get("fisher_w1", [[0.0]]) for v in row]
        + list(ewc_state.get("fisher_w2", [0.0]))
        + [float(ewc_state.get("fisher_b2", 0.0))]
    )

    probe = task_a[0][0]
    t_lat = time.perf_counter_ns()
    for _ in range(500):
        ewc.predict_proba(probe)
    mlp_mean_us = round((time.perf_counter_ns() - t_lat) / 500.0 / 1000.0, 2)

    passed = bool(
        naive_a_after < 0.75
        and ewc_a_after >= 0.90
        and ewc_b_after >= 0.90
        and ewc_a_after_abc >= 0.90
        and ewc_c_after >= 0.90
        and mlp_mean_us < 500.0
    )
    return {
        "passed": passed,
        "naive_task_a_after": naive_a_after,
        "naive_task_b_after": naive_b_after,
        "ewc_task_a_before": ewc_a_before,
        "ewc_task_a_after": ewc_a_after,
        "ewc_task_b_after": ewc_b_after,
        "ewc_task_a_after_abc": ewc_a_after_abc,
        "ewc_task_c_after": ewc_c_after,
        "max_fisher_observed": round(max_fisher, 4),
        "mlp_mean_us": mlp_mean_us,
        "duration_ms": round((time.perf_counter() - t0) * 1000.0, 2),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MemoryOS Memory Keeper — Reclaim VRAM, Install Memory & Train EWC Router")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Show live GPU, host RAM, persistent memory count, and energy savings")
    sub.add_parser("reclaim", help="Unload idle Ollama weights + run GC to free local VRAM/RAM")
    sub.add_parser("audit", help="Verify Naive SGD catastrophic forgetting vs EWC+Replay retention")

    p_inst = sub.add_parser("install", help="Install a persistent memory fact into QuietAdvisorDB.sqlite")
    p_inst.add_argument("topic", help="Topic label (e.g. 'hardware', 'project')")
    p_inst.add_argument("content", help="Fact text to persist across sessions")
    p_inst.add_argument("--tags", default="", help="Comma-separated tags")

    p_rec = sub.add_parser("recall", help="Recall persistent memory facts matching a query")
    p_rec.add_argument("query", nargs="?", default="", help="Search query")

    p_trn = sub.add_parser("train", help="Train continual EWC + Replay SpeculativeOffloadModel")
    p_trn.add_argument("--epochs", type=int, default=80)

    args = parser.parse_args(list(argv) if argv is not None else None)
    vault = MemoryVault()

    if args.cmd == "status":
        prof = MultiGPUDetector.get_active_profile()
        out = {
            "gpu": prof.__dict__,
            "host_ram": _read_host_ram_mb(),
            "vault": vault.get_summary(),
        }
        print(json.dumps(out, indent=2))
        return 0

    if args.cmd == "reclaim":
        rep = reclaim_memory()
        vault.record_energy_event(
            event_type="vram_reclaim",
            vram_reclaimed_mb=rep["vram_freed_mb"],
            details=f"unloaded={rep['unloaded_models']}",
        )
        print(json.dumps(rep, indent=2))
        return 0

    if args.cmd == "install":
        fact = vault.remember(args.topic, args.content, tags=args.tags)
        print(json.dumps(fact, indent=2))
        return 0

    if args.cmd == "recall":
        print(json.dumps(vault.recall(args.query), indent=2))
        return 0

    if args.cmd == "train":
        print(json.dumps(vault.train_continual_model(epochs=args.epochs, seed_defaults=True), indent=2))
        return 0

    if args.cmd == "audit":
        print(json.dumps(run_anti_forgetting_audit(), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
