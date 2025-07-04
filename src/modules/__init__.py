"""
WhisperS2T Appliance - Modular Components
Enhanced modular architecture preserving all original features
"""

__version__ = "0.10.0"
__author__ = "WhisperS2T Team"

from .admin_panel import AdminPanel
from .api_docs import APIDocs
from .chat_history import ChatHistoryManager

# Module exports
from .live_speech import LiveSpeechHandler
from .model_manager import ModelManager
from .upload_handler import UploadHandler

# Optional UpdateManager for backward compatibility
try:
    from .update_config import UpdateConfig
    from .update_manager import UpdateManager

    UPDATE_MANAGER_AVAILABLE = True
except ImportError:
    UpdateConfig = None
    UpdateManager = None
    UPDATE_MANAGER_AVAILABLE = False

__all__ = [
    "LiveSpeechHandler",
    "UploadHandler",
    "AdminPanel",
    "APIDocs",
    "ModelManager",
    "ChatHistoryManager",
    "UpdateConfig",
    "UpdateManager",
    "UPDATE_MANAGER_AVAILABLE",
]
