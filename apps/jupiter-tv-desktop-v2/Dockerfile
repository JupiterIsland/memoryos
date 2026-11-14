# Jupiter TV Desktop - Lightweight Client Dockerfile
# Includes: PyQt6 + headless CPU OpenCV + ffmpeg (NO torch / NO local Ollama)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libqt6gui6 libqt6core6 libqt6multimedia6 \
    libqt6network6 qt6-qpa-plugins \
    ffmpeg \
    xvfb x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy lean desktop client requirements
COPY requirements-desktop.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-desktop.txt

# Copy desktop client and bridge
COPY apps /app/apps
COPY quiet_advisor_ui.py /app/

RUN mkdir -p /tmp/jptv

ENV DISPLAY=:99
ENV QT_QPA_PLATFORM=offscreen
ENV MEMORYOS_ROUTER_URL=http://memoryos-router:5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from apps.jupiter_tv_desktop_v2.router_client import MemoryOSRouterClient; print('OK')" || exit 1

CMD ["xvfb-run", "-a", "python", "apps/jupiter-tv-desktop-v2/app.py"]
