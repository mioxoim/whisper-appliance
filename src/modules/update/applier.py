"""
Update Applier
Professional update application with permission-safe operations
"""

import json
import logging
import os
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class UpdateApplier:
    """
    Professional update application system with permission-safe operations
    """

    def __init__(self, app_root: str, backup_manager=None, maintenance_manager=None):
        self.app_root = app_root
        self.backup_manager = backup_manager
        self.maintenance_manager = maintenance_manager

        # Update state
        self.update_state = {
            "updating": False,
            "backup_created": False,
            "backup_path": None,
            "temp_dir": None,
            "update_source_dir": None,
            "update_log": [],
            "error": None,
            "rollback_available": False,
        }

    def apply_update(self, target_version: str = "latest", compatibility_status: Dict = None) -> Tuple[bool, str]:
        """
        Apply update with comprehensive safety measures

        Args:
            target_version: Version to update to
            compatibility_status: Pre-checked compatibility status

        Returns:
            Tuple[bool, str]: (success, message)
        """
        if self.update_state["updating"]:
            return False, "Update already in progress"

        self.update_state["updating"] = True
        self.update_state["error"] = None
        self.update_state["update_log"] = []

        try:
            self._log_update("🚀 Starting update process...")

            # Enable maintenance mode if available
            if self.maintenance_manager:
                self._log_update("🔧 Enabling maintenance mode...")
                try:
                    self.maintenance_manager.enable_maintenance()
                    self.update_state["maintenance_active"] = True
                except Exception as e:
                    self._log_update(f"⚠️ Maintenance mode failed: {e}")

            # Create backup if backup manager available
            if self.backup_manager:
                self._log_update("💾 Creating backup...")
                backup_success, backup_path = self.backup_manager.create_backup()
                if not backup_success:
                    raise Exception(f"Backup creation failed: {backup_path}")

                self.update_state["backup_created"] = True
                self.update_state["backup_path"] = backup_path
                self.update_state["rollback_available"] = True
                self._log_update(f"✅ Backup created: {backup_path}")

            # Download update
            self._log_update("⬇️ Downloading update...")
            if not self._download_update(target_version):
                raise Exception("Download failed")

            # Apply update using permission-safe strategy
            self._log_update("🔄 Applying permission-safe update...")
            if not self._apply_permission_safe_update():
                raise Exception("Update application failed")

            # Restart services if needed
            self._log_update("🔄 Restarting services...")
            if not self._restart_services():
                self._log_update("⚠️ Service restart failed - manual restart may be required")

            # Cleanup
            self._log_update("🧹 Cleaning up temporary files...")
            self._cleanup_temp_files()

            # Disable maintenance mode
            if self.maintenance_manager and self.update_state.get("maintenance_active"):
                self._log_update("✅ Disabling maintenance mode...")
                try:
                    self.maintenance_manager.disable_maintenance()
                except Exception as e:
                    self._log_update(f"⚠️ Failed to disable maintenance mode: {e}")

            self._log_update("✅ Update completed successfully!")
            return True, "Update completed successfully"

        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            logger.error(error_msg)
            self.update_state["error"] = error_msg
            self._log_update(f"❌ {error_msg}")

            # Attempt rollback if backup available
            if self.update_state["rollback_available"]:
                self._log_update("🔄 Attempting automatic rollback...")
                rollback_success, rollback_msg = self._attempt_rollback()
                if rollback_success:
                    self._log_update(f"✅ Rollback successful: {rollback_msg}")
                else:
                    self._log_update(f"❌ Rollback failed: {rollback_msg}")

            return False, error_msg

        finally:
            self.update_state["updating"] = False

            # Ensure cleanup
            self._cleanup_temp_files()

            # Ensure maintenance mode is disabled
            if self.maintenance_manager and self.update_state.get("maintenance_active"):
                try:
                    self.maintenance_manager.disable_maintenance()
                except:
                    pass

    def _replace_file_safely(self, src_path: str, dst_path: str) -> bool:
        """Replace a single file safely"""
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            # If destination exists, create backup
            if os.path.exists(dst_path):
                backup_path = f"{dst_path}.backup_{int(time.time())}"
                shutil.copy2(dst_path, backup_path)

            # Copy new file
            shutil.copy2(src_path, dst_path)
            return True

        except Exception as e:
            logger.warning(f"Failed to replace {dst_path}: {e}")
            return False

    def _restart_services(self) -> bool:
        """Restart application services"""
        try:
            # Try systemd service restart first
            try:
                result = subprocess.run(
                    ["systemctl", "restart", "whisper-appliance"], capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self._log_update("✅ Systemd service restarted")
                    return True
            except:
                pass

            # Try docker restart
            try:
                result = subprocess.run(["docker", "restart", "whisper-appliance"], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self._log_update("✅ Docker container restarted")
                    return True
            except:
                pass

            # Graceful application restart
            self._log_update("🔄 Attempting graceful restart...")

            # Send SIGTERM to current process for graceful shutdown
            try:
                pid = os.getpid()
                os.kill(pid, signal.SIGTERM)
                return True
            except:
                pass

            self._log_update("⚠️ Automatic restart failed - manual restart required")
            return False

        except Exception as e:
            logger.error(f"Service restart failed: {e}")
            self._log_update(f"❌ Service restart failed: {e}")
            return False

    def _attempt_rollback(self) -> Tuple[bool, str]:
        """Attempt automatic rollback to backup"""
        try:
            if not self.backup_manager or not self.update_state["backup_path"]:
                return False, "No backup available for rollback"

            backup_path = self.update_state["backup_path"]

            # Simple rollback: copy backup files over current files
            updated_files = 0
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    if file == "backup_metadata.json":
                        continue

                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, backup_path)
                    dst_path = os.path.join(self.app_root, rel_path)

                    try:
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                        updated_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to rollback file {rel_path}: {e}")

            return True, f"Rollback completed: {updated_files} files restored"

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False, f"Rollback failed: {str(e)}"

    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.update_state["temp_dir"] and os.path.exists(self.update_state["temp_dir"]):
                shutil.rmtree(self.update_state["temp_dir"])
                self.update_state["temp_dir"] = None
                self.update_state["update_source_dir"] = None
                self._log_update("✅ Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

    def _log_update(self, message: str):
        """Add message to update log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.update_state["update_log"].append(log_entry)
        logger.info(log_entry)

    def get_update_log(self) -> List[str]:
        """Get update log messages"""
        return self.update_state["update_log"].copy()

    def get_update_state(self) -> Dict:
        """Get current update state"""
        return self.update_state.copy()

    def rollback_to_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """
        Manual rollback to specific backup

        Args:
            backup_name: Name of backup to rollback to (latest if None)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.backup_manager:
            return False, "No backup manager available"

        try:
            # Get available backups
            backups = self.backup_manager.list_backups()
            if not backups:
                return False, "No backups available"

            # Select backup
            if backup_name:
                selected_backup = None
                for backup in backups:
                    if backup["name"] == backup_name:
                        selected_backup = backup
                        break
                if not selected_backup:
                    return False, f"Backup '{backup_name}' not found"
            else:
                # Use latest backup
                selected_backup = backups[0]

            backup_path = selected_backup["path"]

            # Perform rollback
            self._log_update(f"🔄 Starting rollback to: {selected_backup['name']}")

            # Enable maintenance mode
            if self.maintenance_manager:
                try:
                    self.maintenance_manager.enable_maintenance()
                except:
                    pass

            # Restore files
            success, message = self._restore_from_backup(backup_path)

            if success:
                # Restart services
                self._restart_services()

                # Disable maintenance mode
                if self.maintenance_manager:
                    try:
                        self.maintenance_manager.disable_maintenance()
                    except:
                        pass

                self._log_update("✅ Rollback completed successfully")
                return True, f"Rollback successful: {message}"
            else:
                return False, f"Rollback failed: {message}"

        except Exception as e:
            logger.error(f"Manual rollback failed: {e}")
            return False, f"Rollback failed: {str(e)}"

    def _restore_from_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Restore files from backup"""
        try:
            updated_files = 0
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    if file == "backup_metadata.json":
                        continue

                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, backup_path)
                    dst_path = os.path.join(self.app_root, rel_path)

                    try:
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                        updated_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to restore file {rel_path}: {e}")

            return True, f"{updated_files} files restored"

        except Exception as e:
            return False, str(e)
