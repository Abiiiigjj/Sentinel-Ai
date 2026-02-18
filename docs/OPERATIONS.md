# ⚙️ SentinelAI Box – Betriebshandbuch

---

## Schnellstart

```bash
# 1. Ollama starten
sudo systemctl start ollama

# 2. Container starten
cd /home/ahmet/Downloads/SentinelAi
docker-compose -f deploy/docker-compose.yml up -d

# 3. Status prüfen
curl -s http://localhost:8000/health

# 4. WebUI öffnen → http://localhost:8501
```

---

## Täglicher Betrieb

### Starten

```bash
sudo systemctl start ollama
docker-compose -f deploy/docker-compose.yml up -d
```

### Stoppen

```bash
docker-compose -f deploy/docker-compose.yml down
sudo systemctl stop ollama
```

### Status prüfen

```bash
# Container-Status
docker ps

# Health-Check
curl -s http://localhost:8000/health | python3 -m json.tool

# Ollama-Status
systemctl status ollama

# Logs anschauen
docker-compose -f deploy/docker-compose.yml logs -f backend
docker-compose -f deploy/docker-compose.yml logs -f frontend
```

---

## Ollama

```bash
# Starten
sudo systemctl start ollama

# Stoppen
sudo systemctl stop ollama

# Autostart aktivieren (optional)
sudo systemctl enable ollama

# Verfügbare Modelle
ollama list

# Modell testen
ollama run mistral-nemo "Hallo, wie geht es dir?"

# Neues Modell laden
ollama pull mistral-nemo
```

**Installierte Modelle:**

| Modell | Größe | Verwendung |
|--------|-------|------------|
| `mistral-nemo:latest` | 7.1 GB | Dokumentanalyse, Chat |
| `mistral:latest` | 4.4 GB | Fallback |
| `nomic-embed-text:latest` | 274 MB | Semantische Suche |

---

## Container-Management

```bash
# Container neu bauen (nach Code-Änderungen)
docker-compose -f deploy/docker-compose.yml down
docker-compose -f deploy/docker-compose.yml build --no-cache
docker-compose -f deploy/docker-compose.yml up -d

# Nur Backend neu starten
docker-compose -f deploy/docker-compose.yml restart backend

# In Container einloggen
docker exec -it sentinelai-backend bash
docker exec -it sentinelai-frontend bash

# Netzwerk prüfen
docker network inspect deploy_sentinel-bridge
```

---

## Troubleshooting

### Problem: `ollama_connected: false`

```bash
# 1. Ollama läuft?
systemctl status ollama

# 2. Ollama starten
sudo systemctl start ollama

# 3. Ollama erreichbar?
curl http://localhost:11434/api/tags

# 4. Backend neu starten
docker-compose -f deploy/docker-compose.yml restart backend

# 5. Health prüfen
curl http://localhost:8000/health
```

### Problem: Frontend nicht erreichbar (Port 8501)

```bash
# Container läuft?
docker ps | grep frontend

# Container-Logs
docker-compose -f deploy/docker-compose.yml logs frontend

# Port belegt?
ss -tlnp | grep 8501
```

### Problem: Backend nicht erreichbar

```bash
# Backend läuft?
docker ps | grep backend

# Backend-Logs
docker-compose -f deploy/docker-compose.yml logs backend

# Health direkt testen
curl http://localhost:8000/health
```

### Problem: Container startet nicht

```bash
# Alle Logs anschauen
docker-compose -f deploy/docker-compose.yml logs

# Container-Status
docker-compose -f deploy/docker-compose.yml ps

# Neu bauen
docker-compose -f deploy/docker-compose.yml build
```

### Problem: Kein Speicherplatz

```bash
# Docker aufräumen
docker system prune -f

# Alte Images entfernen
docker image prune -f

# Speicherplatz prüfen
df -h
```

---

## Daten-Management

### Backup

```bash
# Daten sichern
cp -r /home/ahmet/Downloads/SentinelAi/data /home/ahmet/backup/sentinelai-$(date +%Y%m%d)
```

### Datenbank direkt öffnen

```bash
sqlite3 /home/ahmet/Downloads/SentinelAi/data/sentinel.db

# Alle Dokumente anzeigen
.tables
SELECT id, filename, status, created_at FROM documents;
.quit
```

### Logs

```bash
# Anwendungs-Logs
tail -f /home/ahmet/Downloads/SentinelAi/logs/app.log

# Audit-Logs (DSGVO)
ls /home/ahmet/Downloads/SentinelAi/data/audit/
cat /home/ahmet/Downloads/SentinelAi/data/audit/audit_$(date +%Y-%m).jsonl
```

---

## Netzwerk-Übersicht

| Dienst | Adresse | Erreichbar von |
|--------|---------|----------------|
| Frontend (WebUI) | `http://localhost:8501` | Überall (Browser) |
| Backend API | `http://localhost:8000` | Nur localhost |
| Ollama | `http://localhost:11434` | Nur localhost |
| Backend Health | `http://localhost:8000/health` | Nur localhost |

---

## System-Anforderungen

| Ressource | Minimum | Empfohlen |
|-----------|---------|-----------|
| RAM | 8 GB | 16 GB |
| GPU VRAM | 6 GB | 12 GB (RTX 3060) |
| Speicher | 20 GB | 50 GB |
| CPU | 4 Kerne | 8 Kerne |

---

*Zuletzt aktualisiert: 2026-02-18*
