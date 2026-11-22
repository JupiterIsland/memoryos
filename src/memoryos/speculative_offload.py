"""
Speculative Offload Runtime and Safety Verification for MemoryOS.

Pure Python, zero-dependency inference runtime for SpeculativeOffloadNet.
Loads JSON weights, verifies feature schema & activations, and makes calibrated
routing decisions (offload_now / skip / digest) in <100 microseconds.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS_PATH = REPO_ROOT / "memory" / "models" / "speculative_offload_v1.json"
MAX_FISHER_VALUE = 25.0


def _checkpoint_digest(payload: Dict[str, Any]) -> str:
    canonical_keys = {k: v for k, v in payload.items() if k != "checksum_sha256"}
    blob = json.dumps(canonical_keys, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()

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

        expected_digest = data.get("checksum_sha256")
        if expected_digest is not None:
            actual_digest = _checkpoint_digest(data)
            if str(expected_digest) != actual_digest:
                raise ValueError(
                    f"Checkpoint integrity mismatch in {path}: expected sha256={expected_digest}, got {actual_digest}"
                )

        model = cls(
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
        ewc = data.get("ewc_state")
        if isinstance(ewc, dict):
            model.load_ewc_state(ewc)
        return model

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

    def is_ood(self, features: Union[Dict[str, float], Sequence[float]]) -> bool:
        """Detect out-of-distribution normalized features outside [-0.05, 1.25]."""
        x = self._prepare_vector(features)
        return any(val < -0.05 or val > 1.25 for val in x)

    def decide_with_confidence(
        self,
        features: Union[Dict[str, float], Sequence[float]],
        tau_hi: Union[float, None] = None,
        tau_lo: Union[float, None] = None,
    ) -> Dict[str, Any]:
        """Safe policy envelope: abstains to 'digest' on out-of-distribution inputs and reports confidence."""
        ood = self.is_ood(features)
        p = self.predict_proba(features)
        if ood:
            return {
                "action": "digest",
                "p_offload": round(p, 4),
                "confidence": 0.0,
                "ood_detected": True,
                "abstained": True,
            }
        action = self.decide(features, tau_hi=tau_hi, tau_lo=tau_lo)
        confidence = round(abs(p - 0.5) * 2.0, 4)
        return {
            "action": action,
            "p_offload": round(p, 4),
            "confidence": confidence,
            "ood_detected": False,
            "abstained": False,
        }

    def _forward_cache(self, x: Sequence[float]) -> tuple[List[float], List[float], float]:
        """Return hidden pre-activations, ReLU activations, and output probability."""
        z1 = [
            sum(self.w1[j][i] * x[i] for i in range(self.in_dim)) + self.b1[j]
            for j in range(self.hidden_dim)
        ]
        h = [_relu(v) for v in z1]
        logit = sum(self.w2[j] * h[j] for j in range(self.hidden_dim)) + self.b2
        return z1, h, _sigmoid(logit)

    def load_ewc_state(self, state: Dict[str, Any]) -> None:
        """Restore persisted Fisher importance matrix and anchor parameters."""
        try:
            fw1 = state["fisher_w1"]
            fb1 = state["fisher_b1"]
            fw2 = state["fisher_w2"]
            fb2 = state["fisher_b2"]
            aw1 = state["anchor_w1"]
            ab1 = state["anchor_b1"]
            aw2 = state["anchor_w2"]
            ab2 = state["anchor_b2"]
            if (
                len(fw1) == self.hidden_dim
                and len(aw1) == self.hidden_dim
                and len(fb1) == self.hidden_dim
                and len(fw2) == self.hidden_dim
            ):
                self._ewc_fisher = {
                    "w1": [[_ensure_finite_float(v) for v in row] for row in fw1],
                    "b1": [_ensure_finite_float(v) for v in fb1],
                    "w2": [_ensure_finite_float(v) for v in fw2],
                    "b2": _ensure_finite_float(fb2),
                }
                self._ewc_anchor = {
                    "w1": [[_ensure_finite_float(v) for v in row] for row in aw1],
                    "b1": [_ensure_finite_float(v) for v in ab1],
                    "w2": [_ensure_finite_float(v) for v in aw2],
                    "b2": _ensure_finite_float(ab2),
                }
        except (KeyError, TypeError, ValueError):
            pass

    def export_ewc_state(self) -> Union[Dict[str, Any], None]:
        fisher = getattr(self, "_ewc_fisher", None)
        anchor = getattr(self, "_ewc_anchor", None)
        if not fisher or not anchor:
            return None
        return {
            "fisher_w1": fisher["w1"],
            "fisher_b1": fisher["b1"],
            "fisher_w2": fisher["w2"],
            "fisher_b2": fisher["b2"],
            "anchor_w1": anchor["w1"],
            "anchor_b1": anchor["b1"],
            "anchor_w2": anchor["w2"],
            "anchor_b2": anchor["b2"],
        }

    def save(self, weights_path: Union[str, Path]) -> Path:
        """Persist current MLP weights and any EWC Fisher consolidation anchor to JSON."""
        path = Path(weights_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = {
            "model_name": self.model_name,
            "version": self.version,
            "feature_names": list(self.feature_names),
            "hidden_activation": "relu",
            "output_activation": "sigmoid",
            "thresholds": {"tau_hi": self.tau_hi, "tau_lo": self.tau_lo},
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }
        ewc_state = self.export_ewc_state()
        if ewc_state is not None:
            payload["ewc_state"] = ewc_state
        payload["schema_version"] = 2
        payload["checksum_sha256"] = _checkpoint_digest(payload)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(path)
        return path

    def evaluate(
        self,
        samples: Sequence[tuple[Union[Dict[str, float], Sequence[float]], float]],
    ) -> Dict[str, float]:
        """Evaluate binary accuracy and mean cross-entropy / Brier loss on labeled episodes."""
        if not samples:
            return {"count": 0.0, "accuracy": 0.0, "brier_loss": 0.0}
        correct = 0
        sq_err = 0.0
        for feats, raw_y in samples:
            y = 1.0 if float(raw_y) >= 0.5 else 0.0
            p = self.predict_proba(feats)
            if (p >= 0.5) == (y >= 0.5):
                correct += 1
            sq_err += (p - y) ** 2
        n = float(len(samples))
        return {
            "count": n,
            "accuracy": round(correct / n, 4),
            "brier_loss": round(sq_err / n, 6),
        }

    def compute_fisher_diagonal(
        self,
        samples: Sequence[tuple[Union[Dict[str, float], Sequence[float]], float]],
    ) -> Dict[str, Any]:
        """Estimate diagonal Fisher information around current parameters to protect learned tasks."""
        fw1 = [[0.0 for _ in range(self.in_dim)] for _ in range(self.hidden_dim)]
        fb1 = [0.0 for _ in range(self.hidden_dim)]
        fw2 = [0.0 for _ in range(self.hidden_dim)]
        fb2 = 0.0
        n = max(1, len(samples))
        for feats, raw_y in samples:
            x = self._prepare_vector(feats)
            y = 1.0 if float(raw_y) >= 0.5 else 0.0
            z1, h, p = self._forward_cache(x)
            # Bernoulli log-likelihood gradient wrt logit: (p - y)
            d_logit = p - y
            fb2 += d_logit * d_logit
            for j in range(self.hidden_dim):
                gw2 = d_logit * h[j]
                fw2[j] += gw2 * gw2
                if z1[j] > 0.0:
                    d_z1 = d_logit * self.w2[j]
                    fb1[j] += d_z1 * d_z1
                    for i in range(self.in_dim):
                        gw1 = d_z1 * x[i]
                        fw1[j][i] += gw1 * gw1
        inv_n = 1.0 / n
        return {
            "w1": [[v * inv_n for v in row] for row in fw1],
            "b1": [v * inv_n for v in fb1],
            "w2": [v * inv_n for v in fw2],
            "b2": fb2 * inv_n,
        }

    def consolidate_memory(
        self,
        samples: Sequence[tuple[Union[Dict[str, float], Sequence[float]], float]],
        max_fisher: float = MAX_FISHER_VALUE,
    ) -> None:
        """Snapshot current weights + clipped Fisher importance across tasks (prevents plastic lock)."""
        cap = max(0.1, _ensure_finite_float(max_fisher, "max_fisher"))
        new_fisher = self.compute_fisher_diagonal(samples)
        prev_fisher = getattr(self, "_ewc_fisher", None)
        if prev_fisher is not None:
            new_fisher = {
                "w1": [
                    [min(cap, prev_fisher["w1"][j][i] + new_fisher["w1"][j][i]) for i in range(self.in_dim)]
                    for j in range(self.hidden_dim)
                ],
                "b1": [min(cap, prev_fisher["b1"][j] + new_fisher["b1"][j]) for j in range(self.hidden_dim)],
                "w2": [min(cap, prev_fisher["w2"][j] + new_fisher["w2"][j]) for j in range(self.hidden_dim)],
                "b2": min(cap, prev_fisher["b2"] + new_fisher["b2"]),
            }
        else:
            new_fisher = {
                "w1": [[min(cap, v) for v in row] for row in new_fisher["w1"]],
                "b1": [min(cap, v) for v in new_fisher["b1"]],
                "w2": [min(cap, v) for v in new_fisher["w2"]],
                "b2": min(cap, new_fisher["b2"]),
            }
        self._ewc_fisher = new_fisher
        self._ewc_anchor = {
            "w1": [row[:] for row in self.w1],
            "b1": self.b1[:],
            "w2": self.w2[:],
            "b2": self.b2,
        }

    def fit_continual(
        self,
        new_samples: Sequence[tuple[Union[Dict[str, float], Sequence[float]], float]],
        replay_samples: Sequence[tuple[Union[Dict[str, float], Sequence[float]], float]] = (),
        lr: float = 0.08,
        epochs: int = 80,
        ewc_lambda: float = 15.0,
        consolidate_after: bool = True,
    ) -> Dict[str, Any]:
        """Train on new episodes with Elastic Weight Consolidation + Experience Replay."""
        combined = list(new_samples) + list(replay_samples)
        if not combined:
            return {"steps": 0, "brier_loss": 0.0, "accuracy": 0.0}

        prepared = [(self._prepare_vector(f), 1.0 if float(y) >= 0.5 else 0.0) for f, y in combined]
        fisher = getattr(self, "_ewc_fisher", None)
        anchor = getattr(self, "_ewc_anchor", None)
        use_ewc = bool(fisher and anchor and ewc_lambda > 0.0)
        n = float(len(prepared))

        for _ in range(max(1, int(epochs))):
            gw1 = [[0.0 for _ in range(self.in_dim)] for _ in range(self.hidden_dim)]
            gb1 = [0.0 for _ in range(self.hidden_dim)]
            gw2 = [0.0 for _ in range(self.hidden_dim)]
            gb2 = 0.0

            for x, y in prepared:
                z1, h, p = self._forward_cache(x)
                # Binary cross-entropy gradient wrt logit is cleanly (p - y)
                d_logit = p - y
                gb2 += d_logit
                for j in range(self.hidden_dim):
                    gw2[j] += d_logit * h[j]
                    if z1[j] > 0.0:
                        d_z1 = d_logit * self.w2[j]
                        gb1[j] += d_z1
                        for i in range(self.in_dim):
                            gw1[j][i] += d_z1 * x[i]

            inv_n = 1.0 / n
            # Apply batch gradient + EWC quadratic anchoring penalty
            if use_ewc:
                gb2 = gb2 * inv_n + ewc_lambda * fisher["b2"] * (self.b2 - anchor["b2"])
            else:
                gb2 = gb2 * inv_n
            self.b2 = max(-10.0, min(10.0, self.b2 - lr * max(-5.0, min(5.0, gb2))))

            for j in range(self.hidden_dim):
                grad_w2 = gw2[j] * inv_n
                grad_b1 = gb1[j] * inv_n
                if use_ewc:
                    grad_w2 += ewc_lambda * fisher["w2"][j] * (self.w2[j] - anchor["w2"][j])
                    grad_b1 += ewc_lambda * fisher["b1"][j] * (self.b1[j] - anchor["b1"][j])
                self.w2[j] = max(-10.0, min(10.0, self.w2[j] - lr * max(-5.0, min(5.0, grad_w2))))
                self.b1[j] = max(-10.0, min(10.0, self.b1[j] - lr * max(-5.0, min(5.0, grad_b1))))
                for i in range(self.in_dim):
                    grad_w1 = gw1[j][i] * inv_n
                    if use_ewc:
                        grad_w1 += ewc_lambda * fisher["w1"][j][i] * (self.w1[j][i] - anchor["w1"][j][i])
                    self.w1[j][i] = max(-10.0, min(10.0, self.w1[j][i] - lr * max(-5.0, min(5.0, grad_w1))))

        if consolidate_after:
            self.consolidate_memory(combined)
        metrics = self.evaluate(combined)
        metrics["ewc_protected"] = 1.0 if (use_ewc or self.export_ewc_state() is not None) else 0.0
        metrics["episodes"] = len(combined)
        return metrics
