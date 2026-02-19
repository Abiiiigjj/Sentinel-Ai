# 🗺️ SentinelAI Box – Roadmap

> **Ziel:** MVP → Production-ready, 100% lokales, DSGVO-konformes KI-Dokumentensystem für KMUs

---

## Status-Übersicht

| Phase | Name | Status | Priorität |
|-------|------|--------|-----------|
| 1 | 🏰 Fortress Mode | ✅ **ABGESCHLOSSEN** | Kritisch |
| 2 | 📥 Magic Inbox | ⏳ Ausstehend | Hoch |
| 3 | 👁️ Real World Vision | ✅ **ABGESCHLOSSEN** | Hoch |
| 4 | 🛡️ Compliance Shield | ⏳ Ausstehend | Gesetzlich erforderlich |
| 5 | 🧹 Clean Slate | ⏳ Ausstehend | Deployment |

---

## ✅ Phase 1: Fortress Mode – ABGESCHLOSSEN

**Ziel:** Docker-Netzwerk absichern, Container isolieren

### Was wurde gemacht

- `network_mode: host` entfernt → Bridge-Netzwerk `sentinel-bridge` eingeführt
- Frontend isoliert auf Bridge-Netzwerk (nur Port 8501 nach außen)
- Backend auf `network_mode: host` für Ollama-Zugriff (Hybrid-Lösung)
- Ollama konfiguriert: hört auf `0.0.0.0:11434` statt nur `127.0.0.1`
- Ollama Autostart deaktiviert (`systemctl disable ollama`)

### Geänderte Dateien

- `deploy/docker-compose.yml` – Netzwerk-Konfiguration
- `src/backend/utils/config.py` – `OLLAMA_HOST` Default
- `src/frontend/app.py` – `API_BASE` Default
- `/etc/systemd/system/ollama.service` – `OLLAMA_HOST=0.0.0.0`

### Ergebnis

```json
{"status":"healthy","ollama_connected":true,"model_loaded":true,"vector_store_ready":true}
```

### Bekannte Trade-offs

- Backend Port 8000 ist auf `localhost` erreichbar (aber NICHT im Netzwerk)
- Hybrid-Modus nötig, da Docker Bridge Gateways nicht zurück zum Host routen können

---

## ⏳ Phase 2: Magic Inbox – AUSSTEHEND

**Ziel:** Ordner-Watcher für automatische Dokumentverarbeitung

### Was zu tun ist

- [ ] Neuen Docker-Service `watcher` erstellen
- [ ] Python `watchdog` Library für Ordner-Monitoring
- [ ] Automatischer Upload bei neuen Dateien in `/inbox`
- [ ] Unterstützte Formate: PDF, DOCX, TXT, XLSX
- [ ] Fehler-Handling & Logging
- [ ] Verarbeiteter Ordner `/inbox/processed` für erledigte Dateien

### Technische Details

```yaml
# docker-compose.yml Erweiterung
watcher:
  build: ...
  volumes:
    - ./inbox:/app/inbox
    - ./data:/app/data
  environment:
    - WATCH_DIR=/app/inbox
    - API_BASE=http://localhost:8000
```

---

## ✅ Phase 3: Real World Vision – ABGESCHLOSSEN

**Ziel:** OCR für gescannte Dokumente und Bilder

### Was wurde gemacht

- `tesseract-ocr` + Sprach-Packs (`deu`, `eng`) im Dockerfile installiert
- `poppler-utils` für PDF→Bild Konvertierung installiert
- `pytesseract`, `Pillow`, `pdf2image` als Python-Dependencies hinzugefügt
- Neuer `OCRService` mit Scanned-PDF-Erkennung, Bild-OCR, Pre-Processing
- Automatischer OCR-Fallback in `DocumentService._extract_pdf()` wenn < 50 Zeichen/Seite
- Bild-Upload (.png, .jpg, .jpeg, .tiff) im Upload-Endpoint freigeschaltet
- OCR-Metadaten (`ocr_used`, `ocr_confidence`) in API-Response und Audit-Log

### Geänderte Dateien

- `deploy/Dockerfile` – Tesseract, poppler, libgl1 installiert
- `src/backend/requirements.txt` – pytesseract, Pillow, pdf2image
- `src/backend/services/ocr_service.py` – **NEU** OCR-Pipeline
- `src/backend/services/document_service.py` – OCR-Integration + Bild-Extraktion
- `src/backend/main.py` – OCR-Service Init, Bild-Upload, Response-Felder
- `src/backend/utils/config.py` – OCR-Konfiguration

### Ergebnis

```
INFO:services.ocr_service:✅ OCR Service ready – Tesseract 5.5.0, Sprachen: deu+eng
```

---

## ⏳ Phase 4: Compliance Shield – AUSSTEHEND

**Ziel:** DSGVO-konforme Löschung und unveränderliches Audit-Log

### Was zu tun ist

- [ ] **Physische Löschung:** Dateien wirklich löschen (nicht nur DB-Eintrag)
- [ ] **Audit-Log Immutabilität:** Log-Einträge dürfen nicht geändert werden
- [ ] **Lösch-Bestätigung:** Schriftliche Bestätigung nach Löschung generieren
- [ ] **Datenschutz-Bericht:** Export aller gespeicherten Daten zu einer Person
- [ ] **Aufbewahrungsfristen:** Automatische Löschung nach X Tagen
- [ ] **Verschlüsselung:** Daten at-rest verschlüsseln

### Betroffene Dateien

- `src/backend/services/document_service.py` – Lösch-Logik
- `src/backend/services/audit_service.py` – Immutabilität
- `src/backend/main.py` – Neue DSGVO-Endpunkte

---

## ⏳ Phase 5: Clean Slate – AUSSTEHEND

**Ziel:** Deployment-Vorbereitung und Stress-Tests

### Was zu tun ist

- [ ] **Stress-Test:** 100 Dokumente gleichzeitig verarbeiten
- [ ] **Memory-Profiling:** RAM-Verbrauch unter Last messen
- [ ] **Backup-Strategie:** Automatisches Backup von `/data`
- [ ] **Update-Mechanismus:** Wie wird die App aktualisiert?
- [ ] **Monitoring:** Health-Dashboard für Betrieb
- [ ] **Installer-Skript:** Ein-Klick-Installation für Kunden
- [ ] **Dokumentation:** Benutzerhandbuch für Nicht-Techniker

---

## 🔧 Ollama Betrieb

```bash
# Starten (wenn du SentinelAI nutzen willst)
sudo systemctl start ollama

# Stoppen (wenn fertig)
sudo systemctl stop ollama

# Status prüfen
systemctl status ollama

# Verfügbare Modelle
curl http://localhost:11434/api/tags
```

**Installierte Modelle:**
- `mistral-nemo:latest` (12B) – Hauptmodell für Analyse
- `mistral:latest` (7B) – Fallback
- `nomic-embed-text:latest` – Embeddings für Suche

---

## 🚀 SentinelAI starten

```bash
cd /home/ahmet/Downloads/SentinelAi

# Ollama starten (falls nicht aktiv)
sudo systemctl start ollama

# Container starten
docker-compose -f deploy/docker-compose.yml up -d

# Status prüfen
docker ps
curl http://localhost:8000/health

# WebUI öffnen
# → http://localhost:8501
```

---

*Zuletzt aktualisiert: 2026-02-18*
