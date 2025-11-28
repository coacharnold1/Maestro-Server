# MPD Web Control - Docker Edition
# Multi-stage production build with security hardening

FROM python:3.13-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python dependencies
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.13-slim AS production

LABEL maintainer="Maestro MPD Control"
LABEL version="1.0.0"
LABEL description="Modern web interface for Music Player Daemon with 4 themes"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r mpdweb && \
    useradd -r -g mpdweb -u 1001 -s /bin/false -c "MPD Web User" mpdweb

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/cache /app/data /app/static /app/templates && \
    chown -R mpdweb:mpdweb /app

# Copy application code
COPY --chown=mpdweb:mpdweb app.py .
COPY --chown=mpdweb:mpdweb rudimentary_search.py .
COPY --chown=mpdweb:mpdweb requirements.txt .
COPY --chown=mpdweb:mpdweb static/ ./static/
COPY --chown=mpdweb:mpdweb templates/ ./templates/

# Set default environment variables
ENV MPD_HOST=mpd \
    MPD_PORT=6600 \
    MPD_TIMEOUT=10 \
    MUSIC_DIRECTORY=/music \
    APP_PORT=5003 \
    APP_HOST=0.0.0.0 \
    DEFAULT_THEME=dark \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1

# Switch to non-root user
USER mpdweb

# Health check using internal API endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5003/api/version || exit 1

# Expose port
EXPOSE 5003

# Run application
CMD ["python", "app.py"]