"""Workspace scanning, packing, and Copilot context export utilities for MemoryOS & Jupiter Studio."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

IGNORED_DIRS: Set[str] = {
    ".git",
    ".github",
    ".aider",
    ".vscode",
    ".idea",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "site-packages",
}

ALLOWED_DOTFILES: Set[str] = {
    ".env.example",
}

IGNORED_FILES: Set[str] = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    "QuietAdvisorDB.sqlite",
    "QuietAdvisorDB.sqlite-journal",
    "quiet_advisor.db",
}

BINARY_EXTENSIONS: Set[str] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".bin",
    ".sqlite",
    ".db",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".mp4",
    ".mov",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}

DEFAULT_MAX_FILE_BYTES = 250_000  # 250 KB max per file
DEFAULT_MAX_BUNDLE_CHARS = 240_000  # ~60K tokens max bundle


def is_binary_or_ignored(rel_path: Path) -> bool:
    """Check if a path should be excluded from workspace context."""
    parts = set(rel_path.parts)
    if parts.intersection(IGNORED_DIRS):
        return True
    if any(p.startswith(".") and p not in {".", ".."} for p in rel_path.parts[:-1]):
        return True
    name = rel_path.name
    if name in IGNORED_FILES:
        return True
    if name.startswith(".") and name not in ALLOWED_DOTFILES:
        return True
    if rel_path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    return False


def get_git_status_and_diff(root_dir: Path, max_diff_chars: int = 15_000) -> Dict[str, str]:
    """Retrieve git branch, status --short, and diff summary for the workspace."""
    git_dir = root_dir / ".git"
    if not git_dir.exists():
        return {"branch": "", "status": "", "diff": "", "diff_stat": ""}

    def _run_git(args: List[str]) -> str:
        try:
            res = subprocess.run(
                ["git", "-C", str(root_dir)] + args,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.stdout.strip() if res.returncode == 0 else ""
        except Exception:
            return ""

    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    status = _run_git(["status", "-s"])
    diff_stat = _run_git(["diff", "--stat"])
    diff = _run_git(["diff"])

    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + f"\n... [diff truncated to {max_diff_chars} chars] ..."

    return {
        "branch": branch,
        "status": status,
        "diff_stat": diff_stat,
        "diff": diff,
    }


def scan_workspace_files(root_dir: Path, max_files: int = 250) -> List[Dict[str, Any]]:
    """Scan readable workspace files, sorted with code and configs first."""
    if not root_dir.exists() or not root_dir.is_dir():
        return []

    results: List[Dict[str, Any]] = []
    count = 0

    for root, dirs, files in os.walk(root_dir):
        # Prune ignored directories in place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        rel_root = Path(root).relative_to(root_dir)
        for fname in sorted(files):
            rel_file = rel_root / fname if str(rel_root) != "." else Path(fname)
            if is_binary_or_ignored(rel_file):
                continue

            full_file = root_dir / rel_file
            try:
                st = full_file.stat()
                results.append({
                    "rel_path": str(rel_file).replace("\\", "/"),
                    "size_bytes": st.st_size,
                    "extension": rel_file.suffix.lower(),
                })
                count += 1
                if count >= max_files:
                    return results
            except OSError:
                continue

    return results


def pack_workspace_context(
    root_dir: Path,
    selected_files: Optional[List[str]] = None,
    include_git: bool = True,
    max_total_chars: int = DEFAULT_MAX_BUNDLE_CHARS,
) -> Dict[str, Any]:
    """Pack selected workspace files and git context into a structured markdown bundle."""
    root_dir = root_dir.resolve()
    packed_blocks: List[str] = []
    packed_files: List[str] = []
    total_chars = 0

    git_info = get_git_status_and_diff(root_dir) if include_git else {}
    if git_info.get("branch") or git_info.get("diff") or git_info.get("status"):
        git_block = "## Git Repository State\n"
        if git_info.get("branch"):
            git_block += f"- **Branch**: `{git_info['branch']}`\n"
        if git_info.get("diff_stat"):
            git_block += f"### Changed Files (`git diff --stat`)\n```text\n{git_info['diff_stat']}\n```\n"
        if git_info.get("diff"):
            git_block += f"### Working Diff (`git diff`)\n```diff\n{git_info['diff']}\n```\n"
        elif git_info.get("status"):
            git_block += f"### Git Status\n```text\n{git_info['status']}\n```\n"

        packed_blocks.append(git_block)
        total_chars += len(git_block)

    target_files = selected_files or []
    # If no files specified, pick sensible default core files
    if not target_files:
        all_scanned = scan_workspace_files(root_dir, max_files=40)
        # Prioritize top-level files and src files
        target_files = [
            f["rel_path"]
            for f in all_scanned
            if f["extension"] in {".py", ".ts", ".js", ".html", ".md", ".json", ".yml", ".yaml"}
            and f["size_bytes"] < DEFAULT_MAX_FILE_BYTES
        ][:12]

    for rel_str in target_files:
        rel_path = Path(rel_str)
        if is_binary_or_ignored(rel_path):
            continue

        full_path = (root_dir / rel_path).resolve()
        # Security check: must reside inside root_dir
        try:
            full_path.relative_to(root_dir)
        except ValueError:
            continue

        if not full_path.is_file():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lang = rel_path.suffix.lstrip(".").lower() or "text"
        block = f"### File: `{rel_str}`\n```{lang}\n{content}\n```\n\n"

        if total_chars + len(block) > max_total_chars:
            allowed = max(0, max_total_chars - total_chars - 200)
            if allowed > 1000:
                truncated_content = content[:allowed]
                block = f"### File: `{rel_str}` (Truncated)\n```{lang}\n{truncated_content}\n... [file truncated] ...\n```\n\n"
                packed_blocks.append(block)
                packed_files.append(rel_str)
                total_chars += len(block)
            break

        packed_blocks.append(block)
        packed_files.append(rel_str)
        total_chars += len(block)

    bundle_text = "".join(packed_blocks)
    est_tokens = max(1, total_chars // 4)

    return {
        "root_dir": str(root_dir),
        "packed_files": packed_files,
        "total_chars": total_chars,
        "estimated_tokens": est_tokens,
        "bundle_text": bundle_text,
        "git_info": git_info,
    }


def export_copilot_bundle(
    root_dir: Path,
    user_goal: str = "",
    selected_files: Optional[List[str]] = None,
    assistant_advice: str = "",
) -> str:
    """
    Format a complete, structured prompt ready to copy-paste into GitHub Copilot / Cursor / ChatGPT.
    Answers: 'how do i send the folder send advice to my co pilot'.
    """
    pack = pack_workspace_context(root_dir, selected_files=selected_files)

    header = [
        "# Workspace Context Bundle for Copilot",
        f"**Repository**: `{root_dir.name}`",
        f"**Estimated Context Tokens**: ~{pack['estimated_tokens']:,}",
        f"**Included Files ({len(pack['packed_files'])} total)**: " + ", ".join(f"`{f}`" for f in pack["packed_files"]),
        "",
    ]

    if user_goal.strip():
        header.extend([
            "## Task / Objective",
            user_goal.strip(),
            "",
        ])

    if assistant_advice.strip():
        header.extend([
            "## Architectural Recommendations & Analysis (from Jupiter Studio)",
            assistant_advice.strip(),
            "",
        ])

    header.extend([
        "## Source Code & Workspace Context",
        pack["bundle_text"],
        "",
        "## Instructions for Copilot",
        "1. Review the git state, diffs, and attached project files.",
        "2. Implement surgical, high-quality code changes matching the above recommendations.",
        "3. Provide clean code snippets or unified diffs.",
    ])

    return "\n".join(header)
