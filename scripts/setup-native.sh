#!/bin/bash
#
# SentinelAI Native Setup Script (ohne Docker)
# Nutzt vorhandene Ollama Installation
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           SentinelAI - Native Setup Script                     ║"
echo "║           DSGVO-konformes lokales KI-System                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "📁 Projektverzeichnis: $PROJECT_DIR"
echo ""

# ============== CHECK OLLAMA ==============

echo "🔍 Prüfe Ollama Installation..."

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama gefunden: $(which ollama)${NC}"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama Server läuft${NC}"
    else
        echo "⏳ Starte Ollama Server..."
        ollama serve &
        sleep 3
    fi
    
    echo ""
    echo "📦 Verfügbare Modelle:"
    ollama list
else
    echo -e "${RED}✗ Ollama nicht gefunden${NC}"
    echo "  Bitte installieren: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

echo ""

# ============== CHECK MODELS ==============

echo "🔍 Prüfe benötigte Modelle..."

# Check for embedding model
if ! ollama list | grep -q "nomic-embed-text"; then
    echo "📥 Lade Embedding-Modell herunter..."
    ollama pull nomic-embed-text
else
    echo -e "${GREEN}✓ Embedding-Modell vorhanden${NC}"
fi

# Check for Mistral NeMo
if ollama list | grep -q "mistral-nemo"; then
    echo -e "${GREEN}✓ Mistral NeMo vorhanden${NC}"
elif ollama list | grep -q "mistral"; then
    echo -e "${YELLOW}⚠ Nur Mistral 7B gefunden (NeMo wird empfohlen)${NC}"
else
    echo "📥 Lade Mistral NeMo herunter (kann 10-20 Min dauern)..."
    ollama pull mistral-nemo
fi

echo ""

# ============== CREATE PYTHON VENV ==============

echo "🐍 Erstelle Python Virtual Environment..."

cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"
else
    echo -e "${GREEN}✓ Virtual Environment existiert bereits${NC}"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📦 Installiere Python-Abhängigkeiten..."
pip install --upgrade pip > /dev/null
pip install -e . 2>&1 | tail -5

echo ""

# ============== SPACY MODEL ==============

echo "📥 Installiere spaCy Sprachmodell..."
python -m spacy download de_core_news_lg 2>/dev/null || \
python -m spacy download de_core_news_sm 2>/dev/null || \
echo -e "${YELLOW}⚠ spaCy-Modell konnte nicht installiert werden - Regex-PII aktiv${NC}"

echo ""

# ============== CREATE DATA DIRS ==============

echo "📁 Erstelle Datenverzeichnisse..."
mkdir -p "$PROJECT_DIR/data/vectorstore"
mkdir -p "$PROJECT_DIR/data/documents"
mkdir -p "$PROJECT_DIR/data/audit"
echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}"

echo ""

# ============== CREATE START SCRIPT ==============

cat > "$PROJECT_DIR/start.sh" << 'EOF'
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
EOF

chmod +x "$PROJECT_DIR/start.sh"

# ============== CREATE STOP SCRIPT ==============

cat > "$PROJECT_DIR/stop.sh" << 'EOF'
#!/bin/bash
# SentinelAI Stop Script
pkill -f "uvicorn main:app" 2>/dev/null
echo "✓ Backend gestoppt"
EOF

chmod +x "$PROJECT_DIR/stop.sh"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Setup Abgeschlossen! 🎉                     ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  Starten:                                                     ║"
echo "║    ./start.sh         # Backend auf http://localhost:8000     ║"
echo "║    npm run dev        # Frontend auf http://localhost:3000    ║"
echo "║                                                               ║"
echo "║  API Dokumentation:                                           ║"
echo "║    http://localhost:8000/docs                                 ║"
echo "║                                                               ║"
echo "║  Stoppen:                                                     ║"
echo "║    ./stop.sh                                                  ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
EOF
