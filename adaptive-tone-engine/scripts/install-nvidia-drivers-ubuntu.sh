#!/usr/bin/env bash
set -euo pipefail

# Install NVIDIA drivers on Ubuntu (uses ubuntu-drivers)
# Usage: sudo ./install-nvidia-drivers-ubuntu.sh

echo "Updating apt and installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y build-essential dkms linux-headers-$(uname -r) ubuntu-drivers-common curl

echo "Detecting recommended driver..."
RECOMMENDED=$(ubuntu-drivers devices | awk '/recommended/ {print $3; exit}') || true
if [ -n "$RECOMMENDED" ]; then
  echo "Recommended driver: $RECOMMENDED"
  sudo apt-get install -y "$RECOMMENDED"
else
  echo "No recommended driver found by ubuntu-drivers. Installing latest nvidia-driver-535 as fallback."
  sudo apt-get install -y nvidia-driver-535 || sudo apt-get install -y nvidia-driver-520 || true
fi

echo "Driver installation complete. Run 'nvidia-smi' to verify. A reboot may be required."
