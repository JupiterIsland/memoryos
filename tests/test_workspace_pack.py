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

    def test_blocks_symlink_to_env_and_external_file(self) -> None:
        outside_dir = tempfile.TemporaryDirectory()
        try:
            outside_secret = Path(outside_dir.name) / "outside_secret.txt"
            outside_secret.write_text("TOP_SECRET_OUTSIDE", encoding="utf-8")

            link_to_env = self.root / "innocent_env.txt"
            link_to_outside = self.root / "innocent_outside.txt"
            try:
                link_to_env.symlink_to(self.root / ".env")
                link_to_outside.symlink_to(outside_secret)
            except OSError:
                self.skipTest("Symlinks not supported in this filesystem")

            scanned = [f["rel_path"] for f in workspace_pack.scan_workspace_files(self.root)]
            self.assertNotIn("innocent_env.txt", scanned)
            self.assertNotIn("innocent_outside.txt", scanned)

            packed = workspace_pack.pack_workspace_context(
                self.root,
                selected_files=["innocent_env.txt", "innocent_outside.txt", "src/main.py"],
                include_git=False,
            )
            self.assertEqual(packed["packed_files"], ["src/main.py"])
            self.assertNotIn("SECRET_KEY", packed["bundle_text"])
            self.assertNotIn("TOP_SECRET_OUTSIDE", packed["bundle_text"])
        finally:
            outside_dir.cleanup()

    def test_blocks_case_insensitive_secrets_backslash_traversal_and_binary_nuls(self) -> None:
        (self.root / "credentials.json").write_text('{"api":"secret"}', encoding="utf-8")
        (self.root / "server.PEM").write_text("PRIVATE KEY", encoding="utf-8")
        (self.root / "id_rsa").write_text("SSH KEY", encoding="utf-8")
        (self.root / "binary_no_ext").write_bytes(b"\x7fELF\x00\x01\x02\x03")

        for blocked in (".ENV", r"sub\..\.env", "credentials.json", "server.PEM", "id_rsa"):
            self.assertTrue(workspace_pack.is_binary_or_ignored(blocked), f"Should ignore {blocked}")

        packed = workspace_pack.pack_workspace_context(
            self.root,
            selected_files=[
                ".ENV",
                r"src\..\.env",
                "credentials.json",
                "server.PEM",
                "id_rsa",
                "binary_no_ext",
                "../etc/passwd",
                "src/main.py\x00.txt",
                None,  # type: ignore[list-item]
                123,   # type: ignore[list-item]
                "src/main.py",
            ],
            include_git=False,
        )
        self.assertEqual(packed["packed_files"], ["src/main.py"])
        self.assertNotIn("SECRET_KEY", packed["bundle_text"])
        self.assertNotIn("PRIVATE KEY", packed["bundle_text"])
        self.assertNotIn("SSH KEY", packed["bundle_text"])

    def test_dynamic_fence_for_backticks_and_oversized_file_cap(self) -> None:
        (self.root / "GUIDE.md").write_text("Example:\n```python\nprint(1)\n```\n", encoding="utf-8")
        big_text = "x" * (workspace_pack.DEFAULT_MAX_FILE_BYTES + 10_000)
        (self.root / "huge.txt").write_text(big_text, encoding="utf-8")

        packed = workspace_pack.pack_workspace_context(
            self.root,
            selected_files=["GUIDE.md", "huge.txt"],
            include_git=False,
            max_total_chars=300_000,
        )
        self.assertIn("````md\nExample:", packed["bundle_text"])
        self.assertIn("file truncated at size limit", packed["bundle_text"])

    def test_scan_prunes_virtualenv_and_egg_info_and_reads_git_branch(self) -> None:
        venv_dir = self.root / "custom-env"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
        (venv_dir / "activate.py").write_text("x = 1", encoding="utf-8")

        egg_dir = self.root / "pkg.egg-info"
        egg_dir.mkdir()
        (egg_dir / "PKG-INFO").write_text("Name: pkg", encoding="utf-8")

        scanned = [f["rel_path"] for f in workspace_pack.scan_workspace_files(self.root)]
        self.assertFalse(any(p.startswith("custom-env/") for p in scanned))
        self.assertFalse(any(p.startswith("pkg.egg-info/") for p in scanned))

        # Pure-Python git branch reader
        self.assertEqual(workspace_pack.get_git_branch(self.root), "")
        git_dir = self.root / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/release/v1\n", encoding="utf-8")
        self.assertEqual(workspace_pack.get_git_branch(self.root), "release/v1")
        (git_dir / "HEAD").write_text("e2173ed1234567890abcdef\n", encoding="utf-8")
        self.assertEqual(workspace_pack.get_git_branch(self.root), "e2173ed12345")


if __name__ == "__main__":
    unittest.main()
