"""
Speculative Offload Runtime and Safety Verification for MemoryOS.

Pure Python, zero-dependency inference runtime for SpeculativeOffloadNet.
Loads JSON weights, verifies feature schema & activations, and makes calibrated
routing decisions (offload_now / skip / digest) in <100 microseconds.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS_PATH = REPO_ROOT / "memory" / "models" / "speculative_offload_v1.json"

EXPECTED_FEATURE_NAMES = (
    "mse_delta_norm",
    "context_utilization",
    "secs_since_offload",
    "model_switch_rate",
)


def _ensure_finite_float(val: Any, label: str = "value") -> float:
    if isinstance(val, bool):
        raise ValueError(f"{label} must be a finite numeric float, got bool: {val!r}")
    try:
        out = float(val)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric, got {val!r}") from exc
    if not math.isfinite(out):
        raise ValueError(f"{label} must be finite, got {out!r}")
    return out


def _sigmoid(x: float) -> float:
    x_val = _ensure_finite_float(x, "logit")
    clamped = max(-20.0, min(20.0, x_val))
    return 1.0 / (1.0 + math.exp(-clamped))


def _relu(x: float) -> float:
    return x if x > 0.0 else 0.0


class SpeculativeOffloadModel:
    """Zero-dependency inference runtime for the 2-layer speculative offload MLP."""

    def __init__(
        self,
        w1: Sequence[Sequence[float]],
        b1: Sequence[float],
        w2: Sequence[float],
        b2: float,
        feature_names: Sequence[str] = EXPECTED_FEATURE_NAMES,
        tau_hi: float = 0.65,
        tau_lo: float = 0.35,
        model_name: str = "SpeculativeOffloadNet-v1",
        version: str = "1.0.0",
    ) -> None:
        self.model_name = model_name
        self.version = version
        self.feature_names = list(feature_names)
        self.w1 = [[_ensure_finite_float(v, f"w1[{r}][{c}]") for c, v in enumerate(row)] for r, row in enumerate(w1)]
        self.b1 = [_ensure_finite_float(v, f"b1[{i}]") for i, v in enumerate(b1)]
        self.w2 = [_ensure_finite_float(v, f"w2[{i}]") for i, v in enumerate(w2)]
        self.b2 = _ensure_finite_float(b2, "b2")
        self.tau_hi = _ensure_finite_float(tau_hi, "tau_hi")
        self.tau_lo = _ensure_finite_float(tau_lo, "tau_lo")

        self.in_dim = len(self.feature_names)
        self.hidden_dim = len(self.w1)

        self._validate_dimensions()

    def _validate_dimensions(self) -> None:
        if self.in_dim != 4:
            raise ValueError(f"Expected 4 input features, got {self.in_dim}")
        if self.hidden_dim != 8:
            raise ValueError(f"Expected 8 hidden units, got {self.hidden_dim}")
        if len(self.b1) != self.hidden_dim:
            raise ValueError(f"b1 length ({len(self.b1)}) does not match hidden_dim ({self.hidden_dim})")
        for idx, row in enumerate(self.w1):
            if len(row) != self.in_dim:
                raise ValueError(f"w1 row {idx} length ({len(row)}) != in_dim ({self.in_dim})")
        if len(self.w2) != self.hidden_dim:
            raise ValueError(f"w2 length ({len(self.w2)}) does not match hidden_dim ({self.hidden_dim})")
        if not (0.0 <= self.tau_lo <= self.tau_hi <= 1.0):
            raise ValueError(
                f"Invalid thresholds: require 0.0 <= tau_lo <= tau_hi <= 1.0, got tau_lo={self.tau_lo}, tau_hi={self.tau_hi}"
            )

    @classmethod
    def load(cls, weights_path: Union[str, Path, None] = None) -> "SpeculativeOffloadModel":
        if weights_path is not None:
            path = Path(weights_path)
        else:
            path = DEFAULT_WEIGHTS_PATH
            if not path.is_file():
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass:
                    bundled = Path(meipass) / "memory" / "models" / "speculative_offload_v1.json"
                    if bundled.is_file():
                        path = bundled
        if not path.is_file():
            raise FileNotFoundError(f"Speculative offload model weights not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid weights JSON root in {path}: expected object")

        # Validate schema contract
        raw_features = data.get("feature_names")
        if not raw_features or list(raw_features) != list(EXPECTED_FEATURE_NAMES):
            raise ValueError(
                f"Feature ordering mismatch in {path}. "
                f"Expected: {list(EXPECTED_FEATURE_NAMES)}, got: {raw_features}"
            )

        hidden_act = data.get("hidden_activation")
        if hidden_act != "relu":
            raise ValueError(f"Unsupported hidden_activation: {hidden_act!r} (expected 'relu')")

        output_act = data.get("output_activation")
        if output_act != "sigmoid":
            raise ValueError(f"Unsupported output_activation: {output_act!r} (expected 'sigmoid')")

        w1 = data.get("w1")
        b1 = data.get("b1")
        w2 = data.get("w2")
        b2 = data.get("b2")
        if w1 is None or b1 is None or w2 is None or b2 is None:
            raise ValueError(f"Incomplete weight tensors in {path}")

        thresholds = data.get("thresholds") or {}
        tau_hi = _ensure_finite_float(thresholds.get("tau_hi", 0.65), "tau_hi")
        tau_lo = _ensure_finite_float(thresholds.get("tau_lo", 0.35), "tau_lo")

        return cls(
            w1=w1,
            b1=b1,
            w2=w2,
            b2=b2,
            feature_names=raw_features,
            tau_hi=tau_hi,
            tau_lo=tau_lo,
            model_name=data.get("model_name", "SpeculativeOffloadNet-v1"),
            version=data.get("version", "1.0.0"),
        )

    def _prepare_vector(self, features: Union[Dict[str, float], Sequence[float]]) -> List[float]:
        if isinstance(features, dict):
            vec: List[float] = []
            for name in self.feature_names:
                if name not in features:
                    raise KeyError(f"Missing required feature: '{name}' in {list(features.keys())}")
                vec.append(_ensure_finite_float(features[name], f"feature '{name}'"))
            return vec

        if isinstance(features, (str, bytes)):
            raise ValueError("Features must be a mapping or numeric sequence, not str/bytes")

        if len(features) != self.in_dim:
            raise ValueError(f"Expected {self.in_dim} features, got {len(features)}")
        return [_ensure_finite_float(v, f"feature[{idx}]") for idx, v in enumerate(features)]

    def predict_proba(self, features: Union[Dict[str, float], Sequence[float]]) -> float:
        """Compute P(offload_needed) using 2-layer forward pass."""
        x = self._prepare_vector(features)

        # Layer 1: ReLU(w1 @ x + b1)
        h = [
            _relu(sum(self.w1[j][i] * x[i] for i in range(self.in_dim)) + self.b1[j])
            for j in range(self.hidden_dim)
        ]

        # Layer 2: Sigmoid(w2 @ h + b2)
        logit = sum(self.w2[j] * h[j] for j in range(self.hidden_dim)) + self.b2
        return _sigmoid(logit)

    def decide(
        self,
        features: Union[Dict[str, float], Sequence[float]],
        tau_hi: Union[float, None] = None,
        tau_lo: Union[float, None] = None,
    ) -> str:
        """Classify offload action: 'offload_now', 'skip', or 'digest'."""
        th_hi = self.tau_hi if tau_hi is None else _ensure_finite_float(tau_hi, "tau_hi")
        th_lo = self.tau_lo if tau_lo is None else _ensure_finite_float(tau_lo, "tau_lo")
        if not (0.0 <= th_lo <= th_hi <= 1.0):
            raise ValueError(f"Invalid thresholds: require 0.0 <= tau_lo <= tau_hi <= 1.0, got {th_lo}, {th_hi}")

        p = self.predict_proba(features)
        if p >= th_hi:
            return "offload_now"
        if p <= th_lo:
            return "skip"
        return "digest"
