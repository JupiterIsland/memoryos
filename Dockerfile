# Multi-stage build for MemoryOS CLI
FROM python:3.11-slim AS builder

WORKDIR /build
# Copy dependency files first for better layer caching
COPY pyproject.toml README.md ./
COPY memoryos ./memoryos

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip uninstall -y build  # Remove build tool from final image

# Runtime stage
FROM python:3.11-slim

# Install system dependencies in single RUN to reduce layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY --chown=appuser:appuser --from=builder /build/dist /tmp/dist

RUN pip install --no-cache-dir /tmp/dist/*.whl && \
    rm -rf /tmp/dist /root/.cache

# Switch to non-root user
USER appuser

# Set work directory with proper permissions
VOLUME ["/work"]
WORKDIR /work

ENTRYPOINT ["memoryos"]
CMD ["--help"]
