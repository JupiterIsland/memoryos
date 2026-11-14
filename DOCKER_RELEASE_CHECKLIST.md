# DOCKER RELEASE CHECKLIST - v0.1.0

## Pre-Release (Verification)

- [x] All dependencies locked in `requirements-tv-locked.txt`
- [x] Desktop Dockerfile complete with ffmpeg + PyQt6
- [x] Mobile Dockerfile complete with ffmpeg + Kivy
- [x] docker-compose.yml includes all 3 services (desktop, mobile, ollama)
- [x] Persistent volumes configured (cache + models)
- [x] Health checks defined for all services
- [x] Resource limits set (CPU/Memory)
- [x] Network configuration (custom bridge)
- [x] Build script created and tested
- [x] Test script created and validated
- [x] Documentation complete (DOCKER_DEPLOYMENT_GUIDE.md)

## Build Phase

- [ ] Run: `bash build-docker.sh`
- [ ] Verify: All images build without errors
- [ ] Check: Images present in local Docker
  ```bash
  docker images | grep jupiter-tv
  ```
- [ ] Tag images for registry:
  ```bash
  docker tag jupiter-tv:desktop-latest your-registry/julius-tv:desktop-v0.1.0
  docker tag julius-tv:mobile-latest your-registry/julius-tv:mobile-v0.1.0
  ```

## Testing Phase

- [ ] Run: `bash test-docker.sh`
- [ ] All tests pass
- [ ] Services healthy:
  ```bash
  docker compose -f docker-compose.julius.yml ps
  ```
- [ ] Test scene detection:
  ```bash
  docker exec julius-desktop python test_scene_detection_mvp.py
  ```
- [ ] Test Ollama:
  ```bash
  docker exec julius-ollama ollama list
  ```
- [ ] Test network connectivity:
  ```bash
  docker exec julius-desktop ping ollama
  ```

## Push Phase

- [ ] Login to registry:
  ```bash
  docker login your-registry.com
  ```
- [ ] Push Desktop image:
  ```bash
  docker push your-registry/julius-tv:desktop-v0.1.0
  docker push your-registry/julius-tv:desktop-latest
  ```
- [ ] Push Mobile image:
  ```bash
  docker push your-registry/julius-tv:mobile-v0.1.0
  docker push your-registry/julius-tv:mobile-latest
  ```
- [ ] Verify images on registry:
  ```bash
  docker pull your-registry/julius-tv:desktop-v0.1.0
  docker pull your-registry/julius-tv:mobile-v0.1.0
  ```

## Documentation Phase

- [ ] Update README.md with Docker instructions
- [ ] Create DOCKER_QUICK_START.md
- [ ] Add to GitHub Releases:
  - docker-compose.julius.yml (download link)
  - requirements-tv-locked.txt (download link)
  - DOCKER_DEPLOYMENT_GUIDE.md (embed)
- [ ] Create GitHub tag:
  ```bash
  git tag -a v0.1.0 -m "Initial Docker release"
  git push origin v0.1.0
  ```

## Release Artifacts

Create GitHub Release v0.1.0 with:

### Files to Attach
1. `docker-compose.julius.yml`
2. `requirements-tv-locked.txt`
3. `build-docker.sh`
4. `test-docker.sh`
5. `DOCKER_DEPLOYMENT_GUIDE.md`

### Release Notes Template
```markdown
# Jupiter TV v0.1.0 - Docker Release

## What's New
- Production-ready Docker images
- Desktop (PyQt6) + Mobile (Kivy) containerized
- Offline AI scene detection (Ollama)
- Real torrent streaming (libtorrent)

## Quick Start
\`\`\`bash
docker compose -f docker-compose.julius.yml up
\`\`\`

## What's Inside
- Desktop app: PyQt6 + scene detection
- Mobile app: Kivy + scene detection
- Ollama runtime: CPU-based AI inference
- Persistent volumes: Torrent cache + models

## System Requirements
- Docker 20.10+
- Docker Compose 1.29+
- 8GB RAM minimum
- 10GB disk (for Ollama models)

## Documentation
See DOCKER_DEPLOYMENT_GUIDE.md for:
- Installation
- Configuration
- Troubleshooting
- Performance tuning

## Images Available
- `julius-tv:desktop-v0.1.0` (PyQt6)
- `julius-tv:mobile-v0.1.0` (Kivy)

Push to registry:
\`\`\`bash
docker tag julius-tv:desktop-latest your-registry/julius-tv:desktop-v0.1.0
docker push your-registry/julius-tv:desktop-v0.1.0
\`\`\`
```

## Post-Release Verification

- [ ] Images accessible on registry
- [ ] docker-compose.julius.yml downloads and works
- [ ] Documentation accessible
- [ ] GitHub tag created
- [ ] Release notes visible on GitHub

## Rollback Plan

If issues found:
1. Remove GitHub tag: `git tag -d v0.1.0 && git push --delete origin v0.1.0`
2. Unpush images: `docker rmi your-registry/julius-tv:*-v0.1.0`
3. Fix issues and rebuild
4. Re-release as v0.1.1

---

## Checklist Verification

When complete, fill in dates:

- Build Date: ___________
- Test Date: ___________
- Release Date: ___________
- Verified By: ___________

---

**Status**: Ready for checklist execution
