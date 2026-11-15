#!/usr/bin/env bash
# start-aider-deepseek.sh
# Launch Aider powered by DeepSeek-V4.1-Flash on AMD Token Lab
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  export $(grep -v '^#' .env | xargs -d '\n')
fi

export OPENAI_API_KEY="${TOKENLAB_API_KEY:-}"
export OPENAI_API_BASE="${TOKENLAB_BASE_URL:-https://api.tokenlab.amd.com/v1}"

echo "=========================================================="
echo "  Aider Coding Agent — DeepSeek-V4.1-Flash Mode"
echo "  Target: ${OPENAI_API_BASE}"
echo "=========================================================="

exec aider \
  --model openai/DeepSeek-V4.1-Flash \
  --model-metadata-file .aider.model.metadata.json \
  --model-settings-file .aider.model.settings.yml \
  --no-auto-commits \
  --stream \
  "$@"
