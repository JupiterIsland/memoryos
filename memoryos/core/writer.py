import os
import re
from datetime import datetime, timezone
from pathlib import Path

def slugify(text: str) -> str:
    """Converts a title into a clean URL/filename-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")

def get_next_adr_id(decisions_dir: Path) -> int:
    """Scans the decisions folder to find the highest ADR number."""
    if not decisions_dir.exists():
        return 1
    existing_files = list(decisions_dir.glob("ADR-*.md"))
    if not existing_files:
        return 1
    
    ids = []
    for filepath in existing_files:
        match = re.match(r"^ADR-(\d+)", filepath.name)
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
