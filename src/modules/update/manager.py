"""
WhisperS2T Update Manager
Professional update management system with clean architecture
"""

import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Optional requests import for fallback
try:
    import requests
except ImportError:
    requests = None

from .applier import UpdateApplier
from .backup import UpdateBackupManager
from .checker import UpdateChecker
from .compatibility import UpdateCompatibilityChecker
from .deployment import DeploymentDetector

logger = logging.getLogger(__name__)


class UpdateManager:
    """
    Professional Update Manager for WhisperS2T

    Orchestrates all update-related functionality through modular components:
    - UpdateChecker: Version checking and update detection
    - UpdateCompatibilityChecker: Module compatibility validation
    - UpdateBackupManager: Backup creation and management
    - UpdateApplier: Safe update application and rollback
    - DeploymentDetector: Environment detection and configuration
    """

    def __init__(self, app_root: str = None, maintenance_manager=None):
        # Auto-detect app root if not provided
        if app_root is None:
            detector = DeploymentDetector()
            app_root = detector.find_app_root()

        self.app_root = app_root
        self.maintenance_manager = maintenance_manager

        # Initialize modular components
        self.deployment_detector = DeploymentDetector()
        self.backup_manager = UpdateBackupManager(app_root)
        self.compatibility_checker = UpdateCompatibilityChecker(app_root)
        self.checker = UpdateChecker(app_root)
        self.applier = UpdateApplier(app_root, self.backup_manager, maintenance_manager)

        # Update configuration
        self.config = {
            "repo_url": "https://github.com/GaboCapo/whisper-appliance.git",
            "auto_backup": True,
            "maintenance_mode": True,
            "check_compatibility": True,
            "max_retries": 3,
            "timeout": 300,  # 5 minutes
        }

        # Get deployment info
        self.deployment_info = self.deployment_detector.get_deployment_info()

        logger.info(f"UpdateManager initialized for {self.app_root}")
        logger.info(f"Deployment: {self.deployment_info['deployment_type']}")

    # Delegate methods to appropriate components

    def get_current_version(self) -> str:
        """Get current application version"""
        return self.checker.get_current_version()

    def check_for_updates(self) -> Dict:
        """Check if updates are available"""
        return self.checker.check_for_updates()

    def get_update_status(self) -> Dict:
        """Get comprehensive update status"""
        # Combine status from checker and applier
        checker_status = self.checker.get_update_status()
        applier_status = self.applier.get_update_state()

        return {
            **checker_status,
            "updating": applier_status["updating"],
            "backup_created": applier_status["backup_created"],
            "rollback_available": applier_status["rollback_available"],
            "deployment_info": self.deployment_info,
        }

    def start_update(self, target_version: str = "latest") -> Tuple[bool, str]:
        """
        Start comprehensive update process

        Args:
            target_version: Version to update to

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Check compatibility if enabled
            compatibility_status = None
            if self.config["check_compatibility"]:
                compatibility_status = self.compatibility_checker.check_module_compatibility(target_version)

                if compatibility_status.get("incompatible"):
                    return False, f"Incompatible modules found: {compatibility_status['incompatible']}"

            # Apply update using applier
            return self.applier.apply_update(target_version, compatibility_status)

        except Exception as e:
            logger.error(f"Update process failed: {e}")
            return False, f"Update failed: {str(e)}"

    def rollback_to_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """Rollback to specific backup"""
        return self.applier.rollback_to_backup(backup_name)

    def list_backups(self) -> List[Dict]:
        """List available backups"""
        return self.backup_manager.list_backups()

    def get_deployment_info(self) -> Dict:
        """Get deployment environment information"""
        return self.deployment_info

    def get_update_status(self) -> Dict:
        """
        Get comprehensive update status information

        Returns:
            Dict: Current update status including versions, backup info, and state
        """
        try:
            # Get current version info
            current_version = "unknown"
            try:
                # Try to read version from various sources
                version_sources = [
                    os.path.join(self.app_root, "VERSION"),
                    os.path.join(self.app_root, "src", "__init__.py"),
                    os.path.join(self.app_root, "setup.py"),
                ]

                for source in version_sources:
                    if os.path.exists(source):
                        with open(source, "r") as f:
                            content = f.read()
                            # Look for version patterns
                            import re

                            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
                            if version_match:
                                current_version = version_match.group(1)
                                break
                            # Alternative pattern
                            version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                            if version_match:
                                current_version = version_match.group(1)
                                break
            except:
                pass

            # Get latest version from checker
            latest_version = "unknown"
            update_available = False
            try:
                latest_release = self.checker.get_release_info()
                if latest_release:
                    latest_version = latest_release.get("version", "unknown")
                    update_available = latest_version != current_version and latest_version != "unknown"
            except:
                pass

            # Get applier state
            applier_state = self.applier.get_update_state()

            # Get backup info
            backup_info = []
            try:
                backup_info = self.backup_manager.list_backups()
            except:
                pass

            return {
                "current_version": current_version,
                "latest_version": latest_version,
                "update_available": update_available,
                "updating": applier_state.get("updating", False),
                "backup_created": applier_state.get("backup_created", False),
                "backup_path": applier_state.get("backup_path"),
                "rollback_available": applier_state.get("rollback_available", False),
                "error": applier_state.get("error"),
                "last_update_log": applier_state.get("update_log", [])[-10:] if applier_state.get("update_log") else [],
                "available_backups": len(backup_info),
                "deployment_info": self.deployment_info,
                "maintenance_active": getattr(self, "maintenance_manager", None)
                and hasattr(self.maintenance_manager, "is_maintenance_active")
                and self.maintenance_manager.is_maintenance_active(),
            }

        except Exception as e:
            logger.error(f"Failed to get update status: {e}")
            return {
                "current_version": "unknown",
                "latest_version": "unknown",
                "update_available": False,
                "updating": False,
                "error": f"Status check failed: {str(e)}",
                "deployment_info": self.deployment_info,
            }

    def get_update_log(self) -> List[str]:
        """Get update process log"""
        return self.applier.get_update_log()

    def check_module_compatibility(self, target_version: str) -> Dict:
        """Check module compatibility for target version"""
        return self.compatibility_checker.check_module_compatibility(target_version)

    def create_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """Create manual backup"""
        return self.backup_manager.create_backup(backup_name)

    def cleanup_temp_files(self):
        """Clean up temporary update files"""
        self.applier._cleanup_temp_files()

    def get_release_info(self, version: str = None) -> Optional[Dict]:
        """Get release information for specific version"""
        return self.checker.get_release_info(version)
