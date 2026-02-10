# SentinelAI Box - Production Dockerfile
# Multi-stage build for Python backend + Streamlit frontend

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY src/backend/requirements.txt /app/requirements-backend.txt
COPY src/frontend/requirements.txt /app/requirements-frontend.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements-backend.txt && \
    pip install --no-cache-dir -r /app/requirements-frontend.txt

# Download spaCy German model
RUN python -m spacy download de_core_news_lg

# Copy source code
COPY src/ /app/src/

# Create data directory
RUN mkdir -p /app/data /app/logs

# Environment variables
ENV PYTHONPATH=/app/src/backend:/app/src/frontend:/app
ENV PYTHONUNBUFFERED=1

# Entrypoint script to decide which service to run
COPY deploy/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
