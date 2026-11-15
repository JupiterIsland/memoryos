import json
import os
from pathlib import Path

import httpx

env_path = Path(__file__).resolve().with_name(".env")
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val.strip('"').strip("'")

TOKENLAB_API_KEY = os.environ.get("TOKENLAB_API_KEY", "")
TOKENLAB_BASE_URL = os.environ.get("TOKENLAB_BASE_URL", "https://api.tokenlab.amd.com/v1").rstrip("/")

print("🚀 Firing insight to AMD Token Lab (d3)...")

response = httpx.post(
    f"{TOKENLAB_BASE_URL}/systemone",
    headers={"Authorization": f"Bearer {TOKENLAB_API_KEY}"},
    json={
        "model": "d3",
        "state": "User spent 4 hours tweaking WSL2 network routing instead of writing code.",
        "questions": {
            "q1_intervention": {
                "type": "choice",
                "criteria": {
                    "surface_now": "Should The Quiet Advisor generate an intervention card immediately?",
                    "defer": "Defer to daily digest instead of interrupting now",
                    "ignore": "Do not generate an intervention card",
                },
            }
        },
    },
    timeout=30.0,
)
response.raise_for_status()

print(json.dumps(response.json(), indent=2))
