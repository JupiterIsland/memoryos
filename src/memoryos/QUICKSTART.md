# MemoryOS Router: Quick Start (5 Minutes)

## Setup

### 1. Install Docker
```bash
# macOS
brew install docker

# Linux
apt-get install docker.io

# Windows
choco install docker-desktop
```

### 2. Clone & Navigate
```bash
cd memoryos
```

### 3. Set Environment
```bash
cp .env.example .env
# Edit .env and add your keys:
# TOKENLAB_API_KEY=...
# OPENAI_API_KEY=...
```

---

## Build & Run

### One-Command Start
```bash
make build-router
make up-router
```

### Verify It Works
```bash
make test-health
# Expected: {"status": "healthy", ...}
```

---

## Test the API

### 1. Test Frame Gating
```bash
make test-frame
# Response: {"skip_vision": false, "gate_latency_ms": 4.2, ...}
```

### 2. Test Inference Routing
```bash
make test-route
# Response: {"route": "balanced_code", "model": "Gemma-4-31B-IT", "content": "...", ...}
```

### 3. Test Feedback Loop
```bash
make test-loop
# Response: {"status": "acknowledged", "penalty_applied": 1.5, ...}

# Then test routing again:
make test-route
# Now you should see user_preference_penalty: 1.5 in response
```

---

## Interactive API Docs

Open in browser:
```
http://localhost:5000/docs
```

(FastAPI Swagger UI with try-it-out buttons)

---

## Logs & Debugging

### Watch Logs
```bash
make logs-router
```

### Shell Into Container
```bash
make shell-router
```

### Check Status
```bash
curl http://localhost:5000/api/status | jq .
```

---

## Stop & Cleanup

### Stop Services
```bash
make down
```

### Full Cleanup
```bash
make clean
```

---

## For Jupiter Desktop Developers

The router is now running. Your desktop app should:

1. Extract video frame → calculate delta
   ```python
   delta = calculate_frame_delta(frame)
   # {"brightness": 0.02, "contrast": 0.01, ...}
   ```

2. Call frame gating endpoint
   ```python
   resp = requests.post(
       "http://localhost:5000/api/frame-delta",
       json={
           "session_id": "jupiter-session",
           "frame_delta": delta,
       }
   )
   skip = resp.json()["skip_vision"]
   ```

3. If not skipping, call routing endpoint
   ```python
   resp = requests.post(
       "http://localhost:5000/api/route",
       json={
           "session_id": "jupiter-session",
           "prompt_text": "Describe this frame",
           "image_url": "file:///path/to/frame.jpg",
       }
   )
   inference_result = resp.json()["content"]
   ```

4. Display detector cards, wire up [Acknowledge] button
   ```python
   requests.post(
       "http://localhost:5000/api/acknowledge-card",
       params={
           "user_id": "jupiter-desktop",
           "card_type": "vram_thrashing",
           "action": "acknowledge"
       }
   )
   ```

Full examples in **BRIDGE_PROTOCOL.md**

---

## Troubleshooting

### Port 5000 Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### Container Won't Start
```bash
docker logs memoryos-router
```

### API Returns 500 Error
Check logs:
```bash
make logs-router
```
Likely missing `TOKENLAB_API_KEY` or `OPENAI_API_KEY` in `.env`

### Health Check Fails
Wait 10 seconds (container needs time to start):
```bash
sleep 10
make test-health
```

---

## What's Next

- ✅ Router is running
- ⏳ Wire up Jupiter Desktop to call API
- ⏳ Implement frame delta calculation
- ⏳ Display detector cards in UI
- ⏳ Test feedback loop end-to-end

---

## Need Help?

- **API Questions:** Read `BRIDGE_PROTOCOL.md`
- **Architecture Questions:** Read `REFACTOR_SUMMARY.md`
- **Checklist & TODOs:** Read `REFACTOR_CHECKLIST.md`
- **Implementation:** See `server.py` (FastAPI code)

---

## Commands Reference

```bash
make build-router          # Build image
make up-router             # Start container
make down                  # Stop container
make logs-router           # View logs
make shell-router          # SSH into container
make test-health           # Test /health
make test-frame            # Test /api/frame-delta
make test-route            # Test /api/route
make test-loop             # Test feedback loop
make clean                 # Remove everything
make docs                  # Show docs links
make help                  # Show all commands
```

---

**🚀 You're ready. Start building.**
