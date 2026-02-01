# Discovery API Dockerfile
# Multi-stage build for smaller production images

# =============================================================================
# Stage 1: Builder - Install dependencies and build wheels
# =============================================================================
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY api/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.12-slim AS runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="Discovery API" \
      org.opencontainers.image.description="O*NET-powered opportunity discovery service" \
      org.opencontainers.image.vendor="Amplify.AI" \
      org.opencontainers.image.version="0.1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Application settings
    APP_HOME=/app \
    APP_USER=discovery \
    APP_UID=1000 \
    APP_GID=1000 \
    # API settings
    API_HOST=0.0.0.0 \
    API_PORT=8001 \
    # Python path for module discovery
    PYTHONPATH=/app/src

WORKDIR $APP_HOME

# Create non-root user for security
RUN groupadd --gid $APP_GID $APP_USER \
    && useradd --uid $APP_UID --gid $APP_GID --shell /bin/bash --create-home $APP_USER

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder stage and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY api/src/ ./src/

# Change ownership to non-root user
RUN chown -R $APP_USER:$APP_USER $APP_HOME

# Switch to non-root user
USER $APP_USER

# Expose the API port
EXPOSE 8001

# Health check - verify the API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8001/health || exit 1

# Run uvicorn server
CMD ["uvicorn", "discovery.main:app", "--host", "0.0.0.0", "--port", "8001"]
