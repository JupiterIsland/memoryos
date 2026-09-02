FROM python:3.11-slim

WORKDIR /app

# Install system deps for PyQt6 + ffmpeg
RUN apt-get update && apt-get install -y \
    libqt6gui6 libqt6core6 libqt6multimedia6 \
    ffmpeg xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .
COPY ../shared /app/apps/shared

# Run with virtual display for headless
CMD ["xvfb-run", "-a", "python", "app.py"]
