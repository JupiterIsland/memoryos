"""Personal AI Operations Console — Objective-to-Resource Dispatch Engine.

Models are resources, not the product.
The operator states an objective; OperationsPlanner inspects:
  1. Frank-v1 intent & confidence (0 MB VRAM, sub-millisecond CPU)
  2. Live hardware silicon & VRAM headroom (gpu_backends)
  3. Live provider/resource pool readiness (cloud + NPU + local)
  4. Persistent Memory Vault operational constraints (SQLite WAL)

It emits a deterministic OperationPlan (primary resource, ordered fallback chain,
pre-flight resource actions, and rationale) and records every dispatch in an
auditable SQLite Operations Ledger (`ops_run_log`).
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

_VAULT_MODEL_FAMILIES: Tuple[str, ...] = ("gemma", "qwen", "deepseek", "llama", "bonsai", "inkling", "raon")

_MODEL_FAMILY_CLOUD_FALLBACK: Dict[str, Tuple[str, str, str, bool]] = {
    "gemma": ("cloud:Gemma-4-31B-IT", "cloud", "cloud_design", False),
    "qwen": ("cloud:Qwen3.8-27B", "cloud", "cloud_code", False),
    "deepseek": ("cloud:DeepSeek-V4.1-Flash", "cloud", "cloud_arch", False),
    "llama": ("groq:llama-3.3-70b-versatile", "groq", "cloud_lpu", False),
}


def _detect_vault_priority_family(
    objective: str,
    vault_facts: Optional[Sequence[Dict[str, Any]]],
) -> Optional[str]:
    """Return a high-priority model family token when it appears in BOTH the objective and a pinned vault fact."""
    if not objective or not vault_facts:
        return None
    obj_low = objective.lower()
    fact_blob = " ".join(
        f"{f.get('topic', '')} {f.get('content', '')} {f.get('tags', '')}"
        for f in vault_facts
        if isinstance(f, dict)
    ).lower()
    if not fact_blob.strip():
        return None
    for fam in _VAULT_MODEL_FAMILIES:
        if fam in obj_low and fam in fact_blob:
            return fam
    return None


# Ordered resource candidates per operational intent.
# Each tuple is (target_id, provider_key, tier_label, requires_local_vram).
INTENT_RESOURCE_MATRIX: Dict[str, List[Tuple[str, str, str, bool]]] = {
    "fast_code": [
        ("groq:llama-3.3-70b-versatile", "groq", "cloud_fast_lpu", False),
        ("cerebras:llama-3.3-70b", "cerebras", "cloud_wafer", False),
        ("cloud:Qwen3.8-27B", "cloud", "cloud_amd_tokenlab", False),
        ("openrouter:qwen/qwen-2.5-coder-32b-instruct", "openrouter", "cloud_gateway", False),
        ("hf:Qwen/Qwen2.5-Coder-32B-Instruct", "hf", "cloud_hf", False),
        ("ollama:qwen2.5-coder:7b", "ollama", "local_ollama", True),
        ("lemonade:Qwen3.5-4B-GGUF", "lemonade", "local_lemonade", True),
        ("studio:frank", "studio", "builtin_cpu", False),
    ],
    "architecture": [
        ("cloud:DeepSeek-V4.1-Flash", "cloud", "cloud_amd_tokenlab", False),
        ("openrouter:deepseek/deepseek-chat", "openrouter", "cloud_gateway", False),
        ("hf:deepseek-ai/DeepSeek-R1", "hf", "cloud_hf", False),
        ("groq:qwen/qwen3-32b", "groq", "cloud_fast_lpu", False),
        ("ollama:frank:latest", "ollama", "local_ollama", True),
        ("lemonade:Qwen3.5-4B-GGUF", "lemonade", "local_lemonade", True),
        ("studio:frank", "studio", "builtin_cpu", False),
    ],
    "large_design": [
        ("cloud:Gemma-4-31B-IT", "cloud", "cloud_amd_tokenlab", False),
        ("openrouter:google/gemma-3-27b-it", "openrouter", "cloud_gateway", False),
        ("hf:Qwen/Qwen2.5-72B-Instruct", "hf", "cloud_hf", False),
        ("lemonade:Qwen3.5-4B-GGUF", "lemonade", "local_lemonade", True),
        ("ollama:qwen2.5-coder:7b", "ollama", "local_ollama", True),
        ("studio:frank", "studio", "builtin_cpu", False),
    ],
    "cheap_bg": [
        ("cloud:MiniCPM5-2B", "cloud", "cloud_amd_tokenlab", False),
        ("groq:llama-3.1-8b-instant", "groq", "cloud_fast_lpu", False),
        ("cerebras:llama3.1-8b", "cerebras", "cloud_wafer", False),
        ("lemonade:Bonsai-4B-gguf", "lemonade", "local_lemonade", True),
        ("ollama:qwen2.5-coder:7b", "ollama", "local_ollama", True),
        ("studio:frank", "studio", "builtin_cpu", False),
    ],
    "vram_reclaim": [
        ("studio:frank", "studio", "builtin_cpu", False),
    ],
    "memory_pin": [
        ("studio:frank", "studio", "builtin_cpu", False),
    ],
}


@dataclass
class OperationPlan:
    op_id: str
    objective: str
    intent: str
    intent_confidence: float
    primary_target: str
    primary_tier: str
    fallback_chain: List[str] = field(default_factory=list)
    preflight_actions: List[str] = field(default_factory=list)
    hardware_guard: str = "nominal"
    local_vram_free_mb: int = 0
    local_vram_total_mb: int = 0
    resources_online: int = 0
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _select_live_local_target(
    default_target: str,
    provider_key: str,
    ollama_installed: List[str],
    lemonade_installed: List[str],
) -> Optional[str]:
    """Ensure local candidates resolve to an actually installed model when possible."""
    if provider_key == "ollama":
        if not ollama_installed:
            return None
        wanted = default_target.split(":", 1)[1]
        for m in ollama_installed:
            if m == wanted or m == f"{wanted}:latest":
                return f"ollama:{m}"
        return f"ollama:{ollama_installed[0]}"
    if provider_key == "lemonade":
        if not lemonade_installed:
            return None
        wanted = default_target.split(":", 1)[1]
        if wanted in lemonade_installed:
            return f"lemonade:{wanted}"
        return f"lemonade:{lemonade_installed[0]}"
    return default_target


class OperationsPlanner:
    """Translates an operator objective into a hardware-aware compute dispatch plan."""

    @staticmethod
    def plan_objective(
        objective: str,
        *,
        gpu_profile: Optional[Dict[str, Any]] = None,
        models_info: Optional[Dict[str, Any]] = None,
        frank_prediction: Optional[Dict[str, Any]] = None,
        prefer_local: bool = False,
        vault_facts: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> OperationPlan:
        clean_obj = (objective or "").strip()
        op_id = f"op-{uuid.uuid4().hex[:10]}"

        # 1. Intent from Frank-v1 (or lightweight fallback keyword check)
        low = clean_obj.lower()
        explicit_vram = any(k in low for k in ("vram", "reclaim", "unload", "free memory", "free ram", "flush gpu"))
        explicit_pin = any(k in low for k in ("remember", "pin rule", "memory vault", "never forget", "pin this"))
        intent = "architecture"
        conf = 0.5
        if isinstance(frank_prediction, dict) and frank_prediction.get("intent"):
            intent = str(frank_prediction["intent"])
            conf = float(frank_prediction.get("confidence", 0.5) or 0.5)
            # OOD guard: do not let low-confidence utility guesses (e.g. URLs or chat questions at ~27-35%)
            # hijack a conversational turn into studio:frank's static diagnostic card.
            if intent == "vram_reclaim" and conf < 0.55 and not explicit_vram:
                intent = "architecture"
            elif intent == "memory_pin" and conf < 0.55 and not explicit_pin:
                intent = "architecture"
        else:
            if explicit_vram:
                intent, conf = "vram_reclaim", 0.90
            elif explicit_pin:
                intent, conf = "memory_pin", 0.88
            elif any(k in low for k in ("fix", "bug", "diff", "patch", "refactor", "test", "code")):
                intent, conf = "fast_code", 0.80
            elif any(k in low for k in ("summarize", "changelog", "commit", "short", "brief")):
                intent, conf = "cheap_bg", 0.78
            elif any(k in low for k in ("spec", "design doc", "roadmap", "proposal", "diagram")):
                intent, conf = "large_design", 0.78

        # 2. Live silicon & VRAM guardrails
        gpu = gpu_profile or {}
        total_vram = int(gpu.get("total_vram_mb") or 0)
        free_vram = int(gpu.get("free_vram_mb") or 0)
        gpu_util = float(gpu.get("utilization_pct") or 0.0)
        temp_c = gpu.get("temperature_c")
        vram_tight = (total_vram > 0 and free_vram < 3072) or gpu_util >= 80.0
        thermal_warm = isinstance(temp_c, (int, float)) and float(temp_c) >= 78.0

        preflight: List[str] = []
        guard = "nominal"
        if intent == "vram_reclaim":
            preflight.append("reclaim_vram_and_ram")
            guard = "reclaim_requested"
        elif vram_tight or thermal_warm:
            guard = "protect_local_silicon_offload_cloud"
            if vram_tight:
                preflight.append("skip_local_heavy_weights_vram_tight")
            if thermal_warm:
                preflight.append("thermal_offload_guard_active")

        # 3. Live resource pool resolution
        m_info = models_info or {}
        providers = m_info.get("providers") or {}
        ollama_installed = list(m_info.get("ollama_installed") or [])
        lemonade_installed = list(m_info.get("lemonade_installed") or [])
        resources_online = sum(
            1 for k, v in providers.items()
            if k != "auto" and isinstance(v, dict) and v.get("ready")
        )

        candidates = list(INTENT_RESOURCE_MATRIX.get(intent, INTENT_RESOURCE_MATRIX["architecture"]))
        if prefer_local and not vram_tight:
            # Bubble local providers ahead of cloud when operator requests local-first & silicon has headroom
            candidates.sort(key=lambda item: (0 if item[1] in ("lemonade", "ollama", "studio") else 1))

        # 3b. Pinned Memory Vault high-priority token affinity:
        # When a pinned vault fact matches a model family mentioned in the objective (e.g. "gemma"),
        # prioritize locally cached Lemonade/vLLM/Flare/Ollama weights when silicon has headroom,
        # or offload cleanly to the matching cloud model (0 MB VRAM) when VRAM/thermals are tight.
        vault_family = _detect_vault_priority_family(clean_obj, vault_facts)
        if vault_family and intent not in ("vram_reclaim", "memory_pin"):
            preflight.append(f"vault_priority_token:{vault_family}")
            priority_candidates: List[Tuple[str, str, str, bool]] = []
            if not vram_tight and not thermal_warm:
                for m in lemonade_installed:
                    if vault_family in m.lower():
                        priority_candidates.append((f"lemonade:{m}", "lemonade", "local_npu_vault_affinity", False))
                        break
                if bool((providers.get("vllm") or {}).get("ready")):
                    priority_candidates.append((f"vllm:{vault_family}", "vllm", "local_vllm_vault_affinity", True))
                if bool((providers.get("flare") or {}).get("ready")):
                    priority_candidates.append((f"flare:{vault_family}", "flare", "local_flare_vault_affinity", True))
                for m in ollama_installed:
                    if vault_family in m.lower():
                        priority_candidates.append((f"ollama:{m}", "ollama", "local_cached_vault_affinity", True))
                        break
            cloud_match = _MODEL_FAMILY_CLOUD_FALLBACK.get(vault_family)
            if cloud_match:
                priority_candidates.append(cloud_match)
            if priority_candidates:
                candidates = priority_candidates + candidates

        resolved: List[Tuple[str, str]] = []
        seen_targets = set()
        for target_id, prov_key, tier_label, needs_vram in candidates:
            if prov_key == "studio":
                is_ready = True
            else:
                is_ready = bool((providers.get(prov_key) or {}).get("ready"))
            if not is_ready:
                continue
            if needs_vram and vram_tight and not prefer_local:
                continue
            actual_target = _select_live_local_target(target_id, prov_key, ollama_installed, lemonade_installed)
            if not actual_target or actual_target in seen_targets:
                continue
            seen_targets.add(actual_target)
            resolved.append((actual_target, tier_label))

        if not resolved:
            resolved.append(("studio:frank", "builtin_cpu"))

        primary_target, primary_tier = resolved[0]
        fallback_chain = [t for t, _ in resolved[1:4]]

        vault_note = f" Pinned Memory Vault token '{vault_family}' prioritized." if vault_family else ""
        rationale = (
            f"Frank-v1 classified objective as '{intent}' ({conf * 100:.0f}% conf).{vault_note} "
            f"Selected {primary_target} ({primary_tier}) with {len(fallback_chain)} ready fallback(s); "
            f"hardware guard={guard} (free VRAM={free_vram} MB)."
        )

        return OperationPlan(
            op_id=op_id,
            objective=clean_obj,
            intent=intent,
            intent_confidence=round(conf, 4),
            primary_target=primary_target,
            primary_tier=primary_tier,
            fallback_chain=fallback_chain,
            preflight_actions=preflight,
            hardware_guard=guard,
            local_vram_free_mb=free_vram,
            local_vram_total_mb=total_vram,
            resources_online=resources_online,
            rationale=rationale,
        )


class OperationsLedger:
    """SQLite-backed audit log for every objective dispatched by Jupiter Studio."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ops_run_log (
                    op_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    intent_confidence REAL NOT NULL,
                    primary_target TEXT NOT NULL,
                    executed_target TEXT NOT NULL,
                    hardware_guard TEXT NOT NULL,
                    preflight_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms REAL NOT NULL
                )
                """
            )
            conn.commit()

    def record_run(
        self,
        plan: OperationPlan,
        *,
        executed_target: str,
        status: str,
        latency_ms: float,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ops_run_log
                (op_id, created_at, objective, intent, intent_confidence, primary_target,
                 executed_target, hardware_guard, preflight_json, status, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.op_id,
                    now_iso,
                    plan.objective[:500],
                    plan.intent,
                    float(plan.intent_confidence),
                    plan.primary_target,
                    executed_target,
                    plan.hardware_guard,
                    json.dumps(plan.preflight_actions),
                    status,
                    round(float(latency_ms), 2),
                ),
            )
            conn.commit()

    def list_recent(self, limit: int = 25) -> List[Dict[str, Any]]:
        safe_limit = max(1, min(100, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT op_id, created_at, objective, intent, intent_confidence,
                       primary_target, executed_target, hardware_guard,
                       preflight_json, status, latency_ms
                FROM ops_run_log
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            try:
                item["preflight_actions"] = json.loads(item.pop("preflight_json", "[]"))
            except Exception:
                item["preflight_actions"] = []
            out.append(item)
        return out
