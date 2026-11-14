# Jupiter TV Mobile - Production Dockerfile
# Includes: Kivy + ffmpeg + libtorrent + Ollama client

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Kivy dependencies (SDL2)
    libsdl2-2.0-0 libsdl2-dev \
    libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    zlib1g-dev \
    # FFmpeg + ffprobe (for scene detection)
    ffmpeg \
    # Libtorrent dependencies
    libssl3 libgeoip1 \
    # Build tools (temporary)
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-tv.txt .

# Install Python dependencies
RUN pip install --no-cache-dir \
    -r requirements-tv.txt

# Copy application code
COPY apps /app/apps
COPY . /app

# Create cache directories
RUN mkdir -p /tmp/jptv /home/app/.ollama

# Kivy configuration
ENV KIVY_WINDOW_ICON="app_icon.png"
ENV KIVY_METRICS_DENSITY=1.0
ENV OLLAMA_MODELS=/home/app/.ollama

# Expose port for optional remote access
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from apps.shared.ai import SceneDetector; print('OK')" || exit 1

# Default command
CMD ["python", "apps/jupiter-tv-mobile/main.py"]
