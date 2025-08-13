# Multi-stage Dockerfile for MCP Draw.io Server
# Optimized for size and security with Draw.io CLI support

# Build stage - Python dependencies
FROM python:3.10-alpine as builder

# Set build arguments for cross-platform builds
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Install only essential build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    build-base \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + || true

# Remove build dependencies to reduce image size
RUN apk del .build-deps

# Runtime stage - Minimal execution environment
FROM node:18-alpine as runtime

# Install only essential runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ca-certificates \
    tzdata \
    tini \
    dumb-init \
    && rm -rf /var/cache/apk/* \
    && rm -rf /tmp/*

# Install Draw.io CLI globally with cache cleanup
RUN npm install -g @drawio/drawio-desktop-cli && \
    npm cache clean --force && \
    rm -rf /root/.npm /tmp/* /var/tmp/*

# Create non-root user with minimal privileges for security
RUN addgroup -g 1001 -S mcpuser && \
    adduser -S mcpuser -u 1001 -G mcpuser -s /bin/sh -h /home/mcpuser && \
    mkdir -p /home/mcpuser && \
    chown -R mcpuser:mcpuser /home/mcpuser

# Copy Python virtual environment from builder (optimized)
COPY --from=builder --chown=mcpuser:mcpuser /opt/venv /opt/venv

# Set up optimized Python environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application directory with proper permissions
WORKDIR /app
RUN mkdir -p /app/temp /app/logs /home/mcpuser/.cache && \
    chown -R mcpuser:mcpuser /app /home/mcpuser && \
    chmod 755 /app && \
    chmod 750 /app/temp /app/logs && \
    chmod 700 /home/mcpuser/.cache

# Copy application source code with minimal permissions
COPY --chown=mcpuser:mcpuser --chmod=644 src/ ./src/
COPY --chown=mcpuser:mcpuser --chmod=644 pyproject.toml setup.py README.md ./
COPY --chown=mcpuser:mcpuser --chmod=644 .env.example ./

# Make Python files executable where needed
RUN find ./src -name "*.py" -exec chmod 644 {} \; && \
    chmod 755 ./src/server.py ./src/healthcheck.py

# Switch to non-root user early for security
USER mcpuser

# Expose port (if needed for health checks) - using non-privileged port
EXPOSE 8000

# Security: Run with read-only root filesystem (uncomment if needed)
# Note: This requires proper volume mounts for writable directories
# RUN chmod -R 755 /app && chmod -R 750 /app/temp /app/logs

# Set security-focused environment variables
ENV PYTHONSAFEPATH=1 \
    PYTHONIOENCODING=utf-8

# Comprehensive health check with proper timeout and retry settings
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
    CMD python /app/src/healthcheck.py || exit 1

# Set entrypoint with dumb-init for proper signal handling and zombie reaping
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Default command to run the MCP server
CMD ["python", "-m", "src.server"]

# Metadata labels
LABEL maintainer="MCP Server Team <team@example.com>"
LABEL version="1.0.0"
LABEL description="MCP Server for Draw.io diagram generation from natural language"
LABEL org.opencontainers.image.source="https://github.com/example/mcp-drawio-server"
LABEL org.opencontainers.image.documentation="https://github.com/example/mcp-drawio-server/blob/main/README.md"
LABEL org.opencontainers.image.licenses="MIT"