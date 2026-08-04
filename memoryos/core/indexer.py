import json
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
                fm["filepath"] = str(filepath.relative_to(target_dir)).replace("\\", "/")
                records.append(fm)

    records.sort(key=lambda x: x.get("id", ""), reverse=True)

    index_file = timeline_dir / "index.json"
    index_file.write_text(json.dumps({"decisions": records}, indent=2), encoding="utf-8")
    return index_file
