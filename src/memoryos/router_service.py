"""Lightweight HTTP-agnostic routing & feedback service for MemoryOS Router."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.memoryos.quiet_advisor_db import (
    DEFAULT_DB_PATH,
    QuietAdvisorDB,
    acknowledge_card_sync,
    get_routing_advice_sync,
    record_routed_inference_sync,
)
from src.memoryos.router import (
    gatekeep_frame_with_d3,
    mse_to_frame_delta,
    route_task,
)


def resolve_db_path(explicit: Optional[Path] = None) -> Path:
    if explicit is not None:
        return Path(explicit)
    env_db = os.getenv("QUIET_ADVISOR_DB", "").strip()
    return Path(env_db) if env_db else DEFAULT_DB_PATH


def process_frame_delta(
    payload: Dict[str, Any],
    default_db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Evaluate frame visual/MSE delta with Token Lab d3 and optionally log gatekeep telemetry."""
    t0 = time.perf_counter()
    session_id = str(payload.get("session_id") or "jupiter-desktop")
    user_id = str(payload.get("user_id") or "default")
    context_hint = str(payload.get("context_hint") or "Jupiter Desktop frame delta check")
    previous_response = payload.get("previous_response")
    db_path = resolve_db_path(default_db_path)

    delta_input = payload.get("frame_delta")
    if isinstance(delta_input, dict):
        delta_dict = dict(delta_input)
    elif payload.get("mse_delta") is not None:
        threshold = float(payload.get("threshold") or 12.0)
        delta_dict = mse_to_frame_delta(float(payload["mse_delta"]), threshold=threshold)
    else:
        delta_dict = {"composite_delta": 1.0, "threshold": 0.08, "significant_change": True}

    decision = gatekeep_frame_with_d3(
        delta_info=delta_dict,
        context_hint=context_hint,
    )
    gate_latency = round((time.perf_counter() - t0) * 1000.0, 2)
    skip_vision = bool(decision.get("skip_vision", False))

    if skip_vision and payload.get("log_skip", True):
        record_routed_inference_sync(
            route_result={
                "model": "d3-gatekeeper",
                "d3_decision": decision,
                "d3_skipped": True,
                "gpu_id": "tokenlab-d3-gate",
                "latency_ms": gate_latency,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            },
            user_id=user_id,
            session_id=session_id,
            context_tokens_provided=0,
            db_path=db_path,
        )

    return {
        "session_id": session_id,
        "skip_vision": skip_vision,
        "d3_decision": decision,
        "gate_latency_ms": gate_latency,
        "cached_response": previous_response if skip_vision else None,
    }


def process_route_request(
    payload: Dict[str, Any],
    heat_stream: Any = None,
    default_db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Route an inference or coding prompt via Quiet Advisor preferences + d3 + Token Lab."""
    t0 = time.perf_counter()
    db_path = resolve_db_path(default_db_path)
    session_id = str(payload.get("session_id") or "api-route")
    user_id = str(payload.get("user_id") or "default")
    prompt_text = str(payload.get("prompt_text") or payload.get("prompt") or "").strip()
    if not prompt_text:
        raise ValueError("Request must include non-empty 'prompt' or 'prompt_text'.")

    image_url = payload.get("image_url")
    task_type = payload.get("task_type")
    max_tokens = int(payload.get("max_tokens") or 1024)
    prefer_local = bool(payload.get("prefer_local", False))
    forced_model = payload.get("forced_model")

    # Optional pre-inference d3 frame-delta gatekeeping inside /api/route
    if payload.get("frame_delta") is not None or payload.get("mse_delta") is not None:
        gate_res = process_frame_delta(payload, default_db_path=db_path)
        if gate_res["skip_vision"]:
            cached = gate_res.get("cached_response") or json.dumps(
                {
                    "label": "Static Scene (d3 Gatekept)",
                    "summary": "Skipped heavy VLM call (d3 choice=ignore).",
                    "d3_skipped": True,
                }
            )
            return {
                "session_id": session_id,
                "route": "d3_gatekeep_skip",
                "model": "d3-gatekeeper",
                "content": str(cached),
                "skipped": True,
                "d3_decision": gate_res["d3_decision"],
                "latency_ms": gate_res["gate_latency_ms"],
                "user_preference_penalty": None,
                "local_execution_blocked": False,
                "routing_policy": "d3_frame_delta_ignore",
                "gpu_id": "tokenlab-d3-gate",
                "quiet_advisor_card": None,
                "checkpoint_path": None,
            }

    tlb_context = payload.get("tlb_context")
    if not tlb_context and payload.get("context_from_memory") and heat_stream is not None:
        try:
            hot = heat_stream.scan_for_hot_memories()
            if hot:
                tlb_context = "\n".join(f"[{b.title}] {b.content[:200]}" for b in hot[:3])
        except Exception:
            pass

    if image_url and not forced_model and not task_type:
        forced_model = "Gemma-4-31B-IT"

    routed = route_task(
        prompt_text=prompt_text,
        tlb_context=tlb_context,
        image_url=image_url,
        max_tokens=max_tokens,
        forced_model=forced_model,
        task_type=task_type,
        prefer_local=prefer_local,
        user_id=user_id,
        session_id=session_id,
        log_to_advisor=True,
        db_path=db_path,
    )

    penalty = routed.get("vram_thrashing_penalty")
    quiet_card = None
    if penalty and routed.get("local_execution_blocked"):
        quiet_card = {
            "detector_type": "vram_thrashing",
            "title": "Local VRAM Offload Enforced",
            "confidence": 0.95,
            "description": (
                f"Applied vram_thrashing_penalty={penalty:.2f}. "
                f"Blocked local execution and routed to {routed['model']} on AMD Token Lab."
            ),
        }

    return {
        "session_id": session_id,
        "route": routed["route"],
        "task_type": task_type or routed["route"],
        "model": routed["model"],
        "content": str(routed["content"]),
        "skipped": False,
        "latency_ms": float(routed.get("latency_ms") or round((time.perf_counter() - t0) * 1000.0, 2)),
        "user_preference_penalty": penalty,
        "local_execution_blocked": bool(routed.get("local_execution_blocked")),
        "routing_policy": routed.get("routing_policy", "standard_d3_router"),
        "gpu_id": routed.get("gpu_id", "tokenlab-remote"),
        "d3_decision": routed.get("d3_decision"),
        "usage": routed.get("usage"),
        "quiet_advisor_card": quiet_card,
        "checkpoint_path": routed.get("checkpoint_path"),
    }


def process_acknowledge_card(
    payload: Dict[str, Any],
    default_db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Acknowledge a Quiet Advisor card and write penalty preferences to SQLite."""
    db_path = resolve_db_path(default_db_path)
    card_id = payload.get("card_id")
    card_id_int = int(card_id) if card_id is not None else None
    card_type = str(payload.get("card_type") or payload.get("detector_type") or "vram_thrashing")
    action = str(payload.get("action") or "acknowledge")
    user_id = payload.get("user_id")
    user_id_str = str(user_id) if user_id else None
    penalty_val = payload.get("penalty")
    penalty_float = float(penalty_val) if penalty_val is not None else None

    return acknowledge_card_sync(
        user_id=user_id_str,
        card_id=card_id_int,
        card_type=card_type,
        action=action,
        penalty=penalty_float,
        db_path=db_path,
    )
