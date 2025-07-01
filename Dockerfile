# OpenAI Whisper Web Interface - Docker Container
# Multi-stage build for optimized production image

FROM python:3.11-slim as builder

# Build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies in virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages (use container-optimized requirements)
COPY requirements-container.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements-container.txt

# Production stage
FROM python:3.11-slim

# Runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application user
RUN useradd -m -s /bin/bash whisper && \
    usermod -aG audio whisper

# Application directory
WORKDIR /app

# Copy application files
COPY src/ ./src/
COPY create-ssl-cert.sh ./
COPY auto-update.sh ./
COPY scripts/debug-container.sh ./scripts/
COPY requirements.txt ./

# Set permissions
RUN chown -R whisper:whisper /app && \
    chmod +x create-ssl-cert.sh auto-update.sh scripts/debug-container.sh

# Create directories for volumes
RUN mkdir -p /app/ssl /app/models /app/data /app/logs && \
    chown -R whisper:whisper /app/ssl /app/models /app/data /app/logs

# Switch to application user
USER whisper

# Environment variables
ENV PYTHONPATH=/app \
    FLASK_ENV=production \
    WHISPER_MODEL=base \
    MAX_UPLOAD_SIZE=100MB \
    HTTPS_PORT=5001 \
    SSL_CERT_PATH=/app/ssl/whisper-appliance.crt \
    SSL_KEY_PATH=/app/ssl/whisper-appliance.key

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -k -f https://localhost:5001/health || exit 1

# Expose HTTPS port
EXPOSE 5001

# Copy and set entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
USER whisper

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python3", "/app/src/main.py"]
