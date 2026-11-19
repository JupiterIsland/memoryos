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
    ".tox",
    ".nox",
    ".eggs",
    "htmlcov",
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
    ".env.staging",
    ".env.test",
    "credentials.json",
    "secrets.json",
    "token.json",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
    ".npmrc",
    ".netrc",
    ".pypirc",
    "QuietAdvisorDB.sqlite",
    "QuietAdvisorDB.sqlite-journal",
    "QuietAdvisorDB.sqlite-wal",
    "QuietAdvisorDB.sqlite-shm",
    "quiet_advisor.db",
    "quiet_advisor.db-wal",
    "quiet_advisor.db-shm",
}

_IGNORED_FILES_LOWER: Set[str] = {name.lower() for name in IGNORED_FILES}
_IGNORED_DIRS_LOWER: Set[str] = {name.lower() for name in IGNORED_DIRS}

SENSITIVE_EXTENSIONS: Set[str] = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".jks",
    ".keystore",
    ".kdbx",
    ".sqlite-wal",
    ".sqlite-shm",
    ".db-wal",
    ".db-shm",
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

CODE_PRIORITY_EXTENSIONS: Set[str] = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".rs",
    ".go",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sql",
    ".sh",
    ".ps1",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".md",
    ".html",
    ".css",
}

PRIORITY_TOP_DIRS: Set[str] = {"apps", "src", "tests", "apex_core", "backend", "engine", "scripts"}

DEFAULT_MAX_FILE_BYTES = 250_000  # 250 KB max per file
DEFAULT_MAX_BUNDLE_CHARS = 240_000  # ~60K tokens max bundle


def _normalize_rel_path(rel_path: Path | str) -> Path:
    """Normalize separators so Windows-style paths are checked safely on POSIX too."""
    return Path(str(rel_path).replace("\\", "/"))


def _is_ignored_dir_name(name: str) -> bool:
    low = name.lower()
    if low in _IGNORED_DIRS_LOWER:
        return True
    if name.startswith(".") and name not in {".", ".."}:
        return True
    if low.endswith(".egg-info") or low.endswith(".dist-info"):
        return True
    return False


def _make_markdown_fence(content: str, lang: str = "") -> tuple[str, str]:
    """Return opening and closing code fences guaranteed not to collide with content."""
    longest = 2
    run = 0
    for ch in content:
        if ch == "`":
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0
    fence = "`" * (longest + 1)
    safe_lang = "".join(ch for ch in (lang or "text") if ch.isalnum() or ch in ("_", "-", "+", ".")) or "text"
    return f"{fence}{safe_lang}", fence


def is_binary_or_ignored(rel_path: Path | str) -> bool:
    """Check if a path should be excluded from workspace context (case-insensitive & separator-safe)."""
    norm_path = _normalize_rel_path(rel_path)
    parts = norm_path.parts
    if not parts:
        return True

    for part in parts[:-1]:
        if _is_ignored_dir_name(part):
            return True

    name = norm_path.name
    low_name = name.lower()
    if not name or name in {".", ".."}:
        return True
    if low_name in _IGNORED_FILES_LOWER:
        return True
    if low_name.startswith(".env.") and low_name not in ALLOWED_DOTFILES:
        return True
    if name.startswith(".") and low_name not in ALLOWED_DOTFILES:
        return True

    suffix = norm_path.suffix.lower()
    if suffix in BINARY_EXTENSIONS or suffix in SENSITIVE_EXTENSIONS:
        return True
    return False


def get_git_branch(root_dir: Path | str) -> str:
    """Fast, pure-Python git branch reader with subprocess fallback."""
    root = Path(root_dir)
    git_entry = root / ".git"
    try:
        head_file: Optional[Path] = None
        if git_entry.is_dir():
            head_file = git_entry / "HEAD"
        elif git_entry.is_file():
            pointer = git_entry.read_text(encoding="utf-8", errors="replace").strip()
            if pointer.startswith("gitdir:"):
                git_dir = Path(pointer.split(":", 1)[1].strip())
                if not git_dir.is_absolute():
                    git_dir = (root / git_dir).resolve()
                head_file = git_dir / "HEAD"
        if head_file and head_file.is_file():
            head_txt = head_file.read_text(encoding="utf-8", errors="replace").strip()
            if head_txt.startswith("ref:"):
                ref = head_txt.split(":", 1)[1].strip()
                prefix = "refs/heads/"
                return ref[len(prefix):] if ref.startswith(prefix) else ref
            if head_txt:
                return head_txt[:12]
    except OSError:
        pass
    return ""


def get_git_status_and_diff(root_dir: Path | str, max_diff_chars: int = 15_000) -> Dict[str, str]:
    """Retrieve git branch, status --short, and diff summary for the workspace."""
    root_dir = Path(root_dir)
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

    branch = get_git_branch(root_dir) or _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
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


def _file_sort_key(item: Dict[str, Any]) -> tuple[int, int, int, str]:
    rel = item["rel_path"]
    ext = item["extension"]
    parts = rel.split("/")
    is_code = 0 if ext in CODE_PRIORITY_EXTENSIONS else 1
    if len(parts) == 1:
        dir_rank = 1 if ext == ".md" else 0
    elif parts[0] in PRIORITY_TOP_DIRS:
        dir_rank = 0
    else:
        dir_rank = 2
    depth = len(parts)
    return (is_code, dir_rank, depth, rel.lower())


def scan_workspace_files(root_dir: Path | str, max_files: int = 250) -> List[Dict[str, Any]]:
    """Scan readable workspace files using os.scandir, prioritizing source/config dirs first."""
    root_path = Path(root_dir)
    if not root_path.exists() or not root_path.is_dir():
        return []

    resolved_root = root_path.resolve()
    max_files = max(1, int(max_files))
    scan_cap = max(max_files * 3, 400)
    results: List[Dict[str, Any]] = []

    def _dir_order(name: str, depth: int) -> tuple[int, str]:
        if depth == 0 and name in PRIORITY_TOP_DIRS:
            return (0, name.lower())
        return (1, name.lower())

    def _walk(cur_dir: Path, rel_prefix: str, depth: int) -> None:
        if len(results) >= scan_cap:
            return
        try:
            with os.scandir(cur_dir) as it:
                entries = list(it)
        except OSError:
            return

        subdirs: List[tuple[str, Path]] = []
        files: List[os.DirEntry] = []
        for entry in entries:
            name = entry.name
            try:
                is_sym = entry.is_symlink()
                if entry.is_dir(follow_symlinks=False):
                    if is_sym or _is_ignored_dir_name(name):
                        continue
                    subdir_path = Path(entry.path)
                    if depth <= 1 and (subdir_path / "pyvenv.cfg").is_file():
                        continue
                    subdirs.append((name, subdir_path))
                elif entry.is_file(follow_symlinks=True):
                    files.append(entry)
            except OSError:
                continue

        files.sort(key=lambda e: e.name)
        for entry in files:
            rel_str = f"{rel_prefix}/{entry.name}" if rel_prefix else entry.name
            rel_path = Path(rel_str)
            if is_binary_or_ignored(rel_path):
                continue
            try:
                if entry.is_symlink():
                    target = Path(entry.path).resolve()
                    target_rel = target.relative_to(resolved_root)
                    if is_binary_or_ignored(target_rel):
                        continue
                st = entry.stat(follow_symlinks=True)
                results.append({
                    "rel_path": rel_str,
                    "size_bytes": st.st_size,
                    "extension": rel_path.suffix.lower(),
                })
                if len(results) >= scan_cap:
                    return
            except (OSError, ValueError):
                continue

        subdirs.sort(key=lambda pair: _dir_order(pair[0], depth))
        for name, subdir_path in subdirs:
            next_prefix = f"{rel_prefix}/{name}" if rel_prefix else name
            _walk(subdir_path, next_prefix, depth + 1)
            if len(results) >= scan_cap:
                return

    _walk(resolved_root, "", 0)
    results.sort(key=_file_sort_key)
    return results[:max_files]


def _read_text_bounded(full_path: Path, max_bytes: int) -> Optional[tuple[str, bool]]:
    """Read up to max_bytes from a text file; returns None if binary (NUL bytes) or unreadable."""
    try:
        with full_path.open("rb") as fh:
            raw = fh.read(max_bytes + 1)
    except OSError:
        return None

    # Detect binary files without known extensions via NUL byte check
    if b"\x00" in raw[:4096]:
        return None

    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    return raw.decode("utf-8", errors="replace"), truncated


def pack_workspace_context(
    root_dir: Path | str,
    selected_files: Optional[List[str]] = None,
    include_git: bool = True,
    max_total_chars: int = DEFAULT_MAX_BUNDLE_CHARS,
) -> Dict[str, Any]:
    """Pack selected workspace files and git context into a structured markdown bundle."""
    root_dir = Path(root_dir).resolve()
    max_total_chars = max(1024, int(max_total_chars))
    packed_blocks: List[str] = []
    packed_files: List[str] = []
    seen_resolved: Set[Path] = set()
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

    target_files = selected_files if isinstance(selected_files, list) else []
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

    for item in target_files:
        if not isinstance(item, str) or not item.strip() or "\x00" in item:
            continue
        rel_str = item.strip().replace("\\", "/")
        rel_path = _normalize_rel_path(rel_str)
        if rel_path.is_absolute() or is_binary_or_ignored(rel_path):
            continue

        try:
            full_path = (root_dir / rel_path).resolve()
            # Security check: resolved target must reside inside root_dir AND pass ignore checks
            resolved_rel = full_path.relative_to(root_dir)
        except (OSError, ValueError):
            continue

        if is_binary_or_ignored(resolved_rel):
            continue

        if full_path in seen_resolved or not full_path.is_file():
            continue
        seen_resolved.add(full_path)

        read_res = _read_text_bounded(full_path, min(DEFAULT_MAX_FILE_BYTES, max_total_chars))
        if read_res is None:
            continue
        content, was_size_capped = read_res
        if was_size_capped:
            content += "\n... [file truncated at size limit] ..."

        clean_rel_str = str(resolved_rel).replace("\\", "/")
        lang = resolved_rel.suffix.lstrip(".").lower() or "text"
        open_fence, close_fence = _make_markdown_fence(content, lang)
        block = f"### File: `{clean_rel_str}`\n{open_fence}\n{content}\n{close_fence}\n\n"

        if total_chars + len(block) > max_total_chars:
            allowed = max(0, max_total_chars - total_chars - 200)
            if allowed > 1000:
                truncated_content = content[:allowed]
                open_fence, close_fence = _make_markdown_fence(truncated_content, lang)
                block = (
                    f"### File: `{clean_rel_str}` (Truncated)\n"
                    f"{open_fence}\n{truncated_content}\n... [file truncated] ...\n{close_fence}\n\n"
                )
                packed_blocks.append(block)
                packed_files.append(clean_rel_str)
                total_chars += len(block)
            break

        packed_blocks.append(block)
        packed_files.append(clean_rel_str)
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
    root_dir: Path | str,
    user_goal: str = "",
    selected_files: Optional[List[str]] = None,
    assistant_advice: str = "",
) -> str:
    """
    Format a complete, structured prompt ready to copy-paste into GitHub Copilot / Cursor / ChatGPT.
    Answers: 'how do i send the folder send advice to my co pilot'.
    """
    root_path = Path(root_dir)
    pack = pack_workspace_context(root_path, selected_files=selected_files)
    safe_goal = str(user_goal or "").strip()
    safe_advice = str(assistant_advice or "").strip()

    header = [
        "# Workspace Context Bundle for Copilot",
        f"**Repository**: `{root_path.name}`",
        f"**Estimated Context Tokens**: ~{pack['estimated_tokens']:,}",
        f"**Included Files ({len(pack['packed_files'])} total)**: " + ", ".join(f"`{f}`" for f in pack["packed_files"]),
        "",
    ]

    if safe_goal:
        header.extend([
            "## Task / Objective",
            safe_goal,
            "",
        ])

    if safe_advice:
        header.extend([
            "## Architectural Recommendations & Analysis (from Jupiter Studio)",
            safe_advice,
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
