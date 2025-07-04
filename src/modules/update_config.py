"""
Update Configuration Manager
Handles configuration for different deployment types (git-based vs file-download-based)
Provides smart update system for all deployment scenarios
"""

import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class UpdateConfig:
    """Manages update configuration for different deployment types"""

    def __init__(self, config_path: str = None):
        # Auto-detect config location
        if config_path is None:
            possible_paths = [
                "/opt/whisper-appliance/update-config.json",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "update-config.json"),
                os.path.join(os.getcwd(), "update-config.json"),
                "/tmp/whisper-update-config.json",
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            else:
                # Create default config
                config_path = possible_paths[0] if os.path.exists("/opt/whisper-appliance") else possible_paths[1]

        self.config_path = config_path
        self.config = self._load_or_create_config()

    def _load_or_create_config(self) -> Dict:
        """Load existing config or create default configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                logger.info(f"Loaded update config from: {self.config_path}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}")

        # Create default configuration
        default_config = self._create_default_config()
        self._save_config(default_config)
        return default_config

    def _create_default_config(self) -> Dict:
        """Create default configuration based on deployment detection"""
        deployment_type = self._detect_deployment_type()

        config = {
            "repository": {
                "url": "https://github.com/GaboCapo/whisper-appliance",
                "raw_url": "https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main",
                "api_url": "https://api.github.com/repos/GaboCapo/whisper-appliance",
                "branch": "main",
            },
            "deployment": {
                "type": deployment_type,
                "target_dir": self._detect_target_dir(),
                "service_name": "whisper-appliance.service",
                "service_enabled": True,
            },
            "update_method": "git_pull" if deployment_type == "git_based" else "file_download",
            "version_tracking": {"current_version": self._get_current_version(), "last_update": None, "last_check": None},
            "file_download_config": {
                "files_to_update": [
                    "src/main.py",
                    "src/modules/__init__.py",
                    "src/modules/live_speech.py",
                    "src/modules/upload_handler.py",
                    "src/modules/admin_panel.py",
                    "src/modules/api_docs.py",
                    "src/modules/chat_history.py",
                    "src/modules/model_manager.py",
                    "src/modules/update_manager.py",
                    "src/modules/update_config.py",
                    "src/templates/main_interface.html",
                    "src/whisper-service/audio_input_manager.py",
                    "requirements.txt",
                ],
                "backup_enabled": True,
                "backup_dir": "/opt/whisper-appliance/backups" if os.path.exists("/opt/whisper-appliance") else "./backups",
            },
            "auto_update": {"enabled": False, "schedule": "daily", "time": "02:00"},
        }

        logger.info(f"Created default config for deployment type: {deployment_type}")
        return config

    def _detect_deployment_type(self) -> str:
        """Detect deployment type based on environment"""
        # Check for git repository
        possible_git_dirs = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".git"),
            "/opt/whisper-appliance/.git",
            os.path.join(os.getcwd(), ".git"),
        ]

        for git_dir in possible_git_dirs:
            if os.path.exists(git_dir):
                logger.info(f"Found git repository at: {git_dir}")
                return "git_based"

        # Check for file-based deployment (Proxmox/Container)
        if os.path.exists("/opt/whisper-appliance/src/main.py"):
            logger.info("Detected file-based deployment (Proxmox/Container)")
            return "file_download_based"

        # Check for development environment
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if os.path.exists(os.path.join(current_dir, "src", "main.py")):
            logger.info("Detected development environment")
            return "development"

        logger.warning("Could not determine deployment type, defaulting to file_download_based")
        return "file_download_based"

    def _detect_target_dir(self) -> str:
        """Detect target directory for updates"""
        if os.path.exists("/opt/whisper-appliance"):
            return "/opt/whisper-appliance"

        # Try to find from current file location
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if os.path.exists(os.path.join(current_dir, "src", "main.py")):
            return current_dir

        return os.getcwd()

    def _get_current_version(self) -> str:
        """Get current version using various methods"""
        try:
            # Try git-based version first
            if self._detect_deployment_type() == "git_based":
                result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()

            # Try to read version from a version file if it exists
            version_files = [
                os.path.join(self._detect_target_dir(), "VERSION"),
                os.path.join(self._detect_target_dir(), "src", "VERSION"),
            ]

            for version_file in version_files:
                if os.path.exists(version_file):
                    with open(version_file, "r") as f:
                        return f.read().strip()

            # Fallback to timestamp-based version
            return f"file-{datetime.now().strftime('%Y%m%d')}"

        except Exception as e:
            logger.warning(f"Could not determine current version: {e}")
            return "unknown"

    def _save_config(self, config: Dict) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Saved config to: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get_deployment_type(self) -> str:
        """Get current deployment type"""
        return self.config.get("deployment", {}).get("type", "unknown")

    def get_update_method(self) -> str:
        """Get current update method"""
        return self.config.get("update_method", "file_download")

    def get_repository_info(self) -> Dict:
        """Get repository information"""
        return self.config.get("repository", {})

    def get_target_dir(self) -> str:
        """Get target directory for updates"""
        return self.config.get("deployment", {}).get("target_dir", "/opt/whisper-appliance")

    def get_files_to_update(self) -> list:
        """Get list of files that should be updated"""
        return self.config.get("file_download_config", {}).get("files_to_update", [])

    def update_version(self, new_version: str):
        """Update current version in config"""
        self.config.setdefault("version_tracking", {})["current_version"] = new_version
        self.config["version_tracking"]["last_update"] = datetime.now().isoformat()
        self._save_config(self.config)

    def update_last_check(self):
        """Update last check timestamp"""
        self.config.setdefault("version_tracking", {})["last_check"] = datetime.now().isoformat()
        self._save_config(self.config)

    def get_config(self) -> Dict:
        """Get full configuration"""
        return self.config.copy()

    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_or_create_config()
