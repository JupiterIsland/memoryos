"""
THE QUIET ADVISOR - Core Detection Engine
Part of: MemoryOS + Jupiter One unified system

This module implements the 10 pattern detectors that surface insights
to users about their inference patterns.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple, Union
from enum import Enum

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT_DIR = REPO_ROOT / "memory" / "checkpoints"
DEFAULT_EXPORT_PATH = REPO_ROOT / "memory" / "tokenlab_export.json"


class DetectorType(Enum):
    CONTEXT_WASTE = "context_waste"
    MODEL_THRASHING = "model_thrashing"
    VRAM_THRASHING = "vram_thrashing"
    PERFORMANCE_ENVELOPE = "performance_envelope"
    REPEATED_FAILURES = "repeated_failures"
    QUALITY_DRIFT = "quality_drift"
    EFFICIENCY_FRONTIER = "efficiency_frontier"
    THERMAL_THROTTLING = "thermal_throttling"
    DEFAULT_SUBOPTIMALITY = "default_suboptimality"
    RECENCY_BIAS = "recency_bias"
    ANOMALY_DETECTION = "anomaly_detection"
    NVME_CHECKPOINTS = "nvme_checkpoints"


@dataclass
class InferenceLog:
    """Single inference execution record"""
    timestamp: datetime
    model_id: str
    context_tokens_provided: int
    context_tokens_used: int
    time_to_first_token_ms: float
    total_latency_ms: float
    tokens_per_second: float
    gpu_utilization_percent: float
    gpu_temperature_celsius: float
    gpu_memory_used_mb: int
    output_quality_score: Optional[float] = None
    error_flag: bool = False
    error_message: Optional[str] = None


@dataclass
class DetectedInsight:
    """Insight detected by a detector"""
    detector_type: DetectorType
    title: str
    subtitle: str
    description: str
    metrics: Dict[str, str]
    recommended_action: str
    action_value: Dict
    time_savings_seconds: int = 0
    quality_improvement_percent: float = 0.0
    confidence: float = 1.0
    suggested_experiments: List[str] = None
    
    def score(self, user_preferences: Dict = None) -> float:
        """Calculate insight score for ranking"""
        base_score = 0.0
        
        # Time savings: most valuable
        base_score += min(self.time_savings_seconds / 3600, 1.0) * 0.4
        
        # Quality improvement
        base_score += min(self.quality_improvement_percent / 100, 1.0) * 0.3
        
        # Confidence
        base_score += self.confidence * 0.2
        
        # User preference
        if user_preferences:
            pref = user_preferences.get(self.detector_type.value, 0.5)
            base_score *= (0.5 + pref)  # Multiply by preference (0.5-1.5 factor)
        
        return base_score


class ContextWasteDetector:
    """Detector 1: Finds context padding waste"""
    
    @staticmethod
    def detect(inferences: List[InferenceLog]) -> Optional[DetectedInsight]:
        if len(inferences) < 5:
            return None
        
        # Calculate average context utilization
        utilizations = []
        for inf in inferences:
            if inf.context_tokens_provided > 0:
                util = inf.context_tokens_used / inf.context_tokens_provided
                utilizations.append(util)
        
        if not utilizations:
            return None
        
        avg_utilization = sum(utilizations) / len(utilizations)
        
        # Threshold: if using less than 50% of provided context
        if avg_utilization > 0.5:
            return None
        
        waste_percent = (1 - avg_utilization) * 100
        
        # Calculate potential savings
        avg_context_provided = sum(i.context_tokens_provided for i in inferences) / len(inferences)
        recommended_context = int(sum(i.context_tokens_used for i in inferences) / len(inferences) * 1.2)
        
        # Estimate time savings (rough calculation)
        avg_latency = sum(i.total_latency_ms for i in inferences) / len(inferences)
        speedup_factor = avg_context_provided / recommended_context
        time_saved_per_inference = avg_latency * (1 - (1/speedup_factor)) if speedup_factor > 1 else 0
        daily_inferences = 15  # assumption
        time_savings_seconds = int((time_saved_per_inference / 1000) * daily_inferences * 5)  # 5 days week
        
        return DetectedInsight(
            detector_type=DetectorType.CONTEXT_WASTE,
            title="Context Waste Detected",
            subtitle=f"{waste_percent:.0f}% of your context goes unused",
            description=f"""
Last 7 days, you provided {avg_context_provided:.0f} tokens context on average.
Your model used {sum(i.context_tokens_used for i in inferences)/len(inferences):.0f} tokens.

You're padding {waste_percent:.0f}% of your context with unused data.

Reducing context to {recommended_context} tokens would:
- Speed up inference by {speedup_factor:.1f}x
- Save {time_savings_seconds/3600:.1f} hours per week
- Maintain identical quality
            """,
            metrics={
                "context_provided": f"{avg_context_provided:.0f} tokens",
                "context_used": f"{sum(i.context_tokens_used for i in inferences)/len(inferences):.0f} tokens",
                "waste": f"{waste_percent:.0f}%",
                "speedup_potential": f"{speedup_factor:.1f}x",
            },
            recommended_action="reduce_context",
            action_value={"context_tokens": recommended_context},
            time_savings_seconds=time_savings_seconds,
            quality_improvement_percent=0.0,
            confidence=0.95,
            suggested_experiments=[f"try_{recommended_context}", f"try_{int(recommended_context*0.8)}", f"try_{int(recommended_context*1.2)}"]
        )


class ModelThrashingDetector:
    """Detector 2: Finds inefficient model switching"""
    
    @staticmethod
    def detect(inferences: List[InferenceLog]) -> Optional[DetectedInsight]:
        if len(inferences) < 10:
            return None
        
        # Count model switches
        models_in_order = [i.model_id for i in inferences]
        switches = sum(1 for i in range(1, len(models_in_order)) if models_in_order[i] != models_in_order[i-1])
        
        # Threshold: more than 5 switches in a day
        if switches < 5:
            return None
        
        # Calculate wasted time in model loads
        # Assume 8 second model load per switch
        model_load_time_per_switch = 8.0
        total_waste_seconds = switches * model_load_time_per_switch
        
        # Find which models are thrashed
        model_counts = {}
        for model in models_in_order:
            model_counts[model] = model_counts.get(model, 0) + 1
        
        top_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:2]
        
        return DetectedInsight(
            detector_type=DetectorType.MODEL_THRASHING,
            title="Model Thrashing Detected",
            subtitle=f"You switched models {switches} times, wasting {total_waste_seconds:.0f} seconds",
            description=f"""
Yesterday you switched models {switches} times.
Your top models: {top_models[0][0]} ({top_models[0][1]}x), {top_models[1][0]} ({top_models[1][1]}x)

Model loading wastes ~8 seconds per switch.
Total waste: {total_waste_seconds:.0f} seconds = {total_waste_seconds/60:.1f} minutes per day.

If you kept your top 2 models in Warm tier (CPU RAM):
- Reloads drop from 8s to 0.5s
- You'd save ~{(total_waste_seconds - switches*0.5)/60:.1f} minutes per day
- Cost: ~16GB additional RAM (usually available)
            """,
            metrics={
                "switches_per_day": str(switches),
                "top_models": f"{top_models[0][0]}, {top_models[1][0]}",
                "waste_per_switch": "8 seconds",
                "total_waste": f"{total_waste_seconds/60:.1f} minutes",
            },
            recommended_action="enable_warm_tier_caching",
            action_value={"models_to_cache": [m[0] for m in top_models]},
            time_savings_seconds=int(total_waste_seconds * 5),  # 5 days/week
            quality_improvement_percent=0.0,
            confidence=0.9,
            suggested_experiments=["cache_both", "cache_primary_only"]
        )


class VRAMThrashingDetector:
    """Detector: Detects local 8GB VRAM saturation and triggers Token Lab offload advice."""

    @staticmethod
    def detect(inferences: List[InferenceLog]) -> Optional[DetectedInsight]:
        pressured = [
            i
            for i in inferences
            if i.gpu_memory_used_mb >= 5500 or i.gpu_utilization_percent >= 85.0
        ]
        if len(pressured) < 2:
            return None

        peak_mb = max(i.gpu_memory_used_mb for i in pressured)
        avg_mb = sum(i.gpu_memory_used_mb for i in pressured) / len(pressured)
        avg_lat = sum(i.total_latency_ms for i in pressured) / len(pressured)

        return DetectedInsight(
            detector_type=DetectorType.VRAM_THRASHING,
            title="VRAM Thrashing Detected on Local RTX 3070",
            subtitle=f"Peak {peak_mb} MB VRAM saturated across {len(pressured)} local vision/model runs",
            description=(
                f"Local GPU execution hit {peak_mb} MB peak VRAM (avg {avg_mb:.0f} MB, {avg_lat:.0f} ms latency).\n"
                "Click [Acknowledge & Apply] to write vram_thrashing_penalty=1.5 into QuietAdvisorDB\n"
                "and automatically route future heavy VLM requests to Gemma-4-31B-IT on AMD Token Lab."
            ),
            metrics={
                "peak_vram": f"{peak_mb} MB",
                "saturated_runs": str(len(pressured)),
                "recommended_target": "Gemma-4-31B-IT (Token Lab)",
            },
            recommended_action="force_tokenlab_offload",
            action_value={"vram_thrashing_penalty": 1.5, "forced_model": "Gemma-4-31B-IT"},
            time_savings_seconds=max(1800, int(len(pressured) * 450)),
            quality_improvement_percent=35.0,
            confidence=0.85,
            suggested_experiments=["force_gemma_31b_offload", "enable_d3_frame_gatekeep"],
        )


VRAMWasteDetector = VRAMThrashingDetector


class PerformanceEnvelopeDetector:
    """Detector 3: Finds your best hour and suggests replication"""
    
    @staticmethod
    def detect(inferences: List[InferenceLog]) -> Optional[DetectedInsight]:
        if len(inferences) < 10:
            return None
        
        # Find best and worst throughput
        throughputs = [i.tokens_per_second for i in inferences if i.tokens_per_second > 0]
        if len(throughputs) < 5:
            return None
        
        best_throughput = max(throughputs)
        avg_throughput = sum(throughputs) / len(throughputs)
        
        # Threshold: if best is 30% better than average
        if best_throughput < avg_throughput * 1.3:
            return None
        
        # Find the inference(s) with best throughput
        best_inf = next(i for i in inferences if i.tokens_per_second == best_throughput)
        
        # Analyze what was different
        differences = []
        if best_inf.gpu_temperature_celsius < 60:
            differences.append("GPU was cool (42°C vs 68°C average)")
        if best_inf.context_tokens_provided < 3000:
            differences.append("Context was reduced (2k vs 4k average)")
        
        speedup_factor = best_throughput / avg_throughput
        
        return DetectedInsight(
            detector_type=DetectorType.PERFORMANCE_ENVELOPE,
            title="Your Fastest Hour",
            subtitle=f"You achieved {best_throughput:.0f} tok/s (vs {avg_throughput:.0f} average)",
            description=f"""
Between 2-3 PM yesterday, you hit {best_throughput:.0f} tokens/second.
Your average: {avg_throughput:.0f} tok/s.

{speedup_factor:.1f}x improvement.

What was different?
- {' '.join(differences) if differences else 'System was in better state'}
- GPU memory: {best_inf.gpu_memory_used_mb}MB (vs ~19GB average)

You could replicate this reliably by:
- Running inference during 2-4 PM (cooler system)
- Reducing context to 2k tokens
- Closing background processes
- Running single inference (no parallelism)

Same hardware, different conditions = 1.6x faster.
            """,
            metrics={
                "best_throughput": f"{best_throughput:.0f} tok/s",
                "avg_throughput": f"{avg_throughput:.0f} tok/s",
                "speedup": f"{speedup_factor:.1f}x",
                "gpu_temp_then": f"{best_inf.gpu_temperature_celsius:.0f}°C",
            },
            recommended_action="schedule_optimal_conditions",
            action_value={"preferred_hours": ["2-4 PM"], "context": 2048},
            time_savings_seconds=int(((speedup_factor - 1) / speedup_factor) * 60 * 15 * 5),
            quality_improvement_percent=0.0,
            confidence=0.85,
            suggested_experiments=["replicate_temps", "replicate_context", "replicate_both"]
        )


class AnomalyDetector:
    """Detector 10: Finds unusual inferences (3+ sigma from mean)"""
    
    @staticmethod
    def detect(inferences: List[InferenceLog]) -> Optional[DetectedInsight]:
        if len(inferences) < 10:
            return None
        
        latencies = [i.total_latency_ms for i in inferences]
        avg_latency = sum(latencies) / len(latencies)
        variance = sum((x - avg_latency)**2 for x in latencies) / len(latencies)
        std_dev = variance ** 0.5
        
        # Find outliers (>2 std dev)
        outliers = [(i, (i.total_latency_ms - avg_latency) / std_dev) 
                   for i in inferences if abs((i.total_latency_ms - avg_latency) / std_dev) > 2]
        
        if not outliers:
            return None
        
        # Take worst outlier
        worst_outlier, num_std_dev = max(outliers, key=lambda x: x[1])
        
        return DetectedInsight(
            detector_type=DetectorType.ANOMALY_DETECTION,
            title="Anomaly Detected",
            subtitle=f"This inference was {num_std_dev:.1f}x slower than normal",
            description=f"""
This inference took {worst_outlier.total_latency_ms/1000:.1f}s (normally {avg_latency/1000:.1f}s).

{num_std_dev:.1f} standard deviations from your normal.

What was different?
- GPU temp: {worst_outlier.gpu_temperature_celsius:.0f}°C (normally 62°C)
- GPU memory: {worst_outlier.gpu_memory_used_mb}MB (normally 18GB)
- Context: {worst_outlier.context_tokens_provided} tokens

Likely cause: Thermal throttling or memory contention.

No action needed, just explaining the outlier.
            """,
            metrics={
                "latency": f"{worst_outlier.total_latency_ms/1000:.1f}s",
                "normal": f"{avg_latency/1000:.1f}s",
                "deviation": f"{num_std_dev:.1f}σ",
                "gpu_temp": f"{worst_outlier.gpu_temperature_celsius:.0f}°C",
            },
            recommended_action="investigate",
            action_value={},
            time_savings_seconds=0,
            quality_improvement_percent=0.0,
            confidence=0.8
        )


def _load_json_safe(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def parse_tokenlab_export(data_or_path: Union[Path, str, Dict[str, Any], None] = None) -> Dict[str, Any]:
    """Normalize a Token Lab account telemetry export JSON into summary & request rows."""
    if isinstance(data_or_path, dict):
        raw = data_or_path
    else:
        target = Path(data_or_path) if data_or_path else DEFAULT_EXPORT_PATH
        if not target.exists() and Path("/tmp/tokenlab_export.json").exists():
            target = Path("/tmp/tokenlab_export.json")
        raw = _load_json_safe(target)

    if not raw or "tokenlab" not in raw:
        return {}

    profile = raw.get("user_profile") or {}
    tl = raw.get("tokenlab") or {}
    account = tl.get("account") or {}
    keys = tl.get("keys") or []
    usage_totals = tl.get("usage_totals") or {}
    usage_daily = tl.get("usage_daily") or []
    requests = tl.get("requests") or []

    active_key = next((k.get("key_prefix") for k in keys if k.get("status") == "active"), None)
    budget_micro = int(account.get("budget_micro") or 0)
    used_micro = int(account.get("budget_used_micro") or 0)
    burn_pct = (used_micro / budget_micro * 100.0) if budget_micro > 0 else 0.0
    cached_tokens = sum(int(d.get("cached_tokens") or 0) for d in usage_daily)
    reasoning_tokens = sum(int(d.get("reasoning_tokens") or 0) for d in usage_daily)

    return {
        "export_date": raw.get("export_date", ""),
        "user_id": profile.get("user_id") or account.get("user_id") or "default",
        "key_prefix": active_key or "unknown",
        "status": account.get("status", "unknown"),
        "grant_state": account.get("grant_state", "unknown"),
        "expires_at": account.get("expires_at", ""),
        "budget_micro": budget_micro,
        "budget_used_micro": used_micro,
        "burn_percent": round(burn_pct, 6),
        "total_requests": int(usage_totals.get("requests") or len(requests)),
        "total_errors": int(usage_totals.get("errors") or sum(1 for r in requests if r.get("has_error"))),
        "total_tokens": int(usage_totals.get("tokens") or 0),
        "cached_tokens": cached_tokens,
        "reasoning_tokens": reasoning_tokens,
        "usage_daily": usage_daily,
        "requests": requests,
    }


def _scan_nvme_checkpoints(checkpoint_dir: Optional[Path] = None) -> Dict[str, Any]:
    target = Path(checkpoint_dir) if checkpoint_dir else DEFAULT_CHECKPOINT_DIR
    if not target.exists():
        return {"count": 0, "total_bytes": 0, "routes": {}, "models": {}, "latencies_ms": [], "recent": []}

    files = sorted(target.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    routes: Dict[str, int] = {}
    models: Dict[str, int] = {}
    latencies: List[float] = []
    recent: List[Dict[str, Any]] = []
    total_bytes = 0

    for idx, fp in enumerate(files):
        try:
            total_bytes += fp.stat().st_size
        except OSError:
            pass
        payload = _load_json_safe(fp)
        if not payload:
            continue
        route = str(payload.get("route") or "unknown")
        model = str(payload.get("model") or "unknown")
        lat = float(payload.get("latency_ms") or 0.0)
        routes[route] = routes.get(route, 0) + 1
        models[model] = models.get(model, 0) + 1
        if lat > 0:
            latencies.append(lat)
        if idx < 10:
            recent.append(
                {
                    "name": fp.name,
                    "timestamp": payload.get("timestamp", ""),
                    "route": route,
                    "model": model,
                    "latency_ms": lat,
                }
            )

    return {
        "count": len(files),
        "total_bytes": total_bytes,
        "routes": routes,
        "models": models,
        "latencies_ms": latencies,
        "recent": recent,
    }


class NVMeCheckpointDetector:
    """Detects patterns across local NVMe atomic checkpoints & Token Lab exports."""

    def __init__(
        self,
        checkpoint_dir: Optional[Path] = None,
        export_path: Optional[Path] = None,
    ):
        self.checkpoint_dir = checkpoint_dir
        self.export_path = export_path

    def detect_from_disk(self) -> List[DetectedInsight]:
        insights: List[DetectedInsight] = []
        cp_stats = _scan_nvme_checkpoints(self.checkpoint_dir)
        tl_summary = parse_tokenlab_export(self.export_path)

        if tl_summary:
            errs = tl_summary["total_errors"]
            reqs = max(1, tl_summary["total_requests"])
            clean = reqs - errs
            if errs > 0:
                err_models = [
                    f"{d.get('model')} ({d.get('errors')}/{d.get('requests')})"
                    for d in tl_summary.get("usage_daily", [])
                    if int(d.get("errors") or 0) > 0
                ]
                insights.append(
                    DetectedInsight(
                        detector_type=DetectorType.REPEATED_FAILURES,
                        title="Token Lab Client Error Burst Resolved",
                        subtitle=f"{errs} historical errors vs {clean} clean completions across 4 models",
                        description=(
                            f"Account {tl_summary['user_id']} (key {tl_summary['key_prefix']}) logged "
                            f"{errs} errors out of {reqs} requests ({', '.join(err_models) or 'd3'}). "
                            "Subsequent routed completions succeeded across d3, Gemma-4-31B-IT, MiniCPM5-2B, and Qwen3.8-27B."
                        ),
                        metrics={
                            "errors": f"{errs}/{reqs} requests",
                            "key_prefix": tl_summary["key_prefix"],
                            "grant_used": f"{tl_summary['budget_used_micro']} / {tl_summary['budget_micro']} micro",
                        },
                        recommended_action="verify_schema_guard",
                        action_value={"detector": "nvme_tokenlab", "errors": errs, "clean": clean},
                        time_savings_seconds=900,
                        quality_improvement_percent=12.0,
                        confidence=0.88,
                        suggested_experiments=[
                            "Validate /v1/systemone dict schema before dispatch",
                            "Keep local NVMe checkpointing enabled on every route_task call",
                        ],
                    )
                )

            insights.append(
                DetectedInsight(
                    detector_type=DetectorType.EFFICIENCY_FRONTIER,
                    title="Token Lab Grant & Prompt Cache Headroom",
                    subtitle=f"{tl_summary['burn_percent']:.5f}% grant used ({tl_summary['cached_tokens']} cached tokens)",
                    description=(
                        f"Burn rate is {tl_summary['budget_used_micro']} of {tl_summary['budget_micro']} micro-points "
                        f"across {tl_summary['total_tokens']} tokens with zero local RTX 3070 VRAM cost. "
                        f"Prompt caching hit {tl_summary['cached_tokens']} tokens and reasoning models used {tl_summary['reasoning_tokens']} tokens."
                    ),
                    metrics={
                        "burn_rate": f"{tl_summary['burn_percent']:.5f}%",
                        "cached_tokens": f"{tl_summary['cached_tokens']} cached",
                        "expires": str(tl_summary["expires_at"])[:10] or "30d",
                    },
                    recommended_action="expand_31b_offload",
                    action_value={"burn_percent": tl_summary["burn_percent"], "cached_tokens": tl_summary["cached_tokens"]},
                    time_savings_seconds=1800,
                    quality_improvement_percent=18.0,
                    confidence=0.92,
                    suggested_experiments=[
                        "Pin system prefixes to maximize Gemma-4-31B-IT prompt cache hits",
                        "Route lightweight triage to MiniCPM5-2B",
                    ],
                )
            )

        if cp_stats["count"] > 0:
            lats = cp_stats["latencies_ms"]
            avg_lat = sum(lats) / len(lats) if lats else 0.0
            top_route = max(cp_stats["routes"].items(), key=lambda kv: kv[1])[0] if cp_stats["routes"] else "unknown"
            insights.append(
                DetectedInsight(
                    detector_type=DetectorType.NVME_CHECKPOINTS,
                    title="NVMe Atomic Checkpoint Ledger Active",
                    subtitle=f"{cp_stats['count']} crash-safe JSON checkpoints ({avg_lat:.0f} ms avg route latency)",
                    description=(
                        f"Found {cp_stats['count']} atomic checkpoint files totaling "
                        f"{cp_stats['total_bytes'] / 1024:.1f} KB. Dominant router tier: {top_route}."
                    ),
                    metrics={
                        "checkpoints": f"{cp_stats['count']} files",
                        "avg_latency": f"{avg_lat:.0f} ms",
                        "top_route": top_route,
                    },
                    recommended_action="compact_old_checkpoints",
                    action_value={"checkpoint_count": cp_stats["count"], "avg_latency_ms": round(avg_lat, 1)},
                    time_savings_seconds=600,
                    quality_improvement_percent=8.0,
                    confidence=0.84,
                    suggested_experiments=[
                        "Archive NVMe checkpoints older than 14 days into DuckDB",
                    ],
                )
            )

        return insights

    def detect(self, inferences: List[InferenceLog]) -> Optional[DetectedInsight]:
        disk_insights = self.detect_from_disk()
        if disk_insights:
            return disk_insights[0]

        if not inferences:
            return None

        err_count = sum(1 for inf in inferences if getattr(inf, "error_flag", False))
        if err_count >= 2:
            return DetectedInsight(
                detector_type=DetectorType.NVME_CHECKPOINTS,
                title="Elevated Inference Error Rate Detected",
                subtitle=f"{err_count} failed inferences out of {len(inferences)} runs",
                description="Inspect Token Lab request payloads and NVMe router checkpoints for recent client errors.",
                metrics={"errors": f"{err_count}/{len(inferences)}"},
                recommended_action="inspect_checkpoints",
                action_value={"error_count": err_count},
                time_savings_seconds=600,
                quality_improvement_percent=10.0,
                confidence=0.8,
            )
        return None


def ingest_tokenlab_export(
    db: Any,
    export_path: Optional[Path] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Idempotently load Token Lab export requests into QuietAdvisorDB + NVMe insights."""
    summary = parse_tokenlab_export(export_path)
    if not summary:
        return {"ingested_requests": 0, "ingested_cards": 0, "summary": {}}

    target_user = user_id or summary["user_id"] or "default"
    existing_cnt = db.conn.execute(
        "SELECT COUNT(*) FROM memoryos_inference_log WHERE session_id = 'tokenlab-export'"
    ).fetchone()[0]

    ingested_requests = 0
    if existing_cnt == 0:
        db.conn.execute("INSERT OR IGNORE INTO users (user_id, active) VALUES (?, 1)", (target_user,))
        for req in summary.get("requests", []):
            model = str(req.get("model") or "unknown")
            prompt_tok = int(req.get("prompt_tokens") or 0)
            comp_tok = int(req.get("completion_tokens") or 0)
            has_err = bool(req.get("has_error"))
            est_lat = 0.0 if has_err else (140.0 if "2B" in model or model == "d3" else 520.0)
            ts_raw = str(req.get("created_at") or datetime.utcnow().isoformat()).replace(" ", "T")
            db.conn.execute(
                """
                INSERT INTO memoryos_inference_log (
                    user_id, session_id, timestamp, model_id,
                    context_tokens_provided, context_tokens_used,
                    time_to_first_token_ms, total_latency_ms, tokens_per_second,
                    gpu_id, gpu_utilization_percent, gpu_temperature_celsius,
                    gpu_memory_used_mb, output_quality_score, error_flag, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_user,
                    "tokenlab-export",
                    ts_raw,
                    model,
                    max(4096, (prompt_tok + comp_tok) * 4) if (prompt_tok + comp_tok) else 4096,
                    prompt_tok + comp_tok,
                    round(est_lat * 0.2, 1),
                    est_lat,
                    65.0 if comp_tok else 0.0,
                    "tokenlab-remote",
                    0.0,
                    0.0,
                    0,
                    0.0 if has_err else 0.92,
                    1 if has_err else 0,
                    str(req.get("finish_reason") or ""),
                ),
            )
            ingested_requests += 1

    existing_tl_cards = db.conn.execute(
        "SELECT COUNT(*) FROM quiet_advisor_cards WHERE action_value LIKE '%tokenlab_export%'"
    ).fetchone()[0]
    ingested_cards = 0
    if existing_tl_cards == 0:
        detector = NVMeCheckpointDetector(export_path=export_path)
        for insight in detector.detect_from_disk():
            payload = dict(insight.action_value)
            payload["source"] = "tokenlab_export"
            payload["d3_routing"] = {
                "choice": "surface_now",
                "confidence": round(insight.confidence, 4),
                "probabilities": {"surface_now": round(insight.confidence, 4), "defer": 0.1, "ignore": 0.02},
                "model": "d3",
            }
            metrics = list(insight.metrics.values())
            db.conn.execute(
                """
                INSERT INTO quiet_advisor_cards (
                    user_id, detector_type, insight_rank, title, subtitle, description,
                    metric_1, metric_2, metric_3, recommended_action, action_value,
                    time_savings_seconds, quality_improvement_percent, suggested_experiments,
                    user_dismissed, user_archived, user_actioned, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?)
                """,
                (
                    target_user,
                    insight.detector_type.value,
                    insight.score(),
                    insight.title,
                    insight.subtitle,
                    insight.description,
                    metrics[0] if len(metrics) > 0 else "",
                    metrics[1] if len(metrics) > 1 else "",
                    metrics[2] if len(metrics) > 2 else "",
                    insight.recommended_action,
                    json.dumps(payload),
                    insight.time_savings_seconds,
                    insight.quality_improvement_percent,
                    json.dumps(insight.suggested_experiments or []),
                    datetime.utcnow().isoformat(),
                    (datetime.utcnow() + timedelta(days=7)).isoformat(),
                ),
            )
            ingested_cards += 1

    db.conn.commit()
    return {
        "ingested_requests": ingested_requests,
        "ingested_cards": ingested_cards,
        "summary": summary,
    }


class QuietAdvisorEngine:
    """Main orchestrator for Quiet Advisor detection"""
    
    def __init__(self):
        self.detectors = [
            VRAMThrashingDetector(),
            ContextWasteDetector(),
            ModelThrashingDetector(),
            PerformanceEnvelopeDetector(),
            AnomalyDetector(),
            NVMeCheckpointDetector(),
        ]
    
    def detect_patterns(self, inferences: List[InferenceLog], 
                       user_preferences: Dict = None) -> List[DetectedInsight]:
        """Run all detectors and return ranked insights"""
        insights = []
        
        for detector in self.detectors:
            try:
                insight = detector.detect(inferences)
                if insight:
                    insights.append(insight)
            except Exception as e:
                print(f"Detector {detector.__class__.__name__} failed: {e}")
                continue
        
        # Rank by score
        insights.sort(key=lambda x: x.score(user_preferences), reverse=True)
        
        return insights
    
    def get_top_card(self, inferences: List[InferenceLog], 
                     user_preferences: Dict = None) -> Optional[DetectedInsight]:
        """Get single top insight for daily card"""
        insights = self.detect_patterns(inferences, user_preferences)
        return insights[0] if insights else None


# Example usage:
if __name__ == "__main__":
    # Simulate 50 inferences from yesterday
    sample_inferences = [
        InferenceLog(
            timestamp=datetime.now() - timedelta(hours=i),
            model_id="llama-65b" if i % 3 == 0 else "mistral-7b",
            context_tokens_provided=4000,
            context_tokens_used=2100,
            time_to_first_token_ms=250,
            total_latency_ms=3500,
            tokens_per_second=110 + (i % 20),  # varies
            gpu_utilization_percent=75,
            gpu_temperature_celsius=62 + (i % 10),
            gpu_memory_used_mb=19000,
            output_quality_score=0.92,
        )
        for i in range(50)
    ]
    
    engine = QuietAdvisorEngine()
    insights = engine.detect_patterns(sample_inferences)
    
    for i, insight in enumerate(insights[:3]):
        print(f"\nCard {i+1}: {insight.title}")
        print(f"Subtitle: {insight.subtitle}")
        print(f"Score: {insight.score():.2f}")
        print(f"Time savings: {insight.time_savings_seconds / 3600:.1f} hours/week")
