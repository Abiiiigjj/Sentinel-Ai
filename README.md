# SentinelAI Box - Production Ready

**100% Lokale KI-Dokumentenverarbeitung für Kleinunternehmer**

## 🚀 Quick Start

```bash
./start_box.sh
```

Das war's! Die WebUI öffnet sich automatisch unter `http://localhost:8501`

---

## 📋 Voraussetzungen

- **Docker & Docker Compose** installiert
- **Ollama** (optional, für KI-Features): `ollama serve`
- **8GB RAM** empfohlen
- **10GB Festplattenspeicher**

### Installation

**Ubuntu/Debian:**
```bash
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# Neu einloggen für Gruppenänderung
```

**Ollama (für KI-Analyse):**
```bash
curl https://ollama.ai/install.sh | sh
ollama pull mistral-nemo:12b-instruct-2407-q4_K_M
ollama serve
```

---

## 🛡️ Features

✅ **DSGVO-konform** - Alle Daten bleiben lokal  
✅ **PII-Erkennung** - Automatische Erkennung personenbezogener Daten  
✅ **Semantische Suche** - RAG-basierte Dokumentensuche  
✅ **Status-Workflow** - Neu → In Prüfung → Erledigt  
✅ **Audit-Log** - Manipulationssicheres Compliance-Log  
✅ **Kiosk-UI** - Touchscreen-optimiert, professionell  

---

## 📊 Architektur

```
SentinelAI Box
├── Backend (FastAPI)
│   ├── LLM Service (Ollama + Mistral NeMo)
│   ├── Vector Store (ChromaDB)
│   ├── PII Detection (spaCy de_core_news_lg)
│   └── SQLite Database (persistent)
├── Frontend (Streamlit)
│   ├── Cockpit (Übersicht)
│   ├── Posteingang (Upload)
│   └── Archiv (Suche)
└── Data (persistent volume)
    ├── sentinel.db (Dokumente + Audit-Log)
    ├── vectorstore/ (Embeddings)
    └── documents/ (Uploads)
```

---

## 🔧 Verwaltung

**Status prüfen:**
```bash
docker-compose -f deploy/docker-compose.yml ps
```

**Logs anzeigen:**
```bash
docker-compose -f deploy/docker-compose.yml logs -f
```

**System stoppen:**
```bash
docker-compose -f deploy/docker-compose.yml down
```

**Daten löschen (ACHTUNG!):**
```bash
docker-compose -f deploy/docker-compose.yml down -v
rm -rf data/
```

---

## 📁 Verzeichnisstruktur

```
SentinelAi/
├── src/
│   ├── backend/        # FastAPI Backend
│   └── frontend/       # Streamlit WebUI
├── data/              # Persistent (bleibt bei Updates)
│   ├── sentinel.db
│   ├── vectorstore/
│   └── documents/
├── logs/              # System-Logs
├── deploy/            # Docker-Konfiguration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── entrypoint.sh
└── start_box.sh       # One-Click Start
```

---

## 🔐 Sicherheit & Compliance

- **Keine Cloud-Verbindung** - 100% offline
- **PII-Erkennung** - spaCy NER (Personen, Orte, Organisationen)
- **Audit-Log** - Append-only (immutable)
- **DSGVO Löschrecht** - Permanente Deletion via UI
- **Verschlüsselung** - Optional via Docker Secrets

---

## 🆘 Troubleshooting

**Backend startet nicht:**
```bash
docker-compose -f deploy/docker-compose.yml logs backend
```

**Ollama nicht erreichbar:**
- Prüfe: `curl http://localhost:11434/api/tags`
- Starte: `ollama serve`
- Windows/macOS: Nutze `host.docker.internal:11434`

**Port 8501 bereits belegt:**
```bash
# Ändere Port in deploy/docker-compose.yml:
ports:
  - "8502:8501"  # Dann: http://localhost:8502
```

---

## 📝 Lizenz

Proprietär - SentinelAI Box © 2026

---

## 👨‍💻 Support

Bei Fragen oder Problemen:
- Logs prüfen: `docker-compose logs`
- Health-Check: `curl http://localhost:8000/health`
- WebUI: `http://localhost:8501`
