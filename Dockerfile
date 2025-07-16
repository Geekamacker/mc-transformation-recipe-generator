# Multi-stage Dockerfile for optimized production build
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build dependencies and Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PUID=99
ENV PGID=100

WORKDIR /app

# Install system dependencies and clean up in one layer
RUN apt-get update && apt-get install -y \
    curl \
    gosu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY app.py index.html ./

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create directories and set permissions
RUN mkdir -p data output textures/blocks

# Copy data files
COPY data/ ./data/

# Copy output directory
COPY output/ ./output/

# Copy pack icon
COPY pack_icon.png ./pack_icon.png

# Copy textures
COPY textures/ ./textures/

# Health check with correct port
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5097/health || exit 1

# Expose port
EXPOSE 5097

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run with optimized gunicorn settings
CMD ["gunicorn", "--bind", "0.0.0.0:5097", "--timeout", "120", "--workers", "2", "--worker-class", "sync", "--max-requests", "1000", "--max-requests-jitter", "100", "--preload", "app:app"]