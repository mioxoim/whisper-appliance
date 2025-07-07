"""
WhisperS2T Appliance - Modular Components
Enhanced modular architecture preserving all original features

🎯 MODULAR ARCHITECTURE:
- Core modules: live_speech, upload_handler, admin_panel, api_docs
- Update system: Modular update architecture with enterprise features
- Maintenance system: Enterprise maintenance management
- Clean separation of concerns with backward compatibility

Version: 0.10.0
"""

__version__ = "0.10.0"
__author__ = "WhisperS2T Team"

# Core module imports
from .admin_panel import AdminPanel
from .api_docs import APIDocs
from .chat_history import ChatHistoryManager
from .live_speech import LiveSpeechHandler
from .model_manager import ModelManager
from .upload_handler import UploadHandler

# Update System
try:
    from .update import UpdateManager, create_update_endpoints

    UPDATE_MANAGER_AVAILABLE = True
except ImportError:
    UpdateManager = None
    create_update_endpoints = None
    UPDATE_MANAGER_AVAILABLE = False

# Maintenance System
try:
    from .maintenance import EnterpriseMaintenanceManager, MaintenanceManager

    MAINTENANCE_MANAGER_AVAILABLE = True
except ImportError:
    MaintenanceManager = None
    EnterpriseMaintenanceManager = None
    MAINTENANCE_MANAGER_AVAILABLE = False

# Enterprise Update System Integration (REMOVED - now using single update system)

# Legacy compatibility imports (DEPRECATED - use new modular imports)
try:
    # Legacy UpdateConfig/UpdateManager (if still exists)
    from .update_config import UpdateConfig

    LEGACY_UPDATE_CONFIG_AVAILABLE = True
except ImportError:
    UpdateConfig = None
    LEGACY_UPDATE_CONFIG_AVAILABLE = False

__all__ = [
    # Core modules
    "LiveSpeechHandler",
    "UploadHandler",
    "AdminPanel",
    "APIDocs",
    "ModelManager",
    "ChatHistoryManager",
    # Update System
    "UpdateManager",
    "create_update_endpoints",
    "UPDATE_MANAGER_AVAILABLE",
    # Maintenance System
    "MaintenanceManager",
    "EnterpriseMaintenanceManager",  # Backward compatibility alias
    "MAINTENANCE_MANAGER_AVAILABLE",
    # Legacy compatibility (DEPRECATED)
    "UpdateConfig",
    "LEGACY_UPDATE_CONFIG_AVAILABLE",
    # Legacy aliases for backward compatibility
    "ENTERPRISE_MAINTENANCE_AVAILABLE",  # Maps to MAINTENANCE_MANAGER_AVAILABLE
]

# Backward compatibility aliases
ENTERPRISE_MAINTENANCE_AVAILABLE = MAINTENANCE_MANAGER_AVAILABLE
