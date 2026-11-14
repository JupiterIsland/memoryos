#!/bin/bash
# Build Jupiter TV Docker images

set -e

echo "==============================================="
echo "BUILDING JUPITER TV DOCKER IMAGES"
echo "==============================================="
echo ""

REGISTRY="${REGISTRY:-local}"
VERSION="${VERSION:-latest}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Build Desktop Image
echo -e "${BLUE}[1/3] Building Desktop Image...${NC}"
docker build \
  -f apps/jupiter-tv-desktop-v2/Dockerfile \
  -t ${REGISTRY}/jupiter-tv:desktop-${VERSION} \
  -t ${REGISTRY}/jupiter-tv:desktop-latest \
  .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}[OK] Desktop image built${NC}"
else
  echo -e "${RED}[FAIL] Desktop image build failed${NC}"
  exit 1
fi

echo ""

# Build Mobile Image
echo -e "${BLUE}[2/3] Building Mobile Image...${NC}"
docker build \
  -f apps/jupiter-tv-mobile/Dockerfile \
  -t ${REGISTRY}/jupiter-tv:mobile-${VERSION} \
  -t ${REGISTRY}/jupiter-tv:mobile-latest \
  .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}[OK] Mobile image built${NC}"
else
  echo -e "${RED}[FAIL] Mobile image build failed${NC}"
  exit 1
fi

echo ""

# Build Compose Stack
echo -e "${BLUE}[3/3] Verifying Docker Compose...${NC}"
docker compose -f docker-compose.jupiter.yml config > /dev/null

if [ $? -eq 0 ]; then
  echo -e "${GREEN}[OK] Docker Compose validated${NC}"
else
  echo -e "${RED}[FAIL] Docker Compose validation failed${NC}"
  exit 1
fi

echo ""
echo "==============================================="
echo -e "${GREEN}BUILD COMPLETE${NC}"
echo "==============================================="
echo ""
echo "Images built:"
echo "  - ${REGISTRY}/jupiter-tv:desktop-${VERSION}"
echo "  - ${REGISTRY}/jupiter-tv:mobile-${VERSION}"
echo ""
echo "To start services:"
echo "  docker compose -f docker-compose.jupiter.yml up"
echo ""
echo "To test:"
echo "  docker exec jupiter-desktop python test_scene_detection_mvp.py"
echo ""
