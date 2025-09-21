"""
Metadata management for MDS Knowledge Capture Agent.
Handles SQLite database operations for tracking document metadata.
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages document metadata in SQLite database."""
    
    def __init__(self, db_path: str = "mds_metadata.db"):
        """Initialize metadata manager with database path."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    download_date TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    version TEXT,
                    is_current BOOLEAN DEFAULT 1,
                    archived_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url, sha256_hash)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            raise
    
    def document_exists(self, url: str, file_hash: str) -> bool:
        """Check if document with same URL and hash already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM documents WHERE url = ? AND sha256_hash = ?",
                (url, file_hash)
            )
            return cursor.fetchone()[0] > 0
    
    def get_current_document(self, url: str) -> Optional[Dict[str, Any]]:
        """Get current document metadata for a URL."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE url = ? AND is_current = 1",
                (url,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def add_document(
        self,
        url: str,
        filename: str,
        file_path: str,
        file_size: int,
        file_hash: str,
        version: Optional[str] = None
    ) -> int:
        """Add new document to database."""
        download_date = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO documents 
                    (url, filename, file_path, download_date, file_size_bytes, 
                     sha256_hash, version, is_current)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """, (url, filename, file_path, download_date, file_size, file_hash, version))
                
                doc_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Added document {filename} with ID {doc_id}")
                return doc_id
                
            except sqlite3.IntegrityError:
                logger.warning(f"Document with URL {url} and hash {file_hash} already exists")
                raise
    
    def archive_document(self, doc_id: int, archive_path: str) -> None:
        """Mark document as archived and update path."""
        archived_date = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents 
                SET is_current = 0, archived_date = ?, file_path = ?
                WHERE id = ?
            """, (archived_date, archive_path, doc_id))
            
            conn.commit()
            logger.info(f"Archived document ID {doc_id} to {archive_path}")
    
    def log_download_attempt(self, url: str, status: str, error_message: str = None) -> None:
        """Log download attempt to history table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO download_history (url, status, error_message)
                VALUES (?, ?, ?)
            """, (url, status, error_message))
            
            conn.commit()
    
    def get_all_documents(self, current_only: bool = False) -> List[Dict[str, Any]]:
        """Get all documents from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if current_only:
                cursor.execute("SELECT * FROM documents WHERE is_current = 1 ORDER BY download_date DESC")
            else:
                cursor.execute("SELECT * FROM documents ORDER BY download_date DESC")
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_download_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent download history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM download_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_entries(self, days_old: int = 365) -> int:
        """Remove old archived documents from database (not files)."""
        cutoff_date = datetime.now().replace(days=-days_old).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM documents 
                WHERE is_current = 0 AND archived_date < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old database entries")
            return deleted_count


if __name__ == "__main__":
    # Simple test/validation script
    logging.basicConfig(level=logging.INFO)
    
    # Test the metadata manager
    manager = MetadataManager("test_metadata.db")
    
    # Test adding a document
    test_file_path = "/tmp/test_doc.txt"
    with open(test_file_path, "w") as f:
        f.write("Test document content")
    
    file_hash = manager.calculate_file_hash(test_file_path)
    file_size = os.path.getsize(test_file_path)
    
    doc_id = manager.add_document(
        url="https://test.com/doc.pdf",
        filename="test_doc.pdf",
        file_path=test_file_path,
        file_size=file_size,
        file_hash=file_hash,
        version="1.0"
    )
    
    # Test retrieval
    docs = manager.get_all_documents()
    print(f"Total documents: {len(docs)}")
    
    # Cleanup test files
    os.remove(test_file_path)
    os.remove("test_metadata.db")
    print("✅ Metadata manager validation complete")