#!/bin/bash
# SentinelAI Box - One-Click Start Script
# Startet das gesamte System via Docker Compose

set -e

echo "🛡️  SentinelAI Box - Production Start"
echo "====================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker ist nicht verfügbar!"
    echo ""
    echo "Bitte installiere Docker:"
    echo "  Ubuntu/Debian: sudo apt install docker.io docker-compose"
    echo "  macOS/Windows: https://www.docker.com/products/docker-desktop"
    echo ""
    exit 1
fi

echo "✅ Docker ist verfügbar"

# Check if Ollama is running on host (optional but recommended)
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama läuft auf Host (GPU-Unterstützung aktiv)"
else
    echo "⚠️  Ollama nicht gefunden auf localhost:11434"
    echo "   LLM-Features sind eingeschränkt. Starte Ollama mit:"
    echo "   ollama serve"
    echo ""
fi

# Create data directories if they don't exist
mkdir -p data/vectorstore data/documents data/audit logs

echo ""
echo "🧹 Cleanup alter Container..."

# CRITICAL FIX: Always cleanup old containers to prevent ContainerConfig errors
# This is necessary because docker-compose recreate can fail with ContainerConfig KeyError
cd "$(dirname "$0")"

# Stop and remove old SentinelAI containers if they exist
echo "   Stoppe alte Container..."
docker-compose -f deploy/docker-compose.yml down 2>/dev/null || true

# Remove any orphaned containers with sentinelai in name
OLD_CONTAINERS=$(docker ps -a --format "{{.ID}} {{.Names}}" | grep -i sentinel | awk '{print $1}' || true)
if [ ! -z "$OLD_CONTAINERS" ]; then
    echo "   Entferne Zombie-Container..."
    echo "$OLD_CONTAINERS" | xargs docker rm -f 2>/dev/null || true
fi

# Prune unused networks to avoid conflicts
echo "   Prune Networks..."
docker network prune -f > /dev/null 2>&1 || true

echo "✅ Cleanup abgeschlossen"
echo ""
echo "🚀 Starte SentinelAI Box..."
echo ""

# Build and start containers (fresh start, no recreation issues)
docker-compose -f deploy/docker-compose.yml up -d --build

echo ""
echo "⏳ Warte auf Backend-Start..."
sleep 10

# Check backend health
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend ist bereit!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Versuch $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  Backend-Start dauert länger als erwartet"
    echo "   Prüfe Logs mit: docker-compose -f deploy/docker-compose.yml logs backend"
fi

echo ""
echo "✅ SentinelAI Box läuft!"
echo ""
echo "📊 Status prüfen:"
echo "   docker-compose -f deploy/docker-compose.yml ps"
echo ""
echo "📝 Logs anzeigen:"
echo "   docker-compose -f deploy/docker-compose.yml logs -f"
echo ""
echo "🛑 System stoppen:"
echo "   docker-compose -f deploy/docker-compose.yml down"
echo ""
echo "🌐 Öffne die WebUI:"
echo "   http://localhost:8501"
echo ""

# Try to open browser (Linux with xdg-open)
if command -v xdg-open > /dev/null 2>&1; then
    echo "🚀 Öffne Browser..."
    sleep 2
    xdg-open http://localhost:8501 2>/dev/null &
elif command -v open > /dev/null 2>&1; then
    # macOS
    echo "🚀 Öffne Browser..."
    sleep 2
    open http://localhost:8501 2>/dev/null &
fi

echo ""
echo "🛡️  SentinelAI Box ist bereit!"
