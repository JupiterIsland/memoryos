NVIDIA Riva quickstart and prerequisites

This document describes how to prepare an Ubuntu host to run NVIDIA Riva (speech AI server).

Summary
- Install NVIDIA drivers, CUDA (if required by your workloads), and the NVIDIA Container Toolkit.
- Obtain NVIDIA NGC credentials and the Riva Quick Start package.
- Run the Riva quickstart scripts to pull Riva images and download models. Riva requires acceptance of EULAs on NGC.

Prerequisites (Ubuntu)
- A supported NVIDIA GPU and up-to-date kernel
- Sudo access
- Internet connectivity to access NVIDIA repos and NGC
- Docker (installed) and nvidia-container-toolkit

Scripts included
- scripts/install-nvidia-drivers-ubuntu.sh — Installs drivers via ubuntu-drivers (may require reboot)
- scripts/install-cuda-toolkit.sh — Adds CUDA repo and attempts to install the toolkit
- scripts/install-nvidia-container-toolkit.sh — Installs nvidia-docker2 / nvidia-container-toolkit and restarts Docker
- scripts/install-riva-prereqs.sh — Checks GPU, Docker, and nvidia-container-toolkit and outlines next steps for Riva

High-level steps
1) On Ubuntu host: run the driver installer and reboot if needed
   sudo ./scripts/install-nvidia-drivers-ubuntu.sh
   sudo reboot

2) Install CUDA toolkit (optional, needed for development)
   sudo ./scripts/install-cuda-toolkit.sh 12.1
   # add PATH/LD_LIBRARY_PATH to ~/.bashrc if necessary

3) Install NVIDIA Container Toolkit
   sudo ./scripts/install-nvidia-container-toolkit.sh

4) Prepare Riva (manual steps because NGC/EULA)
   - Create an NGC account and API key
   - Install ngc CLI and authenticate: https://docs.nvidia.com/ngc/ngc-quick-start-guide/index.html
   - Obtain Riva Quick Start package from NGC (requires EULA acceptance)
   - Follow Riva Quick Start instructions: run riva-setup, which downloads models then launches services via docker-compose.

Notes and caveats
- Riva images and models are sizable; ensure sufficient disk space.
- Model downloads require NGC authentication. This cannot be automated without your API key and explicit consent.
- If your Docker uses cgroup v2, recent NVIDIA container toolkit versions support it; consult NVIDIA docs for any additional flags.

Support
- NVIDIA Riva docs: https://developer.nvidia.com/riva
- NGC: https://ngc.nvidia.com
