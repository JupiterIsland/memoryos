"""Export QuietAdvisorDB.sqlite telemetry & cards to ChatML JSONL for QLoRA fine-tuning."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "QuietAdvisorDB.sqlite"
OUT_PATH = REPO_ROOT / "memory" / "datasets" / "jupiter_advisor_train.jsonl"


SYSTEM_PROMPT = "You are Jupiter-Advisor, a hardware-aware AI optimization assistant."


def _make_example(user_prompt: str, assistant_reply: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_reply},
        ]
    }


def _recommend_for_inference(row: sqlite3.Row) -> str:
    provided = int(row["context_tokens_provided"] or 0)
    used = int(row["context_tokens_used"] or 0)
    vram_mb = int(row["gpu_memory_used_mb"] or 0)
    error_flag = bool(row["error_flag"])
    model_id = str(row["model_id"] or "unknown")
    gpu_id = str(row["gpu_id"] or "unknown")

    advice = []
    if error_flag:
        advice.append(
            f"Inference error on {model_id} ({gpu_id}). Switch to /v1/messages failover or enable automatic Token Lab <-> MI300X fallback."
        )
    if provided > 0 and used / provided < 0.25:
        advice.append(
            f"Context utilization is low ({used}/{provided} tokens, {100.0 * used / provided:.1f}%). Trim system/history padding to cut latency and grant usage."
        )
    if vram_mb > 6500:
        advice.append(
            f"Local VRAM high ({vram_mb} MB on {gpu_id}). Offload 27B/31B models to tokenlab-remote or enable MEMORYOS_QUANT_MODE=4bit."
        )
    if not advice:
        advice.append(
            f"Healthy route on {gpu_id} with {model_id} ({used}/{provided} tokens, {row['total_latency_ms']:.1f} ms). Keep d3 auto-routing enabled."
        )
    return " ".join(advice)


def export_dataset(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            cards = conn.execute(
                "SELECT detector_type, title, subtitle, description, recommended_action, action_value "
                "FROM quiet_advisor_cards"
            ).fetchall()
            for c in cards:
                action = str(c["recommended_action"] or "Apply Quiet Advisor optimization.")
                if c["action_value"]:
                    action = f"{action} (target: {c['action_value']})"
                records.append(
                    _make_example(
                        f"Detector: {c['detector_type']}\nIssue: {c['title']}\nSummary: {c['subtitle'] or ''}\nDetails: {c['description']}",
                        action,
                    )
                )

            inferences = conn.execute(
                "SELECT model_id, context_tokens_provided, context_tokens_used, total_latency_ms, "
                "gpu_id, gpu_memory_used_mb, error_flag FROM memoryos_inference_log"
            ).fetchall()
            for inf in inferences:
                prompt = (
                    f"Telemetry sample -> model={inf['model_id']}, gpu={inf['gpu_id']}, "
                    f"context={inf['context_tokens_used']}/{inf['context_tokens_provided']}, "
                    f"latency_ms={inf['total_latency_ms']}, vram_mb={inf['gpu_memory_used_mb']}, "
                    f"error={bool(inf['error_flag'])}. What should Quiet Advisor recommend?"
                )
                records.append(_make_example(prompt, _recommend_for_inference(inf)))
        finally:
            conn.close()

    if not records:
        records.append(
            _make_example(
                "VRAM usage exceeded 85% while gaming.",
                "Offload heavy 31B inference to remote cloud and enable MEMORYOS_QUANT_MODE=8bit.",
            )
        )

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return len(records)


if __name__ == "__main__":
    count = export_dataset()
    print(f"Exported {count} training examples to {OUT_PATH}")
