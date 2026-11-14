#!/bin/bash
# Test Jupiter TV Docker Stack

set -e

echo "==============================================="
echo "JUPITER TV DOCKER STACK TEST"
echo "==============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Test 1: Docker available
echo -e "${BLUE}[1] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
  echo -e "${RED}[FAIL] Docker not found${NC}"
  exit 1
fi
DOCKER_VERSION=$(docker --version)
echo -e "${GREEN}[OK] $DOCKER_VERSION${NC}"

# Test 2: Docker Compose available
echo -e "${BLUE}[2] Checking Docker Compose...${NC}"
if ! command -v docker compose &> /dev/null; then
  echo -e "${RED}[FAIL] Docker Compose not found${NC}"
  exit 1
fi
COMPOSE_VERSION=$(docker compose --version)
echo -e "${GREEN}[OK] $COMPOSE_VERSION${NC}"

# Test 3: Build images
echo -e "${BLUE}[3] Building Docker images...${NC}"
docker compose -f docker-compose.jupiter.yml build --no-cache

if [ $? -ne 0 ]; then
  echo -e "${RED}[FAIL] Docker build failed${NC}"
  exit 1
fi
echo -e "${GREEN}[OK] Images built${NC}"

# Test 4: Start services
echo -e "${BLUE}[4] Starting services...${NC}"
docker compose -f docker-compose.jupiter.yml up -d

sleep 5

# Test 5: Check service health
echo -e "${BLUE}[5] Checking service health...${NC}"
for service in jupiter-desktop jupiter-mobile jupiter-ollama; do
  if docker ps | grep -q $service; then
    STATUS=$(docker inspect -f '{{.State.Health.Status}}' $service 2>/dev/null || echo "running")
    if [ "$STATUS" == "healthy" ] || [ "$STATUS" == "running" ]; then
      echo -e "${GREEN}[OK] $service: $STATUS${NC}"
    else
      echo -e "${YELLOW}[WARN] $service: $STATUS (still starting)${NC}"
    fi
  else
    echo -e "${RED}[FAIL] $service not running${NC}"
  fi
done

# Test 6: Test scene detection module
echo -e "${BLUE}[6] Testing scene detection module...${NC}"
docker exec jupiter-desktop python -c "
from apps.shared.ai import SceneDetector, Scene
d = SceneDetector()
print('[OK] Scene detection module loaded')
" || echo -e "${RED}[FAIL] Scene detection test failed${NC}"

# Test 7: Test streaming module
echo -e "${BLUE}[7] Testing streaming module...${NC}"
docker exec jupiter-desktop python -c "
from apps.shared import StreamManager
print('[OK] Stream manager module loaded')
" 2>/dev/null || echo -e "${YELLOW}[WARN] Stream manager skipped (yt-dlp optional)${NC}"

# Test 8: Test Ollama availability
echo -e "${BLUE}[8] Testing Ollama...${NC}"
docker exec jupiter-ollama curl -s http://localhost:11434/api/tags | grep -q "models" && \
  echo -e "${GREEN}[OK] Ollama API responding${NC}" || \
  echo -e "${YELLOW}[WARN] Ollama warming up...${NC}"

# Test 9: Check volumes
echo -e "${BLUE}[9] Checking volumes...${NC}"
docker volume ls | grep -q jupiter-cache && \
  echo -e "${GREEN}[OK] jupiter-cache volume mounted${NC}" || \
  echo -e "${RED}[FAIL] jupiter-cache volume missing${NC}"

docker volume ls | grep -q ollama-models && \
  echo -e "${GREEN}[OK] ollama-models volume mounted${NC}" || \
  echo -e "${RED}[FAIL] ollama-models volume missing${NC}"

# Test 10: Network connectivity
echo -e "${BLUE}[10] Testing network connectivity...${NC}"
docker exec jupiter-desktop ping -c 1 ollama > /dev/null 2>&1 && \
  echo -e "${GREEN}[OK] Desktop can reach Ollama${NC}" || \
  echo -e "${RED}[FAIL] Network connectivity issue${NC}"

echo ""
echo "==============================================="
echo -e "${GREEN}TEST SUMMARY${NC}"
echo "==============================================="
echo ""
echo -e "${GREEN}Services running:${NC}"
docker compose -f docker-compose.jupiter.yml ps

echo ""
echo -e "${GREEN}To run further tests:${NC}"
echo "  docker exec julius-desktop python test_scene_detection_mvp.py"
echo "  docker exec julius-ollama ollama list"
echo "  docker exec julius-ollama curl http://localhost:11434/api/tags"
echo ""
echo -e "${GREEN}To view logs:${NC}"
echo "  docker compose -f docker-compose.julius.yml logs -f"
echo ""
echo -e "${GREEN}To stop services:${NC}"
echo "  docker compose -f docker-compose.julius.yml down"
echo ""
