import json
from pathlib import Path

def query_timeline(target_dir: Path, tag: str = None):
    index_path = target_dir / "memory" / "timeline" / "index.json"
    if not index_path.exists():
        return {"error": "No timeline index found. Run 'memoryos index' first."}
    data = json.loads(index_path.read_text())
    results = data.get("records", [])
    if tag:
        results = [r for r in results if tag in r.get("tags", "")]
    return results
