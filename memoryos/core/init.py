from pathlib import Path

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
            "# MemoryOS Repository Memory\n\n"
            "This folder contains structured institutional context:\n"
            "* `decisions/`: Architecture decision records and trade-offs.\n"
            "* `events/`: Operational milestones, releases, and incidents.\n"
            "* `projects/`: System scope, boundaries, and specs.\n"
            "* `timeline/`: Compiled chronological indexes.\n",
            encoding="utf-8"
        )

    return created_any
