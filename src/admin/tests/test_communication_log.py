import os
import json
import unittest
from datetime import datetime
from ..communication_log import CommunicationLog, LOG_FILE

class TestCommunicationLog(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.test_log_file = "test_communication_logs.json"
        # Ensure a clean state for each test
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        self.comm_log = CommunicationLog(log_file=self.test_log_file)

    def tearDown(self):
        """Tear down after test methods."""
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_add_log_creates_file(self):
        """Test that adding a log creates the log file if it doesn't exist."""
        self.comm_log.add_log("Hello", "test_model", "Hi there")
        self.assertTrue(os.path.exists(self.test_log_file))

    def test_add_log_adds_entry(self):
        """Test that a log entry is correctly added."""
        user_input = "Test input"
        model = "test_model_v2"
        response = "Test response"
        self.comm_log.add_log(user_input, model, response)
        logs = self.comm_log.get_logs()
        self.assertEqual(len(logs), 1)
        log_entry = logs[0]
        self.assertEqual(log_entry["user_input"], user_input)
        self.assertEqual(log_entry["model"], model)
        self.assertEqual(log_entry["response"], response)
        self.assertTrue("timestamp" in log_entry)

    def test_get_logs_empty(self):
        """Test retrieving logs when the log file is empty or new."""
        logs = self.comm_log.get_logs()
        self.assertEqual(len(logs), 0)

    def test_get_logs_multiple_entries(self):
        """Test retrieving multiple log entries."""
        self.comm_log.add_log("Input 1", "model_a", "Response 1")
        self.comm_log.add_log("Input 2", "model_b", "Response 2")
        logs = self.comm_log.get_logs()
        self.assertEqual(len(logs), 2)

    def test_get_logs_limit(self):
        """Test the limit parameter for retrieving logs."""
        for i in range(5):
            self.comm_log.add_log(f"Input {i}", f"model_{i}", f"Response {i}")

        limited_logs = self.comm_log.get_logs(limit=3)
        self.assertEqual(len(limited_logs), 3)
        # Check if it returns the last N entries
        self.assertEqual(limited_logs[0]["user_input"], "Input 2")
        self.assertEqual(limited_logs[-1]["user_input"], "Input 4")

    def test_log_file_structure(self):
        """Test the structure of the log file (JSON array of objects)."""
        self.comm_log.add_log("Structure test", "struct_model", "Data")
        with open(self.test_log_file, 'r') as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0], dict)
        self.assertIn("timestamp", data[0])
        self.assertIn("user_input", data[0])
        self.assertIn("model", data[0])
        self.assertIn("response", data[0])

    def test_init_uses_default_log_file(self):
        """Test that CommunicationLog uses LOG_FILE by default."""
        # Temporarily move the default log file if it exists
        default_log_exists = os.path.exists(LOG_FILE)
        if default_log_exists:
            os.rename(LOG_FILE, LOG_FILE + ".backup")

        try:
            comm_log_default = CommunicationLog()
            self.assertEqual(comm_log_default.log_file, LOG_FILE)
            # Check if it creates the default log file
            comm_log_default.add_log("Default file test", "default", "Test")
            self.assertTrue(os.path.exists(LOG_FILE))
        finally:
            # Clean up: remove the created default log file
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            # Restore the backup if it existed
            if default_log_exists:
                os.rename(LOG_FILE + ".backup", LOG_FILE)


if __name__ == '__main__':
    unittest.main()
