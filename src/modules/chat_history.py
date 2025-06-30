"""
Chat History Manager
Simple SQLite-based chat history for transcriptions
Stores all transcriptions with timestamps, models, and metadata
"""

import logging
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """Manages chat history using SQLite database"""

    def __init__(self, db_path: str = None):
        import os

        # Use different paths for development vs production
        if db_path is None:
            # Try production path first, fallback to local development path
            try:
                prod_path = "/opt/whisper-appliance/data/chat_history.db"
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                self.db_path = prod_path
                logger.info(f"📁 Using production database path: {self.db_path}")
            except (PermissionError, OSError):
                # Fallback to local development path
                dev_path = os.path.expanduser("~/.whisper-appliance/chat_history.db")
                os.makedirs(os.path.dirname(dev_path), exist_ok=True)
                self.db_path = dev_path
                logger.info(f"📁 Using development database path: {self.db_path}")
        else:
            self.db_path = db_path

        self.db_lock = threading.Lock()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transcriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        text TEXT NOT NULL,
                        language TEXT,
                        model_used TEXT,
                        source_type TEXT,  -- 'live', 'upload', 'api'
                        filename TEXT,     -- for uploads
                        duration REAL,     -- in seconds, if available
                        confidence REAL,   -- if available
                        metadata TEXT      -- JSON string for additional data
                    )
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON transcriptions(timestamp DESC)
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_source_type 
                    ON transcriptions(source_type)
                """
                )

                conn.commit()
                logger.info("✅ Chat history database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def add_transcription(
        self,
        text: str,
        language: str = None,
        model_used: str = None,
        source_type: str = "unknown",
        filename: str = None,
        duration: float = None,
        confidence: float = None,
        metadata: dict = None,
    ) -> int:
        """Add a new transcription to the history"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    import json

                    metadata_json = json.dumps(metadata) if metadata else None

                    cursor = conn.execute(
                        """
                        INSERT INTO transcriptions 
                        (text, language, model_used, source_type, filename, duration, confidence, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (text, language, model_used, source_type, filename, duration, confidence, metadata_json),
                    )

                    transcription_id = cursor.lastrowid
                    conn.commit()

                    logger.info(f"📝 Added transcription #{transcription_id} ({source_type})")
                    return transcription_id

        except Exception as e:
            logger.error(f"Failed to add transcription: {e}")
            return -1

    def get_recent_transcriptions(self, limit: int = 50) -> List[Dict]:
        """Get recent transcriptions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access

                cursor = conn.execute(
                    """
                    SELECT * FROM transcriptions 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                transcriptions = []
                for row in cursor.fetchall():
                    transcription = dict(row)

                    # Parse metadata JSON
                    if transcription["metadata"]:
                        import json

                        try:
                            transcription["metadata"] = json.loads(transcription["metadata"])
                        except:
                            transcription["metadata"] = {}

                    transcriptions.append(transcription)

                return transcriptions

        except Exception as e:
            logger.error(f"Failed to get recent transcriptions: {e}")
            return []

    def get_transcriptions_by_source(self, source_type: str, limit: int = 50) -> List[Dict]:
        """Get transcriptions filtered by source type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute(
                    """
                    SELECT * FROM transcriptions 
                    WHERE source_type = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (source_type, limit),
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get transcriptions by source: {e}")
            return []

    def search_transcriptions(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Search transcriptions by text content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute(
                    """
                    SELECT * FROM transcriptions 
                    WHERE text LIKE ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (f"%{search_term}%", limit),
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to search transcriptions: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Get chat history statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total count
                total_count = conn.execute("SELECT COUNT(*) FROM transcriptions").fetchone()[0]

                # Count by source type
                source_counts = {}
                for row in conn.execute("SELECT source_type, COUNT(*) FROM transcriptions GROUP BY source_type"):
                    source_counts[row[0]] = row[1]

                # Count by model
                model_counts = {}
                for row in conn.execute(
                    "SELECT model_used, COUNT(*) FROM transcriptions WHERE model_used IS NOT NULL GROUP BY model_used"
                ):
                    model_counts[row[0]] = row[1]

                # Recent activity (last 24 hours)
                recent_count = conn.execute(
                    """
                    SELECT COUNT(*) FROM transcriptions 
                    WHERE timestamp > datetime('now', '-1 day')
                """
                ).fetchone()[0]

                return {
                    "total_transcriptions": total_count,
                    "source_breakdown": source_counts,
                    "model_breakdown": model_counts,
                    "last_24h": recent_count,
                }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def clear_old_entries(self, days: int = 30) -> int:
        """Clear entries older than specified days"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        """
                        DELETE FROM transcriptions 
                        WHERE timestamp < datetime('now', '-{} days')
                    """.format(
                            days
                        )
                    )

                    deleted_count = cursor.rowcount
                    conn.commit()

                    logger.info(f"🗑️ Cleared {deleted_count} old transcriptions (older than {days} days)")
                    return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear old entries: {e}")
            return 0

    def export_history(self, format: str = "json") -> str:
        """Export chat history in various formats"""
        try:
            transcriptions = self.get_recent_transcriptions(limit=1000)

            if format.lower() == "json":
                import json

                return json.dumps(transcriptions, indent=2, default=str)

            elif format.lower() == "csv":
                import csv
                import io

                output = io.StringIO()
                if transcriptions:
                    writer = csv.DictWriter(output, fieldnames=transcriptions[0].keys())
                    writer.writeheader()
                    writer.writerows(transcriptions)

                return output.getvalue()

            else:
                return "Unsupported format"

        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return ""
