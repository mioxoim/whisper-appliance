"""
Configuration Package
Settings and Configuration Management
"""

from .legacy import (
    get_enterprise_maintenance_config_with_fallback,
    get_maintenance_config_with_fallback,
    save_enterprise_maintenance_config,
    save_maintenance_config,
)
from .manager import ConfigManager, config_manager

__version__ = "0.8.0"
__all__ = [
    "ConfigManager",
    "config_manager",
    "get_maintenance_config_with_fallback",
    "get_enterprise_maintenance_config_with_fallback",
    "save_maintenance_config",
    "save_enterprise_maintenance_config",
]
