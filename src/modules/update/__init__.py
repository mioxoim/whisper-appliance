"""
WhisperS2T Update Package
Professional modular update system with clean architecture

Components:
- UpdateManager: Main orchestrator for all update operations
- UpdateChecker: Version checking and update detection
- UpdateApplier: Safe update application with rollback
- UpdateBackupManager: Backup creation and management
- UpdateCompatibilityChecker: Module compatibility validation
- DeploymentDetector: Environment detection and configuration

Enterprise Features:
- Enterprise package: Enhanced deployment detection and Flask integration
- Permission-safe operations for LXC environments
- Professional audit logging and monitoring
"""

from .applier import UpdateApplier
from .backup import UpdateBackupManager
from .checker import UpdateChecker
from .compatibility import UpdateCompatibilityChecker
from .deployment import DeploymentDetector, DeploymentType
from .manager import UpdateManager

__version__ = "0.8.0"


# Factory function for backward compatibility
def create_update_manager(app_root: str = None, maintenance_manager=None) -> UpdateManager:
    """
    Create UpdateManager instance (factory function for backward compatibility)

    Args:
        app_root: Application root directory (auto-detected if None)
        maintenance_manager: Maintenance mode manager instance

    Returns:
        UpdateManager: Configured update manager
    """
    return UpdateManager(app_root, maintenance_manager)


__all__ = [
    # Main classes
    "UpdateManager",
    "UpdateChecker",
    "UpdateApplier",
    "UpdateBackupManager",
    "UpdateCompatibilityChecker",
    "DeploymentDetector",
    "DeploymentType",
    # Factory function
    "create_update_manager",
    # Enterprise package (available as submodule)
    # from modules.update.enterprise import integrate_with_flask_app
]
