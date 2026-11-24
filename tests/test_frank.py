import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from memoryos.frank import (
    DEFAULT_FRANK_WEIGHTS_PATH,
    FRANK_INTENTS,
    TRAINING_CURRICULUM,
    FrankModel,
    _grad_dot,
    _project_agem_gradients,
    featurize_text,
    run_frank_assistant_turn,
)
from tests.test_jupiter_studio import LiveStudioServerMixin


class TestFrankModel(unittest.TestCase):
    def test_frank_pretrained_checkpoint_accuracy_and_latency(self) -> None:
        self.assertTrue(DEFAULT_FRANK_WEIGHTS_PATH.is_file())
        frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
        self.assertGreaterEqual(frank.evaluate(TRAINING_CURRICULUM), 0.90)

        p1 = frank.predict("Free locked GPU VRAM before gaming")
        self.assertEqual(p1["model"], "Frank-v1")
        self.assertEqual(p1["intent"], "vram_reclaim")
        self.assertLess(p1["latency_us"], 5000.0)

        p2 = frank.predict("Write a fast python function and pytest unit tests")
        self.assertEqual(p2["intent"], "fast_code")

    def test_frank_continual_teaching_retains_curriculum_and_rejects_tamper(self) -> None:
        frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
        frank.consolidate(TRAINING_CURRICULUM)

        custom_phrase = "yo frank clear out my gpu buffers before valorant"
        res = frank.fit_continual(
            [(custom_phrase, "vram_reclaim")] * 4,
            replay_samples=TRAINING_CURRICULUM,
            epochs=45,
            lr=0.25,
            ewc_lambda=6.0,
        )
        self.assertTrue(res["trained"])
        self.assertTrue(res["ewc_protected"])
        self.assertGreaterEqual(res["curriculum_retention"], 0.90)
        self.assertEqual(frank.predict(custom_phrase)["intent"], "vram_reclaim")

        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = Path(tmpdir) / "frank_test.json"
            frank.save(ckpt)
            reloaded = FrankModel.load(ckpt)
            self.assertEqual(reloaded.predict(custom_phrase)["intent"], "vram_reclaim")

            # Tampered checksum rejected loudly
            raw = json.loads(ckpt.read_text(encoding="utf-8"))
            raw["b2"][0] = float(raw["b2"][0]) + 3.14
            ckpt.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ValueError):
                FrankModel.load(ckpt)

    def test_frank_assistant_turn_renders_telemetry_and_vault(self) -> None:
        out = run_frank_assistant_turn(
            prompt="Remember that 8GB RTX 3070 stays free for rendering",
            gpu_profile={"device_name": "NVIDIA GeForce RTX 3070 Laptop GPU", "used_vram_mb": 1200, "total_vram_mb": 8192, "power_watts": 19.2},
            vault_summary={"facts_count": 2, "estimated_wh_saved": 0.45},
            recalled_facts=[{"topic": "hardware", "content": "Never saturate 8 GB VRAM"}],
        )
        self.assertIn("Frank-v1", out["content"])
        self.assertIn("RTX 3070", out["content"])
        self.assertIn("Never saturate 8 GB VRAM", out["content"])

    def test_frank_agem_gradient_projection_and_retention(self) -> None:
        g_ref = ([[1.0, 0.0]], [0.5], [[0.0, 2.0]], [1.0])
        g_conflict = ([[-2.0, 1.0]], [-0.5], [[0.5, -1.0]], [-0.5])
        self.assertLess(_grad_dot(g_conflict, g_ref), 0.0)
        g_proj, projected = _project_agem_gradients(g_conflict, g_ref)
        self.assertTrue(projected)
        self.assertGreaterEqual(_grad_dot(g_proj, g_ref), -1e-9)

        g_aligned = ([[1.0, 0.5]], [0.2], [[0.1, 1.0]], [0.3])
        g_same, projected2 = _project_agem_gradients(g_aligned, g_ref)
        self.assertFalse(projected2)
        self.assertEqual(g_same, g_aligned)

        frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
        frank.consolidate(TRAINING_CURRICULUM)
        phrase = "yo frank purge idle gpu weights right now before blender"
        res = frank.fit_continual(
            [(phrase, "vram_reclaim")] * 4,
            replay_samples=TRAINING_CURRICULUM,
            epochs=40,
            lr=0.25,
            ewc_lambda=6.0,
            use_agem=True,
        )
        self.assertTrue(res["trained"])
        self.assertTrue(res["agem_enabled"])
        self.assertIsInstance(res["agem_projections"], int)
        self.assertGreaterEqual(res["curriculum_retention"], 0.90)
        self.assertEqual(frank.predict(phrase)["intent"], "vram_reclaim")

    def test_frank_featurize_edge_cases_and_unicode(self) -> None:
        """Featurizer handles empty, whitespace, extreme lengths, and multilingual text without crashing."""
        for text in ("", "   \t\n  ", "a", "🧠 GPU VRAM を解放して", "Русский текст для роутера", "x" * 50000):
            vec = featurize_text(text, dim=128)
            self.assertEqual(len(vec), 128)
            for val in vec:
                self.assertFalse(val != val, "Vector must not contain NaN")
                self.assertFalse(abs(val) == float("inf"), "Vector must not contain Inf")
            # If tokens exist, L2 norm should be normalized to 1.0; if empty, norm is 0.0
            l2_norm = sum(v * v for v in vec) ** 0.5
            self.assertTrue(abs(l2_norm - 1.0) < 1e-4 or abs(l2_norm) < 1e-4)

        # Empty string yields all zeros
        empty_vec = featurize_text("", dim=128)
        self.assertEqual(sum(empty_vec), 0.0)

    def test_frank_zero_learning_rate_and_lambda_invariants(self) -> None:
        """Zero learning rate preserves weights exactly; lambda=0 disables EWC penalty."""
        frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
        w1_before = [r[:] for r in frank.w1]
        b1_before = frank.b1[:]

        # lr = 0.0 -> weights unchanged
        frank.fit_continual(
            [("some prompt", "fast_code")],
            epochs=10,
            lr=0.0,
        )
        self.assertEqual(frank.w1, w1_before)
        self.assertEqual(frank.b1, b1_before)

    def test_frank_multi_intent_sequential_continual_learning(self) -> None:
        """Sequential teaching across multiple distinct intents preserves core curriculum retention."""
        frank = FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH)
        frank.consolidate(TRAINING_CURRICULUM)

        sequence = [
            ("accelerate inner loop using numba jit", "fast_code"),
            ("pin custom thermal threshold into persistent memory", "memory_pin"),
            ("drop idle whisper model from host ram", "vram_reclaim"),
        ]
        for phrase, intent in sequence:
            res = frank.fit_continual(
                [(phrase, intent)] * 4,
                replay_samples=TRAINING_CURRICULUM,
                epochs=35,
                lr=0.20,
                ewc_lambda=6.0,
                use_agem=True,
            )
            self.assertTrue(res["trained"])
            self.assertGreaterEqual(res["curriculum_retention"], 0.88)
            self.assertEqual(frank.predict(phrase)["intent"], intent)

        # After all 3 updates, core curriculum retention remains high
        retention = frank.evaluate(TRAINING_CURRICULUM)
        self.assertGreaterEqual(retention, 0.88)

    def test_frank_corrupted_checkpoint_recovery(self) -> None:
        """Corrupted checkpoint structure raises ValueError on load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_ckpt = Path(tmpdir) / "corrupt_frank.json"
            bad_ckpt.write_text('{"w1": [[1.0]], "checksum_sha256": "bad"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                FrankModel.load(bad_ckpt)


class TestFrankHTTP(LiveStudioServerMixin, unittest.TestCase):
    def test_frank_endpoints_and_stream_chat(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = Path(tmpdir) / "frank_http.sqlite"
            test_ckpt = Path(tmpdir) / "frank_v1.json"
            FrankModel.load(DEFAULT_FRANK_WEIGHTS_PATH).save(test_ckpt)

            with patch("apps.jupiter_studio._get_studio_db_path", return_value=test_db), patch(
                "src.memoryos.frank.DEFAULT_FRANK_WEIGHTS_PATH", test_ckpt
            ):
                # 1. Status endpoint
                status, _, raw = self._raw_request("GET", "/api/frank/status")
                self.assertEqual(status, 200)
                st = json.loads(raw)
                self.assertEqual(st["model"], "Frank-v1")
                self.assertEqual(st["intents"], list(FRANK_INTENTS))

                # 2. Invalid teach rejected with 400
                status, _, _ = self._raw_request(
                    "POST",
                    "/api/frank/teach",
                    body=json.dumps({"prompt": "hi", "intent": "invalid_class"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(status, 400)

                # 3. Valid continual teach updates Frank and preserves curriculum
                status, _, raw = self._raw_request(
                    "POST",
                    "/api/frank/teach",
                    body=json.dumps({"prompt": "dump idle local runner memory now", "intent": "vram_reclaim"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(status, 200)
                taught = json.loads(raw)
                self.assertTrue(taught["taught"])
                self.assertTrue(taught["agem_enabled"])
                self.assertGreaterEqual(taught["curriculum_retention"], 0.90)

                # 4. Sync and SSE chat against built-in studio:frank target work completely offline
                status, _, raw = self._raw_request(
                    "POST",
                    "/api/chat",
                    body=json.dumps({"prompt": "Free my GPU memory", "target": "studio:frank"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(status, 200)
                sync_res = json.loads(raw)
                self.assertIn("Frank-v1", sync_res["content"])
                self.assertTrue(sync_res["is_local"])

                status, hdrs, raw = self._raw_request(
                    "POST",
                    "/api/chat/stream",
                    body=json.dumps({"prompt": "Refactor python router", "target": "studio:frank"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(status, 200)
                self.assertIn("text/event-stream", hdrs.get("content-type", ""))
                sse = raw.decode("utf-8")
                self.assertIn("event: start", sse)
                self.assertIn("Frank-v1", sse)
                self.assertIn("event: done", sse)

                # 5. Live Frank prediction tracking (GET /api/frank/predict & POST /api/frank/predict)
                status, _, raw = self._raw_request("GET", "/api/frank/predict?q=")
                self.assertEqual(status, 200)
                idle_pred = json.loads(raw)
                self.assertEqual(idle_pred["intent"], "idle")
                self.assertEqual(idle_pred["confidence"], 0.0)

                status, _, raw = self._raw_request(
                    "GET",
                    "/api/frank/predict?q=Write+a+fast+python+function+to+parse+JSONL",
                )
                self.assertEqual(status, 200)
                get_pred = json.loads(raw)
                self.assertIn(get_pred["intent"], FRANK_INTENTS)
                self.assertGreater(get_pred["confidence"], 0.0)
                self.assertLessEqual(get_pred["confidence"], 1.0)
                self.assertGreater(get_pred["confidence_pct"], 0.0)
                self.assertIn("probs", get_pred)

                status, _, raw = self._raw_request(
                    "POST",
                    "/api/frank/predict",
                    body=json.dumps({"prompt": "Free up locked GPU VRAM before launching my game"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(status, 200)
                post_pred = json.loads(raw)
                self.assertEqual(post_pred["intent"], "vram_reclaim")

                status, _, raw = self._raw_request("GET", "/api/frank/status")
                self.assertEqual(status, 200)
                st_after = json.loads(raw)
                self.assertIsNotNone(st_after.get("last_prediction"))
                self.assertEqual(st_after["last_prediction"]["intent"], "vram_reclaim")

                # 6. UI markup exposes collapsible Sidebar toggle & FRANK decision chip
                status, _, raw = self._raw_request("GET", "/")
                self.assertEqual(status, 200)
                html = raw.decode("utf-8")
                for needle in (
                    "btn-toggle-sidebar",
                    "btn-settings-menu",
                    "settings-popover",
                    "frank-hero-card",
                    "frank-summary-text",
                    "btn-toggle-math",
                    "rad-frank",
                    "updateFrankTelemetry",
                    "/api/frank/predict",
                    "sidebar-collapsed",
                ):
                    self.assertIn(needle, html)


if __name__ == "__main__":
    unittest.main()
