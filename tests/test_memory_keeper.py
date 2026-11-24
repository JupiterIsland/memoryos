import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from memoryos.memory_keeper import MemoryVault, reclaim_memory
from memoryos.speculative_offload import DEFAULT_WEIGHTS_PATH, SpeculativeOffloadModel


def _task_a_gaming_samples():
    """Regime A: gaming workload where high visual delta forces offload even during low context, while steady high-switch desktop UI stays skipped."""
    return [
        ({"mse_delta_norm": 0.95, "context_utilization": 0.15, "secs_since_offload": 0.90, "model_switch_rate": 0.05}, 1.0),
        ({"mse_delta_norm": 0.88, "context_utilization": 0.20, "secs_since_offload": 0.80, "model_switch_rate": 0.05}, 1.0),
        ({"mse_delta_norm": 0.10, "context_utilization": 0.55, "secs_since_offload": 0.10, "model_switch_rate": 0.85}, 0.0),
        ({"mse_delta_norm": 0.12, "context_utilization": 0.50, "secs_since_offload": 0.15, "model_switch_rate": 0.80}, 0.0),
    ] * 6


def _task_b_coding_samples():
    """Regime B: shifted developer workload where high model-switch / medium context offloads, while high visual motion with fresh offload skips."""
    return [
        ({"mse_delta_norm": 0.10, "context_utilization": 0.65, "secs_since_offload": 0.25, "model_switch_rate": 0.90}, 1.0),
        ({"mse_delta_norm": 0.14, "context_utilization": 0.70, "secs_since_offload": 0.30, "model_switch_rate": 0.85}, 1.0),
        ({"mse_delta_norm": 0.85, "context_utilization": 0.10, "secs_since_offload": 0.05, "model_switch_rate": 0.05}, 0.0),
        ({"mse_delta_norm": 0.80, "context_utilization": 0.12, "secs_since_offload": 0.08, "model_switch_rate": 0.08}, 0.0),
    ] * 6


def _blank_model() -> SpeculativeOffloadModel:
    # Deterministic non-degenerate ReLU weights so gradients propagate cleanly on first pass
    w1 = [
        [0.4, 0.2, 0.1, -0.1],
        [-0.2, 0.4, 0.2, 0.1],
        [0.3, -0.1, 0.3, 0.2],
        [0.1, 0.3, -0.1, 0.4],
        [-0.3, -0.2, 0.4, 0.1],
        [0.2, 0.1, 0.1, 0.3],
        [0.35, 0.25, -0.2, 0.1],
        [-0.1, 0.2, 0.3, -0.2],
    ]
    b1 = [0.05] * 8
    w2 = [0.25, -0.15, 0.2, 0.3, -0.1, 0.25, 0.2, -0.15]
    return SpeculativeOffloadModel(w1=w1, b1=b1, w2=w2, b2=0.0)


class TestMemoryKeeperAndContinualLearning(unittest.TestCase):
    def test_ewc_plus_replay_prevents_catastrophic_forgetting(self) -> None:
        task_a = _task_a_gaming_samples()
        task_b = _task_b_coding_samples()

        # Baseline naive SGD without EWC or replay catastrophically forgets Task A when shifted to Task B
        naive = _blank_model()
        naive.fit_continual(task_a, lr=0.22, epochs=120, ewc_lambda=0.0, consolidate_after=False)
        self.assertGreaterEqual(naive.evaluate(task_a)["accuracy"], 0.90)
        naive.fit_continual(task_b, replay_samples=(), lr=0.30, epochs=180, ewc_lambda=0.0, consolidate_after=False)
        naive_a_after = naive.evaluate(task_a)["accuracy"]
        self.assertLess(naive_a_after, 0.75, f"Expected naive SGD baseline to forget Task A, got {naive_a_after}")

        # Continual update on Task B (Developer coding workload) with EWC + Replay retains both regimes
        ewc_model = _blank_model()
        ewc_model.fit_continual(task_a, lr=0.22, epochs=120, ewc_lambda=0.0, consolidate_after=True)
        a_before = ewc_model.evaluate(task_a)["accuracy"]
        self.assertGreaterEqual(a_before, 0.90)

        ewc_model.fit_continual(task_b, replay_samples=task_a, lr=0.22, epochs=150, ewc_lambda=8.0, consolidate_after=True)
        a_after = ewc_model.evaluate(task_a)["accuracy"]
        b_after = ewc_model.evaluate(task_b)["accuracy"]

        self.assertGreaterEqual(a_after, 0.90, f"EWC+Replay lost Task A accuracy: {a_after}")
        self.assertGreaterEqual(b_after, 0.90, f"EWC+Replay failed Task B accuracy: {b_after}")

    def test_sparse_replay_control_arm_vs_ewc_plus_replay(self) -> None:
        task_a = _task_a_gaming_samples()
        task_b = _task_b_coding_samples()

        # Sparse replay-only control arm (ewc_lambda=0.0, 4 replay samples vs 24 Task B samples)
        replay_only = _blank_model()
        replay_only.fit_continual(task_a, lr=0.22, epochs=120, ewc_lambda=0.0, consolidate_after=False)
        self.assertGreaterEqual(replay_only.evaluate(task_a)["accuracy"], 0.90)
        replay_only.fit_continual(
            task_b, replay_samples=task_a[:4], lr=0.22, epochs=150, ewc_lambda=0.0, consolidate_after=False
        )
        replay_only_a = replay_only.evaluate(task_a)
        replay_only_b = replay_only.evaluate(task_b)
        self.assertLess(replay_only_a["accuracy"], 0.75, f"Expected sparse replay-only to drop Task A: {replay_only_a}")
        self.assertGreaterEqual(replay_only_b["accuracy"], 0.90)

        # EWC + sparse replay under the exact same sparse budget (ewc_lambda=8.0, replay_samples=task_a[:4])
        ewc_sparse = _blank_model()
        ewc_sparse.fit_continual(task_a, lr=0.22, epochs=120, ewc_lambda=0.0, consolidate_after=True)
        ewc_sparse.fit_continual(
            task_b, replay_samples=task_a[:4], lr=0.22, epochs=150, ewc_lambda=8.0, consolidate_after=True
        )
        ewc_sparse_a = ewc_sparse.evaluate(task_a)
        ewc_sparse_b = ewc_sparse.evaluate(task_b)
        self.assertGreaterEqual(ewc_sparse_a["accuracy"], replay_only_a["accuracy"])
        self.assertLess(ewc_sparse_a["brier_loss"], replay_only_a["brier_loss"])
        self.assertGreaterEqual(ewc_sparse_b["accuracy"], 0.90)

        # Under non-saturated Task A consolidation, EWC + sparse replay prevents Task A accuracy drop where sparse replay alone fails
        sparse_ctrl = _blank_model()
        sparse_ctrl.fit_continual(task_a, lr=0.22, epochs=50, ewc_lambda=0.0, consolidate_after=False)
        self.assertGreaterEqual(sparse_ctrl.evaluate(task_a)["accuracy"], 0.90)
        sparse_ctrl.fit_continual(
            task_b, replay_samples=task_a[:4], lr=0.15, epochs=30, ewc_lambda=0.0, consolidate_after=False
        )
        sparse_ctrl_a = sparse_ctrl.evaluate(task_a)["accuracy"]
        self.assertLess(sparse_ctrl_a, 0.75)

        ewc_guarded = _blank_model()
        ewc_guarded.fit_continual(task_a, lr=0.22, epochs=50, ewc_lambda=0.0, consolidate_after=True)
        ewc_guarded.fit_continual(
            task_b, replay_samples=task_a[:4], lr=0.15, epochs=30, ewc_lambda=120.0, consolidate_after=True
        )
        ewc_guarded_a = ewc_guarded.evaluate(task_a)["accuracy"]
        ewc_guarded_b = ewc_guarded.evaluate(task_b)["accuracy"]
        self.assertGreater(ewc_guarded_a, sparse_ctrl_a)
        self.assertGreaterEqual(ewc_guarded_a, 0.90)
        self.assertGreaterEqual(ewc_guarded_b, 0.90)

    def test_checkpoint_save_and_load_preserves_ewc_fisher_state(self) -> None:
        task_a = _task_a_gaming_samples()
        model = SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)
        model.fit_continual(task_a, lr=0.10, epochs=40, ewc_lambda=10.0, consolidate_after=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = Path(tmpdir) / "continual.json"
            model.save(ckpt)
            reloaded = SpeculativeOffloadModel.load(ckpt)

            probe = task_a[0][0]
            self.assertAlmostEqual(model.predict_proba(probe), reloaded.predict_proba(probe), places=8)
            self.assertIsNotNone(reloaded.export_ewc_state())

    def test_memory_vault_cross_restart_persistence_recall_and_ewc_training(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "vault.sqlite"
            weights = Path(tmpdir) / "continual_weights.json"

            # Session 1 installs facts & trains from episodes
            v1 = MemoryVault(db_path=db, weights_path=weights)
            f1 = v1.remember("hardware", "Laptop GPU is RTX 3070 8GB VRAM; offload 31B models.", tags="gpu,gaming", importance=2.0)
            v1.remember("dev", "Never stage QuietAdvisorDB.sqlite in git commits.", tags="git,ci", importance=1.5)
            train_res = v1.train_continual_model(new_episodes=_task_a_gaming_samples()[:6], epochs=50)
            self.assertTrue(train_res["trained"])
            self.assertTrue(train_res["ewc_protected"])
            self.assertTrue(weights.is_file())

            # Session 2 (fresh instance) recalls persisted knowledge without forgetting
            v2 = MemoryVault(db_path=db, weights_path=weights)
            hits = v2.recall("RTX 3070 8GB gaming VRAM")
            self.assertTrue(any(h["id"] == f1["id"] for h in hits))
            self.assertEqual(hits[0]["topic"], "hardware")
            self.assertGreaterEqual(v2.get_summary()["facts_count"], 2)
            self.assertTrue(v2.forget(int(f1["id"])))
            self.assertEqual(v2.get_summary()["facts_count"], 1)

    def test_reclaim_memory_unloads_local_ollama_only_and_blocks_remote_hosts(self) -> None:
        called_urls = []

        def fake_http_json(url: str, payload=None, timeout: float = 1.5):
            called_urls.append((url, payload))
            if url.endswith("/api/ps"):
                return {"models": [{"name": "qwen2.5-coder:7b"}]}
            if url.endswith("/api/generate"):
                return {"done": True}
            return {}

        before_prof = SimpleNamespace(device_name="NVIDIA GeForce RTX 3070 Laptop GPU", used_vram_mb=5200, total_vram_mb=8192, power_watts=82.0)
        after_prof = SimpleNamespace(device_name="NVIDIA GeForce RTX 3070 Laptop GPU", used_vram_mb=1200, total_vram_mb=8192, power_watts=18.0)

        with patch("memoryos.memory_keeper._http_json", side_effect=fake_http_json), patch(
            "memoryos.memory_keeper.MultiGPUDetector.get_active_profile", side_effect=[before_prof, after_prof]
        ):
            rep = reclaim_memory(ollama_host="http://127.0.0.1:11434")

        self.assertEqual(rep["vram_freed_mb"], 4000)
        self.assertEqual(rep["unloaded_models"], ["qwen2.5-coder:7b"])
        self.assertTrue(any(u.endswith("/api/generate") and p.get("keep_alive") == 0 for u, p in called_urls if p))

        # Remote non-local URL must never be queried
        called_urls.clear()
        with patch("memoryos.memory_keeper._http_json", side_effect=fake_http_json), patch(
            "memoryos.memory_keeper.MultiGPUDetector.get_active_profile", return_value=after_prof
        ):
            reclaim_memory(ollama_host="https://evil.example:11434")
        self.assertEqual(called_urls, [])

    def test_energy_ledger_and_mlp_microbenchmark_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "energy.sqlite"
            vault = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "m.json")
            vault.record_energy_event("d3_skip", vram_saved_mb=16200, calls_skipped=10)
            summary = vault.get_summary()
            self.assertEqual(summary["calls_skipped"], 10)
            self.assertEqual(summary["peak_vram_saved_mb"], 16200.0)
            self.assertGreater(summary["estimated_wh_saved"], 0.0)

        # Microbenchmark: 1,000 speculative evaluations stay well under 500 us/call (safe for 144Hz game loops)
        model = SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)
        sample = {"mse_delta_norm": 0.42, "context_utilization": 0.55, "secs_since_offload": 0.50, "model_switch_rate": 0.20}
        t0 = time.perf_counter_ns()
        for _ in range(1000):
            model.predict_proba(sample)
        avg_us = (time.perf_counter_ns() - t0) / 1000.0 / 1000.0
        self.assertLess(avg_us, 500.0, f"Speculative MLP too slow for realtime frame budget: {avg_us:.2f} us")

    def test_ood_abstention_checksum_tamper_fisher_clip_and_provenance_quarantine(self) -> None:
        from memoryos.speculative_offload import MAX_FISHER_VALUE
        from memoryos.memory_keeper import run_anti_forgetting_audit

        # 1. OOD inputs abstain safely to 'digest' with zero confidence
        model = SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)
        ood_res = model.decide_with_confidence({"mse_delta_norm": 4.2, "context_utilization": 0.5, "secs_since_offload": 0.2, "model_switch_rate": 0.1})
        self.assertTrue(ood_res["ood_detected"])
        self.assertTrue(ood_res["abstained"])
        self.assertEqual(ood_res["action"], "digest")
        self.assertEqual(ood_res["confidence"], 0.0)

        # 2. Tampered checkpoint checksum is rejected loudly on load()
        task_a = _task_a_gaming_samples()
        model.fit_continual(task_a, lr=0.10, epochs=30, ewc_lambda=5.0, consolidate_after=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt = Path(tmpdir) / "signed.json"
            model.save(ckpt)
            raw = json.loads(ckpt.read_text(encoding="utf-8"))
            raw["w2"][0] = float(raw["w2"][0]) + 1.2345
            ckpt.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ValueError):
                SpeculativeOffloadModel.load(ckpt)

            # 3. Replay provenance quarantine blocks untrusted external episodes from EWC training
            db = Path(tmpdir) / "quarantine.sqlite"
            v = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "q_weights.json")
            v.record_episode(task_a[0][0], 0.0, source="quarantined_external")
            res_empty = v.train_continual_model(seed_defaults=False)
            self.assertFalse(res_empty["trained"])

        # 4. Repeated consolidation cannot cause Fisher inflation plastic lock (> MAX_FISHER_VALUE)
        stress = _blank_model()
        for _ in range(40):
            stress.consolidate_memory(task_a, max_fisher=MAX_FISHER_VALUE)
        st = stress.export_ewc_state()
        max_f = max(max(row) for row in st["fisher_w1"])
        self.assertLessEqual(max_f, MAX_FISHER_VALUE)

        # 5. Multi-task A->B->C staleness & retention audit passes cleanly
        audit = run_anti_forgetting_audit()
        self.assertTrue(audit["passed"])
        self.assertGreaterEqual(audit["ewc_task_a_after_abc"], 0.90)
        self.assertLessEqual(audit["max_fisher_observed"], MAX_FISHER_VALUE)

    def test_corrupted_continual_checkpoint_quarantined_and_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "recover.sqlite"
            bad_ckpt = Path(tmpdir) / "continual.json"
            bad_ckpt.write_text('{"w1": [], "checksum_sha256": "deadbeef"}', encoding="utf-8")

            vault = MemoryVault(db_path=db, weights_path=bad_ckpt)
            recovered = vault._load_or_init_model()
            self.assertIsNotNone(recovered)
            self.assertFalse(bad_ckpt.exists())
            self.assertTrue(bad_ckpt.with_suffix(".json.corrupt").is_file())

    def test_cli_pin_subcommand_persists_fact(self) -> None:
        from unittest import mock
        from memoryos import memory_keeper as mk

        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "pin_cli.sqlite"
            ckpt = Path(tmpdir) / "pin_weights.json"
            with mock.patch.object(mk, "MemoryVault", lambda: MemoryVault(db_path=db, weights_path=ckpt)):
                rc = mk.main([
                    "pin",
                    "Gemma is a family of lightweight, state-of-the-art open models from Google.",
                    "--topic",
                    "models",
                ])
            self.assertEqual(rc, 0)
            v = MemoryVault(db_path=db, weights_path=ckpt)
            recalled = v.recall("Gemma", limit=3)
            self.assertEqual(len(recalled), 1)
            self.assertEqual(recalled[0]["topic"], "models")
            self.assertIn("Gemma is a family", recalled[0]["content"])

    def test_memory_vault_lexical_ranking_and_importance(self) -> None:
        """Recall scores higher importance and exact lexical overlap at the top."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "rank.sqlite"
            v = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "w.json")
            v.remember("hardware", "NVIDIA RTX 3070 8GB GDDR6", importance=1.0)
            v.remember("hardware", "NVIDIA RTX 3070 Mobile Laptop VRAM constraint", importance=3.5)
            v.remember("hardware", "Apple Silicon M2 unified RAM", importance=1.0)

            results = v.recall("RTX 3070 VRAM", limit=3)
            self.assertGreaterEqual(len(results), 2)
            self.assertEqual(results[0]["importance"], 3.5)
            self.assertIn("Mobile Laptop", results[0]["content"])

    def test_memory_vault_topic_and_content_truncation_safety(self) -> None:
        """Topic clamped to 80 chars, content to 4000 chars, empty content rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "trunc.sqlite"
            v = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "w.json")
            f = v.remember("T" * 200, "C" * 8000, importance=10.0)
            self.assertLessEqual(len(f["topic"]), 80)
            self.assertLessEqual(len(f["content"]), 4000)
            self.assertEqual(f["importance"], 5.0)

            with self.assertRaises(ValueError):
                v.remember("topic", "")

    def test_memory_vault_energy_ledger_aggregation(self) -> None:
        """Energy savings ledger aggregates peak VRAM, skipped calls, and Wh saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "energy_agg.sqlite"
            v = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "w.json")
            v.record_energy_event("vram_reclaim", vram_reclaimed_mb=2048.0, calls_skipped=5, power_delta_w=150.0, duration_s=2.0)
            v.record_energy_event("d3_skip", vram_saved_mb=8192.0, calls_skipped=5)
            s = v.get_summary()
            self.assertEqual(s["calls_skipped"], 10)
            self.assertEqual(s["peak_vram_saved_mb"], 8192.0)
            self.assertEqual(s["total_vram_reclaimed_mb"], 2048.0)
            self.assertGreater(s["estimated_wh_saved"], 0.0)

    def test_memory_vault_forget_nonexistent_and_duplicate_fact(self) -> None:
        """Forgetting non-existent id returns False; duplicate updates existing record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "forget.sqlite"
            v = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "w.json")
            self.assertFalse(v.forget(9999))

            v.remember("rule", "Never commit .env secrets", importance=1.0)
            self.assertEqual(len(v.list_facts()), 1)
            # Re-remembering same content updates rather than duplicating
            v.remember("rule", "Never commit .env secrets", tags="security", importance=2.0)
            self.assertEqual(len(v.list_facts()), 1)
            self.assertEqual(v.list_facts()[0]["importance"], 2.0)
            self.assertIn("security", v.list_facts()[0]["tags"])

    def test_memory_vault_concurrent_reads_and_writes(self) -> None:
        """Concurrent threads reading and writing under SQLite WAL mode succeed cleanly."""
        import concurrent.futures

        with tempfile.TemporaryDirectory() as tmpdir:
            db = Path(tmpdir) / "concurrent.sqlite"
            v = MemoryVault(db_path=db, weights_path=Path(tmpdir) / "w.json")

            def worker(tid: int):
                v.remember(f"topic-{tid % 3}", f"Fact content from thread {tid}", importance=1.0)
                recalled = v.recall(f"thread {tid}", limit=5)
                v.record_energy_event("skip", calls_skipped=1)
                return len(recalled) >= 1

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                results = list(ex.map(worker, range(16)))
            self.assertTrue(all(results))
            self.assertEqual(v.get_summary()["facts_count"], 16)


if __name__ == "__main__":
    unittest.main()
