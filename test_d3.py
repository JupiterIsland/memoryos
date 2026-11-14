import json
import os
from pathlib import Path
from openai import OpenAI

env_path = Path(__file__).resolve().with_name(".env")
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val.strip('"').strip("'")

tl_client = OpenAI(
    api_key=os.environ["TOKENLAB_API_KEY"],
    base_url=os.environ["TOKENLAB_BASE_URL"],
)

print("🚀 Firing insight to AMD Token Lab (d3)...")

response = tl_client.post(
    "/systemone",
    cast_to=dict,
    body={
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
)

print(json.dumps(response, indent=2))
