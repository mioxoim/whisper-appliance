"""
Configuration Manager
Centralized configuration management for WhisperS2T Appliance
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration management"""

    def __init__(self, config_root: str = None):
        """Initialize configuration manager

        Args:
            config_root: Root directory for configuration files
        """
        if config_root is None:
            # Auto-detect config directory
            current_dir = Path(__file__).parent
            self.config_root = current_dir / "settings"
        else:
            self.config_root = Path(config_root)

        self.config_root.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration from JSON file

        Args:
            config_name: Name of configuration (without .json extension)

        Returns:
            Configuration dictionary
        """
        config_path = self.config_root / f"{config_name}.json"

        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading config {config_name}: {e}")
            return {}

    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to JSON file

        Args:
            config_name: Name of configuration (without .json extension)
            config_data: Configuration data to save

        Returns:
            True if successful, False otherwise
        """
        config_path = self.config_root / f"{config_name}.json"

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved: {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config {config_name}: {e}")
            return False

    def get_maintenance_config(self) -> Dict[str, Any]:
        """Get maintenance mode configuration"""
        return self.load_config("maintenance")

    def get_update_maintenance_config(self) -> Dict[str, Any]:
        """Get update maintenance mode configuration"""
        return self.load_config("update_maintenance")

    def update_maintenance_config(self, config_data: Dict[str, Any]) -> bool:
        """Update maintenance mode configuration"""
        return self.save_config("maintenance", config_data)

    def update_update_maintenance_config(self, config_data: Dict[str, Any]) -> bool:
        """Update update maintenance mode configuration"""
        return self.save_config("update_maintenance", config_data)


# Legacy compatibility functions
def load_legacy_config(legacy_path: str) -> Dict[str, Any]:
    """Load configuration from legacy path for backward compatibility

    Args:
        legacy_path: Path to legacy configuration file

    Returns:
        Configuration dictionary
    """
    try:
        if os.path.exists(legacy_path):
            with open(legacy_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading legacy config {legacy_path}: {e}")

    return {}


# Global config manager instance
config_manager = ConfigManager()
