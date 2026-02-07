#!/bin/bash
#
# SentinelAI Setup Script
# Installs and configures the complete local LLM stack
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           SentinelAI - Setup Script                           ║"
echo "║           DSGVO-konformes lokales KI-System                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Running as root. Consider running as regular user.${NC}"
fi

# Detect OS
OS="unknown"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
fi

echo "📋 Detected OS: $OS"
echo ""

# ============== CHECK PREREQUISITES ==============

echo "🔍 Checking prerequisites..."

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker installed${NC}"
    docker --version
else
    echo -e "${RED}✗ Docker not found${NC}"
    echo "  Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
    docker compose version
else
    echo -e "${RED}✗ Docker Compose not found${NC}"
    echo "  Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo -e "${YELLOW}⚠ NVIDIA GPU not detected - LLM will run on CPU (slow)${NC}"
fi

# Check NVIDIA Container Toolkit
if docker info 2>/dev/null | grep -q "Runtimes.*nvidia"; then
    echo -e "${GREEN}✓ NVIDIA Container Toolkit installed${NC}"
else
    echo -e "${YELLOW}⚠ NVIDIA Container Toolkit not detected${NC}"
    echo "  For GPU acceleration, install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
fi

echo ""

# ============== CREATE DIRECTORIES ==============

echo "📁 Creating data directories..."
mkdir -p data/vectorstore
mkdir -p data/documents
mkdir -p data/audit
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# ============== SETUP OLLAMA ==============

echo "🚀 Setting up Ollama..."

# Start Ollama container first
docker compose up -d ollama

echo "⏳ Waiting for Ollama to start..."
sleep 10

# Pull required models
echo "📥 Downloading Mistral NeMo 12B (this may take a while)..."
docker compose exec ollama ollama pull mistral-nemo:12b-instruct-2407-q4_K_M || {
    echo -e "${YELLOW}⚠ Could not pull optimized model, trying default...${NC}"
    docker compose exec ollama ollama pull mistral-nemo || {
        echo -e "${RED}Failed to pull Mistral NeMo. Please run manually:${NC}"
        echo "  docker compose exec ollama ollama pull mistral-nemo"
    }
}

echo "📥 Downloading embedding model..."
docker compose exec ollama ollama pull nomic-embed-text

echo -e "${GREEN}✓ Models downloaded${NC}"
echo ""

# ============== BUILD AND START SERVICES ==============

echo "🔨 Building and starting all services..."
docker compose build
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 15

# ============== HEALTH CHECK ==============

echo "🏥 Running health checks..."

# Check backend
if curl -s http://localhost:8000/health | grep -q "healthy\|degraded"; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠ Backend not responding yet - may still be initializing${NC}"
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags | grep -q "models"; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama not responding${NC}"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                         ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  Services:                                                    ║"
echo "║    Backend API:  http://localhost:8000                        ║"
echo "║    API Docs:     http://localhost:8000/docs                   ║"
echo "║    Ollama:       http://localhost:11434                       ║"
echo "║                                                               ║"
echo "║  Commands:                                                    ║"
echo "║    Start:        docker compose up -d                         ║"
echo "║    Stop:         docker compose down                          ║"
echo "║    Logs:         docker compose logs -f                       ║"
echo "║    Shell:        docker compose exec backend bash             ║"
echo "║                                                               ║"
echo "║  Frontend (development):                                      ║"
echo "║    cd SentinelAi && npm install && npm run dev                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "💡 Tip: Run 'docker compose logs -f' to monitor the services"
