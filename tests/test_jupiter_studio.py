"""Unit tests for Jupiter Studio endpoints and workspace integration."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.jupiter_studio import JupiterStudioHandler


class DummyRequest:
    def __init__(self, body: bytes = b""):
        self.body = body

    def makefile(self, *args, **kwargs):
        import io
        return io.BytesIO(self.body)


class TestJupiterStudioHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = JupiterStudioHandler.__new__(JupiterStudioHandler)
        self.handler.headers = {}
        self.handler.wfile = MagicMock()
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def test_resolve_target_auto_d3(self) -> None:
        with patch.dict(os.environ, {"TOKENLAB_API_KEY": "test-ci-tokenlab-key"}):
            model, provider, is_local = self.handler._resolve_target("auto:d3", "Write a Python script", False)
        self.assertFalse(is_local)
        self.assertIn("AMD Token Lab", provider)

    def test_resolve_target_ollama(self) -> None:
        model, provider, is_local = self.handler._resolve_target("ollama:qwen2.5-coder:7b", "Hi", False)
        self.assertEqual(model, "qwen2.5-coder:7b")
        self.assertTrue(is_local)
        self.assertEqual(provider, "Local Ollama")

    def test_workspace_files_endpoint(self) -> None:
        self.handler.path = "/api/workspace/files"
        sent_data = {}

        def fake_send_json(data, status=200):
            nonlocal sent_data
            sent_data = data

        self.handler._send_json = fake_send_json
        self.handler.do_GET()

        self.assertIn("files", sent_data)
        self.assertIn("repo_root", sent_data)
        self.assertTrue(len(sent_data["files"]) > 0)

    def test_resolve_target_local_vllm_and_nvidia_flare(self) -> None:
        model, provider, is_local = self.handler._resolve_target("vllm:Qwen/Qwen3.8-Flash-Next", "Hi", False)
        self.assertEqual(model, "Qwen/Qwen3.8-Flash-Next")
        self.assertEqual(provider, "Local vLLM (Spark)")
        self.assertFalse(is_local)

        model, provider, is_local = self.handler._resolve_target("flare:DeepSeek-V4.1-Flash", "Hi", False)
        self.assertEqual(model, "DeepSeek-V4.1-Flash")
        self.assertEqual(provider, "NVIDIA Flare (Spark)")
        self.assertFalse(is_local)

    def test_call_cloud_direct_local_vllm_and_flare_no_api_key_required(self) -> None:
        captured_reqs = []

        class FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "ok from spark"}}]}).encode("utf-8")

        def fake_urlopen(req, timeout=45.0):
            captured_reqs.append(req)
            return FakeResp()

        with patch.dict(
            os.environ,
            {
                "LOCAL_VLLM_BASE_URL": "http://127.0.0.1:8000/v1",
                "LOCAL_VLLM_API_KEY": "EMPTY",
                "NVIDIA_FLARE_BASE_URL": "http://127.0.0.1:8080/v1",
                "NVIDIA_FLARE_API_KEY": "EMPTY",
            },
        ), patch("apps.jupiter_studio.urllib.request.urlopen", side_effect=fake_urlopen):
            c1, e1 = self.handler._call_cloud_direct("Local vLLM (Spark)", "Qwen/Qwen3.8-Flash-Next", "ping")
            c2, e2 = self.handler._call_cloud_direct("NVIDIA Flare (Spark)", "DeepSeek-V4.1-Flash", "ping")

        self.assertEqual((c1, e1), ("ok from spark", ""))
        self.assertEqual((c2, e2), ("ok from spark", ""))
        self.assertEqual(captured_reqs[0].full_url, "http://127.0.0.1:8000/v1/chat/completions")
        self.assertEqual(captured_reqs[1].full_url, "http://127.0.0.1:8080/v1/chat/completions")
        self.assertNotIn("Authorization", captured_reqs[0].headers)
        self.assertNotIn("Authorization", captured_reqs[1].headers)

    def test_format_uploaded_files_and_truncation(self) -> None:
        formatted = self.handler._format_uploaded_files(
            [
                {"name": "notes.py", "size": 24, "content": "print('hello studio')"},
                {"name": "big.log", "size": 500, "content": "A" * 500},
            ],
            max_chars_per_file=50,
            max_total_chars=80,
        )
        self.assertIn("#### notes.py", formatted)
        self.assertIn("print('hello studio')", formatted)
        self.assertIn("#### big.log", formatted)
        self.assertIn("... [truncated]", formatted)


if __name__ == "__main__":
    unittest.main()
