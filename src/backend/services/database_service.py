"""
Database Service - SQLite Integration
Persistent storage for documents and audit logs (DSGVO-compliant)
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQLite database service for persistent storage."""
    
    def __init__(self, db_path: str = "data/sentinel.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    status TEXT DEFAULT 'Neu',
                    chunk_count INTEGER DEFAULT 0,
                    pii_detected BOOLEAN DEFAULT 0,
                    pii_summary TEXT,
                    summary TEXT,
                    keywords TEXT,
                    topics TEXT,
                    last_modified TEXT,
                    archived BOOLEAN DEFAULT 0
                )
            """)
            
            # Audit log table (append-only, no deletes allowed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user TEXT DEFAULT 'system',
                    document_id TEXT,
                    metadata TEXT,
                    ip_address TEXT
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_status 
                ON documents(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_uploaded 
                ON documents(uploaded_at DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_log(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_document 
                ON audit_log(document_id)
            """)
            
            logger.info("Database schema initialized")
    
    # ========== DOCUMENTS CRUD ==========
    
    def add_document(
        self,
        doc_id: str,
        filename: str,
        file_size: int = 0,
        file_type: str = "",
        chunk_count: int = 0,
        pii_detected: bool = False,
        pii_summary: str = "",
        summary: str = ""
    ) -> bool:
        """Add a new document."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents (
                        id, filename, uploaded_at, file_size, file_type,
                        chunk_count, pii_detected, pii_summary, summary, last_modified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, filename, datetime.utcnow().isoformat(),
                    file_size, file_type, chunk_count, pii_detected,
                    pii_summary, summary, datetime.utcnow().isoformat()
                ))
            logger.info(f"Document added: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    def get_all_documents(
        self,
        status: Optional[str] = None,
        archived: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all documents with optional filters."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM documents WHERE archived = ?"
                params: List[Any] = [archived]
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY uploaded_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def update_document_status(
        self,
        doc_id: str,
        status: str
    ) -> bool:
        """Update document status."""
        valid_statuses = ["Neu", "In Prüfung", "Erledigt", "Archiviert"]
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}")
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE documents 
                    SET status = ?, last_modified = ?
                    WHERE id = ?
                """, (status, datetime.utcnow().isoformat(), doc_id))
            logger.info(f"Document {doc_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            return False
    
    def update_document_analysis(
        self,
        doc_id: str,
        summary: str = "",
        keywords: str = "",
        topics: str = ""
    ) -> bool:
        """Update document analysis results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE documents 
                    SET summary = ?, keywords = ?, topics = ?, last_modified = ?
                    WHERE id = ?
                """, (summary, keywords, topics, datetime.utcnow().isoformat(), doc_id))
            return True
        except Exception as e:
            logger.error(f"Error updating document analysis: {e}")
            return False
    
    def archive_document(self, doc_id: str) -> bool:
        """Archive a document (soft delete)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE documents 
                    SET archived = 1, status = 'Archiviert', last_modified = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), doc_id))
            logger.info(f"Document archived: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error archiving document: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Permanently delete a document (DSGVO right to deletion)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            logger.warning(f"Document permanently deleted: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    # ========== AUDIT LOG (Append-only) ==========
    
    def add_audit_log(
        self,
        action: str,
        user: str = "system",
        document_id: Optional[str] = None,
        metadata: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Add an audit log entry (append-only, immutable)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_log (
                        timestamp, action, user, document_id, metadata, ip_address
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    action,
                    user,
                    document_id,
                    metadata,
                    ip_address
                ))
            return True
        except Exception as e:
            logger.error(f"Error adding audit log: {e}")
            return False
    
    def get_audit_logs(
        self,
        document_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs (read-only)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if document_id:
                    cursor.execute("""
                        SELECT * FROM audit_log 
                        WHERE document_id = ?
                        ORDER BY timestamp DESC LIMIT ?
                    """, (document_id, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM audit_log 
                        ORDER BY timestamp DESC LIMIT ?
                    """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    # NOTE: No delete_audit_log() method - audit logs are immutable!
    
    # ========== STATISTICS ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Document counts by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM documents 
                    WHERE archived = 0
                    GROUP BY status
                """)
                status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
                
                # Total documents
                cursor.execute("SELECT COUNT(*) as count FROM documents WHERE archived = 0")
                total_docs = cursor.fetchone()["count"]
                
                # PII documents
                cursor.execute("SELECT COUNT(*) as count FROM documents WHERE pii_detected = 1 AND archived = 0")
                pii_docs = cursor.fetchone()["count"]
                
                # Audit log entries
                cursor.execute("SELECT COUNT(*) as count FROM audit_log")
                audit_count = cursor.fetchone()["count"]
                
                return {
                    "total_documents": total_docs,
                    "pii_documents": pii_docs,
                    "status_counts": status_counts,
                    "audit_entries": audit_count
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
