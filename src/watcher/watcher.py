"""
SentinelAI Inbox Watcher – Phase 2: Magic Inbox
Watches /inbox for new documents and uploads them via the Backend API.

Rules enforced:
- Stability check: wait until file size is stable for 2 seconds
- On success: move to /processed, chmod 666
- On error: move to /error, write .log file, chmod 666, never crash
"""
import os
import stat
import time
import shutil
import logging
import traceback
from datetime import datetime
from pathlib import Path

import httpx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------------------------------------------------------------------------
# Configuration (all via environment variables)
# ---------------------------------------------------------------------------
WATCH_DIR = os.getenv("WATCH_DIR", "/app/inbox")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
STABILITY_SECONDS = int(os.getenv("STABILITY_SECONDS", "2"))
UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "120"))

SUPPORTED_FORMATS = {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".png", ".jpg"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinelai.watcher")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _ensure_dirs() -> tuple[Path, Path]:
    """Ensure processed/ and error/ subdirectories exist."""
    processed = Path(WATCH_DIR) / "processed"
    error = Path(WATCH_DIR) / "error"
    processed.mkdir(parents=True, exist_ok=True)
    error.mkdir(parents=True, exist_ok=True)
    return processed, error


def _set_permissions(filepath: Path) -> None:
    """Set file permissions to 666 so the host user can read/write/delete."""
    try:
        filepath.chmod(stat.S_IRUSR | stat.S_IWUSR |
                       stat.S_IRGRP | stat.S_IWGRP |
                       stat.S_IROTH | stat.S_IWOTH)  # 0o666
    except OSError as exc:
        logger.warning(f"⚠️ chmod 666 fehlgeschlagen für {filepath}: {exc}")


def _wait_for_stable_size(filepath: str, interval: float = 0.5) -> bool:
    """
    Wait until the file size is unchanged for STABILITY_SECONDS.
    Returns True if stable, False if the file vanished.
    """
    previous_size = -1
    stable_since = None  # type: float | None

    while True:
        try:
            current_size = os.path.getsize(filepath)
        except OSError:
            # File was removed before we could process it
            return False

        if current_size == previous_size:
            if stable_since is None:
                stable_since = time.monotonic()
            elif (time.monotonic() - stable_since) >= STABILITY_SECONDS:
                return True
        else:
            stable_since = None

        previous_size = current_size
        time.sleep(interval)


def _write_error_log(error_dir: Path, filename: str, error_msg: str) -> None:
    """Write a per-file .log with error details into the error directory."""
    log_path = error_dir / f"{filename}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Datei: {filename}\n")
            f.write(f"Zeitpunkt: {timestamp}\n")
            f.write(f"Fehler:\n{error_msg}\n")
        _set_permissions(log_path)
        logger.info(f"📝 Fehler-Log geschrieben: {log_path.name}")
    except OSError as exc:
        logger.error(f"Fehler-Log konnte nicht geschrieben werden: {exc}")

# ---------------------------------------------------------------------------
# Inbox event handler
# ---------------------------------------------------------------------------

class InboxHandler(FileSystemEventHandler):
    """Handles new files arriving in the inbox directory."""

    def __init__(self) -> None:
        super().__init__()
        self.processed_dir, self.error_dir = _ensure_dirs()

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Ignore files in subdirectories (processed/, error/)
        if filepath.parent != Path(WATCH_DIR):
            return

        # Ignore hidden files and temporary files
        if filepath.name.startswith(".") or filepath.name.startswith("~"):
            return

        ext = filepath.suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            logger.info(f"⏭️ Ignoriert (nicht unterstützt): {filepath.name} ({ext})")
            return

        logger.info(f"📄 Neue Datei erkannt: {filepath.name}")
        self._process_file(filepath)

    def _process_file(self, filepath: Path) -> None:
        """Upload the file to the backend API and move it accordingly."""
        filename = filepath.name

        try:
            # --- Step 1: Wait for stable file size (scanner support) ---
            logger.info(f"⏳ Stabilitäts-Check ({STABILITY_SECONDS}s) für: {filename}")
            if not _wait_for_stable_size(str(filepath)):
                logger.warning(f"⚠️ Datei verschwunden während Stabilitäts-Check: {filename}")
                return

            # --- Step 2: Upload via API ---
            logger.info(f"📤 Upload gestartet: {filename}")
            with open(filepath, "rb") as f:
                response = httpx.post(
                    f"{API_BASE}/documents/upload",
                    files={"file": (filename, f)},
                    timeout=UPLOAD_TIMEOUT,
                )

            # --- Step 3: Handle response ---
            if response.status_code == 200:
                # Success → move to processed/
                dest = self.processed_dir / filename
                # Handle duplicate filenames
                if dest.exists():
                    stem = filepath.stem
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dest = self.processed_dir / f"{stem}_{ts}{filepath.suffix}"

                shutil.move(str(filepath), str(dest))
                _set_permissions(dest)
                logger.info(f"✅ Verarbeitet: {filename} → processed/{dest.name}")
            else:
                # API returned an error
                error_msg = (
                    f"HTTP {response.status_code}\n"
                    f"Response: {response.text}"
                )
                self._move_to_error(filepath, error_msg)

        except httpx.TimeoutException:
            self._move_to_error(filepath, f"Upload-Timeout nach {UPLOAD_TIMEOUT}s")
        except httpx.ConnectError:
            self._move_to_error(
                filepath,
                "Backend nicht erreichbar. Ist der Backend-Container gestartet?"
            )
        except Exception as exc:
            # Catch-all: never crash
            tb = traceback.format_exc()
            self._move_to_error(filepath, f"Unerwarteter Fehler:\n{tb}")

    def _move_to_error(self, filepath: Path, error_msg: str) -> None:
        """Move a file to the error directory and write an error log."""
        filename = filepath.name
        logger.error(f"❌ Fehler bei {filename}: {error_msg.splitlines()[0]}")

        try:
            dest = self.error_dir / filename
            if dest.exists():
                stem = filepath.stem
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = self.error_dir / f"{stem}_{ts}{filepath.suffix}"

            shutil.move(str(filepath), str(dest))
            _set_permissions(dest)
            _write_error_log(self.error_dir, dest.name, error_msg)
        except Exception as exc:
            logger.error(f"❌ Konnte Datei nicht nach error/ verschieben: {exc}")

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Start the inbox watcher."""
    _ensure_dirs()

    logger.info("=" * 60)
    logger.info("📥 SentinelAI Magic Inbox – Watcher gestartet")
    logger.info(f"   Überwache:  {WATCH_DIR}")
    logger.info(f"   API:        {API_BASE}")
    logger.info(f"   Formate:    {', '.join(sorted(SUPPORTED_FORMATS))}")
    logger.info(f"   Stabilität: {STABILITY_SECONDS}s")
    logger.info("=" * 60)

    observer = Observer()
    observer.schedule(InboxHandler(), WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Watcher wird gestoppt...")
        observer.stop()

    observer.join()
    logger.info("👋 Watcher beendet.")


if __name__ == "__main__":
    main()
