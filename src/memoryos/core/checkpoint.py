import json
from pathlib import Path
from datetime import datetime

class CheckpointEngine:
    def __init__(self, target_dir: Path):
        self.checkpoint_dir = target_dir / "memory" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self):
        name = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = self.checkpoint_dir / name
        state = {"timestamp": datetime.now().isoformat(), "version": "0.1.0"}
        path.write_text(json.dumps(state, indent=2))
        print(f"💾 Checkpoint saved: {name}")

    def load(self, name: str):
        path = self.checkpoint_dir / name
        if not path.exists():
            print("❌ Checkpoint not found.")
            return
        state = json.loads(path.read_text())
        print(f"🔄 Loaded checkpoint from {state['timestamp']}")
