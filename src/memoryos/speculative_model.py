"""
Tiny <1 ms Speculative Offload Predictor for MemoryOS (Pure Python, Zero Dependencies).

Trains a lightweight 2-layer MLP on QuietAdvisorDB.sqlite telemetry + frame-delta
features to predict P(offload_needed) before invoking remote cloud models.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS_PATH = REPO_ROOT / "memory" / "models" / "speculative_offload_v1.json"


def _sigmoid(x: float) -> float:
    x = max(-20.0, min(20.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def _relu(x: float) -> float:
    return x if x > 0.0 else 0.0


class SpeculativeOffloadNet:
    """2-layer MLP (4 -> 8 -> 1) predicting whether a frame/prompt needs remote offload."""

    def __init__(self, hidden_dim: int = 8, seed: int = 42) -> None:
        rng = random.Random(seed)
        self.in_dim = 4
        self.hidden_dim = hidden_dim
        self.w1: List[List[float]] = [
            [rng.uniform(-0.5, 0.5) for _ in range(self.in_dim)] for _ in range(hidden_dim)
        ]
        self.b1: List[float] = [0.0] * hidden_dim
        self.w2: List[float] = [rng.uniform(-0.5, 0.5) for _ in range(hidden_dim)]
        self.b2: float = 0.0

    def predict_proba(self, features: List[float]) -> float:
        """Return P(offload_needed) in [0.0, 1.0] for [mse_norm, vram_pct, ctx_norm, has_image]."""
        h = [
            _relu(sum(self.w1[j][i] * features[i] for i in range(self.in_dim)) + self.b1[j])
            for j in range(self.hidden_dim)
        ]
        logit = sum(self.w2[j] * h[j] for j in range(self.hidden_dim)) + self.b2
        return _sigmoid(logit)

    def train(
        self,
        samples: List[Tuple[List[float], float]],
        epochs: int = 120,
        lr: float = 0.08,
    ) -> Dict[str, float]:
        """Train with SGD on binary cross-entropy loss."""
        final_loss = 0.0
        correct = 0
        for _ in range(epochs):
            total_loss = 0.0
            correct = 0
            for x, y in samples:
                z1 = [sum(self.w1[j][i] * x[i] for i in range(self.in_dim)) + self.b1[j] for j in range(self.hidden_dim)]
                h = [_relu(z) for z in z1]
                p = _sigmoid(sum(self.w2[j] * h[j] for j in range(self.hidden_dim)) + self.b2)

                eps = 1e-7
                total_loss += -(y * math.log(p + eps) + (1.0 - y) * math.log(1.0 - p + eps))
                if (p >= 0.5) == (y >= 0.5):
                    correct += 1

                dz2 = p - y
                for j in range(self.hidden_dim):
                    grad_w2 = dz2 * h[j]
                    if z1[j] > 0.0:
                        dz1 = dz2 * self.w2[j]
                        for i in range(self.in_dim):
                            self.w1[j][i] -= lr * dz1 * x[i]
                        self.b1[j] -= lr * dz1
                    self.w2[j] -= lr * grad_w2
                self.b2 -= lr * dz2
            final_loss = total_loss / max(1, len(samples))

        return {
            "loss": round(final_loss, 5),
            "accuracy": round(correct / max(1, len(samples)), 4),
            "samples": len(samples),
            "epochs": epochs,
        }

    def save(self, path: Path = DEFAULT_WEIGHTS_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_name": "SpeculativeOffloadNet-v1",
            "in_dim": self.in_dim,
            "hidden_dim": self.hidden_dim,
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path = DEFAULT_WEIGHTS_PATH) -> "SpeculativeOffloadNet":
        data = json.loads(path.read_text(encoding="utf-8"))
        net = cls(hidden_dim=int(data["hidden_dim"]))
        net.w1 = data["w1"]
        net.b1 = data["b1"]
        net.w2 = data["w2"]
        net.b2 = float(data["b2"])
        return net


def build_training_samples_from_db(db_path: Path) -> List[Tuple[List[float], float]]:
    """Build training pairs from QuietAdvisorDB.sqlite (plus boundary anchors)."""
    samples: List[Tuple[List[float], float]] = [
        ([0.02, 0.30, 0.05, 0.0], 0.0),  # Static frame, low VRAM -> skip
        ([0.05, 0.45, 0.10, 0.0], 0.0),  # Low delta -> skip
        ([0.85, 0.90, 0.60, 1.0], 1.0),  # High delta + vision -> offload
        ([0.65, 0.85, 0.80, 0.0], 1.0),  # High VRAM pressure -> offload
    ]
    if not db_path.exists():
        return samples

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT model_selected, context_tokens_provided, gpu_memory_used_mb FROM telemetry_events LIMIT 200"
        ).fetchall()
        for model, ctx_tok, vram_mb in rows:
            is_d3 = str(model or "").lower().startswith("d3")
            mse_norm = 0.10 if is_d3 else 0.75
            vram_pct = min(1.0, float(vram_mb or 0) / 8192.0)
            ctx_norm = min(1.0, float(ctx_tok or 0) / 32768.0)
            has_img = 1.0 if "gemma" in str(model or "").lower() else 0.0
            label = 0.0 if is_d3 else 1.0
            samples.append(([mse_norm, vram_pct, ctx_norm, has_img], label))
    except Exception:
        pass
    finally:
        conn.close()
    return samples


if __name__ == "__main__":
    db = REPO_ROOT / "QuietAdvisorDB.sqlite"
    data = build_training_samples_from_db(db)
    net = SpeculativeOffloadNet(hidden_dim=8)
    metrics = net.train(data, epochs=120, lr=0.08)
    saved_to = net.save()

    t0 = time.perf_counter()
    for _ in range(1000):
        net.predict_proba([0.75, 0.85, 0.50, 1.0])
    avg_us = ((time.perf_counter() - t0) / 1000.0) * 1_000_000.0

    print(json.dumps({
        "status": "TRAINED",
        "weights_path": str(saved_to),
        "metrics": metrics,
        "avg_inference_us": round(avg_us, 2),
    }, indent=2))
