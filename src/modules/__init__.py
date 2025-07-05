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

# Enterprise Update System
try:
    from .maintenance_mode import MaintenanceModeManager, MaintenanceModeMiddleware
    from .shopware_update_manager import ShopwareStyleUpdateManager, UpdateBackupManager, UpdateCompatibilityChecker

    ENTERPRISE_UPDATE_AVAILABLE = True
except ImportError:
    MaintenanceModeManager = None
    MaintenanceModeMiddleware = None
    ShopwareStyleUpdateManager = None
    UpdateCompatibilityChecker = None
    UpdateBackupManager = None
    ENTERPRISE_UPDATE_AVAILABLE = False

__all__ = [
    "LiveSpeechHandler",
    "UploadHandler",
    "AdminPanel",
    "APIDocs",
    "ModelManager",
    "ChatHistoryManager",
    # Enterprise Update System
    "MaintenanceModeManager",
    "MaintenanceModeMiddleware",
    "ShopwareStyleUpdateManager",
    "UpdateCompatibilityChecker",
    "UpdateBackupManager",
    "ENTERPRISE_UPDATE_AVAILABLE",
]
