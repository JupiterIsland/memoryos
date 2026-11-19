"""Unit tests for The Quiet Advisor detectors, thermal guard, health score, and SQL safety."""

import asyncio
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quiet_advisor_detectors import (
    AnomalyDetector,
    ContextWasteDetector,
    DetectedInsight,
    DetectorType,
    InferenceLog,
    QuietAdvisorEngine,
    ThermalThrottlingDetector,
    VRAMThrashingDetector,
    compute_workstation_health,
    ingest_tokenlab_export,
)
from quiet_advisor_scheduler import CardActionHandler, CardDisplayService, QuietAdvisorScheduler
from src.memoryos.quiet_advisor_db import QuietAdvisorDB


def _make_inference(**overrides) -> InferenceLog:
    base = {
        "timestamp": datetime.utcnow(),
        "model_id": "Gemma-4-31B-IT",
        "context_tokens_provided": 4096,
        "context_tokens_used": 2800,
        "time_to_first_token_ms": 120.0,
        "total_latency_ms": 500.0,
        "tokens_per_second": 60.0,
        "gpu_utilization_percent": 30.0,
        "gpu_temperature_celsius": 55.0,
        "gpu_memory_used_mb": 1200,
        "output_quality_score": 0.92,
        "error_flag": False,
        "error_message": None,
    }
    base.update(overrides)
    return InferenceLog(**base)


class TestQuietAdvisorDetectors(unittest.TestCase):
    def test_detected_insight_suggested_experiments_default_factory(self):
        a = DetectedInsight(
            detector_type=DetectorType.CONTEXT_WASTE,
            title="A",
            subtitle="sub",
            description="desc",
            metrics={},
            recommended_action="act",
            action_value={},
        )
        b = DetectedInsight(
            detector_type=DetectorType.CONTEXT_WASTE,
            title="B",
            subtitle="sub",
            description="desc",
            metrics={},
            recommended_action="act",
            action_value={},
        )
        self.assertEqual(a.suggested_experiments, [])
        a.suggested_experiments.append("exp_1")
        self.assertEqual(b.suggested_experiments, [])

    def test_context_waste_respects_min_samples_and_zero_division(self):
        # 3 inferences must NOT trigger (requires >= 5)
        small = [_make_inference(context_tokens_provided=8192, context_tokens_used=200) for _ in range(3)]
        self.assertIsNone(ContextWasteDetector.detect(small))

        # 5 inferences with 0 tokens used must not raise ZeroDivisionError
        zero_used = [_make_inference(context_tokens_provided=8192, context_tokens_used=0) for _ in range(5)]
        insight = ContextWasteDetector.detect(zero_used)
        self.assertIsNotNone(insight)
        self.assertEqual(insight.detector_type, DetectorType.CONTEXT_WASTE)
        self.assertGreaterEqual(insight.action_value["context_tokens"], 1)

    def test_anomaly_detector_handles_zero_variance(self):
        identical = [_make_inference(total_latency_ms=400.0) for _ in range(12)]
        self.assertIsNone(AnomalyDetector.detect(identical))

        with_spike = [_make_inference(total_latency_ms=400.0) for _ in range(11)]
        with_spike.append(_make_inference(total_latency_ms=5000.0))
        insight = AnomalyDetector.detect(with_spike)
        self.assertIsNotNone(insight)
        self.assertEqual(insight.detector_type, DetectorType.ANOMALY_DETECTION)

    def test_vram_thrashing_detector(self):
        low = [_make_inference(gpu_memory_used_mb=1000, gpu_utilization_percent=20.0) for _ in range(5)]
        self.assertIsNone(VRAMThrashingDetector.detect(low))

        high = [_make_inference(gpu_memory_used_mb=6800, gpu_utilization_percent=91.0) for _ in range(3)]
        insight = VRAMThrashingDetector.detect(high)
        self.assertIsNotNone(insight)
        self.assertEqual(insight.detector_type, DetectorType.VRAM_THRASHING)
        self.assertEqual(insight.recommended_action, "force_tokenlab_offload")

    def test_thermal_throttling_detector(self):
        cool = [_make_inference(gpu_temperature_celsius=58.0, tokens_per_second=70.0) for _ in range(5)]
        self.assertIsNone(ThermalThrottlingDetector.detect(cool))

        mixed = [
            _make_inference(gpu_temperature_celsius=58.0, tokens_per_second=75.0),
            _make_inference(gpu_temperature_celsius=60.0, tokens_per_second=75.0),
            _make_inference(gpu_temperature_celsius=84.0, tokens_per_second=45.0),
            _make_inference(gpu_temperature_celsius=87.0, tokens_per_second=42.0),
            _make_inference(gpu_temperature_celsius=89.0, tokens_per_second=40.0),
        ]
        insight = ThermalThrottlingDetector.detect(mixed)
        self.assertIsNotNone(insight)
        self.assertEqual(insight.detector_type, DetectorType.THERMAL_THROTTLING)
        self.assertEqual(insight.recommended_action, "force_tokenlab_offload")
        self.assertEqual(insight.action_value["peak_temp_c"], 89.0)
        self.assertIn("throughput drop", insight.subtitle)

    def test_workstation_health_score(self):
        idle = compute_workstation_health([])
        self.assertEqual(idle["score"], 100)
        self.assertEqual(idle["grade"], "A")

        healthy = [
            _make_inference(
                gpu_memory_used_mb=0,
                gpu_temperature_celsius=45.0,
                context_tokens_provided=4096,
                context_tokens_used=3800,
                error_flag=False,
            )
            for _ in range(5)
        ]
        h_res = QuietAdvisorEngine.compute_workstation_health(healthy)
        self.assertGreaterEqual(h_res["score"], 95)
        self.assertEqual(h_res["grade"], "A")

        stressed = [
            _make_inference(
                gpu_memory_used_mb=7900,
                gpu_temperature_celsius=92.0,
                context_tokens_provided=8192,
                context_tokens_used=400,
                error_flag=True,
            )
            for _ in range(5)
        ]
        s_res = QuietAdvisorEngine.compute_workstation_health(stressed)
        self.assertLess(s_res["score"], 40)
        self.assertEqual(s_res["grade"], "F")
        self.assertEqual(s_res["status"], "critical")

    def test_ingest_tokenlab_export_atomic_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite"
            export_path = Path(tmp) / "export.json"
            export_payload = {
                "export_date": "2026-11-19",
                "user_profile": {"user_id": "tester-1"},
                "tokenlab": {
                    "account": {
                        "user_id": "tester-1",
                        "status": "active",
                        "grant_state": "active",
                        "budget_micro": 10000000,
                        "budget_used_micro": 78,
                        "expires_at": "2026-12-19",
                    },
                    "keys": [{"key_prefix": "tl_test", "status": "active"}],
                    "usage_totals": {"requests": 2, "errors": 0, "tokens": 512},
                    "usage_daily": [{"model": "Gemma-4-31B-IT", "cached_tokens": 120, "reasoning_tokens": 64}],
                    "requests": [
                        {"model": "Gemma-4-31B-IT", "prompt_tokens": 128, "completion_tokens": 128, "has_error": False},
                        {"model": "d3", "prompt_tokens": 64, "completion_tokens": 16, "has_error": False},
                    ],
                },
            }
            export_path.write_text(json.dumps(export_payload), encoding="utf-8")

            db = QuietAdvisorDB(db_path)
            try:
                first = ingest_tokenlab_export(db, export_path=export_path)
                self.assertFalse(first["skipped"])
                self.assertEqual(first["ingested_requests"], 2)
                self.assertGreaterEqual(first["ingested_cards"], 1)

                second = ingest_tokenlab_export(db, export_path=export_path)
                self.assertTrue(second["skipped"])
                self.assertEqual(second["ingested_requests"], 0)
                self.assertEqual(second["ingested_cards"], 0)

                total_rows = db.conn.execute("SELECT COUNT(*) FROM memoryos_inference_log").fetchone()[0]
                self.assertEqual(total_rows, 2)
            finally:
                db.close()

    def test_scheduler_and_action_handler_sql_injection_safety(self):
        async def _run():
            with tempfile.TemporaryDirectory() as tmp:
                db = QuietAdvisorDB(Path(tmp) / "sqli.sqlite")
                try:
                    engine = QuietAdvisorEngine()
                    scheduler = QuietAdvisorScheduler(db, engine)
                    handler = CardActionHandler(db)
                    display = CardDisplayService(db)

                    hostile_user = "alice' OR '1'='1; DROP TABLE users; --"
                    now = datetime.utcnow()
                    await db.insert(
                        "memoryos.inference_log",
                        {
                            "user_id": "bob",
                            "session_id": "s1",
                            "timestamp": now.isoformat(),
                            "model_id": "Gemma-4-31B-IT",
                            "context_tokens_provided": 4096,
                            "context_tokens_used": 1000,
                            "time_to_first_token_ms": 100.0,
                            "total_latency_ms": 400.0,
                            "tokens_per_second": 60.0,
                            "gpu_id": "tokenlab-remote",
                            "gpu_utilization_percent": 0.0,
                            "gpu_temperature_celsius": 50.0,
                            "gpu_memory_used_mb": 0,
                        },
                    )
                    card_id = await db.insert(
                        "quiet_advisor.cards",
                        {
                            "user_id": "bob",
                            "detector_type": "thermal_throttling",
                            "insight_rank": 0.9,
                            "title": "Thermal Test",
                            "subtitle": "Sub",
                            "description": "Desc",
                            "recommended_action": "force_tokenlab_offload",
                            "action_value": json.dumps({"thermal_penalty": 1.4, "forced_model": "Gemma-4-31B-IT"}),
                            "user_dismissed": False,
                            "user_archived": False,
                            "user_actioned": False,
                            "created_at": now.isoformat(),
                            "expires_at": (now + timedelta(days=7)).isoformat(),
                        },
                    )

                    # Hostile user_id must NOT leak bob's inferences or cards or drop tables
                    leaked_infs = await scheduler._get_user_inferences(
                        hostile_user, now - timedelta(hours=1), window_hours=2
                    )
                    self.assertEqual(leaked_infs, [])
                    self.assertIsNone(await display.get_card_for_user(hostile_user))
                    self.assertEqual(await display.get_card_archive(hostile_user), [])

                    # Hostile card_id must NOT mutate bob's card
                    await handler.handle_action("bob", f"{card_id} OR 1=1", "dismiss")
                    row = await db.query_one("SELECT user_dismissed FROM quiet_advisor.cards WHERE id = ?", (card_id,))
                    self.assertEqual(row["user_dismissed"], 0)

                    # Legitimate acknowledge updates bob's card and writes unified preferences
                    await handler.handle_action("bob", str(card_id), "acknowledge")
                    prefs = await scheduler._get_user_preferences("bob")
                    self.assertTrue(prefs.get("force_remote_offload"))
                    self.assertEqual(prefs.get("vram_thrashing_penalty"), 1.4)
                finally:
                    db.close()

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main(verbosity=2)
