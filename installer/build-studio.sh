#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OS_NAME="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH_NAME="$(uname -m)"
PKG_NAME="JupiterStudio-${OS_NAME}-${ARCH_NAME}"

echo "[1/3] Checking PyInstaller..."
python3 -m PyInstaller --version

echo "[2/3] Building standalone dist/JupiterStudio..."
python3 -m PyInstaller --clean --noconfirm installer/JupiterStudio.spec

if [[ ! -f "dist/JupiterStudio" ]]; then
  echo "Build failed: dist/JupiterStudio not found." >&2
  exit 1
fi

echo "[3/3] Packaging dist/${PKG_NAME}.tar.gz..."
STAGE_DIR="dist/${PKG_NAME}"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp dist/JupiterStudio "$STAGE_DIR/JupiterStudio"
cp .env.example "$STAGE_DIR/.env.example"
cp README.md "$STAGE_DIR/README.md"
[[ -f LICENSE ]] && cp LICENSE "$STAGE_DIR/LICENSE"

tar -czf "dist/${PKG_NAME}.tar.gz" -C dist "$PKG_NAME"
echo "[OK] Built dist/${PKG_NAME}.tar.gz"
