"""Unit and live HTTP tests for the Personal AI Operations Console (src/memoryos/ops_console.py)."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.request import Request, urlopen

import apps.jupiter_studio as jupiter_studio
from src.memoryos.ops_console import OperationsLedger, OperationsPlanner


class TestOperationsConsoleUnit(unittest.TestCase):
    def test_vram_tight_protects_local_silicon_and_offloads_to_cloud(self) -> None:
        plan = OperationsPlanner.plan_objective(
            "Fix the race condition in router.py and add unit tests",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 1200, "utilization_pct": 88.0, "temperature_c": 81.0},
            models_info={
                "providers": {
                    "groq": {"ready": True},
                    "cloud": {"ready": True},
                    "ollama": {"ready": True},
                    "lemonade": {"ready": True},
                    "studio": {"ready": True},
                },
                "ollama_installed": ["qwen2.5-coder:7b"],
                "lemonade_installed": ["Qwen3.5-4B-GGUF"],
            },
            frank_prediction={"intent": "fast_code", "confidence": 0.94},
        )
        self.assertEqual(plan.intent, "fast_code")
        self.assertEqual(plan.primary_target, "groq:llama-3.3-70b-versatile")
        self.assertEqual(plan.hardware_guard, "protect_local_silicon_offload_cloud")
        self.assertIn("skip_local_heavy_weights_vram_tight", plan.preflight_actions)
        self.assertIn("thermal_offload_guard_active", plan.preflight_actions)
        self.assertNotIn("ollama:qwen2.5-coder:7b", plan.fallback_chain)

    def test_offline_mode_falls_back_to_installed_local_or_frank(self) -> None:
        plan = OperationsPlanner.plan_objective(
            "Summarize this module",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 6400, "utilization_pct": 10.0},
            models_info={
                "providers": {
                    "cloud": {"ready": False},
                    "groq": {"ready": False},
                    "lemonade": {"ready": True},
                    "ollama": {"ready": True},
                    "studio": {"ready": True},
                },
                "ollama_installed": ["frank:latest", "qwen2.5-coder:7b"],
                "lemonade_installed": ["Bonsai-4B-gguf"],
            },
            frank_prediction={"intent": "cheap_bg", "confidence": 0.89},
        )
        self.assertEqual(plan.primary_target, "lemonade:Bonsai-4B-gguf")
        self.assertIn("ollama:qwen2.5-coder:7b", plan.fallback_chain)
        self.assertIn("studio:frank", plan.fallback_chain)

    def test_vram_reclaim_objective_adds_preflight_and_uses_zero_vram_frank(self) -> None:
        plan = OperationsPlanner.plan_objective(
            "Free VRAM and unload idle models before gaming",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 2000, "utilization_pct": 60.0},
            models_info={"providers": {"studio": {"ready": True}}},
            frank_prediction={"intent": "vram_reclaim", "confidence": 0.97},
        )
        self.assertEqual(plan.primary_target, "studio:frank")
        self.assertIn("reclaim_vram_and_ram", plan.preflight_actions)

    def test_low_confidence_ood_prompt_does_not_hijack_to_static_frank(self) -> None:
        plan = OperationsPlanner.plan_objective(
            "https://www.mlh.com/events/prizes",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 6400, "utilization_pct": 12.0},
            models_info={"providers": {"cloud": {"ready": True}, "studio": {"ready": True}}},
            frank_prediction={"intent": "vram_reclaim", "confidence": 0.272},
        )
        self.assertEqual(plan.intent, "architecture")
        self.assertNotEqual(plan.primary_target, "studio:frank")
        self.assertNotIn("reclaim_vram_and_ram", plan.preflight_actions)

        plan2 = OperationsPlanner.plan_objective(
            "frank give me a suggestion that this app may work with that link",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 6400, "utilization_pct": 12.0},
            models_info={"providers": {"cloud": {"ready": True}, "studio": {"ready": True}}},
            frank_prediction={"intent": "memory_pin", "confidence": 0.308},
        )
        self.assertEqual(plan2.intent, "architecture")
        self.assertNotEqual(plan2.primary_target, "studio:frank")

    def test_vault_pinned_token_prioritizes_cached_local_or_cloud_offload(self) -> None:
        gemma_fact = [{
            "topic": "pinned",
            "content": "Gemma is a family of lightweight, state-of-the-art open models from Google.",
            "tags": "gemma,models",
        }]
        # 1. Healthy local silicon + locally cached Gemma in Lemonade -> routes directly to Lemonade
        plan_local = OperationsPlanner.plan_objective(
            "Compare Gemma architecture against Qwen for local inference",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 6400, "utilization_pct": 15.0, "temperature_c": 52.0},
            models_info={
                "providers": {"cloud": {"ready": True}, "lemonade": {"ready": True}, "ollama": {"ready": True}, "studio": {"ready": True}},
                "lemonade_installed": ["Gemma-4-E2B-it-GGUF"],
                "ollama_installed": ["gemma4:12b"],
            },
            frank_prediction={"intent": "architecture", "confidence": 0.85},
            vault_facts=gemma_fact,
        )
        self.assertEqual(plan_local.primary_target, "lemonade:Gemma-4-E2B-it-GGUF")
        self.assertIn("vault_priority_token:gemma", plan_local.preflight_actions)
        self.assertIn("gemma", plan_local.rationale.lower())

        # 2. Hot/tight local VRAM -> protects GPU (0 MB local VRAM) and offloads to cloud:Gemma-4-31B-IT
        plan_cloud = OperationsPlanner.plan_objective(
            "Compare Gemma architecture against Qwen for local inference",
            gpu_profile={"total_vram_mb": 8192, "free_vram_mb": 1100, "utilization_pct": 88.0, "temperature_c": 82.0},
            models_info={
                "providers": {"cloud": {"ready": True}, "lemonade": {"ready": True}, "ollama": {"ready": True}, "studio": {"ready": True}},
                "lemonade_installed": ["Gemma-4-E2B-it-GGUF"],
                "ollama_installed": ["gemma4:12b"],
            },
            frank_prediction={"intent": "architecture", "confidence": 0.85},
            vault_facts=gemma_fact,
        )
        self.assertEqual(plan_cloud.primary_target, "cloud:Gemma-4-31B-IT")
        self.assertIn("vault_priority_token:gemma", plan_cloud.preflight_actions)
        self.assertEqual(plan_cloud.hardware_guard, "protect_local_silicon_offload_cloud")

    def test_operations_ledger_persists_runs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "ops_test.sqlite"
            ledger = OperationsLedger(db)
            plan = OperationsPlanner.plan_objective(
                "Audit architecture",
                models_info={"providers": {"cloud": {"ready": True}, "studio": {"ready": True}}},
                frank_prediction={"intent": "architecture", "confidence": 0.91},
            )
            ledger.record_run(plan, executed_target=plan.primary_target, status="completed", latency_ms=14.2)
            rows = ledger.list_recent(limit=5)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["op_id"], plan.op_id)
            self.assertEqual(rows[0]["executed_target"], "cloud:DeepSeek-V4.1-Flash")
            self.assertEqual(rows[0]["status"], "completed")


class TestOperationsConsoleHTTP(unittest.TestCase):
    def test_ops_plan_dispatch_and_ledger_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp_db = Path(td) / "studio_ops_http.sqlite"
            with mock.patch.object(jupiter_studio, "_get_studio_db_path", return_value=temp_db):
                srv = ThreadingHTTPServer(("127.0.0.1", 0), jupiter_studio.JupiterStudioHandler)
                port = srv.server_address[1]
                th = threading.Thread(target=srv.serve_forever, daemon=True)
                th.start()
                try:
                    base = f"http://127.0.0.1:{port}"
                    headers = {"Content-Type": "application/json", "Origin": base}

                    # 1. Plan an objective
                    req = Request(
                        f"{base}/api/ops/plan",
                        data=json.dumps({"objective": "Audit architecture bottlenecks"}).encode("utf-8"),
                        headers=headers,
                        method="POST",
                    )
                    with urlopen(req, timeout=5) as resp:
                        plan = json.loads(resp.read().decode("utf-8"))
                    self.assertIn("primary_target", plan)
                    self.assertIn("fallback_chain", plan)
                    self.assertTrue(plan["op_id"].startswith("op-"))

                    # 2. Dispatch objective (dry_run=True to avoid side effects)
                    req2 = Request(
                        f"{base}/api/ops/dispatch",
                        data=json.dumps({"objective": "Audit architecture bottlenecks", "dry_run": True}).encode("utf-8"),
                        headers=headers,
                        method="POST",
                    )
                    with urlopen(req2, timeout=5) as resp:
                        dispatched = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(dispatched["status"], "planned")
                    self.assertIn("DRY-RUN PLAN", dispatched["content"])

                    # 3. Verify Operations Ledger recorded the run
                    with urlopen(f"{base}/api/ops/ledger", timeout=5) as resp:
                        ledger_data = json.loads(resp.read().decode("utf-8"))
                    self.assertGreaterEqual(len(ledger_data["runs"]), 1)
                    self.assertEqual(ledger_data["runs"][0]["status"], "planned")
                finally:
                    srv.shutdown()
                    srv.server_close()


if __name__ == "__main__":
    unittest.main()
