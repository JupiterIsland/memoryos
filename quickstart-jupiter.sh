#!/bin/bash
# Quick start for Jupiter TV Refactored Apps

echo "🚀 Jupiter TV Apps - Quick Start"
echo "=================================="
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-tv.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "Choose your app:"
echo ""
echo "Desktop (PyQt6):"
echo "  python apps/jupiter-tv-desktop-v2/app.py"
echo ""
echo "Mobile (Kivy):"
echo "  python apps/jupiter-tv-mobile/main.py"
echo ""
echo "Docker Desktop:"
echo "  docker build -f apps/jupiter-tv-desktop-v2/Dockerfile -t jupiter-desktop ."
echo "  docker run -it jupiter-desktop"
echo ""
echo "Docker Mobile:"
echo "  docker build -f apps/jupiter-tv-mobile/Dockerfile -t jupiter-mobile ."
echo "  docker run -it jupiter-mobile"
echo ""
echo "Docker Compose (both):"
echo "  docker compose -f docker-compose.jupiter.yml up"
echo ""
