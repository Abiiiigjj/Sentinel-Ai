# SentinelAI - DSGVO-konforme Lokale KI

<div align="center">
  <h3>🛡️ Sichere, Offline-fähige KI-Dokumentenanalyse</h3>
  <p>EU AI Act & DSGVO konform • Mistral NeMo 12B • 100% Datensouveränität</p>
</div>

---

## 🎯 Überblick

SentinelAI ist eine vollständig lokale KI-Lösung für Dokumentenanalyse und intelligente Assistenz. Alle Daten bleiben auf Ihrem Rechner - keine Cloud, keine API-Aufrufe, keine Kompromisse bei der Datensicherheit.

### ✨ Features

- 🤖 **Lokales LLM**: Mistral NeMo 12B mit 12GB VRAM
- 📄 **Dokumentenanalyse**: PDF, DOCX, TXT, Markdown
- 🔍 **RAG-System**: Kontextbasierte Antworten aus Ihren Dokumenten
- 🛡️ **PII-Erkennung**: Automatische Maskierung sensibler Daten
- 📊 **Compliance Dashboard**: DSGVO & EU AI Act Übersicht
- 🔒 **Audit Logging**: Lückenlose Protokollierung

---

## 🚀 Schnellstart

### Voraussetzungen

- Docker & Docker Compose
- NVIDIA GPU mit 12GB+ VRAM (RTX 3060/4070 oder besser)
- NVIDIA Container Toolkit
- 16GB+ RAM empfohlen

### Installation

```bash
# Repository klonen
cd /home/ahmet/Downloads/SentinelAi

# Setup-Skript ausführen
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Das Setup-Skript:
1. ✅ Überprüft Docker & GPU
2. ✅ Startet Ollama Container
3. ✅ Lädt Mistral NeMo 12B herunter (~7GB)
4. ✅ Lädt Embedding-Modell herunter
5. ✅ Startet alle Services

### Manueller Start

```bash
# Services starten
docker compose up -d

# Logs verfolgen
docker compose logs -f

# Services stoppen
docker compose down
```

### Frontend starten (Entwicklung)

```bash
npm install
npm run dev
```

---

## 📁 Projektstruktur

```
SentinelAi/
├── backend/                 # Python FastAPI Backend
│   ├── main.py              # API Endpoints
│   ├── services/            # Business Logic
│   │   ├── llm_service.py   # Ollama Integration
│   │   ├── vector_store.py  # ChromaDB
│   │   ├── pii_service.py   # PII Erkennung
│   │   ├── document_service.py
│   │   └── audit_service.py
│   ├── utils/
│   │   └── config.py        # Einstellungen
│   └── Dockerfile
├── components/              # React Komponenten
├── services/
│   └── geminiService.ts     # Frontend API Client
├── docker-compose.yml       # Container Orchestrierung
├── scripts/
│   └── setup.sh             # Automatisches Setup
└── data/                    # Persistente Daten (gitignored)
    ├── vectorstore/         # ChromaDB
    ├── documents/           # Dokumentmetadaten
    └── audit/               # Audit Logs
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

Kopieren Sie `.env.example` nach `.env` und passen Sie an:

```bash
# LLM Modell (Standard: Mistral NeMo 12B)
LLM_MODEL=mistral-nemo:12b-instruct-2407-q4_K_M

# Für schwächere GPUs (8GB VRAM):
LLM_MODEL=mistral:7b-instruct-q4_K_M

# PII-Erkennung deaktivieren
PII_DETECTION_ENABLED=false
```

### Modelle wechseln

```bash
# Verfügbare Modelle anzeigen
docker compose exec ollama ollama list

# Alternatives Modell herunterladen
docker compose exec ollama ollama pull llama3.1:8b
```

---

## 📖 API Dokumentation

Nach dem Start verfügbar unter: **http://localhost:8000/docs**

### Wichtige Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | System-Status |
| `/chat` | POST | Chat mit LLM |
| `/chat/stream` | POST | Streaming Chat |
| `/documents/upload` | POST | Dokument hochladen |
| `/documents` | GET | Alle Dokumente |
| `/documents/{id}` | DELETE | Dokument löschen (DSGVO) |
| `/compliance/stats` | GET | Compliance Statistiken |
| `/compliance/audit` | GET | Audit Log |

---

## 🔒 Sicherheit & Compliance

### DSGVO Konformität

- ✅ **Keine Datenübertragung**: Alle Verarbeitung lokal
- ✅ **Recht auf Löschung**: DELETE Endpoints implementiert
- ✅ **Audit Trail**: Alle Aktionen werden protokolliert
- ✅ **PII-Schutz**: Automatische Erkennung & Maskierung

### EU AI Act

- ✅ **Risikokategorie**: Minimal (Dokumentenanalyse)
- ✅ **Transparenz**: KI-Nutzung gekennzeichnet
- ✅ **Keine verbotenen Praktiken**

---

## 🛠️ Entwicklung

### Backend Tests

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

### spaCy Modell installieren

```bash
python -m spacy download de_core_news_lg
```

---

## 📝 Lizenz

MIT License - Siehe [LICENSE](LICENSE)

---

## 🤝 Support

Bei Fragen oder Problemen erstellen Sie ein Issue oder kontaktieren Sie uns unter support@sentinell.ai
