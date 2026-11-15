"""Unit tests for NVIDIA NIM / Brev OpenAI-compatible routing in router.py."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.memoryos import router


class TestNvidiaBrevRouter(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_cloud_status_reports_nvidia_brev_credentials(self) -> None:
        os.environ["NVIDIA_API_KEY"] = "nvapi-test-key"
        os.environ["NVIDIA_BASE_URL"] = "https://brev.example.invalid/v1/"
        os.environ["BREV_ORG_ID"] = "org-test-123"

        status = router.get_cloud_provider_status()["nvidia_brev"]
        self.assertTrue(status["configured"])
        self.assertEqual(status["base_url"], "https://brev.example.invalid/v1")
        self.assertEqual(status["brev_org_id"], "org-test-123")

    def test_route_task_direct_nvidia_provider(self) -> None:
        os.environ["NVIDIA_API_KEY"] = "nvapi-test-key"
        os.environ["NVIDIA_BASE_URL"] = "https://integrate.api.nvidia.com/v1"

        with (
            patch.object(router, "select_model_with_d3", return_value={"selected_tier": "balanced_code", "selected_model": "Qwen3.8-27B"}),
            patch.object(router, "_invoke_remote_chat", return_value=("NVIDIA OK", {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12})) as remote_mock,
        ):
            res = router.route_task(
                "Ping NVIDIA",
                cloud_provider="nvidia",
                save_checkpoint=False,
                log_to_advisor=False,
            )

        self.assertEqual(res["gpu_id"], "nvidia-brev-remote")
        self.assertEqual(res["routing_policy"], "nvidia_brev_direct")
        self.assertEqual(res["model"], "qwen/qwen2.5-coder-32b-instruct")
        self.assertEqual(res["content"], "NVIDIA OK")
        self.assertFalse(res["error_flag"])
        self.assertEqual(remote_mock.call_args.kwargs["base_url"], "https://integrate.api.nvidia.com/v1")
        self.assertEqual(remote_mock.call_args.kwargs["api_key"], "nvapi-test-key")

    def test_route_task_fails_over_from_tokenlab_to_nvidia(self) -> None:
        os.environ["TOKENLAB_API_KEY"] = "tl-test-key"
        os.environ["NVIDIA_API_KEY"] = "nvapi-test-key"
        os.environ["DO_MODEL_ACCESS_KEY"] = ""
        os.environ["DIGITALOCEAN_INFERENCE_KEY"] = ""

        with (
            patch.object(router, "select_model_with_d3", return_value={"selected_tier": "fast_light", "selected_model": "MiniCPM5-2B"}),
            patch.object(router, "_invoke_tokenlab_chat", side_effect=RuntimeError("429 busy")),
            patch.object(router, "_invoke_remote_chat", return_value=("FAILOVER OK", {"prompt_tokens": 8, "completion_tokens": 2, "total_tokens": 10})),
        ):
            res = router.route_task(
                "Hi",
                save_checkpoint=False,
                log_to_advisor=False,
            )

        self.assertEqual(res["gpu_id"], "nvidia-brev-remote")
        self.assertEqual(res["routing_policy"], "nvidia_brev_failover")
        self.assertEqual(res["model"], "qwen/qwen2.5-7b-instruct")
        self.assertEqual(res["content"], "FAILOVER OK")
        self.assertFalse(res["error_flag"])


if __name__ == "__main__":
    unittest.main()
