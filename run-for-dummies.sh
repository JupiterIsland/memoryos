#!/usr/bin/env bash
# ==============================================================================
# MemoryOS // The Quiet Advisor — "For Dummies" 1-Command Launcher (Linux/WSL2)
# Flagship Model: Gemma-4-31B-IT (AMD Token Lab)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================="
echo "  MemoryOS // The Quiet Advisor (For Dummies Edition)"
echo "  Flagship Model: Gemma-4-31B-IT (AMD Token Lab)"
echo "====================================================="

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "[1/4] Created .env from .env.example (add your TOKENLAB_API_KEY later if needed)."
else
  echo "[1/4] Found .env configuration."
fi

if [[ -f .env ]]; then
  set -a
  source <(tr -d '\r' < .env)
  set +a
fi

export MEMORYOS_DEFAULT_MODEL="${MEMORYOS_DEFAULT_MODEL:-Gemma-4-31B-IT}"

if [[ ! -f QuietAdvisorDB.sqlite ]]; then
  echo "[2/4] Seeding showcase database (50 inferences, 7 cards, 20 checkpoints)..."
  python3 -B seed_gamer_showcase.py >/dev/null
else
  echo "[2/4] Showcase database ready (QuietAdvisorDB.sqlite)."
fi

echo "[3/4] Checking Gemma-4-31B-IT & Cloud Provider readiness..."
python3 -B -c "from src.memoryos.router import get_cloud_provider_status; s = get_cloud_provider_status(); print('      AMD Token Lab configured:', s['amd_tokenlab']['configured']); print('      DigitalOcean MI300X configured:', s['digitalocean_mi300x']['configured'])"

echo "[4/4] Starting Quiet Advisor Dashboard at http://127.0.0.1:8765 ..."
echo "      Press Ctrl+C to stop."
exec python3 -B apps/quiet_advisor_ui/server.py --host 127.0.0.1 --port 8765 --db "${QUIET_ADVISOR_DB:-QuietAdvisorDB.sqlite}" --no-browser
