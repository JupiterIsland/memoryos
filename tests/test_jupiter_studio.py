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


if __name__ == "__main__":
    unittest.main()
