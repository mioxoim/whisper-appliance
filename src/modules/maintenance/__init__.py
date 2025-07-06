"""
Maintenance Module
Enterprise-level maintenance mode management for WhisperS2T Appliance

Components:
- MaintenanceManager: Core maintenance mode functionality
- EnterpriseMaintenanceManager: Backward compatibility alias
"""

from .manager import EnterpriseMaintenanceManager, MaintenanceManager

__version__ = "0.8.0"

__all__ = [
    "MaintenanceManager",
    "EnterpriseMaintenanceManager",  # Backward compatibility
]
