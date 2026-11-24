"""
Frank — Custom Built-In Neural Helper Model for MemoryOS / Jupiter Studio.

A lightweight, pure-Python 128->24->6 Hashing N-Gram Neural Classifier (3,246 params)
with Elastic Weight Consolidation (EWC) + Experience Replay continual learning and
SHA-256 checkpoint verification. Runs on CPU in <1 ms (0 MB GPU VRAM), classifies Studio
workloads, powers `studio:frank` local diagnostic replies cleanly offline, and learns new
user phrasing without catastrophically forgetting core routing intents.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRANK_WEIGHTS_PATH = REPO_ROOT / "memory" / "models" / "frank_v1.json"

FRANK_INTENTS: Tuple[str, ...] = (
    "fast_code",
    "architecture",
    "large_design",
    "cheap_bg",
    "vram_reclaim",
    "memory_pin",
)

FEAT_DIM = 128
HIDDEN_DIM = 24
NUM_CLASSES = len(FRANK_INTENTS)
MAX_FRANK_FISHER = 20.0

TRAINING_CURRICULUM: List[Tuple[str, str]] = [
    # fast_code
    ("Write a fast python function to parse JSONL files", "fast_code"),
    ("Fix this typescript bug in the React component diff", "fast_code"),
    ("Refactor SQL query and write pytest unit tests", "fast_code"),
    ("Debug null pointer exception in python class method", "fast_code"),
    ("Generate a clean bash script and git patch", "fast_code"),
    ("Write unit tests for HTTP POST handler in python", "fast_code"),
    # architecture
    ("Review the distributed system architecture and trade-offs", "architecture"),
    ("Perform a release-blocking security audit and threat model", "architecture"),
    ("Compare microservices vs monolith database lock bottlenecks", "architecture"),
    ("Inspect system design and failure recovery strategy", "architecture"),
    ("Evaluate cache invalidation and horizontal scale design", "architecture"),
    ("Audit EWC continual learning stability and circuit breakers", "architecture"),
    # large_design
    ("Analyze this massive product specification and RFC design doc", "large_design"),
    ("Review screenshot diagram and long multi-document spec", "large_design"),
    ("Synthesize the full 40-page technical design document", "large_design"),
    ("Inspect attached UI mockup image and long PRD doc", "large_design"),
    ("Read this giant log trace and multi-document spec bundle", "large_design"),
    ("Summarize the complete vision and design RFC bundle", "large_design"),
    # cheap_bg
    ("Summarize this short note quickly", "cheap_bg"),
    ("Generate a concise session title and 3 tags", "cheap_bg"),
    ("Clean up formatting and fix capitalization", "cheap_bg"),
    ("Classify this brief log message as info or warn", "cheap_bg"),
    ("Convert this small list into markdown bullets", "cheap_bg"),
    ("Draft a quick two word label", "cheap_bg"),
    # vram_reclaim
    ("Free up locked GPU VRAM before launching my game", "vram_reclaim"),
    ("Unload idle Ollama models and release host RAM memory", "vram_reclaim"),
    ("My RTX 3070 memory is full clean up GPU memory right now", "vram_reclaim"),
    ("Clear VRAM cache to boost FPS and cool down GPU", "vram_reclaim"),
    ("Reclaim system RAM and flush unused local runner weights", "vram_reclaim"),
    ("Stop VRAM thrashing by freeing memory before compiling", "vram_reclaim"),
    # memory_pin
    ("Remember that my laptop has an 8GB RTX 3070 GPU forever", "memory_pin"),
    ("Pin this project rule into the persistent memory vault", "memory_pin"),
    ("Save hardware constraint so Studio never forgets it", "memory_pin"),
    ("Install persistent workspace memory across sessions", "memory_pin"),
    ("Recall my stored deployment preferences and GPU limits", "memory_pin"),
    ("Never forget never commit sqlite database files to git", "memory_pin"),
]


def _clamp(v: float, lo: float = -20.0, hi: float = 20.0) -> float:
    return lo if v < lo else (hi if v > hi else v)


def _relu(x: float) -> float:
    return x if x > 0.0 else 0.0


def _softmax(logits: Sequence[float]) -> List[float]:
    m = max(logits)
    exps = [math.exp(_clamp(z - m, -30.0, 30.0)) for z in logits]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


def featurize_text(text: str, dim: int = FEAT_DIM) -> List[float]:
    """Deterministic signed feature-hashing vector over words, bigrams, and 3-char trigrams."""
    vec = [0.0] * dim
    cleaned = re.sub(r"\s+", " ", str(text or "").lower()).strip()
    if not cleaned:
        return vec
    tokens = re.findall(r"[a-z0-9_+#.-]{2,}", cleaned)
    features: List[Tuple[str, float]] = []
    for i, tok in enumerate(tokens):
        features.append((f"w:{tok}", 1.5))
        if i + 1 < len(tokens):
            features.append((f"b:{tok}_{tokens[i + 1]}", 1.2))
        if len(tok) >= 4:
            for k in range(len(tok) - 2):
                features.append((f"c:{tok[k:k + 3]}", 0.35))
    # Explicit structural signal for very long inputs -> favors large_design
    if len(cleaned) >= 4000:
        features.append(("meta:long_context", 3.0))

    for feat, weight in features:
        h = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        val = int.from_bytes(h, "little")
        idx = val % dim
        sign = 1.0 if ((val >> 6) & 1) == 0 else -1.0
        vec[idx] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _grad_dot(
    a: Tuple[List[List[float]], List[float], List[List[float]], List[float]],
    b: Tuple[List[List[float]], List[float], List[List[float]], List[float]],
) -> float:
    aw1, ab1, aw2, ab2 = a
    bw1, bb1, bw2, bb2 = b
    total = 0.0
    for j in range(len(aw1)):
        total += ab1[j] * bb1[j]
        row_a = aw1[j]
        row_b = bw1[j]
        for i in range(len(row_a)):
            total += row_a[i] * row_b[i]
    for c in range(len(aw2)):
        total += ab2[c] * bb2[c]
        row_a = aw2[c]
        row_b = bw2[c]
        for j in range(len(row_a)):
            total += row_a[j] * row_b[j]
    return total


def _project_agem_gradients(
    g_new: Tuple[List[List[float]], List[float], List[List[float]], List[float]],
    g_ref: Tuple[List[List[float]], List[float], List[List[float]], List[float]],
    eps: float = 1e-12,
) -> Tuple[Tuple[List[List[float]], List[float], List[List[float]], List[float]], bool]:
    """Averaged GEM half-space projection: if g_new . g_ref < 0, remove the conflicting component."""
    dot = _grad_dot(g_new, g_ref)
    if dot >= 0.0:
        return g_new, False
    ref_norm_sq = _grad_dot(g_ref, g_ref)
    if ref_norm_sq <= eps:
        return g_new, False
    scale = dot / (ref_norm_sq + eps)
    nw1, nb1, nw2, nb2 = g_new
    rw1, rb1, rw2, rb2 = g_ref
    pw1 = [[nw1[j][i] - scale * rw1[j][i] for i in range(len(nw1[j]))] for j in range(len(nw1))]
    pb1 = [nb1[j] - scale * rb1[j] for j in range(len(nb1))]
    pw2 = [[nw2[c][j] - scale * rw2[c][j] for j in range(len(nw2[c]))] for c in range(len(nw2))]
    pb2 = [nb2[c] - scale * rb2[c] for c in range(len(nb2))]
    return (pw1, pb1, pw2, pb2), True


def _frank_digest(payload: Dict[str, Any]) -> str:
    clean = {k: v for k, v in payload.items() if k != "checksum_sha256"}
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class FrankModel:
    """Custom 128->24->6 Hashing N-Gram Neural Helper (3,246 params) with EWC continual memory."""

    def __init__(
        self,
        w1: List[List[float]],
        b1: List[float],
        w2: List[List[float]],
        b2: List[float],
        intents: Sequence[str] = FRANK_INTENTS,
        model_name: str = "Frank-v1",
        version: str = "1.0.0",
        ewc_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.model_name = model_name
        self.version = version
        self.intents = list(intents)
        self.w1 = [[float(v) for v in row] for row in w1]
        self.b1 = [float(v) for v in b1]
        self.w2 = [[float(v) for v in row] for row in w2]
        self.b2 = [float(v) for v in b2]
        self.in_dim = len(self.w1[0])
        self.hidden_dim = len(self.w1)
        self.out_dim = len(self.w2)
        self._ewc_fisher: Optional[Dict[str, Any]] = None
        self._ewc_anchor: Optional[Dict[str, Any]] = None
        if ewc_state:
            self._load_ewc_state(ewc_state)

    @classmethod
    def create_fresh(cls) -> "FrankModel":
        """Deterministic small pseudo-random initialization with balanced scale."""
        w1 = []
        for j in range(HIDDEN_DIM):
            row = []
            for i in range(FEAT_DIM):
                seed = ((j * 131 + i * 37 + 17) % 100) / 100.0 - 0.5
                row.append(round(seed * 0.28, 5))
            w1.append(row)
        b1 = [0.02] * HIDDEN_DIM
        w2 = []
        for c in range(NUM_CLASSES):
            row = []
            for j in range(HIDDEN_DIM):
                seed = ((c * 97 + j * 53 + 11) % 100) / 100.0 - 0.5
                row.append(round(seed * 0.25, 5))
            w2.append(row)
        b2 = [0.0] * NUM_CLASSES
        return cls(w1=w1, b1=b1, w2=w2, b2=b2)

    @classmethod
    def load(cls, weights_path: Optional[Path] = None) -> "FrankModel":
        if weights_path is not None:
            path = Path(weights_path)
        else:
            path = DEFAULT_FRANK_WEIGHTS_PATH
            if not path.is_file():
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass:
                    bundled = Path(meipass) / "memory" / "models" / "frank_v1.json"
                    if bundled.is_file():
                        path = bundled
        if not path.is_file():
            # Auto-train deterministic baseline if shipped without checkpoint
            model = cls.create_fresh()
            model.fit_continual(TRAINING_CURRICULUM, epochs=110, lr=0.45, ewc_lambda=0.0)
            return model

        data = json.loads(path.read_text(encoding="utf-8"))
        expected = data.get("checksum_sha256")
        if expected is not None and str(expected) != _frank_digest(data):
            raise ValueError(f"Frank checkpoint integrity mismatch at {path}")
        return cls(
            w1=data["w1"],
            b1=data["b1"],
            w2=data["w2"],
            b2=data["b2"],
            intents=data.get("intents", FRANK_INTENTS),
            model_name=data.get("model_name", "Frank-v1"),
            version=data.get("version", "1.0.0"),
            ewc_state=data.get("ewc_state"),
        )

    def _load_ewc_state(self, st: Dict[str, Any]) -> None:
        self._ewc_fisher = st.get("fisher")
        self._ewc_anchor = st.get("anchor")

    def save(self, weights_path: Path = DEFAULT_FRANK_WEIGHTS_PATH) -> Path:
        path = Path(weights_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = {
            "schema_version": 2,
            "model_name": self.model_name,
            "version": self.version,
            "intents": list(self.intents),
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }
        if self._ewc_fisher and self._ewc_anchor:
            payload["ewc_state"] = {"fisher": self._ewc_fisher, "anchor": self._ewc_anchor}
        payload["checksum_sha256"] = _frank_digest(payload)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(path)
        return path

    def _forward(self, x: Sequence[float]) -> Tuple[List[float], List[float], List[float]]:
        z1 = [sum(self.w1[j][i] * x[i] for i in range(self.in_dim)) + self.b1[j] for j in range(self.hidden_dim)]
        h = [_relu(v) for v in z1]
        logits = [sum(self.w2[c][j] * h[j] for j in range(self.hidden_dim)) + self.b2[c] for c in range(self.out_dim)]
        return z1, h, _softmax(logits)

    def predict(self, prompt: str) -> Dict[str, Any]:
        t0 = time.perf_counter_ns()
        x = featurize_text(prompt, dim=self.in_dim)
        _, _, probs = self._forward(x)
        best_idx = max(range(len(probs)), key=lambda i: probs[i])
        latency_us = round((time.perf_counter_ns() - t0) / 1000.0, 2)
        return {
            "model": self.model_name,
            "version": self.version,
            "intent": self.intents[best_idx],
            "confidence": round(float(probs[best_idx]), 4),
            "probs": {self.intents[i]: round(float(probs[i]), 4) for i in range(self.out_dim)},
            "latency_us": latency_us,
        }

    def evaluate(self, samples: Sequence[Tuple[str, str]]) -> float:
        if not samples:
            return 0.0
        ok = 0
        for text, lbl in samples:
            if self.predict(text)["intent"] == lbl:
                ok += 1
        return round(ok / len(samples), 4)

    def consolidate(self, samples: Sequence[Tuple[str, str]]) -> None:
        fw1 = [[0.0] * self.in_dim for _ in range(self.hidden_dim)]
        fb1 = [0.0] * self.hidden_dim
        fw2 = [[0.0] * self.hidden_dim for _ in range(self.out_dim)]
        fb2 = [0.0] * self.out_dim
        n = max(1, len(samples))
        for text, lbl in samples:
            if lbl not in self.intents:
                continue
            target_idx = self.intents.index(lbl)
            x = featurize_text(text, dim=self.in_dim)
            z1, h, probs = self._forward(x)
            d_logits = [probs[c] - (1.0 if c == target_idx else 0.0) for c in range(self.out_dim)]
            d_h = [0.0] * self.hidden_dim
            for c in range(self.out_dim):
                fb2[c] += d_logits[c] * d_logits[c]
                for j in range(self.hidden_dim):
                    g2 = d_logits[c] * h[j]
                    fw2[c][j] += g2 * g2
                    d_h[j] += d_logits[c] * self.w2[c][j]
            for j in range(self.hidden_dim):
                if z1[j] > 0.0:
                    fb1[j] += d_h[j] * d_h[j]
                    for i in range(self.in_dim):
                        g1 = d_h[j] * x[i]
                        fw1[j][i] += g1 * g1

        prev = self._ewc_fisher
        inv_n = 1.0 / n
        new_f = {
            "w1": [[min(MAX_FRANK_FISHER, (prev["w1"][j][i] if prev else 0.0) + fw1[j][i] * inv_n) for i in range(self.in_dim)] for j in range(self.hidden_dim)],
            "b1": [min(MAX_FRANK_FISHER, (prev["b1"][j] if prev else 0.0) + fb1[j] * inv_n) for j in range(self.hidden_dim)],
            "w2": [[min(MAX_FRANK_FISHER, (prev["w2"][c][j] if prev else 0.0) + fw2[c][j] * inv_n) for j in range(self.hidden_dim)] for c in range(self.out_dim)],
            "b2": [min(MAX_FRANK_FISHER, (prev["b2"][c] if prev else 0.0) + fb2[c] * inv_n) for c in range(self.out_dim)],
        }
        self._ewc_fisher = new_f
        self._ewc_anchor = {
            "w1": [r[:] for r in self.w1],
            "b1": self.b1[:],
            "w2": [r[:] for r in self.w2],
            "b2": self.b2[:],
        }

    def _batch_gradients(
        self,
        prepared: Sequence[Tuple[List[float], int]],
    ) -> Tuple[List[List[float]], List[float], List[List[float]], List[float]]:
        gw1 = [[0.0] * self.in_dim for _ in range(self.hidden_dim)]
        gb1 = [0.0] * self.hidden_dim
        gw2 = [[0.0] * self.hidden_dim for _ in range(self.out_dim)]
        gb2 = [0.0] * self.out_dim
        if not prepared:
            return gw1, gb1, gw2, gb2
        for x, target_idx in prepared:
            z1, h, probs = self._forward(x)
            d_logits = [probs[c] - (1.0 if c == target_idx else 0.0) for c in range(self.out_dim)]
            d_h = [0.0] * self.hidden_dim
            for c in range(self.out_dim):
                gb2[c] += d_logits[c]
                for j in range(self.hidden_dim):
                    gw2[c][j] += d_logits[c] * h[j]
                    d_h[j] += d_logits[c] * self.w2[c][j]
            for j in range(self.hidden_dim):
                if z1[j] > 0.0:
                    gb1[j] += d_h[j]
                    for i in range(self.in_dim):
                        gw1[j][i] += d_h[j] * x[i]
        inv_n = 1.0 / float(len(prepared))
        for j in range(self.hidden_dim):
            gb1[j] *= inv_n
            for i in range(self.in_dim):
                gw1[j][i] *= inv_n
        for c in range(self.out_dim):
            gb2[c] *= inv_n
            for j in range(self.hidden_dim):
                gw2[c][j] *= inv_n
        return gw1, gb1, gw2, gb2

    def fit_continual(
        self,
        samples: Sequence[Tuple[str, str]],
        replay_samples: Sequence[Tuple[str, str]] = (),
        epochs: int = 80,
        lr: float = 0.35,
        ewc_lambda: float = 6.0,
        use_agem: bool = False,
    ) -> Dict[str, Any]:
        """Train Frank incrementally across intent classes with EWC anchor + Experience Replay (+ optional A-GEM)."""
        new_valid = [(t, lbl) for t, lbl in list(samples) if lbl in self.intents]
        replay_valid = [(t, lbl) for t, lbl in list(replay_samples) if lbl in self.intents]
        combined = new_valid + replay_valid
        if not combined:
            return {"trained": False, "accuracy": self.evaluate(TRAINING_CURRICULUM)}
        new_prepared = [(featurize_text(t, dim=self.in_dim), self.intents.index(lbl)) for t, lbl in new_valid]
        replay_prepared = [(featurize_text(t, dim=self.in_dim), self.intents.index(lbl)) for t, lbl in replay_valid]
        all_prepared = new_prepared + replay_prepared
        use_ewc = bool(self._ewc_fisher and self._ewc_anchor and ewc_lambda > 0.0)
        agem_active = bool(use_agem and new_prepared and replay_prepared)
        agem_projections = 0

        for _ in range(max(1, int(epochs))):
            if agem_active:
                g_new = self._batch_gradients(new_prepared)
                g_ref = self._batch_gradients(replay_prepared)
                (gw1, gb1, gw2, gb2), projected = _project_agem_gradients(g_new, g_ref)
                if projected:
                    agem_projections += 1
            else:
                gw1, gb1, gw2, gb2 = self._batch_gradients(all_prepared)

            fisher = self._ewc_fisher
            anchor = self._ewc_anchor
            for c in range(self.out_dim):
                g_b2 = gb2[c] + (ewc_lambda * fisher["b2"][c] * (self.b2[c] - anchor["b2"][c]) if use_ewc else 0.0)
                self.b2[c] = _clamp(self.b2[c] - lr * _clamp(g_b2, -4.0, 4.0), -12.0, 12.0)
                for j in range(self.hidden_dim):
                    g_w2 = gw2[c][j] + (ewc_lambda * fisher["w2"][c][j] * (self.w2[c][j] - anchor["w2"][c][j]) if use_ewc else 0.0)
                    self.w2[c][j] = _clamp(self.w2[c][j] - lr * _clamp(g_w2, -4.0, 4.0), -12.0, 12.0)
            for j in range(self.hidden_dim):
                g_b1 = gb1[j] + (ewc_lambda * fisher["b1"][j] * (self.b1[j] - anchor["b1"][j]) if use_ewc else 0.0)
                self.b1[j] = _clamp(self.b1[j] - lr * _clamp(g_b1, -4.0, 4.0), -12.0, 12.0)
                for i in range(self.in_dim):
                    g_w1 = gw1[j][i] + (ewc_lambda * fisher["w1"][j][i] * (self.w1[j][i] - anchor["w1"][j][i]) if use_ewc else 0.0)
                    self.w1[j][i] = _clamp(self.w1[j][i] - lr * _clamp(g_w1, -4.0, 4.0), -12.0, 12.0)

        self.consolidate(combined)
        acc = self.evaluate(combined)
        base_acc = self.evaluate(TRAINING_CURRICULUM)
        return {
            "trained": True,
            "episodes": len(combined),
            "accuracy": acc,
            "curriculum_retention": base_acc,
            "ewc_protected": bool(self._ewc_fisher is not None),
            "agem_enabled": agem_active,
            "agem_projections": agem_projections,
        }


def run_frank_assistant_turn(
    prompt: str,
    gpu_profile: Optional[Dict[str, Any]] = None,
    vault_summary: Optional[Dict[str, Any]] = None,
    recalled_facts: Optional[Sequence[Dict[str, Any]]] = None,
    frank_model: Optional[FrankModel] = None,
) -> Dict[str, Any]:
    """Generate a deterministic, grounded offline reply from Frank using live telemetry + Memory Vault."""
    model = frank_model or FrankModel.load()
    pred = model.predict(prompt)
    intent = pred["intent"]
    conf_pct = round(pred["confidence"] * 100.0, 1)

    gpu = gpu_profile or {}
    dev = gpu.get("device_name") or "Local CPU / Unified Host"
    used_mb = int(gpu.get("used_vram_mb") or 0)
    total_mb = int(gpu.get("total_vram_mb") or 0)
    watts = gpu.get("power_watts")
    watts_str = f"{watts:.1f} W" if isinstance(watts, (int, float)) else "n/a"

    vs = vault_summary or {}
    facts_n = int(vs.get("facts_count") or 0)
    wh_saved = float(vs.get("estimated_wh_saved") or 0.0)

    route_advice = {
        "fast_code": "Fast coding diff → route via **Groq** (`llama-3.3-70b-versatile`) or **Token Lab** (`Qwen3.8-27B`) / **Lemonade** offline.",
        "architecture": "Architecture review → route via **AMD Token Lab** (`DeepSeek-V4.1-Flash`) or **OpenRouter** (`deepseek-chat`).",
        "large_design": "Large design doc / vision → route via **AMD Token Lab** (`Gemma-4-31B-IT`) or **OpenRouter**.",
        "cheap_bg": "Lightweight background task → route via **MiniCPM5-2B** or local **Bonsai-4B** (`0.53 GB`).",
        "vram_reclaim": "Action: click **`Free VRAM & RAM`** (top of left rail / Memory tab) or run `python -m memoryos.memory_keeper reclaim` to unload idle Ollama runners.",
        "memory_pin": "Action: use **`Pin`** in the **Memory** tab (or `python -m memoryos.memory_keeper install`) so your constraint stays injected across sessions.",
    }.get(intent, "Balanced Studio routing active (`auto:d3`).")

    lines = [
        f"**Frank-v1** *(Built-In Local Neural Helper · `0 MB` VRAM · `{pred['latency_us']} μs`)*",
        "",
        f"- **Classified Intent:** `{intent}` (`{conf_pct}%` confidence across 6 continual EWC classes)",
        f"- **Recommended Route / Action:** {route_advice}",
        f"- **Live Silicon:** `{dev}` · VRAM `{used_mb}/{total_mb} MB` · Power `{watts_str}`",
        f"- **Memory Vault:** `{facts_n}` pinned facts · `{wh_saved:.2f} Wh` energy savings logged",
    ]
    facts_list = [f for f in (recalled_facts or []) if f.get("content")]
    if facts_list:
        lines.append("")
        lines.append("**Recalled From Persistent Memory:**")
        for item in facts_list[:3]:
            lines.append(f"- `[{item.get('topic', 'general')}]` {item['content']}")

    return {
        "content": "\n".join(lines),
        "prediction": pred,
    }
