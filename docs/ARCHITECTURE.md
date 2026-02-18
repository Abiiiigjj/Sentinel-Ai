# 🏗️ SentinelAI Box – Architektur

---

## System-Übersicht

```
┌─────────────────────────────────────────────────────────┐
│                     HOST MACHINE                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              sentinel-bridge (Docker)             │   │
│  │                                                   │   │
│  │  ┌─────────────────┐                             │   │
│  │  │   Frontend      │                             │   │
│  │  │   Streamlit     │◄── Port 8501 (extern)       │   │
│  │  │   :8501         │                             │   │
│  │  └────────┬────────┘                             │   │
│  │           │ http://localhost:8000                 │   │
│  └───────────┼───────────────────────────────────────┘  │
│              │                                           │
│  ┌───────────▼───────────────────────────────────────┐  │
│  │   Backend (host network mode)                     │  │
│  │   FastAPI :8000                                   │  │
│  │                                                   │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │   │ PII      │ │ Vector   │ │ LLM Service      │ │  │
│  │   │ Service  │ │ Store    │ │ (Ollama Client)  │ │  │
│  │   │ (spaCy)  │ │ (Chroma) │ │                  │ │  │
│  │   └──────────┘ └──────────┘ └────────┬─────────┘ │  │
│  └─────────────────────────────────────┼─────────────┘  │
│                                        │                 │
│  ┌─────────────────────────────────────▼─────────────┐  │
│  │   Ollama Service (localhost:11434)                 │  │
│  │   - mistral-nemo:12B (Analyse)                    │  │
│  │   - nomic-embed-text (Embeddings)                 │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  📁 /data          📁 /logs                             │
│     sentinel.db       app.log                           │
│     vectorstore/      audit/                            │
│     audit/                                              │
└─────────────────────────────────────────────────────────┘
```

---

## Komponenten

### Frontend (`src/frontend/app.py`)
- **Framework:** Streamlit
- **Port:** 8501 (extern erreichbar)
- **Netzwerk:** `sentinel-bridge` (isoliert)
- **Kommunikation:** REST API → Backend via `http://localhost:8000`

### Backend (`src/backend/main.py`)
- **Framework:** FastAPI + Uvicorn
- **Port:** 8000 (nur localhost)
- **Netzwerk:** `host` (für Ollama-Zugriff)
- **Datenbank:** SQLite (`data/sentinel.db`)

### Services (Backend)

| Service | Datei | Funktion |
|---------|-------|----------|
| `LLMService` | `services/llm_service.py` | Ollama-Integration, Chat, Embeddings |
| `PIIService` | `services/pii_service.py` | PII-Erkennung mit spaCy (`de_core_news_lg`) |
| `DocumentService` | `services/document_service.py` | Upload, Verarbeitung, Suche |
| `VectorStore` | `services/vector_store.py` | ChromaDB für semantische Suche |
| `AuditService` | `services/audit_service.py` | DSGVO-Audit-Log |
| `DatabaseService` | `services/database_service.py` | SQLite CRUD |
| `NLPAnalysisService` | `services/nlp_analysis_service.py` | Textanalyse |

---

## Datenpersistenz

```
data/
├── sentinel.db          # SQLite Hauptdatenbank
├── vectorstore/         # ChromaDB Vektordaten
│   └── chroma.sqlite3
└── audit/               # DSGVO Audit-Logs
    └── audit_YYYY-MM.jsonl
```

**Wichtig:** Das `data/` Verzeichnis ist als Docker Volume gemountet → Daten überleben Container-Neustarts.

---

## API Endpunkte

| Methode | Endpunkt | Funktion |
|---------|----------|----------|
| GET | `/health` | System-Status inkl. Ollama |
| POST | `/documents/upload` | Dokument hochladen |
| GET | `/documents` | Alle Dokumente auflisten |
| GET | `/documents/{id}` | Einzelnes Dokument |
| DELETE | `/documents/{id}` | Dokument löschen |
| POST | `/chat` | LLM Chat |
| POST | `/search` | Semantische Suche |
| GET | `/audit` | Audit-Log abrufen |

---

## Docker-Konfiguration

```yaml
# deploy/docker-compose.yml (aktueller Stand)

backend:
  network_mode: "host"          # Für Ollama localhost:11434
  environment:
    - OLLAMA_HOST=http://localhost:11434

frontend:
  networks: [sentinel-bridge]   # Isoliert
  ports: ["8501:8501"]
  environment:
    - API_BASE=http://localhost:8000
```

---

## Technologie-Stack

| Bereich | Technologie | Version |
|---------|-------------|---------|
| Backend | FastAPI | ~0.100 |
| Frontend | Streamlit | ~1.28 |
| LLM | Ollama + Mistral-NeMo 12B | latest |
| Embeddings | nomic-embed-text | latest |
| Vektordatenbank | ChromaDB | ~0.4 |
| Datenbank | SQLite | 3.x |
| NLP/PII | spaCy | ~3.7 |
| Container | Docker + Docker Compose | 3.8 |

---

*Zuletzt aktualisiert: 2026-02-18*
