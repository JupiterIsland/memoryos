"""Export QuietAdvisorDB.sqlite telemetry & cards to ChatML JSONL for QLoRA fine-tuning."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "QuietAdvisorDB.sqlite"
OUT_PATH = REPO_ROOT / "memory" / "datasets" / "jupiter_advisor_train.jsonl"


def export_dataset(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            cards = conn.execute(
                "SELECT detector_type, title, description, recommendation FROM advisor_cards"
            ).fetchall()
            for c in cards:
                records.append({
                    "messages": [
                        {"role": "system", "content": "You are Jupiter-Advisor, a hardware-aware AI optimization assistant."},
                        {"role": "user", "content": f"Detector: {c['detector_type']}\nIssue: {c['title']}\nDetails: {c['description']}"},
                        {"role": "assistant", "content": str(c["recommendation"] or "Apply Quiet Advisor optimization.")},
                    ]
                })
        except Exception:
            pass
        finally:
            conn.close()

    if not records:
        records.append({
            "messages": [
                {"role": "system", "content": "You are Jupiter-Advisor, a hardware-aware AI optimization assistant."},
                {"role": "user", "content": "VRAM usage exceeded 85% while gaming."},
                {"role": "assistant", "content": "Offload heavy 31B inference to remote cloud and enable MEMORYOS_QUANT_MODE=8bit."},
            ]
        })

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return len(records)


if __name__ == "__main__":
    count = export_dataset()
    print(f"Exported {count} training examples to {OUT_PATH}")
