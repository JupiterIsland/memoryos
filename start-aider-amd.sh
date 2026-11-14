#!/usr/bin/env bash
# start-aider-amd.sh
# Linux / Ubuntu / WSL2 Launcher for AMD Token Lab Dual-Brain Aider Agent
# Pairs Gemma-4-31B-IT (Architect) + Qwen3.8-27B (8K Surgical Diff Editor) + MiniCPM5-2B (Fast Scout)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: .env file not found at $ENV_FILE. Copy .env.example to .env and set TOKENLAB_API_KEY." >&2
    exit 1
fi

# Load .env safely
set -a
# shellcheck disable=SC1090
source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | sed 's/\r$//')
set +a

MODEL="${TOKENLAB_MODEL:-Gemma-4-31B-IT}"
EDITOR_MODEL="${TOKENLAB_EDITOR_MODEL:-Qwen3.8-27B}"
WEAK_MODEL="${TOKENLAB_WEAK_MODEL:-MiniCPM5-2B}"
API_BASE="${TOKENLAB_BASE_URL:-${TOKENLAB_API_BASE:-https://api.tokenlab.amd.com/v1}}"
API_KEY="${TOKENLAB_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
    echo "ERROR: TOKENLAB_API_KEY is not set in $ENV_FILE" >&2
    exit 1
fi

export OPENAI_API_BASE="$API_BASE"
export OPENAI_BASE_URL="$API_BASE"
export OPENAI_API_KEY="$API_KEY"
export OPENAI_MODEL_NAME="$MODEL"
export PATH="$HOME/.local/bin:$PATH"

# Configure AMD Zen Software Studio v5.3 (AOCL / ZenDNN) optimal thread affinity
CORES="$(nproc --all 2>/dev/null || echo 8)"
export OMP_NUM_THREADS="$CORES"
export BLIS_NUM_THREADS="$CORES"
export ZENDNN_PRIMITIVE_CACHE_CAPACITY="1024"

echo "=========================================================="
echo "  AMD Token Lab Dual-Brain Aider Agent (Linux / WSL2)"
echo "=========================================================="
echo "  API Base               : $API_BASE"
echo "  Architect Brain (31B)  : $MODEL"
echo "  Surgical Diff Brain    : $EDITOR_MODEL (editor-diff, 8K)"
echo "  Fast Scout Brain (2B)  : $WEAK_MODEL"
echo "=========================================================="

if ! command -v aider >/dev/null 2>&1; then
    echo "[*] Installing Aider via aider-install..."
    python3 -m pip install --upgrade aider-install
    aider-install
fi

SETTINGS_ARGS=()
[[ -f "$REPO_ROOT/.aider.model.settings.yml" ]] && SETTINGS_ARGS+=(--model-settings-file .aider.model.settings.yml)
[[ -f "$REPO_ROOT/.aider.model.metadata.json" ]] && SETTINGS_ARGS+=(--model-metadata-file .aider.model.metadata.json)

DEFAULT_FILES=(
    "apps/quiet_advisor_ui/server.py"
    "src/memoryos/router.py"
    "src/memoryos/server.py"
)

exec aider \
    --architect \
    --model "openai/$MODEL" \
    --editor-model "openai/$EDITOR_MODEL" \
    --editor-edit-format editor-diff \
    --weak-model "openai/$WEAK_MODEL" \
    "${SETTINGS_ARGS[@]}" \
    --no-show-model-warnings \
    "$@" \
    "${DEFAULT_FILES[@]}"
