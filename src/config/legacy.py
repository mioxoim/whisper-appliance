"""
Legacy Configuration Bridge
Provides backward compatibility for existing configuration paths
"""

import logging
import os
from typing import Any, Dict

from .manager import config_manager, load_legacy_config

logger = logging.getLogger(__name__)


def get_maintenance_config_with_fallback() -> Dict[str, Any]:
    """Get maintenance config with legacy fallback

    Returns:
        Maintenance configuration, checking new location first, then legacy
    """
    # Try new config location first
    config = config_manager.get_maintenance_config()

    if not config:
        # Fallback to legacy location
        legacy_path = os.path.join(os.path.dirname(__file__), "..", "maintenance_config.json")
        config = load_legacy_config(legacy_path)
        logger.info("Using legacy maintenance config")

    return config


def get_enterprise_maintenance_config_with_fallback() -> Dict[str, Any]:
    """Get enterprise maintenance config with legacy fallback

    Returns:
        Update maintenance configuration, checking new location first, then legacy
    """
    # Try new config location first
    config = config_manager.get_update_maintenance_config()

    if not config:
        # Fallback to legacy location
        legacy_path = os.path.join(os.path.dirname(__file__), "..", "enterprise_maintenance_config.json")
        config = load_legacy_config(legacy_path)
        logger.info("Using legacy enterprise maintenance config")

    return config


def save_maintenance_config(config_data: Dict[str, Any]) -> bool:
    """Save maintenance config to new location

    Args:
        config_data: Configuration data to save

    Returns:
        True if successful
    """
    return config_manager.update_maintenance_config(config_data)


def save_enterprise_maintenance_config(config_data: Dict[str, Any]) -> bool:
    """Save update maintenance config to new location

    Args:
        config_data: Configuration data to save

    Returns:
        True if successful
    """
    return config_manager.update_update_maintenance_config(config_data)
