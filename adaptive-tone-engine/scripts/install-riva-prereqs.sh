#!/usr/bin/env bash
set -euo pipefail

# Check prerequisites for NVIDIA Riva on Ubuntu
# Usage: ./install-riva-prereqs.sh

echo "Checking for NVIDIA GPU..."
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi not found. Please install NVIDIA drivers first."
  exit 1
fi

echo "Checking Docker availability..."
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Install Docker and docker-compose first. See scripts/install-docker-ubuntu.sh"
  exit 1
fi

echo "Checking nvidia-container-toolkit..."
if ! dpkg -l | grep -q nvidia-container-toolkit; then
  echo "nvidia-container-toolkit not installed. Run scripts/install-nvidia-container-toolkit.sh"
  exit 1
fi

# Riva requires NGC access and model downloads. Provide next-step instructions.
cat <<'EOF'
Prerequisites satisfied (approx). Next steps to get Riva:

1) Sign up/log in to NVIDIA NGC and create an API key: https://catalog.ngc.nvidia.com/
2) On the Ubuntu host, install the 'ngc' CLI and configure it with your API key.
3) Use the Riva Quick Start package (available on NGC) and follow its riva-setup instructions to download models.
   - The Riva Quick Start includes scripts to pull container images and model archives; you must accept EULAs on NGC.
4) Run the Riva setup (it typically provides a docker-compose-based launcher).

See README_RIVA.md in the repository for a step-by-step guide.
EOF
