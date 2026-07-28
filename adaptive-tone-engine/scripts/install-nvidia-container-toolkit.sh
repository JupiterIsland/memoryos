#!/usr/bin/env bash
set -euo pipefail

# Install NVIDIA Container Toolkit (nvidia-docker2 / nvidia-container-toolkit)
# Usage: sudo ./install-nvidia-container-toolkit.sh

distribution="$(. /etc/os-release; echo $ID$VERSION_ID)"

# Add the package repositories
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update -y
sudo apt-get install -y nvidia-docker2 nvidia-container-toolkit || sudo apt-get install -y nvidia-container-toolkit

# Restart docker
sudo systemctl restart docker

# Test with sample image
echo "Testing NVIDIA runtime with docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi"
sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi || echo "Test failed; ensure GPU drivers are installed and docker restarted"
