# Stage 1: Builder
FROM python:3.11-slim as builder

# Use uv for faster dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
# --system flag installs to the system site-packages (appropriate for Docker)
RUN uv pip install --system .

# Stage 2: Final
FROM python:3.11-slim

# Install runtime dependencies
# ffmpeg: for multimedia processing
# libpq5: for PostgreSQL connection
# curl: for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security: Run as non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Ensure appuser has permissions to the app directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check to ensure service is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the application with 2 workers for concurrency
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
