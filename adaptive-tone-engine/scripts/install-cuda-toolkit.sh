#!/usr/bin/env bash
set -euo pipefail

# Install CUDA Toolkit from NVIDIA repos (Ubuntu)
# Usage: sudo ./install-cuda-toolkit.sh [cuda-version]
# Example: sudo ./install-cuda-toolkit.sh 12.1

CUDA_VER=${1:-"12.1"}
DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
CODENAME=$(lsb_release -cs)

echo "Installing CUDA Toolkit $CUDA_VER for $DISTRO $CODENAME"

# Add NVIDIA package repository for CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/${CODENAME}/x86_64/cuda-${CODENAME}.pin -O /tmp/cuda.pin || true
sudo mv /tmp/cuda.pin /etc/apt/preferences.d/cuda-repository-pin-600 || true

# Add repo GPG key and repository
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/${CODENAME}/x86_64/7fa2af80.pub || true
echo "deb https://developer.download.nvidia.com/compute/cuda/repos/${CODENAME}/x86_64/ /" | sudo tee /etc/apt/sources.list.d/cuda.list

sudo apt-get update -y

# Try installing specific toolkit package, fallback to meta 'cuda-toolkit-<ver>' or 'cuda'
if ! sudo apt-get install -y "cuda-toolkit-$CUDA_VER"; then
  echo "cuda-toolkit-$CUDA_VER not available; attempting generic 'cuda' package"
  sudo apt-get install -y cuda || echo "Install may require manual steps; see README_RIVA.md for guidance"
fi

# Add environment guidance
echo "CUDA install attempted. Add to PATH and LD_LIBRARY_PATH if needed:"
echo "  export PATH=/usr/local/cuda/bin:\$PATH"
echo "  export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH"

echo "Verify with: nvcc --version or nvidia-smi"