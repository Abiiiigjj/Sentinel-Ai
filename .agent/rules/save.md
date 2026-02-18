---
trigger: always_on
glob: "**/*"
description: Project specific rules for SentinelAi

1. DIE GOLDENEN REGELN (Core Principles)
OFFLINE FIRST: Die Box muss ohne Internet funktionieren. Keine Cloud-APIs (OpenAI, AWS, etc.), keine externen Fonts/Scripts.

GERMAN COMPLIANCE: Datenschutz (DSGVO) steht über allem. Keine PII (persönliche Daten) unverschlüsselt/unnötig speichern.

HANDWERKER-TAUGLICH: Simpel, robust, unzerstörbar. UI-Texte und Logs immer auf Deutsch. Code-Kommentare auf Englisch.

2. TECHNISCHE LEITPLANKEN (Architecture Constraints)
Linux Hybrid Setup (WICHTIG):

Backend & Watcher: MÜSSEN network_mode: "host" nutzen. (Grund: Zugriff auf lokale Ollama-Instanz und Dateirechte-Management).

Frontend: MUSS im bridge Netzwerk isoliert sein. Nur Port 8501 darf nach außen zeigen.

Pfade: Nutze immer relative Pfade (./data) oder Docker Volumes. Keine absoluten Pfade (/home/user/...).

Datenbank: ChromaDB Persistenz immer in ./data/vectorstore mappen.

3. PHASE 2 SPEZIAL: "THE MAGIC INBOX" (Watcher Rules)
Wenn du den Datei-Watcher baust, beachte zwingend diese 3 Punkte:

Stabilitäts-Check: Warte, bis die Dateigröße für 2 Sekunden unverändert bleibt, bevor du sie verarbeitest (Scannner sind langsam!).

Rechte-Fix (CRITICAL): Wenn du eine Datei verschoben hast (nach /processed), setze sofort chmod 666.

Warum: Damit der Handwerker (Host-User) die Datei auch vom PC aus öffnen/löschen kann und nicht ausgesperrt wird.

Fehler-Handling: Wenn eine Datei korrupt ist -> ab in den /error Ordner und eine .log Datei dazu schreiben. Niemals abstürzen.


