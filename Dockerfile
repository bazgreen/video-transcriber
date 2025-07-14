# Production-Ready Dockerfile
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-full.txt

# Development stage
FROM base as development
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
COPY . .
RUN chown -R app:app /app
USER app
CMD ["python", "main.py"]

# Production stage
FROM base as production
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/data /app/logs /app/results && \
    chown -R app:app /app

# Install production-specific dependencies
RUN pip install --no-cache-dir gunicorn gevent

# Setup health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

USER app

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "300", "main:app"]

# GPU-enabled stage for AI processing
FROM nvidia/cuda:11.8-runtime-ubuntu22.04 as gpu-production
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    ffmpeg \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

# Copy requirements and install
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-full.txt

# Install GPU-specific packages
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy application
COPY --chown=app:app . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "gevent", "--timeout", "600", "main:app"]
