"""
Chat History Manager
Simple SQLite-based chat history for transcriptions with robust fallback
Stores all transcriptions with timestamps, models, and metadata
"""

import logging
import sqlite3
import tempfile
import threading
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """Manages chat history using SQLite database with robust error handling"""

    def __init__(self, db_path: str = None):
        import os

        self.db_path = None
        self.db_lock = threading.Lock()
        self.database_enabled = False

        # Use different paths for development vs production
        if db_path is None:
            # Try production path first
            try:
                prod_path = "/opt/whisper-appliance/data/chat_history.db"
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                # Test write access
                test_file = os.path.join(os.path.dirname(prod_path), ".test_write")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                self.db_path = prod_path
                logger.info(f"📁 Using production database path: {self.db_path}")
            except (PermissionError, OSError, IOError) as e:
                logger.warning(f"⚠️ Cannot write to production path: {e}")
                # Try fallback to home directory
                try:
                    dev_path = os.path.expanduser("~/.whisper-appliance/chat_history.db")
                    os.makedirs(os.path.dirname(dev_path), exist_ok=True)
                    # Test write access
                    test_file = os.path.join(os.path.dirname(dev_path), ".test_write")
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    self.db_path = dev_path
                    logger.info(f"📁 Using development database path: {self.db_path}")
                except (PermissionError, OSError, IOError) as e2:
                    logger.warning(f"⚠️ Cannot write to home directory: {e2}")
                    # Final fallback to temp directory
                    temp_dir = tempfile.gettempdir()
                    self.db_path = os.path.join(temp_dir, "whisper_chat_history.db")
                    logger.warning(f"📁 Using temporary database path: {self.db_path}")
        else:
            self.db_path = db_path

        # Initialize database
        try:
            self._init_database()
            self.database_enabled = True
        except Exception as e:
            logger.error(f"❌ Failed to initialize chat history database: {e}")
            # Create minimal fallback that doesn't crash
            self.db_path = None
            self.database_enabled = False
            logger.warning("⚠️ Chat history will be disabled due to database init failure")

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        if self.db_path is None:
            logger.warning("⚠️ Database path is None, skipping database initialization")
            return

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
                        source_type TEXT,
                        filename TEXT,
                        duration REAL,
                        confidence REAL,
                        metadata TEXT
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
            raise

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
        if not self.database_enabled:
            logger.warning("⚠️ Database disabled, transcription not saved")
            return -1

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

                    return cursor.lastrowid

        except Exception as e:
            logger.error(f"Failed to add transcription: {e}")
            return -1

    def get_recent_transcriptions(self, limit: int = 50) -> List[Dict]:
        """Get recent transcriptions"""
        if not self.database_enabled:
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM transcriptions 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get recent transcriptions: {e}")
            return []

    def search_transcriptions(self, query: str, limit: int = 50) -> List[Dict]:
        """Search transcriptions by text content"""
        if not self.database_enabled:
            return []

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
                    (f"%{query}%", limit),
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to search transcriptions: {e}")
            return []

    def get_transcriptions_by_source(self, source_type: str, limit: int = 50) -> List[Dict]:
        """Get transcriptions by source type"""
        if not self.database_enabled:
            return []

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

    def get_statistics(self) -> Dict:
        """Get chat history statistics"""
        if not self.database_enabled:
            return {
                "total_transcriptions": 0,
                "source_breakdown": {},
                "model_breakdown": {},
                "recent_activity": [],
                "database_enabled": False,
            }

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total count
                total_count = conn.execute("SELECT COUNT(*) FROM transcriptions").fetchone()[0]

                # Source breakdown
                source_cursor = conn.execute(
                    """
                    SELECT source_type, COUNT(*) as count 
                    FROM transcriptions 
                    GROUP BY source_type
                """
                )
                source_breakdown = {row[0]: row[1] for row in source_cursor.fetchall()}

                # Model breakdown
                model_cursor = conn.execute(
                    """
                    SELECT model_used, COUNT(*) as count 
                    FROM transcriptions 
                    WHERE model_used IS NOT NULL 
                    GROUP BY model_used
                """
                )
                model_breakdown = {row[0]: row[1] for row in model_cursor.fetchall()}

                # Recent activity (last 7 days)
                recent_cursor = conn.execute(
                    """
                    SELECT DATE(timestamp) as date, COUNT(*) as count 
                    FROM transcriptions 
                    WHERE timestamp >= datetime('now', '-7 days') 
                    GROUP BY DATE(timestamp) 
                    ORDER BY date DESC
                """
                )
                recent_activity = [{"date": row[0], "count": row[1]} for row in recent_cursor.fetchall()]

                return {
                    "total_transcriptions": total_count,
                    "source_breakdown": source_breakdown,
                    "model_breakdown": model_breakdown,
                    "recent_activity": recent_activity,
                    "database_enabled": True,
                }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_transcriptions": 0,
                "source_breakdown": {},
                "model_breakdown": {},
                "recent_activity": [],
                "database_enabled": False,
            }

    def export_history(self, format: str = "json") -> str:
        """Export chat history in specified format"""
        if not self.database_enabled:
            if format == "csv":
                return "timestamp,text,language,model_used,source_type,filename\n# Database disabled"
            else:
                return '{"error": "Database disabled", "transcriptions": []}'

        try:
            transcriptions = self.get_recent_transcriptions(limit=10000)  # Export all

            if format == "csv":
                import csv
                import io

                output = io.StringIO()
                if transcriptions:
                    writer = csv.DictWriter(
                        output, fieldnames=["timestamp", "text", "language", "model_used", "source_type", "filename"]
                    )
                    writer.writeheader()
                    for t in transcriptions:
                        writer.writerow(
                            {
                                "timestamp": t.get("timestamp", ""),
                                "text": t.get("text", ""),
                                "language": t.get("language", ""),
                                "model_used": t.get("model_used", ""),
                                "source_type": t.get("source_type", ""),
                                "filename": t.get("filename", ""),
                            }
                        )
                else:
                    output.write("timestamp,text,language,model_used,source_type,filename\n")

                return output.getvalue()

            else:  # JSON format
                import json

                return json.dumps({"transcriptions": transcriptions, "export_timestamp": datetime.now().isoformat()}, indent=2)

        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            if format == "csv":
                return f"timestamp,text,language,model_used,source_type,filename\n# Export failed: {str(e)}"
            else:
                return f'{{"error": "Export failed: {str(e)}", "transcriptions": []}}'
            logger.error(f"Failed to export history: {e}")
            if format == "csv":
                return f"timestamp,text,language,model_used,source_type,filename\n# Export failed: {str(e)}"
            else:
                return f'{{"error": "Export failed: {str(e)}", "transcriptions": []}}'

    def update_transcription(self, transcription_id: int, text: str) -> bool:
        """Update transcription text by ID"""
        if not self.database_enabled:
            logger.warning("⚠️ Database disabled, transcription not updated")
            return False

        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("UPDATE transcriptions SET text = ? WHERE id = ?", (text, transcription_id))
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update transcription {transcription_id}: {e}")
            return False

    def delete_transcription(self, transcription_id: int) -> bool:
        """Delete transcription by ID"""
        if not self.database_enabled:
            logger.warning("⚠️ Database disabled, transcription not deleted")
            return False

        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM transcriptions WHERE id = ?", (transcription_id,))
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete transcription {transcription_id}: {e}")
            return False

    def import_history(self, file_content: str, file_format: str, filename: str = None) -> Dict:
        """Import chat history from JSON or CSV content"""
        if not self.database_enabled:
            return {"status": "error", "error": "Database disabled, cannot import history", "imported_count": 0}

        try:
            imported_count = 0
            errors = []

            if file_format.lower() == "json":
                imported_count, errors = self._import_from_json(file_content)
            elif file_format.lower() == "csv":
                imported_count, errors = self._import_from_csv(file_content)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported format: {file_format}. Use 'json' or 'csv'",
                    "imported_count": 0,
                }

            if errors:
                return {
                    "status": "partial_success",
                    "message": f"Imported {imported_count} transcriptions with {len(errors)} errors",
                    "imported_count": imported_count,
                    "errors": errors[:10],  # Limit error list
                }
            else:
                return {
                    "status": "success",
                    "message": f"Successfully imported {imported_count} transcriptions",
                    "imported_count": imported_count,
                }

        except Exception as e:
            logger.error(f"Failed to import history: {e}")
            return {"status": "error", "error": f"Import failed: {str(e)}", "imported_count": 0}

    def _import_from_json(self, content: str) -> tuple:
        """Import transcriptions from JSON content"""
        import json

        imported_count = 0
        errors = []

        try:
            data = json.loads(content)

            # Handle different JSON structures
            transcriptions = []
            if isinstance(data, dict):
                if "transcriptions" in data:
                    transcriptions = data["transcriptions"]
                elif "data" in data:
                    transcriptions = data["data"]
                else:
                    # Assume the dict itself is a single transcription
                    transcriptions = [data]
            elif isinstance(data, list):
                transcriptions = data
            else:
                raise ValueError(
                    "Invalid JSON structure. Expected object with 'transcriptions' key or array of transcriptions"
                )

            for i, item in enumerate(transcriptions):
                try:
                    if not isinstance(item, dict):
                        errors.append(f"Line {i+1}: Invalid item type, expected object")
                        continue

                    # Extract required text field
                    text = item.get("text", "").strip()
                    if not text:
                        errors.append(f"Line {i+1}: Missing or empty 'text' field")
                        continue

                    # Extract optional fields with defaults
                    language = item.get("language")
                    model_used = item.get("model_used")
                    source_type = item.get("source_type", "imported")
                    filename = item.get("filename")
                    duration = item.get("duration")
                    confidence = item.get("confidence")
                    metadata = item.get("metadata")

                    # Convert string numbers to float if needed
                    if duration and isinstance(duration, str):
                        try:
                            duration = float(duration)
                        except ValueError:
                            duration = None

                    if confidence and isinstance(confidence, str):
                        try:
                            confidence = float(confidence)
                        except ValueError:
                            confidence = None

                    # Add to database
                    result_id = self.add_transcription(
                        text=text,
                        language=language,
                        model_used=model_used,
                        source_type=source_type,
                        filename=filename,
                        duration=duration,
                        confidence=confidence,
                        metadata=metadata,
                    )

                    if result_id > 0:
                        imported_count += 1
                    else:
                        errors.append(f"Line {i+1}: Failed to insert transcription")

                except Exception as e:
                    errors.append(f"Line {i+1}: {str(e)}")
                    continue

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

        return imported_count, errors

    def _import_from_csv(self, content: str) -> tuple:
        """Import transcriptions from CSV content"""
        import csv
        import io

        imported_count = 0
        errors = []

        try:
            # Parse CSV content
            csv_file = io.StringIO(content)
            csv_reader = csv.DictReader(csv_file)

            # Check for required columns
            if not csv_reader.fieldnames:
                raise ValueError("CSV file appears to be empty or invalid")

            required_fields = ["text"]
            missing_fields = [field for field in required_fields if field not in csv_reader.fieldnames]
            if missing_fields:
                raise ValueError(f"Missing required CSV columns: {', '.join(missing_fields)}")

            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is line 1)
                try:
                    # Extract and validate text
                    text = row.get("text", "").strip()
                    if not text:
                        errors.append(f"Line {row_num}: Missing or empty 'text' field")
                        continue

                    # Extract optional fields
                    language = row.get("language", "").strip() or None
                    model_used = row.get("model_used", "").strip() or None
                    source_type = row.get("source_type", "").strip() or "imported"
                    filename = row.get("filename", "").strip() or None

                    # Handle numeric fields
                    duration = None
                    confidence = None

                    if row.get("duration"):
                        try:
                            duration = float(row["duration"])
                        except ValueError:
                            errors.append(f"Line {row_num}: Invalid duration value")

                    if row.get("confidence"):
                        try:
                            confidence = float(row["confidence"])
                        except ValueError:
                            errors.append(f"Line {row_num}: Invalid confidence value")

                    # Add to database
                    result_id = self.add_transcription(
                        text=text,
                        language=language,
                        model_used=model_used,
                        source_type=source_type,
                        filename=filename,
                        duration=duration,
                        confidence=confidence,
                        metadata=None,
                    )

                    if result_id > 0:
                        imported_count += 1
                    else:
                        errors.append(f"Line {row_num}: Failed to insert transcription")

                except Exception as e:
                    errors.append(f"Line {row_num}: {str(e)}")
                    continue

        except Exception as e:
            raise ValueError(f"CSV parsing error: {str(e)}")

        return imported_count, errors

    def get_transcriptions_by_date_range(self, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict]:
        """Get transcriptions filtered by date range"""
        if not self.database_enabled:
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM transcriptions WHERE 1=1"
                params = []

                if start_date:
                    query += " AND DATE(timestamp) >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND DATE(timestamp) <= ?"
                    params.append(end_date)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get transcriptions by date range: {e}")
            return []
