# SentinelAI Box - Production Dockerfile
# Multi-stage build for Python backend + Streamlit frontend

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY src/backend/requirements.txt /app/requirements-backend.txt
COPY src/frontend/requirements.txt /app/requirements-frontend.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements-backend.txt && \
    pip install --no-cache-dir -r /app/requirements-frontend.txt

# Install spaCy German model from local .whl (OFFLINE - kein Download!)
COPY src/backend/models/de_core_news_lg-3.8.0-py3-none-any.whl /tmp/de_core_news_lg-3.8.0-py3-none-any.whl
RUN pip install --no-cache-dir /tmp/de_core_news_lg-3.8.0-py3-none-any.whl && rm /tmp/de_core_news_lg-3.8.0-py3-none-any.whl

# Copy source code
COPY src/ /app/src/

# Create non-root user for running the application
RUN groupadd -r -g 1000 sentinel && useradd -r -u 1000 -g sentinel -d /app -s /sbin/nologin sentinel

# Create data directories and set ownership
RUN mkdir -p /app/data /app/logs && \
    chown -R sentinel:sentinel /app

# Environment variables
ENV PYTHONPATH=/app/src/backend:/app/src/frontend:/app
ENV PYTHONUNBUFFERED=1

# Entrypoint script to decide which service to run
COPY deploy/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && chown sentinel:sentinel /app/entrypoint.sh

# Run as non-root user
USER sentinel

ENTRYPOINT ["/app/entrypoint.sh"]
