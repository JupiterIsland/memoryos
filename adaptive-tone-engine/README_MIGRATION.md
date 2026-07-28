Migration and Docker setup

Overview
- These scripts help install Docker on Ubuntu and AlmaLinux 9, and migrate git repositories from AlmaLinux machines to a single Ubuntu host while preserving history.

Files
- scripts/install-docker-ubuntu.sh: Installs Docker Engine on Ubuntu, adds specified user to docker group.
- scripts/install-docker-alma9.sh: Attempts Docker CE install on AlmaLinux 9; falls back to Podman if Docker is unavailable.
- scripts/migrate-repos-alma.sh: Run on AlmaLinux to mirror local git repos and scp bare mirrors to the Ubuntu host.
- scripts/receive-repos-ubuntu.sh: Run on Ubuntu to convert incoming bare mirrors into working clones under the destination Dev folder.
- docker-compose.yml: Compose file to run the Adaptive Tone Engine container.

Typical workflow
1. On the Ubuntu host, create the destination folder: sudo mkdir -p /home/ubuntu/Dev && sudo chown ubuntu:ubuntu /home/ubuntu/Dev
2. Run scripts/install-docker-ubuntu.sh on Ubuntu to prepare Docker.
3. On each AlmaLinux host, run scripts/install-docker-alma9.sh to prepare Docker/Podman, then run scripts/migrate-repos-alma.sh <ubuntu-user> <ubuntu-host> /home/ubuntu/Dev /home/alma/Dev
4. Back on Ubuntu, run scripts/receive-repos-ubuntu.sh /home/ubuntu/Dev to create working clones.

Notes & caveats
- SSH access between hosts is required. For large repos consider rsync instead of scp.
- Scripts assume default user paths; adjust SOURCE and DEST paths as needed.
- If Docker CE install fails on AlmaLinux, Podman is a compatible alternative; the podman-docker package provides a docker CLI wrapper.
- Always verify backups before mass-moving repositories.
