import pytest
import os
import sys
from flask import Flask

import datetime # Added import for datetime
# Add src directory to Python path to allow for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from admin import init_admin_panel, CommunicationLog, create_admin_blueprint # Import create_admin_blueprint

# Use a different log file for testing to avoid conflicts with development logs
TEST_LOG_FILE = "test_integration_communication_logs.json"

@pytest.fixture(scope='session', autouse=True)
def cleanup_test_log_file():
    """Ensure the test log file is removed before and after test session."""
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)
    yield
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key' # Required for session or other security features
    app.config['SERVER_NAME'] = 'localhost.test' # Added SERVER_NAME for url_for

    # Initialize a communication log with a dedicated test file
    # This instance is primarily for setup if needed by the admin panel initialization
    # The actual CommunicationLog used by the admin panel will be instantiated within init_admin_panel
    # but we ensure it uses the test log file by setting it up here or by modifying how init_admin_panel works.

    # For simplicity in this example, we'll assume init_admin_panel can be
    # adapted or already allows for specifying a log file, or we'll mock.
    # For now, we'll create a dummy system_stats and model_manager

    mock_model_manager = None # Replace with a mock if needed
    mock_system_stats = {
            "uptime_start": datetime.datetime.now() - datetime.timedelta(hours=1), # Changed to datetime object
            "total_transcriptions": 0,
            "transcriptions_by_source": {"live": 0, "upload": 0, "api": 0}
    }

    # Crucially, ensure the CommunicationLog within the admin panel uses the test log file.
    # One way is to make CommunicationLog a singleton or configurable.
    # For this example, let's assume CommunicationLog can be instantiated with a specific file.
    # We will ensure the admin panel's CommunicationLog instance uses TEST_LOG_FILE.
    # This might require a slight refactor of AdminPanel or CommunicationLog instantiation,
    # or more advanced patching/mocking in tests.

    # A simple approach: The CommunicationLog class itself could check an env var for the log file path during tests.
    # Or, the AdminPanel could accept a communication_log_instance.
    # For now, let's ensure the default log file for CommunicationLog is patched for tests.

    original_log_file = CommunicationLog.LOG_FILE
    CommunicationLog.LOG_FILE = TEST_LOG_FILE

    # Create a new blueprint instance for each app fixture
    admin_bp_instance = create_admin_blueprint()
    init_admin_panel(app, admin_bp_instance, model_manager=mock_model_manager, system_stats=mock_system_stats)

    # Reset to original after app context
    yield app

    CommunicationLog.LOG_FILE = original_log_file


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def communication_log_instance():
    """Provides a CommunicationLog instance using the test log file."""
    # This instance is for directly manipulating logs in tests
    log_instance = CommunicationLog(log_file=TEST_LOG_FILE)
    # Clear logs before each test using this fixture
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)
    # Re-initialize to create an empty log file
    log_instance = CommunicationLog(log_file=TEST_LOG_FILE)
    return log_instance
