"""
Communication Log Module
Handles storage and retrieval of communication logs.
"""

import datetime
import json
import os

class CommunicationLog:
    LOG_FILE = "communication_logs.json" # Class attribute for default log file

    def __init__(self, log_file=None):
        # Use the class attribute LOG_FILE if no specific log_file is provided
        self.log_file = log_file if log_file is not None else self.LOG_FILE

        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)

    def add_log(self, user_input, model, response):
        """Adds a new log entry."""
        logs = self._read_logs()
        new_log = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": user_input,
            "model": model,
            "response": response
        }
        logs.append(new_log)
        self._write_logs(logs)

    def get_logs(self, limit=None):
        """Retrieves logs, optionally limited to the most recent entries."""
        logs = self._read_logs()
        if limit:
            return logs[-limit:]
        return logs

    def _read_logs(self):
        """Reads logs from the log file."""
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return []

    def _write_logs(self, logs):
        """Writes logs to the log file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=4)
        except IOError:
            # Handle error (e.g., log to system logger)
            pass
