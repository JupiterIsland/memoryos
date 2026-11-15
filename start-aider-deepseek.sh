#!/usr/bin/env bash
# start-aider-deepseek.sh
# Launch Aider powered by DeepSeek-V4.1-Flash on AMD Token Lab
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  set -a
  # Strip Windows CRLF line endings cleanly before sourcing
  source <(tr -d '\r' < .env)
  set +a
fi

export OPENAI_API_KEY="${TOKENLAB_API_KEY:-}"
export OPENAI_API_BASE="${TOKENLAB_BASE_URL:-https://api.tokenlab.amd.com/v1}"

echo "=========================================================="
echo "  Aider Coding Agent — DeepSeek-V4.1-Flash Mode"
echo "  Target: ${OPENAI_API_BASE}"
echo "=========================================================="

AIDER_BIN=""
if command -v aider >/dev/null 2>&1; then
  AIDER_BIN="aider"
elif [[ -f "/mnt/c/Users/RJMed/.local/bin/aider.exe" ]]; then
  AIDER_BIN="/mnt/c/Users/RJMed/.local/bin/aider.exe"
fi

if [[ -z "$AIDER_BIN" ]]; then
  echo "ERROR: aider not found. Running with Windows aider.exe fallback..."
  AIDER_BIN="/mnt/c/Users/RJMed/.local/bin/aider.exe"
fi

exec "$AIDER_BIN" \
  --model openai/DeepSeek-V4.1-Flash \
  --model-metadata-file .aider.model.metadata.json \
  --model-settings-file .aider.model.settings.yml \
  --no-auto-commits \
  --stream \
  "$@"
