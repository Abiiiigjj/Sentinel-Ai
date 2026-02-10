#!/bin/bash
# Entrypoint script - decides which service to start

set -e

SERVICE_TYPE=${SERVICE_TYPE:-backend}

if [ "$SERVICE_TYPE" = "backend" ]; then
    echo "🚀 Starting SentinelAI Backend..."
    cd /app
    exec uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
elif [ "$SERVICE_TYPE" = "frontend" ]; then
    echo "🎨 Starting SentinelAI Frontend..."
    cd /app
    exec streamlit run src/frontend/app.py --server.port=8501 --server.address=0.0.0.0
else
    echo "❌ Unknown SERVICE_TYPE: $SERVICE_TYPE"
    echo "Valid options: backend, frontend"
    exit 1
fi
