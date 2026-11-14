# MemoryOS Router + Jupiter Desktop Bridge
## Hybrid Desktop System Architecture

```
┌─────────────────────────────────────┐
│   Jupiter Desktop (PyQt6)           │
│   - Frame extraction (cv2)          │
│   - MSE delta calculation           │
│   - UI + playback controls          │
└──────────┬──────────────────────────┘
           │
           │ HTTP POST /api/frame-delta
           │ HTTP POST /api/route
           │ POST /api/acknowledge-card
           │
        localhost:5000
           │
┌──────────▼──────────────────────────┐
│   MemoryOS Router (FastAPI)         │
│   - d3 model tier selection         │
│   - Token Lab routing               │
│   - User preference penalties       │
│   - Quiet Advisor DB logging        │
└──────────────────────────────────────┘
```

---

## API Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-15T10:30:45.123456Z",
  "services": {
    "heat_stream": true,
    "quiet_advisor_db": true,
    "tlb": true
  }
}
```

---

### 2. Frame Delta Check (Step 1: Gate VLM Call?)
```bash
POST /api/frame-delta

{
  "session_id": "jupiter-session-001",
  "frame_delta": {
    "brightness": 0.02,
    "contrast": 0.01,
    "intensity": 0.005,
    "palette_shift": 0.008,
    "composite_delta": 0.025
  },
  "context_hint": "YouTube video scene 42",
  "previous_response": "null or cached VLM output"
}
```

**Response:**
```json
{
  "session_id": "jupiter-session-001",
  "skip_vision": false,
  "d3_decision": {
    "choice": "surface_now",
    "confidence": 0.92,
    "probabilities": {"ignore": 0.03, "defer": 0.05, "surface_now": 0.92}
  },
  "gate_latency_ms": 4.2
}
```

**Logic:**
- If `skip_vision=true`: Frame hasn't changed significantly → reuse cached VLM output from `previous_response`
- If `skip_vision=false`: Frame changed → proceed to `/api/route` for full inference

---

### 3. Route Inference (Step 2: Heavy Lifting)
```bash
POST /api/route

{
  "session_id": "jupiter-session-001",
  "prompt_text": "Describe this video frame: [frame metadata]",
  "image_url": "file:///tmp/frame_0042.jpg or base64 data URI",
  "max_tokens": 1024,
  "user_id": "jupiter-desktop",
  "context_from_memory": true
}
```

**Response:**
```json
{
  "session_id": "jupiter-session-001",
  "route": "balanced_code",
  "model": "Gemma-4-31B-IT",
  "content": "Scene shows a person typing at a desk. Lighting is cool-toned...",
  "latency_ms": 2847.5,
  "user_preference_penalty": null,
  "quiet_advisor_card": null,
  "checkpoint_path": "/app/checkpoints/route_20241115_103045.json"
}
```

**Logic:**
- d3 selects model tier (fast_light, balanced_code, vision_heavy, long_context)
- User preference penalties are applied (e.g., if user clicked "avoid local VRAM", penalty→remote routing)
- Token Lab API is called (or falls back to Gemma-4-31B-IT)
- Result is logged to Quiet Advisor DB
- Checkpoint is saved (for replay/debugging)

---

### 4. Acknowledge Quiet Advisor Card (Closed Loop!)
When user clicks **[Acknowledge & Apply]** on a Quiet Advisor detector card in the PyQt6 UI:

```bash
POST /api/acknowledge-card

{
  "user_id": "jupiter-desktop",
  "card_type": "vram_thrashing",
  "action": "acknowledge"
}
```

**Response:**
```json
{
  "status": "acknowledged",
  "user_id": "jupiter-desktop",
  "card_type": "vram_thrashing",
  "penalty_applied": 1.5,
  "action": "acknowledge",
  "timestamp": "2024-11-15T10:30:45.123456Z"
}
```

**Closed Loop (The Magic):**
1. User sees Quiet Advisor card: "VRAM thrashing detected (confidence 0.85)"
2. User clicks [Acknowledge & Apply]
3. Router updates `quiet_advisor_user_preferences[vram_thrashing_penalty] = 1.5`
4. **Next inference request** reads the penalty
5. d3 demotes tier selection (skips local VRAM, defaults to remote Token Lab)
6. Result: No more thrashing ✓

---

### 5. Get Hot Memories (Context Window)
```bash
GET /api/memory/hot?limit=5
```

**Response:**
```json
{
  "status": "success",
  "total": 3,
  "memories": [
    {
      "id": "mem_1234567890",
      "title": "Video Scene 42 Analysis",
      "content": "Scene shows person at desk, cool-toned lighting, background has monitor...",
      "heat_score": 0.92,
      "access_count": 5
    }
  ]
}
```

**Usage:**
- Inject into Jupiter Desktop's context window for multi-turn conversations
- Heat scores indicate relevance (0.0 = cold, 1.0 = hot)

---

### 6. Router Status
```bash
GET /api/status
```

**Response:**
```json
{
  "timestamp": "2024-11-15T10:30:45.123456Z",
  "services": {
    "heat_stream": true,
    "quiet_advisor_db": true
  },
  "gpu": {
    "total_mb": 24000,
    "used_mb": 16000,
    "free_mb": 8000,
    "utilization_pct": 66.7
  },
  "active_sessions": 1
}
```

---

## Running the Router

### Option 1: Docker Compose (Recommended)
```bash
cp .env.example .env
# Fill in TOKENLAB_API_KEY, OPENAI_API_KEY, etc.

docker compose -f docker-compose-router.yml up -d

# Check logs
docker logs -f memoryos-router

# Test
curl http://localhost:5000/health
```

### Option 2: Local Python
```bash
pip install -r requirements-router.txt

export TOKENLAB_API_KEY=your-key
export OPENAI_API_KEY=your-key
export MEMORYOS_DIR=./memory

python server.py
```

---

## Jupiter Desktop Integration (PyQt6)

### Pseudocode: Frame Extraction → Router Call

```python
import cv2
import requests
from pathlib import Path

class JupiterVideoPlayer:
    def __init__(self, router_url="http://localhost:5000"):
        self.router_url = router_url
        self.session_id = "jupiter-session-001"
        self.last_response = None
        self.last_frame_hash = None
    
    def on_frame_update(self, frame):
        """Called when video frame changes."""
        # Step 1: Calculate MSE delta
        delta = self.calculate_frame_delta(frame)
        
        # Step 2: Check if we should skip VLM
        gate_resp = requests.post(
            f"{self.router_url}/api/frame-delta",
            json={
                "session_id": self.session_id,
                "frame_delta": delta,
                "context_hint": f"Video scene {self.current_frame_number}",
                "previous_response": self.last_response,
            }
        )
        
        if gate_resp.json()["skip_vision"]:
            # Reuse cached response
            print(f"✓ Skipped VLM call (d3 decision: ignore, delta={delta['composite_delta']:.3f})")
            return self.last_response
        
        # Step 3: Full routing
        route_resp = requests.post(
            f"{self.router_url}/api/route",
            json={
                "session_id": self.session_id,
                "prompt_text": "Describe this video frame...",
                "image_url": self.frame_to_data_uri(frame),
                "max_tokens": 1024,
                "user_id": "jupiter-desktop",
                "context_from_memory": True,
            }
        )
        
        result = route_resp.json()
        self.last_response = result["content"]
        self.last_frame_hash = hash(frame.tobytes())
        
        return result
    
    def calculate_frame_delta(self, frame):
        """Calculate brightness/contrast/palette changes."""
        # MSE, histogram, etc.
        # Return: {"brightness": 0.02, "contrast": 0.01, ...}
        pass
    
    def on_user_acknowledges_card(self, card_type, action):
        """User clicks [Acknowledge & Apply] on a Quiet Advisor card."""
        resp = requests.post(
            f"{self.router_url}/api/acknowledge-card",
            params={
                "user_id": "jupiter-desktop",
                "card_type": card_type,
                "action": action,
            }
        )
        
        print(f"✓ Preference updated: {card_type} penalty = {resp.json()['penalty_applied']}")
```

---

## Dependency Breakdown

| Service | Image Size | Dependencies | Purpose |
|---------|-----------|--------------|---------|
| **memoryos-router** | ~150MB | openai, duckdb, fastapi, numpy | d3 routing + Token Lab calls + Quiet Advisor logging |
| **jupiter-desktop** | ~200MB (local only) | PyQt6, opencv-python-headless, numpy | Frame extraction, MSE delta, UI |
| **jupiter-vision-worker** | ~5GB (optional) | torch, torchvision, basicsr, realesrgan | Local TensorRT/VLM (only if refusing Token Lab) |

---

## Next Steps

✅ **MemoryOS Router** is containerized and ready.
⏳ **Jupiter Desktop** needs to implement `/api/frame-delta` + `/api/route` calls.
⏳ **Feedback Loop** wired: user preference penalty → routing decision.

The monolith is dead. Long live the service architecture. 🎉
