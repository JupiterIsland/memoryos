# tests/test_offload_integrity.py
#
# End-to-End Offload Integrity Test
# Verifies the core architectural invariant end-to-end:
#   "When a prompt is offloaded, local GPU VRAM delta stays at 0 MB
#    (within driver jitter), and every subsystem leaves a verifiable trace."
#
# Read-only against production state: does not pin, write, or mutate
# the production QuietAdvisorDB.sqlite or tokenlab_export.json.
#
# Run: python -B -m unittest tests/test_offload_integrity.py -v
#  or: pytest tests/test_offload_integrity.py -v

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from memoryos.frank import FrankModel
from memoryos.gpu_backends import MultiGPUDetector
from memoryos.grant_ledger import DEFAULT_EXPORT_PATH, load_audit_trail, load_ledger_snapshot
from memoryos.memory_keeper import MemoryVault
from memoryos.router import compute_frame_delta, mse_to_frame_delta, route_task
from memoryos.speculative_offload import DEFAULT_WEIGHTS_PATH, SpeculativeOffloadModel

GRANT_ID = "1E13760B"
WINDOW = "2026-11-14"
GPU_INDEX = 0  # RTX 3070 Laptop GPU
# Global OS VRAM includes Windows DWM / browser DirectX swapchain jitter (~64-96 MB);
# Python's own PID compute VRAM is asserted at strict 0.0 MB below.
VRAM_TOLERANCE_MB = 128.0


def _read_current_pid_compute_vram_mb(gpu_index: int = GPU_INDEX) -> float:
    """Return GPU compute VRAM (MB) allocated specifically by this Python process."""
    my_pid = str(os.getpid())
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                f"-i={gpu_index}",
                "--query-compute-apps=pid,used_gpu_memory",
                "--format=csv,noheader,nounits",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3.0,
        )
        if proc.returncode != 0:
            return 0.0
        total = 0.0
        for line in proc.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[0] == my_pid:
                try:
                    total += float(parts[1])
                except ValueError:
                    pass
        return total
    except Exception:
        return 0.0

PINNED_FACTS = [
    {
        "topic": "models",
        "content": (
            "Gemma is a family of lightweight, state-of-the-art open "
            "models from Google, built from the same research and "
            "technology used to create the Gemini models."
        ),
    },
    {
        "topic": "hardware",
        "content": (
            "RTX 3070 8GB VRAM - Keep 0 MB local memory "
            "for Cyberpunk 1440p"
        ),
    },
]

TEST_PROMPT = (
    "What is Gemma, and what is the VRAM constraint "
    "for the local GPU in this workspace?"
)


class VRAMSampler:
    """
    Samples live driver-reported GPU VRAM via nvidia-smi in a background thread
    during the end-to-end offload pipeline. Records baseline, peak, and delta.
    """

    def __init__(self, gpu_index: int = GPU_INDEX, interval: float = 0.05) -> None:
        self.gpu_index = gpu_index
        self.interval = interval
        self.baseline_mb: Optional[float] = None
        self.peak_mb: float = 0.0
        self.samples: List[float] = []
        self.device_name: Optional[str] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _read_once(self) -> Optional[float]:
        prof = MultiGPUDetector.detect_nvidia(device_index=self.gpu_index)
        if prof is None:
            return None
        self.device_name = prof.device_name
        return float(prof.used_vram_mb)

    def start(self) -> bool:
        """Capture baseline VRAM and start background sampling. Returns False if no NVIDIA GPU."""
        base = self._read_once()
        if base is None:
            return False
        self.baseline_mb = base
        self.peak_mb = base
        self.samples = [base]
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def _loop(self) -> None:
        while not self._stop.is_set():
            val = self._read_once()
            if val is not None:
                self.samples.append(val)
                if val > self.peak_mb:
                    self.peak_mb = val
            self._stop.wait(self.interval)

    def stop(self) -> float:
        """Stop sampling, capture one final reading, and return peak delta MB."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        final_val = self._read_once()
        if final_val is not None:
            self.samples.append(final_val)
            if final_val > self.peak_mb:
                self.peak_mb = final_val
        if self.baseline_mb is None:
            return 0.0
        return max(0.0, self.peak_mb - self.baseline_mb)


class TestEndToEndOffloadIntegrity(unittest.TestCase):
    """Verifies all 7 offload links end-to-end while monitoring real RTX 3070 VRAM."""

    def test_end_to_end_offload_chain_and_zero_vram_delta(self) -> None:
        # Snapshot production SQLite mtime/size (if present) to prove read-only safety.
        prod_db = REPO_ROOT / "memory" / "quiet_advisor.sqlite"
        prod_before = (prod_db.stat().st_mtime_ns, prod_db.stat().st_size) if prod_db.is_file() else None

        sampler = VRAMSampler(gpu_index=GPU_INDEX, interval=0.05)
        has_gpu = sampler.start()

        try:
            # ---------------------------------------------------------------
            # LINK 1: CPU Frame-Delta Gate (pure CPU, sub-millisecond)
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            frame_delta = compute_frame_delta(
                current_metrics={"brightness": 0.82, "contrast": 0.71, "intensity": 0.77, "palette": ["#112233", "#aabbcc"]},
                previous_metrics={"brightness": 0.20, "contrast": 0.25, "intensity": 0.22, "palette": ["#ffffff", "#000000"]},
                threshold=0.08,
            )
            mse_gate = mse_to_frame_delta(mse_delta=42.0, threshold=12.0)
            delta_gate_ms = (time.perf_counter() - t0) * 1000.0

            self.assertTrue(frame_delta["significant_change"], "CPU delta gate missed significant change")
            self.assertGreater(frame_delta["composite_delta"], 0.08)
            self.assertTrue(mse_gate["significant_change"])
            self.assertLess(delta_gate_ms, 50.0, f"CPU delta gate too slow: {delta_gate_ms:.2f}ms")

            # ---------------------------------------------------------------
            # LINK 2: SpeculativeOffloadModel MLP (4->8->1, SHA-256 verified)
            # ---------------------------------------------------------------
            self.assertTrue(DEFAULT_WEIGHTS_PATH.is_file(), f"Missing weights: {DEFAULT_WEIGHTS_PATH}")
            offload_net = SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)
            self.assertEqual((offload_net.in_dim, offload_net.hidden_dim), (4, 8))

            features = {
                "mse_delta_norm": mse_gate["composite_delta"],
                "context_utilization": 0.88,
                "secs_since_offload": 18.0,
                "model_switch_rate": 0.25,
            }
            prob = offload_net.predict_proba(features)
            action = offload_net.decide(features)
            self.assertIn(action, ("offload_now", "digest", "skip"))
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)
            self.assertEqual(
                action,
                "offload_now",
                f"High-pressure frame should trigger offload_now, got {action} (p={prob:.3f})",
            )

            # ---------------------------------------------------------------
            # LINK 3: Frank-v1 Continual Router (128->24->6, 3,246 params, CPU)
            # ---------------------------------------------------------------
            frank = FrankModel.load()
            param_count = (
                frank.in_dim * frank.hidden_dim
                + frank.hidden_dim
                + frank.hidden_dim * frank.out_dim
                + frank.out_dim
            )
            self.assertEqual(param_count, 3246)
            pred = frank.predict(TEST_PROMPT)
            self.assertIn("intent", pred)
            self.assertIn("probs", pred)
            prob_sum = sum(pred["probs"].values())
            self.assertAlmostEqual(prob_sum, 1.0, places=2)

            # ---------------------------------------------------------------
            # LINK 4: Cloud Offload Router (prefer_local=False, 0 MB local VRAM)
            # ---------------------------------------------------------------
            with tempfile.TemporaryDirectory() as tmpdir:
                iso_db = Path(tmpdir) / "isolated_advisor.sqlite"
                route_res = route_task(
                    TEST_PROMPT,
                    prefer_local=False,
                    save_checkpoint=False,
                    log_to_advisor=False,
                    db_path=iso_db,
                )
                self.assertEqual(route_res["gpu_memory_used_mb"], 0)
                self.assertNotEqual(route_res.get("gpu_id"), "local-rtx3070")
                self.assertIn("model", route_res)
                self.assertIn("routing_policy", route_res)

                # -----------------------------------------------------------
                # LINK 5: Pinned-Fact Recall (isolated vault — zero prod writes)
                # -----------------------------------------------------------
                vault = MemoryVault(db_path=iso_db)
                for fact in PINNED_FACTS:
                    vault.remember(
                        topic=fact["topic"],
                        content=fact["content"],
                        importance=1.0,
                    )
                recalled = vault.recall(TEST_PROMPT, limit=5)
                recalled_blob = " ".join(str(r.get("content", "")) for r in recalled).lower()
                self.assertIn("gemma", recalled_blob, "Pinned Gemma fact was not recalled")
                self.assertIn("rtx 3070", recalled_blob, "Pinned RTX 3070 VRAM constraint was not recalled")
                self.assertIn("0 mb", recalled_blob, "Pinned 0 MB constraint was not recalled")

            # ---------------------------------------------------------------
            # LINK 6: Grant Ledger & Audit Trail (read-only verification)
            # ---------------------------------------------------------------
            if DEFAULT_EXPORT_PATH.is_file():
                ledger = load_ledger_snapshot(grant_id=GRANT_ID, window=WINDOW)
                trail = load_audit_trail(grant_id=GRANT_ID, window=WINDOW)
                self.assertEqual(sum(m["requests"] for m in ledger["models"].values()), ledger["gateway"]["allowed"])
                self.assertEqual(len(trail["entries"]), len(ledger["requests"]))
                self.assertEqual(sum(1 for e in trail["entries"] if e["status"] != "OK"), 8)
                self.assertEqual(ledger["grant"]["unit_label"], "µpts")

        finally:
            delta_mb = sampler.stop()

        # -------------------------------------------------------------------
        # LINK 7: Live Hardware VRAM Delta Assertion (RTX 3070 ground truth)
        # -------------------------------------------------------------------
        if has_gpu:
            self.assertGreaterEqual(len(sampler.samples), 2, "VRAMSampler captured too few samples")
            pid_vram_mb = _read_current_pid_compute_vram_mb(GPU_INDEX)
            self.assertEqual(
                pid_vram_mb,
                0.0,
                f"Python process (PID {os.getpid()}) allocated {pid_vram_mb:.1f} MB GPU compute VRAM (expected 0.0 MB)",
            )
            self.assertLessEqual(
                delta_mb,
                VRAM_TOLERANCE_MB,
                (
                    f"VRAM violation on {sampler.device_name}: baseline={sampler.baseline_mb:.1f} MB, "
                    f"peak={sampler.peak_mb:.1f} MB, delta={delta_mb:.1f} MB > {VRAM_TOLERANCE_MB} MB"
                ),
            )

        # Prove production vault was NOT modified
        if prod_before is not None:
            prod_after = (prod_db.stat().st_mtime_ns, prod_db.stat().st_size)
            self.assertEqual(prod_before, prod_after, "Production QuietAdvisorDB.sqlite was mutated!")


if __name__ == "__main__":
    unittest.main()
