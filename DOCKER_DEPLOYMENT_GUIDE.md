# Jupiter TV - Docker Deployment Guide

## Quick Start

### Option 1: Desktop (PyQt6) with GUI Forwarding
```bash
docker compose -f docker-compose.jupiter.yml up jupiter-desktop
```

### Option 2: Mobile (Kivy)
```bash
docker compose -f docker-compose.jupiter.yml up jupiter-mobile
```

### Option 3: Full Stack (Desktop + Mobile + Ollama)
```bash
docker compose -f docker-compose.jupiter.yml up
```

---

## Prerequisites

### On Host System
- Docker >= 20.10
- Docker Compose >= 1.29
- 8GB RAM minimum (for Ollama)
- Linux/macOS: X11 forwarding (for desktop GUI)
- Windows: WSL2 with Docker Desktop

### First-Time Setup
```bash
# Build all images
docker compose -f docker-compose.jupiter.yml build

# Download Ollama models (optional, ~2GB)
docker exec jupiter-ollama ollama pull llama2:7b
docker exec jupiter-ollama ollama pull mistral:7b
```

---

## Architecture

```
Docker Network (jupiter-net)
├── jupiter-desktop (PyQt6 + Qt6 libraries)
│   ├── libtorrent (torrent streaming)
│   ├── FFmpeg (scene detection)
│   └── Ollama client (AI requests)
│
├── jupiter-mobile (Kivy + SDL2)
│   ├── libtorrent (torrent streaming)
│   ├── FFmpeg (scene detection)
│   └── Ollama client (AI requests)
│
└── ollama (CPU-based LLM inference)
    ├── llama2:7b (or custom models)
    └── Persistent model storage

Volumes:
├── jupiter-cache → /tmp/jptv (torrent downloads)
└── ollama-models → /root/.ollama (model storage)
```

---

## Environment Variables

### For Desktop
```bash
DISPLAY=:99                    # Virtual display
QT_QPA_PLATFORM=offscreen     # Headless rendering
OLLAMA_HOST=http://ollama:11434  # Ollama API endpoint
```

### For Mobile
```bash
KIVY_WINDOW_ICON=app_icon.png
OLLAMA_HOST=http://ollama:11434
```

### For Ollama
```bash
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODELS=/root/.ollama
```

---

## Usage Examples

### Run Desktop App
```bash
docker compose -f docker-compose.jupiter.yml up jupiter-desktop
```
Then open X11 window (if forwarded) or SSH into container with X11 forwarding.

### Run Mobile App
```bash
docker compose -f docker-compose.jupiter.yml up jupiter-mobile
# Access via SSH or container shell
```

### Run Full Stack
```bash
docker compose -f docker-compose.jupiter.yml up
# All 3 services start: desktop, mobile, ollama
```

### Execute Commands in Running Container
```bash
# Run test suite
docker exec jupiter-desktop python test_scene_detection_mvp.py

# Run scene detector
docker exec jupiter-desktop python -c "
from apps.shared.ai import SceneDetector
d = SceneDetector()
scenes = d.detect('/tmp/test.mp4')
print(f'Found {len(scenes)} scenes')
"

# Check Ollama status
docker exec jupiter-ollama ollama list
```

---

## Volumes & Persistence

### jupiter-cache
- **Path**: `/tmp/jptv`
- **Purpose**: Torrent downloads (streaming cache)
- **Size**: Depends on active streams (typically 100MB-1GB)
- **Cleanup**: `docker volume rm jupiter-cache` (clears all cached torrents)

### ollama-models
- **Path**: `/root/.ollama` in container, `ollama-models` volume on host
- **Purpose**: LLM model storage (llama2, mistral, etc.)
- **Size**: ~7GB per 7B model, ~40GB per 70B model
- **Persistence**: Persists across container restarts

---

## Performance Tuning

### For Limited Resources
```yaml
# Edit docker-compose.jupiter.yml limits
deploy:
  resources:
    limits:
      cpus: '1'      # Reduce from 2
      memory: 2G     # Reduce from 4G
```

### For High Performance
```yaml
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 16G
    reservations:
      cpus: '4'
      memory: 8G
```

### Ollama Optimization
- Use smaller models: `ollama pull mistral:7b` (4GB vs 14GB)
- Or use `ollama pull neural-chat:7b` (5GB, faster)
- Use quantized models: `ollama pull llama2:3b` (2GB)

---

## Network

All services communicate via custom bridge network `jupiter-net` with fixed subnet:
- Ollama: `172.20.0.2:11434`
- Desktop: `172.20.0.3`
- Mobile: `172.20.0.4`

### Port Mappings
- Ollama API: `localhost:11434` → container:11434
- Mobile optional API: `localhost:8000` → container:8000
- Desktop X11: `/tmp/.X11-unix` (volume mount)

---

## Health Checks

All services include health checks:

```bash
# Check service health
docker compose -f docker-compose.jupiter.yml ps

# View health status
docker ps --format "{{.Names}}\t{{.Status}}"
```

Expected output:
```
jupiter-desktop    Up X minutes (healthy)
jupiter-mobile     Up X minutes (healthy)
jupiter-ollama     Up X minutes (healthy)
```

---

## Troubleshooting

### "Ollama connection refused"
```bash
# Wait for Ollama to start
docker compose -f docker-compose.jupiter.yml up ollama

# In another terminal, verify
curl http://localhost:11434/api/tags
```

### "No space left on device" (Ollama models)
```bash
# Check volume size
docker volume inspect ollama-models

# Clear old images
docker image prune -a

# Reduce model size
docker exec jupiter-ollama ollama pull mistral:7b  # Smaller than llama2
```

### "X11 forwarding not working"
```bash
# On Linux with SSH
ssh -X user@host
docker compose -f docker-compose.jupiter.yml up jupiter-desktop

# On macOS (use XQuartz)
brew install xquartz
# Then restart Docker and retry
```

### "Desktop UI won't display"
```bash
# Use headless mode (no GUI needed)
docker exec -it jupiter-desktop bash
python -c "from apps.shared.ai import SceneDetector; print('OK')"
```

---

## Cleanup

### Stop Services
```bash
docker compose -f docker-compose.julius.yml down
```

### Remove Everything
```bash
# Stop and remove containers
docker compose -f docker-compose.julius.yml down

# Remove images
docker rmi julius-tv:desktop-latest julius-tv:mobile-latest

# Remove volumes
docker volume rm julius-cache ollama-models
```

### Clean Cache (Keep Models)
```bash
docker volume rm julius-cache
```

---

## Production Deployment

### Multi-Host Setup
```bash
# Use Docker Swarm or Kubernetes
docker swarm init
docker stack deploy -c docker-compose.julius.yml julius-tv
```

### Resource Isolation
```yaml
# Per service limits (edit docker-compose.julius.yml)
cpuset_cpus: '0-3'        # Limit to specific CPU cores
cpuset_mems: '0'          # Bind to specific NUMA node
```

### Logging
```bash
# View logs
docker compose -f docker-compose.julius.yml logs -f julius-desktop

# Save logs
docker compose -f docker-compose.julius.yml logs > julius-tv.log

# Structured logging
docker exec julius-ollama python -u app.py >> /var/log/julius-tv.log 2>&1
```

---

## Testing the Stack

### Verify All Services Running
```bash
docker compose -f docker-compose.julius.yml ps
```

### Test Desktop Detection
```bash
docker exec julius-desktop python test_scene_detection_mvp.py
```

### Test Mobile Detection
```bash
docker exec julius-mobile python test_scene_detection_mvp.py
```

### Test Ollama
```bash
docker exec julius-ollama ollama pull llama2:7b
docker exec julius-ollama ollama list
```

### Full Integration Test
```bash
docker compose -f docker-compose.julius.yml exec julius-desktop bash -c "
python -c '
from apps.shared.ai import SceneDetector
from apps.shared.stream_manager import StreamManager
print(\"[PASS] Scene detection ready\")
print(\"[PASS] Stream manager ready\")
'
"
```

---

## Build Arguments

### Customize Builds
```bash
docker compose -f docker-compose.julius.yml build --build-arg PYTHON_VERSION=3.10

# Or in docker-compose.julius.yml:
build:
  context: .
  dockerfile: Dockerfile
  args:
    PYTHON_VERSION: 3.11
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Build Jupiter TV Docker Images
on: [push, release]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v4
        with:
          context: .
          file: ./apps/julius-tv-desktop-v2/Dockerfile
          push: true
          tags: julius-tv:desktop-latest
```

---

## Support & Documentation

- **Desktop GUI**: See `ARCHITECTURE.md`
- **Scene Detection**: See `MVP_SCENE_DETECTION_README.md`
- **Streaming**: See `STREAMING_COMPLETE.md`
- **Troubleshooting**: See above section or GitHub Issues

---

**Status**: ✅ Production-ready Docker setup  
**Version**: v0.1.0  
**Last Updated**: 2024
