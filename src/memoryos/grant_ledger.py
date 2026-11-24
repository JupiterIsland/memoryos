"""
Grant Ledger Reconciliation Engine — Read-Only Telemetry Auditor
================================================================
Reconciles AMD Token Lab / Grant telemetry exports against:
  1. Per-model request and token sums vs usage_totals
  2. Per-model micro-point (µpts / points_micro) burn vs account budget_used_micro
  3. Honest reporting of any unattributed upstream gap (never synthesized)
  4. Canonical unit label consistency (µpts) across ledger and UI
  5. Audit-trail 1:1 coverage and explicit error row visibility
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_PATH = REPO_ROOT / "memory" / "tokenlab_export.json"


def load_raw_export(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the raw export JSON without writing or mutating any state."""
    p = Path(path) if path else DEFAULT_EXPORT_PATH
    if not p.is_file():
        raise FileNotFoundError(f"Token Lab export not found at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def load_ledger_snapshot(
    grant_id: str = "1E13760B",
    window: str = "2026-11-14",
    export_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load a normalized grant ledger snapshot for a specific grant and window."""
    raw = load_raw_export(export_path)
    tl = raw.get("tokenlab", {})
    account = tl.get("account", {})
    totals = tl.get("usage_totals", {})
    daily = tl.get("usage_daily", [])
    gateway_daily = tl.get("gateway_daily", [])
    raw_reqs = tl.get("requests", [])

    models: Dict[str, Dict[str, int]] = {}
    for entry in daily:
        if window and entry.get("day") != window:
            continue
        m = entry.get("model", "unknown")
        toks = int(entry.get("prompt_tokens", 0)) + int(entry.get("completion_tokens", 0))
        models[m] = {
            "requests": int(entry.get("requests", 0)),
            "tokens": toks,
            "upts": int(entry.get("points_micro", 0)),
            "errors": int(entry.get("errors", 0)),
        }

    requests_list: List[Dict[str, Any]] = []
    for i, r in enumerate(raw_reqs):
        rid = f"req-{grant_id.lower()}-{i:03d}"
        requests_list.append({
            "id": rid,
            "created_at": r.get("created_at"),
            "model": r.get("model"),
            "prompt_tokens": r.get("prompt_tokens", 0),
            "completion_tokens": r.get("completion_tokens", 0),
            "tokens": r.get("prompt_tokens", 0) + r.get("completion_tokens", 0),
            "upts": r.get("points_micro", 0),
            "status": "ERROR" if r.get("has_error") else "OK",
            "finish_reason": r.get("finish_reason"),
        })

    consumed = int(account.get("budget_used_micro", 0))
    usage_totals_upts = int(totals.get("points_micro", 0))
    per_model_upts = sum(m["upts"] for m in models.values())
    gap = consumed - per_model_upts

    # Never synthesize an overhead attribution bucket; pass through only if upstream provides one.
    raw_overhead = tl.get("overhead_attribution") or raw.get("overhead_attribution") or {}
    attributed_total = int(raw_overhead.get("total", 0)) if isinstance(raw_overhead, dict) else 0
    unattributed_gap = gap - attributed_total

    gateway_allowed_daily = sum(
        int(g.get("allowed", 0))
        for g in gateway_daily
        if not window or g.get("day") == window
    )

    unit_label = "µpts"

    return {
        "grant_id": account.get("access_grant_id", grant_id),
        "window": window,
        "models": models,
        "gateway": {
            "allowed": int(totals.get("requests", 0)),
            "gateway_daily_allowed": gateway_allowed_daily,
            "tokens": int(totals.get("tokens", 0)),
            "errors": int(totals.get("errors", 0)),
            "unit_label": unit_label,
        },
        "grant": {
            "allocated": int(account.get("budget_micro", 0)),
            "consumed": consumed,
            "usage_totals_upts": usage_totals_upts,
            "per_model_upts": per_model_upts,
            "unattributed_gap": unattributed_gap,
            "unit_label": unit_label,
        },
        "overhead_attribution": raw_overhead if isinstance(raw_overhead, dict) else {},
        "requests": requests_list,
    }


def load_audit_trail(
    grant_id: str = "1E13760B",
    window: str = "2026-11-14",
    export_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load audit trail entries corresponding to the ledger window."""
    snapshot = load_ledger_snapshot(grant_id=grant_id, window=window, export_path=export_path)
    entries = []
    for r in snapshot["requests"]:
        entries.append({
            "id": r["id"],
            "created_at": r["created_at"],
            "model": r["model"],
            "tokens": r["tokens"],
            "upts": r["upts"],
            "status": r["status"],
            "finish_reason": r.get("finish_reason"),
        })

    return {
        "grant_id": grant_id,
        "window": window,
        "entries": entries,
        "out_of_window_errors": None,
    }
