import json
from pathlib import Path

def build_timeline_index(target_dir: Path):
    memory_dir = target_dir / "memory"
    decisions_dir = memory_dir / "decisions"
    events_dir = memory_dir / "events"
    timeline_dir = memory_dir / "timeline"
    timeline_dir.mkdir(parents=True, exist_ok=True)
    
    records = []
    
    # ADRs
    if decisions_dir.exists():
        for fp in decisions_dir.glob("*.md"):
            content = fp.read_text()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = {}
                    for line in parts[1].splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meta[k.strip()] = v.strip().strip('"')
                    meta["filepath"] = str(fp.relative_to(target_dir))
                    meta["type"] = "decision"
                    records.append(meta)
                    
    # Events
    if events_dir.exists():
        for fp in events_dir.glob("*.md"):
            content = fp.read_text()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = {}
                    for line in parts[1].splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meta[k.strip()] = v.strip().strip('"')
                    meta["filepath"] = str(fp.relative_to(target_dir))
                    meta["type"] = "event"
                    records.append(meta)

    records.sort(key=lambda x: x.get("id", ""), reverse=True)
    index_file = timeline_dir / "index.json"
    index_file.write_text(json.dumps({"records": records}, indent=2), encoding="utf-8")
