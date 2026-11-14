import re
from datetime import datetime, timezone
from pathlib import Path

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")

def get_next_adr_id(decisions_dir: Path) -> int:
    if not decisions_dir.exists():
        return 1
    existing_files = list(decisions_dir.glob("ADR-*.md"))
    if not existing_files:
        return 1
    ids = [int(m.group(1)) for f in existing_files if (m := re.match(r"^ADR-(\d+)", f.name))]
    return max(ids) + 1 if ids else 1

def create_decision_adr(title, decision, reason, evidence, outcome, impact, target_dir: Path):
    decisions_dir = target_dir / "memory" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    adr_id = get_next_adr_id(decisions_dir)
    filename = f"ADR-{adr_id:04d}-{slugify(title)}.md"
    file_path = decisions_dir / filename

    content = f'''---
id: ADR-{adr_id:04d}
title: "{title}"
date: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
status: accepted
---
# ADR-{adr_id:04d}: {title}
## Decision
{decision}
## Reason
{reason}
## Evidence
{evidence}
## Outcome
{outcome}
'''
    file_path.write_text(content, encoding="utf-8")
