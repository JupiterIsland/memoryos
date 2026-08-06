#!/bin/bash
set -e

# Simple start script for development
cd /opt/jupiter-tv || cd "$(pwd)"
python3 src/jupiter_tv.py "$@"
