from pathlib import Path

TARGET_DOMAINS = ["decisions", "events", "projects", "timeline", "checkpoints"]

def initialize_memory_repo(target_dir: Path = Path(".")) -> bool:
    memory_base = target_dir / "memory"
    created_any = False
    for domain in TARGET_DOMAINS:
        domain_path = memory_base / domain
        if not domain_path.exists():
            domain_path.mkdir(parents=True, exist_ok=True)
            created_any = True
            
    readme_path = memory_base / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# MemoryOS Repository Memory\n\nThis folder contains institutional context.\n")
    return created_any
