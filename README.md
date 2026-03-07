# SentinelAI Box - Production Ready

**100% Lokale KI-Dokumentenverarbeitung für Steuerberater und Buchhaltungsbüros**

## 🚀 Quick Start

```bash
./start_box.sh
```

Das war's! Die WebUI öffnet sich automatisch unter `http://localhost:8501`

---

## 📋 Voraussetzungen

- **Docker & Docker Compose** installiert
- **Ollama** (optional, für KI-Features): `ollama serve`
- **16GB RAM** empfohlen
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
✅ **Audit-Log** - Durch SQLite-Trigger auf Datenbankebene geschützt (unveränderlich)
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
├── Watcher Service (Folder Watcher)
│   └── Automatische Dokumentverarbeitung aus /inbox
└── Data (persistent volume)
    ├── sentinel.db (Dokumente + Audit-Log)
    ├── vectorstore/ (Embeddings)
    ├── inbox/ (Eingangsordner für Watcher)
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

## 📚 Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| [docs/ROADMAP.md](docs/ROADMAP.md) | Alle Phasen – was getan wurde, was noch kommt |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System-Architektur und Komponenten |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Betrieb, Starten, Stoppen, Troubleshooting |
| [docs/PHASE2_MAGIC_INBOX.md](docs/PHASE2_MAGIC_INBOX.md) | Implementierungsplan: Folder Watcher |

---

## 📁 Verzeichnisstruktur

```
SentinelAi/
├── src/
│   ├── backend/        # FastAPI Backend
│   ├── frontend/       # Streamlit WebUI
│   └── watcher/        # Folder Watcher Service
├── data/              # Persistent (bleibt bei Updates)
│   ├── sentinel.db
│   ├── vectorstore/
│   ├── documents/
│   └── inbox/         # Eingangsordner für Watcher
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
- **Audit-Log** - Durch SQLite-Trigger auf Datenbankebene geschützt (unveränderlich)
- **DSGVO Löschrecht** - Permanente Deletion via UI

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
