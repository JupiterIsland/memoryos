import requests

SYSTEM_PROMPT = """
You are Jupiter TV's AI technician. You know the user's watch history and streaming status (MemoryOS context).
- If a stream fails, suggest an alternative (lower quality, cached link, or a different host).
- If asked for recommendations, suggest 3 items based on history.
- Keep responses short and action-oriented.
"""


def ask_technician(user_text, memory_context=None, endpoint="http://127.0.0.1:11434/api/generate"):
    payload = {
        "system": SYSTEM_PROMPT,
        "prompt": user_text,
        "context": memory_context or {}
    }
    try:
        r = requests.post(endpoint, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("text") or data.get("output") or ""
    except Exception as e:
        return f"Technician unavailable: {e}"
