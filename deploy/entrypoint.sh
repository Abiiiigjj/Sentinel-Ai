#!/bin/bash
# Entrypoint script - decides which service to start

set -e

SERVICE_TYPE=${SERVICE_TYPE:-backend}

if [ "$SERVICE_TYPE" = "backend" ]; then
    echo "🚀 Starting SentinelAI Backend (SECURE MODE)..."
    # WICHTIG: --host 127.0.0.1 bindet die API nur an Localhost.
    # Kein Zugriff von außen möglich!
    cd /app
    exec uvicorn src.backend.main:app --host 127.0.0.1 --port 8000

elif [ "$SERVICE_TYPE" = "frontend" ]; then
    echo "🎨 Starting SentinelAI Frontend..."
    # Frontend muss auf 0.0.0.0 hören, damit der Handwerker
    # via LAN darauf zugreifen kann.
    cd /app
    exec streamlit run src/frontend/app.py --server.port=8501 --server.address=0.0.0.0

elif [ "$SERVICE_TYPE" = "watcher" ]; then
    echo "👀 Starting SentinelAI Inbox Watcher..."
    # Sicherstellen, dass die Ordner existieren
    mkdir -p /app/data/inbox /app/data/processed /app/data/error
    cd /app
    exec python src/watcher/watcher.py

else
    echo "❌ Unknown SERVICE_TYPE: $SERVICE_TYPE"
    echo "Valid options: backend, frontend, watcher"
    exit 1
fi
