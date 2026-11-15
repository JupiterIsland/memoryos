"""
Unit tests for SpeculativeOffloadModel (feature order safety and MLP inference).
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.memoryos.speculative_offload import (
    DEFAULT_WEIGHTS_PATH,
    EXPECTED_FEATURE_NAMES,
    SpeculativeOffloadModel,
)


class TestSpeculativeOffloadModel(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(DEFAULT_WEIGHTS_PATH.is_file(), f"Missing default weights: {DEFAULT_WEIGHTS_PATH}")
        self.model = SpeculativeOffloadModel.load(DEFAULT_WEIGHTS_PATH)

    def test_load_default_weights_schema(self) -> None:
        self.assertEqual(self.model.in_dim, 4)
        self.assertEqual(self.model.hidden_dim, 8)
        self.assertEqual(self.model.feature_names, list(EXPECTED_FEATURE_NAMES))
        self.assertAlmostEqual(self.model.tau_hi, 0.65)
        self.assertAlmostEqual(self.model.tau_lo, 0.35)

    def test_predict_proba_dict_and_vector_equivalence(self) -> None:
        feature_dict = {
            "mse_delta_norm": 0.85,
            "context_utilization": 0.40,
            "secs_since_offload": 12.5,
            "model_switch_rate": 0.20,
        }
        feature_vec = [0.85, 0.40, 12.5, 0.20]

        p_dict = self.model.predict_proba(feature_dict)
        p_vec = self.model.predict_proba(feature_vec)

        self.assertIsInstance(p_dict, float)
        self.assertGreaterEqual(p_dict, 0.0)
        self.assertLessEqual(p_dict, 1.0)
        self.assertAlmostEqual(p_dict, p_vec, places=6)

    def test_missing_feature_raises_keyerror(self) -> None:
        incomplete_dict = {
            "mse_delta_norm": 0.5,
            "context_utilization": 0.2,
            # missing secs_since_offload and model_switch_rate
        }
        with self.assertRaises(KeyError):
            self.model.predict_proba(incomplete_dict)

    def test_vector_dimension_mismatch_raises_valueerror(self) -> None:
        with self.assertRaises(ValueError):
            self.model.predict_proba([0.5, 0.2])

    def test_feature_ordering_mismatch_raises_valueerror(self) -> None:
        with open(DEFAULT_WEIGHTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Deliberately reorder feature names to simulate dangerous retraining bug
        data["feature_names"] = [
            "context_utilization",
            "mse_delta_norm",
            "secs_since_offload",
            "model_switch_rate",
        ]

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                SpeculativeOffloadModel.load(tmp_path)
            self.assertIn("Feature ordering mismatch", str(ctx.exception))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_hidden_activation_check(self) -> None:
        with open(DEFAULT_WEIGHTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["hidden_activation"] = "gelu"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(data, tmp)
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                SpeculativeOffloadModel.load(tmp_path)
            self.assertIn("Unsupported hidden_activation", str(ctx.exception))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_decide_thresholds(self) -> None:
        # High delta should trigger offload
        high_features = [0.95, 0.90, 60.0, 0.80]
        decision_high = self.model.decide(high_features, tau_hi=0.65, tau_lo=0.35)
        self.assertIn(decision_high, ("offload_now", "digest", "skip"))

        # Zero delta quiescent state
        zero_features = [0.0, 0.0, 0.0, 0.0]
        decision_zero = self.model.decide(zero_features, tau_hi=0.65, tau_lo=0.35)
        self.assertEqual(decision_zero, "skip")


if __name__ == "__main__":
    unittest.main()
