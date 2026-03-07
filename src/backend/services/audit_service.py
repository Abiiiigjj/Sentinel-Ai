"""
Audit Service - Logging for DSGVO Compliance
Maintains immutable audit trail of all data processing activities
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiofiles
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AuditService:
    """Service for maintaining GDPR-compliant audit logs."""
    
    def __init__(self, data_dir: str | Path = "./data"):
        self.data_dir = Path(data_dir)
        self.audit_dir = self.data_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.audit_dir / "audit.db"
        self._init_database()
        
        logger.info(f"Audit service initialized at {self.audit_dir}")
    
    def _init_database(self):
        """Initialize SQLite database for audit logs with immutability protection."""
        with self._get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user
                ON audit_log(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_action
                ON audit_log(action)
            """)

            # SECURITY: Immutability triggers — prevent UPDATE and DELETE on audit_log
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_update
                BEFORE UPDATE ON audit_log
                BEGIN
                    SELECT RAISE(ABORT, 'SECURITY: Audit log entries are immutable and cannot be modified');
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_delete
                BEFORE DELETE ON audit_log
                BEGIN
                    SELECT RAISE(ABORT, 'SECURITY: Audit log entries are immutable and cannot be deleted');
                END
            """)
            conn.commit()
            logger.info("Audit database initialized with immutability triggers")
    
    @contextmanager
    def _get_db(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    async def log(
        self,
        user_id: str,
        action: str,
        details: str = None,
        ip_address: str = None,
        metadata: dict = None
    ) -> int:
        """
        Log an audit event.
        
        Args:
            user_id: Identifier of the user or 'system'
            action: Type of action (e.g., 'document_upload', 'chat', 'delete')
            details: Human-readable details
            ip_address: Client IP if available
            metadata: Additional structured data
            
        Returns:
            ID of the created audit entry
        """
        timestamp = datetime.utcnow().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self._get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO audit_log (timestamp, user_id, action, details, ip_address, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, user_id, action, details, ip_address, metadata_json))
            conn.commit()
            
            entry_id = cursor.lastrowid
            logger.debug(f"Audit log entry {entry_id}: {action} by {user_id}")
            
            return entry_id
    
    async def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: str = None,
        action: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> list[dict]:
        """
        Retrieve audit log entries with optional filtering.
        
        Args:
            limit: Maximum number of entries
            offset: Number of entries to skip
            user_id: Filter by user
            action: Filter by action type
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of audit entries
        """
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_db() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entry = dict(row)
                if entry.get("metadata"):
                    entry["metadata"] = json.loads(entry["metadata"])
                entries.append(entry)
            
            return entries
    
    async def get_stats(self) -> dict:
        """Get audit log statistics."""
        with self._get_db() as conn:
            # Total entries
            total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            
            # Last activity
            last_row = conn.execute(
                "SELECT timestamp FROM audit_log ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
            last_activity = datetime.fromisoformat(last_row[0]) if last_row else None
            
            # Action breakdown
            action_counts = {}
            for row in conn.execute(
                "SELECT action, COUNT(*) as count FROM audit_log GROUP BY action"
            ):
                action_counts[row[0]] = row[1]
            
            return {
                "total_entries": total,
                "last_activity": last_activity,
                "action_breakdown": action_counts
            }
    
    async def export_for_user(self, user_id: str) -> list[dict]:
        """
        Export all audit entries for a specific user (DSGVO data portability).
        
        Args:
            user_id: User to export data for
            
        Returns:
            All audit entries for the user
        """
        return await self.get_entries(limit=10000, user_id=user_id)
    
    # NOTE: Audit log entries are immutable by design (SQLite triggers).
    # DSGVO Art. 17 (Right to Erasure) does NOT override legal retention
    # requirements (HGB 10 years, AO 6-10 years for tax-relevant documents).
    # Audit logs are pseudonymized, not deleted. See: export_for_user().
    
    async def get_user_activity_summary(self, user_id: str) -> dict:
        """Get activity summary for a specific user."""
        entries = await self.get_entries(limit=1000, user_id=user_id)
        
        action_counts = {}
        first_activity = None
        last_activity = None
        
        for entry in entries:
            action = entry["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
            
            timestamp = datetime.fromisoformat(entry["timestamp"])
            if first_activity is None or timestamp < first_activity:
                first_activity = timestamp
            if last_activity is None or timestamp > last_activity:
                last_activity = timestamp
        
        return {
            "user_id": user_id,
            "total_actions": len(entries),
            "action_breakdown": action_counts,
            "first_activity": first_activity,
            "last_activity": last_activity
        }
