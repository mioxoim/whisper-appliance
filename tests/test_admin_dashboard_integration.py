import pytest
from flask import url_for
import datetime

# Import the CommunicationLog that will be used by the app context
# This ensures we are using the same class that the app uses.
from admin import CommunicationLog


def test_dashboard_shows_no_logs_message(client, app): # Added app fixture
    """Test that the dashboard shows a 'no logs' message when no logs exist."""
    with app.app_context(): # Added app_context
        response = client.get(url_for('admin.admin_dashboard'))
    assert response.status_code == 200
    assert b"No communication logs available." in response.data
    assert b"Timestamp" not in response.data # Table headers shouldn't be there

def test_dashboard_displays_communication_logs(client, app, communication_log_instance):
    """Test that communication logs are displayed on the dashboard."""
    # Add some logs using the test-specific instance
    timestamp1_dt = datetime.datetime.now() - datetime.timedelta(minutes=10)
    timestamp1_iso = timestamp1_dt.isoformat()

    communication_log_instance.add_log("Hello bot", "test_model_1", "Hi human")
    # Manually create the second log with a specific timestamp for ordering check
    logs = communication_log_instance._read_logs()
    logs.append({
        "timestamp": timestamp1_iso, # Older timestamp
        "user_input": "Older input",
        "model": "test_model_0",
        "response": "Older response"
    })
    communication_log_instance._write_logs(logs)

    communication_log_instance.add_log("Another question", "test_model_2", "Another answer")

    with app.app_context(): # Added app_context
        response = client.get(url_for('admin.admin_dashboard'))
    assert response.status_code == 200

    # Check for table headers
    assert b"Timestamp" in response.data
    assert b"User Input" in response.data
    assert b"Model Used" in response.data
    assert b"Response" in response.data

    # Check for log content (newest first if not sorted, or check for presence)
    # The default get_logs fetches all and they are appended, so last one is newest
    assert b"Hello bot" in response.data
    assert b"test_model_1" in response.data
    assert b"Hi human" in response.data

    assert b"Older input" in response.data
    assert b"test_model_0" in response.data
    assert b"Older response" in response.data
    # Check the specific timestamp format if important, or just its presence
    assert bytes(timestamp1_iso, 'utf-8') in response.data

    assert b"Another question" in response.data
    assert b"test_model_2" in response.data
    assert b"Another answer" in response.data

    assert b"No communication logs available." not in response.data

def test_dashboard_log_order(client, app, communication_log_instance):
    """Test that logs are displayed in the order they were added (newest last by default)."""

    # Add logs in a specific order
    entry1_time = (datetime.datetime.now() - datetime.timedelta(minutes=2)).isoformat()
    entry2_time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).isoformat()
    entry3_time = datetime.datetime.now().isoformat()

    # Manually add to control timestamps precisely for order assertion
    log_data = [
        {"timestamp": entry1_time, "user_input": "First entry", "model": "m1", "response": "r1"},
        {"timestamp": entry2_time, "user_input": "Second entry", "model": "m2", "response": "r2"},
        {"timestamp": entry3_time, "user_input": "Third entry", "model": "m3", "response": "r3"},
    ]
    communication_log_instance._write_logs(log_data)

    with app.app_context(): # Added app_context
        response = client.get(url_for('admin.admin_dashboard'))
    assert response.status_code == 200

    response_data_str = response.data.decode('utf-8')

    # Find positions of entries. Assuming simple string presence is enough.
    # The default rendering in the template iterates logs as they are in the list.
    # The CommunicationLog.get_logs() returns them in appended order.
    pos1 = response_data_str.find("First entry")
    pos2 = response_data_str.find("Second entry")
    pos3 = response_data_str.find("Third entry")

    assert pos1 != -1 and pos2 != -1 and pos3 != -1, "Not all log entries found in response"
    assert pos1 < pos2 < pos3, "Logs are not displayed in the correct order (oldest first)"

def test_dashboard_handles_empty_log_file_gracefully(client, app, communication_log_instance):
    """Test that if the log file is empty (but exists), it shows 'no logs'."""
    # communication_log_instance fixture already ensures an empty log file is created
    # if it doesn't exist, or clears it.

    # Ensure it's truly empty by writing an empty list
    communication_log_instance._write_logs([])

    with app.app_context(): # Added app_context
        response = client.get(url_for('admin.admin_dashboard'))
    assert response.status_code == 200
    assert b"No communication logs available." in response.data
    assert b"Timestamp" not in response.data # Table headers shouldn't be there if no logs

def test_dashboard_handles_malformed_log_file(client, app, communication_log_instance):
    """Test how the dashboard handles a malformed log file."""
    # Write invalid JSON to the log file
    with open(communication_log_instance.log_file, 'w') as f:
        f.write("this is not valid json")

    with app.app_context(): # Added app_context
        response = client.get(url_for('admin.admin_dashboard'))
    assert response.status_code == 200
    # The CommunicationLog._read_logs() should catch JSONDecodeError and return []
    # So, the dashboard should behave as if there are no logs.
    assert b"No communication logs available." in response.data
    assert b"Timestamp" not in response.data

# It might be useful to also test with a very large number of logs if pagination
# were implemented, or to ensure performance doesn't degrade significantly.
# For now, this covers basic display and data handling.
