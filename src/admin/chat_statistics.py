"""
Chat Statistics Manager for WhisperAppliance Admin
Handles transcription history and statistics
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ChatStatisticsManager:
    """Manages chat history statistics and display"""
    
    def __init__(self, chat_history=None):
        self.chat_history = chat_history
    
    def get_statistics(self):
        """Get chat history statistics"""
        if not self.chat_history:
            return self._get_empty_statistics()
        
        try:
            # Get recent history
            recent_history = self.chat_history.get_recent_history(limit=100)
            
            # Calculate statistics
            total_transcriptions = len(recent_history)
            
            # Count by source
            sources = {"live": 0, "upload": 0, "api": 0}
            for entry in recent_history:
                source = entry.get("source", "api")
                if source in sources:
                    sources[source] += 1
            
            # Time-based statistics
            now = datetime.now()
            last_24h = sum(1 for entry in recent_history 
                          if self._is_within_hours(entry.get("timestamp"), 24))
            last_7d = sum(1 for entry in recent_history 
                         if self._is_within_days(entry.get("timestamp"), 7))
            
            # Language statistics
            languages = {}
            for entry in recent_history:
                lang = entry.get("language", "unknown")
                languages[lang] = languages.get(lang, 0) + 1
            
            # Average duration
            durations = [entry.get("duration", 0) for entry in recent_history if entry.get("duration")]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "total": total_transcriptions,
                "by_source": sources,
                "last_24h": last_24h,
                "last_7d": last_7d,
                "languages": languages,
                "avg_duration": round(avg_duration, 2),
                "recent": recent_history[:10]  # Last 10 entries
            }
            
        except Exception as e:
            logger.error(f"Error getting chat statistics: {e}")
            return self._get_empty_statistics()
    
    def _get_empty_statistics(self):
        """Return empty statistics structure"""
        return {
            "total": 0,
            "by_source": {"live": 0, "upload": 0, "api": 0},
            "last_24h": 0,
            "last_7d": 0,
            "languages": {},
            "avg_duration": 0,
            "recent": []
        }
    
    def _is_within_hours(self, timestamp, hours):
        """Check if timestamp is within specified hours"""
        if not timestamp:
            return False
        try:
            if isinstance(timestamp, str):
                ts = datetime.fromisoformat(timestamp)
            else:
                ts = timestamp
            return (datetime.now() - ts) < timedelta(hours=hours)
        except:
            return False
    
    def _is_within_days(self, timestamp, days):
        """Check if timestamp is within specified days"""
        return self._is_within_hours(timestamp, days * 24)
    
    def format_history_entry(self, entry):
        """Format a history entry for display"""
        return {
            "timestamp": entry.get("timestamp", ""),
            "text": entry.get("text", "")[:100] + "..." if len(entry.get("text", "")) > 100 else entry.get("text", ""),
            "source": entry.get("source", "api"),
            "language": entry.get("language", "auto"),
            "duration": entry.get("duration", 0)
        }
    
    def get_export_data(self, format="json"):
        """Get data for export"""
        if not self.chat_history:
            return {"error": "No chat history available"}
        
        history = self.chat_history.get_all_history()
        
        if format == "json":
            return history
        elif format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if history:
                writer = csv.DictWriter(output, fieldnames=history[0].keys())
                writer.writeheader()
                writer.writerows(history)
            
            return output.getvalue()
        
        return {"error": "Unsupported format"}
