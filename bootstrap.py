import os
from pathlib import Path

# File structure mapping
FILES = {
    "memoryos/__init__.py": '"""MemoryOS Core Package"""\n__version__ = "0.1.0"\n',
    
    "memoryos/core/__init__.py": "",
    
    "memoryos/core/init.py": '''from pathlib import Path

TARGET_DOMAINS = ["decisions", "events", "projects", "timeline"]

def initialize_memory_repo(target_dir: Path = Path(".")) -> bool:
    """Scaffolds the /memory subdirectories inside the target repository."""
    memory_base = target_dir / "memory"
    
    created_any = False
    for domain in TARGET_DOMAINS:
        domain_path = memory_base / domain
        if not domain_path.exists():
            domain_path.mkdir(parents=True, exist_ok=True)
            created_any = True
            
    readme_path = memory_base / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "# MemoryOS Repository Memory\\n\\n"
            "This folder contains structured institutional context:\\n"
            "* `decisions/`: Architecture decision records and trade-offs.\\n"
            "* `events/`: Operational milestones, releases, and incidents.\\n"
            "* `projects/`: System scope, boundaries, and specs.\\n"
            "* `timeline/`: Compiled chronological indexes.\\n",
            encoding="utf-8"
        )

    return created_any
''',

    "memoryos/core/writer.py": '''import os
import re
from datetime import datetime, timezone
from pathlib import Path

def slugify(text: str) -> str:
    """Converts a title into a clean URL/filename-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\\w\\s-]", "", text)
    return re.sub(r"[-\\s]+", "-", text).strip("-")

def get_next_adr_id(decisions_dir: Path) -> int:
    """Scans the decisions folder to find the highest ADR number."""
    if not decisions_dir.exists():
        return 1
    existing_files = list(decisions_dir.glob("ADR-*.md"))
    if not existing_files:
        return 1
    
    ids = []
    for filepath in existing_files:
        match = re.match(r"^ADR-(\\d+)", filepath.name)
        if match:
            ids.append(int(match.group(1)))
    return max(ids) + 1 if ids else 1

def create_decision_adr(
    title: str,
    decision: str,
    reason: str,
    evidence: str,
    outcome: str,
    impact: dict = None,
    target_dir: Path = Path(".")
) -> Path:
    """Generates a structured Markdown ADR file in memory/decisions/."""
    decisions_dir = target_dir / "memory" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    adr_id = get_next_adr_id(decisions_dir)
    filename = f"ADR-{adr_id:04d}-{slugify(title)}.md"
    file_path = decisions_dir / filename

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    impact = impact or {}

    content = f"""---
id: ADR-{adr_id:04d}
title: "{title}"
date: {today_str}
status: accepted
tags: []
impact:
  time_saved: "{impact.get('time_saved', 'N/A')}"
  cost_impact: "{impact.get('cost_impact', 'N/A')}"
  risk_reduction: "{impact.get('risk_reduction', 'N/A')}"
  strategic_value: "{impact.get('strategic_value', 'N/A')}"
---

# ADR-{adr_id:04d}: {title}

## 1. Decision
{decision}

## 2. Date
{today_str}

## 3. Reason
{reason}

## 4. Evidence
{evidence}

## 5. Outcome
{outcome}
"""

    file_path.write_text(content, encoding="utf-8")
    return file_path
''',

    "memoryos/core/indexer.py": '''import json
from pathlib import Path

def parse_simple_frontmatter(content: str) -> dict:
    """Extracts frontmatter key-value pairs from Markdown files."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    
    frontmatter_text = parts[1].strip()
    data = {}
    
    for line in frontmatter_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                data[key] = val
    return data

def build_timeline_index(target_dir: Path = Path(".")) -> Path:
    """Parses all ADRs in memory/decisions/ and builds memory/timeline/index.json."""
    memory_dir = target_dir / "memory"
    decisions_dir = memory_dir / "decisions"
    timeline_dir = memory_dir / "timeline"
    timeline_dir.mkdir(parents=True, exist_ok=True)

    records = []
    if decisions_dir.exists():
        for filepath in decisions_dir.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")
            fm = parse_simple_frontmatter(content)
            if fm:
                fm["filepath"] = str(filepath.relative_to(target_dir)).replace("\\\\", "/")
                records.append(fm)

    records.sort(key=lambda x: x.get("id", ""), reverse=True)

    index_file = timeline_dir / "index.json"
    index_file.write_text(json.dumps({"decisions": records}, indent=2), encoding="utf-8")
    return index_file
''',

    "memoryos/cli.py": '''#!/usr/bin/env python3
import argparse
from pathlib import Path
from memoryos.core.init import initialize_memory_repo
from memoryos.core.writer import create_decision_adr
from memoryos.core.indexer import build_timeline_index

def main():
    parser = argparse.ArgumentParser(
        prog="memoryos",
        description="MemoryOS: Institutional decision and context memory CLI."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: memoryos init
    init_parser = subparsers.add_parser("init", help="Initialize memory/ structure")
    init_parser.add_argument("--path", type=str, default=".", help="Target directory path")

    # Command: memoryos log decision
    log_parser = subparsers.add_parser("log", help="Log an entry into MemoryOS")
    log_subparsers = log_parser.add_subparsers(dest="log_type", help="Type of log entry")

    dec_parser = log_subparsers.add_parser("decision", help="Log a new Architecture Decision Record")
    dec_parser.add_argument("--title", required=True, help="Short title of the decision")
    dec_parser.add_argument("--decision", required=True, help="What was decided?")
    dec_parser.add_argument("--reason", required=True, help="Why was this decision made?")
    dec_parser.add_argument("--evidence", default="N/A", help="Supporting benchmarks or data")
    dec_parser.add_argument("--outcome", default="Pending review", help="Expected or observed outcome")
    dec_parser.add_argument("--time-saved", default="N/A", help="Estimated time saved")
    dec_parser.add_argument("--cost-impact", default="N/A", help="Cost impact or budget delta")
    dec_parser.add_argument("--risk-reduction", default="N/A", help="Risk reduction achieved")
    dec_parser.add_argument("--strategic-value", default="N/A", help="Long-term strategic value")

    # Command: memoryos index
    index_parser = subparsers.add_parser("index", help="Compile memory/timeline/index.json")
    index_parser.add_argument("--path", type=str, default=".", help="Target directory path")

    args = parser.parse_args()

    if args.command == "init":
        target = Path(args.path)
        initialize_memory_repo(target)
        print(f"Success: Initialized memory/ taxonomy in {target.resolve()}")

    elif args.command == "log" and args.log_type == "decision":
        impact = {
            "time_saved": args.time_saved,
            "cost_impact": args.cost_impact,
            "risk_reduction": args.risk_reduction,
            "strategic_value": args.strategic_value
        }
        file_created = create_decision_adr(
            title=args.title,
            decision=args.decision,
            reason=args.reason,
            evidence=args.evidence,
            outcome=args.outcome,
            impact=impact
        )
        print(f"Success: Created {file_created}")
        
        # Auto-rebuild timeline index
        index_file = build_timeline_index()
        print(f"Success: Updated {index_file}")

    elif args.command == "index":
        target = Path(args.path)
        index_file = build_timeline_index(target)
        print(f"Success: Compiled timeline index at {index_file.resolve()}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
''',

    "pyproject.toml": '''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "memoryos"
version = "0.1.0"
description = "Institutional decision memory CLI"
readme = "README.md"
requires-python = ">=3.8"

[project.scripts]
memoryos = "memoryos.cli:main"
''',

    ".gitignore": '''__pycache__/
*.py[cod]
*$py.class
build/
dist/
*.egg-info/
.venv
venv/
.vscode/
.idea/
memory/
'''
}

def build_project():
    base_dir = Path(".")
    print("Scaffolding MemoryOS package...")
    
    for rel_path, content in FILES.items():
        file_path = base_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content.lstrip(), encoding="utf-8")
        print(f"  [+] Created {rel_path}")

    print("\nProject scaffold complete!")

if __name__ == "__main__":
    build_project()