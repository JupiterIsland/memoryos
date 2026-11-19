"""Unit tests for workspace_pack.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.memoryos import workspace_pack


class TestWorkspacePack(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

        # Create mock project files
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('hello world')", encoding="utf-8")
        (self.root / "README.md").write_text("# Test Repo", encoding="utf-8")
        (self.root / ".env").write_text("SECRET_KEY=12345", encoding="utf-8")
        (self.root / ".env.example").write_text("TOKENLAB_API_KEY=your_key", encoding="utf-8")
        (self.root / ".aider.chat.history.md").write_text("huge chat log", encoding="utf-8")
        (self.root / ".clinerules").write_text("rules", encoding="utf-8")
        (self.root / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
        (self.root / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "main.cpython-310.pyc").write_bytes(b"\x00\x00")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_scan_workspace_files_excludes_ignored_and_binary(self) -> None:
        files = workspace_pack.scan_workspace_files(self.root)
        rel_paths = [f["rel_path"] for f in files]
        self.assertIn("src/main.py", rel_paths)
        self.assertIn("README.md", rel_paths)
        self.assertIn(".env.example", rel_paths)
        self.assertNotIn(".env", rel_paths)
        self.assertNotIn(".aider.chat.history.md", rel_paths)
        self.assertNotIn(".clinerules", rel_paths)
        self.assertNotIn(".gitignore", rel_paths)
        self.assertNotIn("image.png", rel_paths)
        self.assertNotIn("__pycache__/main.cpython-310.pyc", rel_paths)

    def test_pack_workspace_context(self) -> None:
        packed = workspace_pack.pack_workspace_context(
            self.root,
            selected_files=["src/main.py", "README.md"],
            include_git=False,
        )
        self.assertEqual(len(packed["packed_files"]), 2)
        self.assertIn("print('hello world')", packed["bundle_text"])
        self.assertIn("# Test Repo", packed["bundle_text"])
        self.assertNotIn("SECRET_KEY", packed["bundle_text"])

    def test_export_copilot_bundle(self) -> None:
        bundle = workspace_pack.export_copilot_bundle(
            self.root,
            user_goal="Refactor main.py",
            selected_files=["src/main.py"],
            assistant_advice="Use type hints and dataclasses.",
        )
        self.assertIn("Workspace Context Bundle for Copilot", bundle)
        self.assertIn("Refactor main.py", bundle)
        self.assertIn("Use type hints and dataclasses", bundle)
        self.assertIn("print('hello world')", bundle)
        self.assertNotIn("SECRET_KEY", bundle)


if __name__ == "__main__":
    unittest.main()
