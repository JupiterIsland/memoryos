import json
import time
import secrets
from pathlib import Path
from datetime import datetime

def log_event(event_type: str, context: dict, target_dir: Path):
    events_dir = target_dir / "memory" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    evt_id = f"evt-{int(time.time())}-{secrets.token_hex(4)}"
    filepath = events_dir / f"{evt_id}.md"

    content = f'''---
id: {evt_id}
timestamp: {datetime.now().isoformat()}
type: {event_type}
status: {context.get('status', 'completed')}
priority: {context.get('priority', 'normal')}
---
# {event_type}: {evt_id}
{context.get('note', 'No additional details provided.')}
'''
    filepath.write_text(content, encoding="utf-8")
