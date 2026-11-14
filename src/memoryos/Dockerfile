# Multi-stage build: MemoryOS + Quiet Advisor + Jupiter TV
# Stage 1: Builder (torch, CUDA dependencies)
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies for torch + opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Pre-download torch (CPU or GPU variant — set BUILD_TORCH_VARIANT env)
RUN pip install --user --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (lean image with dependencies)
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python site-packages from builder
COPY --from=builder /root/.local /root/.local

# Set PATH
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TOKENLAB_API_KEY=${TOKENLAB_API_KEY} \
    NVIDIA_API_KEY=${NVIDIA_API_KEY} \
    OPENAI_API_KEY=${OPENAI_API_KEY}

# Copy application
COPY . .

# Create data directories
RUN mkdir -p \
    /app/memory/timeline \
    /app/memory/heatstream \
    /app/tlb_hot_cache \
    /app/checkpoints \
    /app/graph \
    /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default: Start MemoryOS CLI (override with docker run -it memoryos memoryos <command>)
ENTRYPOINT ["python", "-m", "memoryos.cli"]
CMD ["--help"]
