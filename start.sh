#!/bin/bash
# SentinelAI Start Script

cd "$(dirname "$0")"

# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⏳ Starte Ollama..."
    ollama serve &
    sleep 3
fi

# Start Backend
echo "🚀 Starte SentinelAI Backend..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
