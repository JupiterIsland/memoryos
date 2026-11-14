FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY apex_core/ apex_core/
COPY backend/ backend/ || true

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    numpy==1.24.3 \
    transformers==4.40.0 \
    torch==2.3.0

# Create storage directories for memory tiers
RUN mkdir -p /nvme/checkpoints && \
    mkdir -p /app/.cache/mrameda && \
    mkdir -p /app/models

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI server
CMD ["python", "-m", "uvicorn", "apex_core.backend:app", "--host", "0.0.0.0", "--port", "8000"]
