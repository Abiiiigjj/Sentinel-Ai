# 📥 Phase 2: Magic Inbox – Implementierungsplan

**Status:** ⏳ Ausstehend  
**Priorität:** Hoch – Game Changer für Benutzerfreundlichkeit

---

## Ziel

Nutzer legen Dokumente in einen Ordner (`/inbox`) – SentinelAI verarbeitet sie automatisch. Keine manuelle Interaktion nötig.

---

## Konzept

```
/inbox/
  ├── rechnung_2026-02.pdf    ← Nutzer legt ab
  ├── vertrag_mueller.docx    ← Nutzer legt ab
  └── processed/              ← Nach Verarbeitung verschoben
        ├── rechnung_2026-02.pdf
        └── vertrag_mueller.docx
```

---

## Implementierungsschritte

### Schritt 1: Watcher-Service erstellen

**Neue Datei:** `src/watcher/watcher.py`

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import httpx
import time
import os

WATCH_DIR = os.getenv("WATCH_DIR", "/app/inbox")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
SUPPORTED_FORMATS = {".pdf", ".docx", ".txt", ".xlsx", ".png", ".jpg"}

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext not in SUPPORTED_FORMATS:
            return
        
        # Warten bis Datei vollständig geschrieben
        time.sleep(1)
        
        # Upload via API
        self._upload_file(filepath)
    
    def _upload_file(self, filepath):
        try:
            with open(filepath, "rb") as f:
                response = httpx.post(
                    f"{API_BASE}/documents/upload",
                    files={"file": f},
                    timeout=60.0
                )
            
            if response.status_code == 200:
                # In processed/ verschieben
                processed_dir = os.path.join(WATCH_DIR, "processed")
                os.makedirs(processed_dir, exist_ok=True)
                os.rename(filepath, os.path.join(processed_dir, os.path.basename(filepath)))
                print(f"✅ Verarbeitet: {os.path.basename(filepath)}")
            else:
                print(f"❌ Fehler bei {filepath}: {response.text}")
                
        except Exception as e:
            print(f"❌ Upload-Fehler: {e}")

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(InboxHandler(), WATCH_DIR, recursive=False)
    observer.start()
    print(f"👀 Überwache: {WATCH_DIR}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

### Schritt 2: Requirements erweitern

**Datei:** `src/watcher/requirements.txt`

```
watchdog==3.0.0
httpx==0.25.0
```

### Schritt 3: docker-compose.yml erweitern

```yaml
  watcher:
    build:
      context: ..
      dockerfile: deploy/Dockerfile.watcher
    container_name: sentinelai-watcher
    environment:
      - SERVICE_TYPE=watcher
      - WATCH_DIR=/app/inbox
      - API_BASE=http://localhost:8000
    volumes:
      - ./inbox:/app/inbox
      - ../data:/app/data
    network_mode: "host"
    restart: unless-stopped
    depends_on:
      - backend
```

### Schritt 4: Inbox-Ordner erstellen

```bash
mkdir -p /home/ahmet/Downloads/SentinelAi/inbox/processed
```

### Schritt 5: Entrypoint erweitern

**Datei:** `deploy/entrypoint.sh`

```bash
elif [ "$SERVICE_TYPE" = "watcher" ]; then
    echo "👀 Starting Inbox Watcher..."
    python /app/src/watcher/watcher.py
```

---

## Zu erledigende Aufgaben

- [ ] `src/watcher/watcher.py` erstellen
- [ ] `src/watcher/requirements.txt` erstellen
- [ ] `deploy/Dockerfile.watcher` erstellen (oder Dockerfile erweitern)
- [ ] `deploy/docker-compose.yml` um Watcher-Service erweitern
- [ ] `inbox/` Ordner anlegen
- [ ] `deploy/entrypoint.sh` erweitern
- [ ] Testen: Datei in `/inbox` legen → automatisch verarbeitet?
- [ ] Fehler-Handling: Was passiert bei ungültigen Dateien?
- [ ] Logging: Verarbeitete Dateien protokollieren

---

## Test-Szenario

```bash
# 1. Watcher starten
docker-compose -f deploy/docker-compose.yml up -d watcher

# 2. Testdatei in Inbox legen
cp /tmp/test.pdf /home/ahmet/Downloads/SentinelAi/inbox/

# 3. Watcher-Logs beobachten
docker logs -f sentinelai-watcher

# 4. Prüfen ob Dokument verarbeitet wurde
curl http://localhost:8000/documents | python3 -m json.tool

# 5. Prüfen ob Datei in processed/ verschoben
ls /home/ahmet/Downloads/SentinelAi/inbox/processed/
```

---

*Zuletzt aktualisiert: 2026-02-18*
