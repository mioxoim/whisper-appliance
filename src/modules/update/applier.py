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

    def _download_update(self, target_version: str = "latest") -> bool:
        """
        Download update from GitHub with robust fallback strategies

        Args:
            target_version: Version to download (latest or specific version)

        Returns:
            bool: True if download successful
        """
        try:
            # Create temporary directory
            self.update_state["temp_dir"] = tempfile.mkdtemp(prefix="whisper_update_")
            temp_dir = self.update_state["temp_dir"]

            # GitHub repository info
            repo_owner = "GaboCapo"
            repo_name = "whisper-appliance"

            if target_version == "latest":
                # Get latest release info
                api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
                self._log_update(f"🔍 Fetching latest release info from {api_url}")

                try:
                    with urllib.request.urlopen(api_url, timeout=30) as response:
                        release_data = json.loads(response.read().decode())
                        download_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/main.zip"
                        target_version = release_data.get("tag_name", "main")
                except Exception as e:
                    # Fallback to main branch
                    self._log_update(f"⚠️ API request failed, using main branch: {e}")
                    download_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/main.zip"
                    target_version = "main"
            else:
                # Specific version download
                download_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/tags/{target_version}.zip"

            self._log_update(f"⬇️ Downloading from: {download_url}")

            # Download with multiple fallback strategies
            zip_path = os.path.join(temp_dir, "update.zip")

            # Strategy 1: urllib.request
            try:
                urllib.request.urlretrieve(download_url, zip_path)
                self._log_update("✅ Download successful with urllib")
            except Exception as e:
                self._log_update(f"⚠️ urllib download failed: {e}")

                # Strategy 2: curl fallback
                try:
                    result = subprocess.run(
                        ["curl", "-L", "-o", zip_path, download_url, "--max-time", "300"],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )

                    if result.returncode != 0:
                        raise Exception(f"curl failed: {result.stderr}")
                    self._log_update("✅ Download successful with curl")
                except Exception as e:
                    self._log_update(f"⚠️ curl download failed: {e}")

                    # Strategy 3: wget fallback
                    try:
                        result = subprocess.run(
                            ["wget", "-O", zip_path, download_url, "--timeout=300"],
                            capture_output=True,
                            text=True,
                            timeout=300,
                        )

                        if result.returncode != 0:
                            raise Exception(f"wget failed: {result.stderr}")
                        self._log_update("✅ Download successful with wget")
                    except Exception as e:
                        self._log_update(f"❌ All download strategies failed: {e}")
                        return False

            # Verify download
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000:
                self._log_update("❌ Downloaded file is invalid or too small")
                return False

            # Extract update
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)

            self._log_update("📦 Extracting update archive...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find the extracted directory (usually whisper-appliance-main or whisper-appliance-version)
            extracted_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
            if not extracted_dirs:
                self._log_update("❌ No directories found in extracted archive")
                return False

            # Use the first (and usually only) extracted directory
            source_dir = os.path.join(extract_dir, extracted_dirs[0])
            self.update_state["update_source_dir"] = source_dir

            self._log_update(f"✅ Update extracted to: {source_dir}")
            return True

        except Exception as e:
            self._log_update(f"❌ Download failed: {e}")
            logger.error(f"Update download failed: {e}")
            return False

    def _apply_permission_safe_update(self) -> bool:
        """
        Apply update using permission-safe file replacement strategy

        Returns:
            bool: True if update applied successfully
        """
        try:
            source_dir = self.update_state.get("update_source_dir")
            if not source_dir or not os.path.exists(source_dir):
                self._log_update("❌ No valid source directory for update")
                return False

            self._log_update(f"🔄 Applying update from: {source_dir}")

            # Define critical files and directories to update
            update_patterns = [
                ("src/", "src/"),  # Main application code
                ("scripts/", "scripts/"),  # Deployment scripts
                ("requirements.txt", "requirements.txt"),  # Dependencies
                ("README.md", "README.md"),  # Documentation
                ("CHANGELOG.md", "CHANGELOG.md"),  # Change log
            ]

            updated_files = 0
            failed_files = 0

            for src_pattern, dst_pattern in update_patterns:
                src_path = os.path.join(source_dir, src_pattern)
                dst_path = os.path.join(self.app_root, dst_pattern)

                if not os.path.exists(src_path):
                    self._log_update(f"⚠️ Source not found: {src_pattern}")
                    continue

                if os.path.isfile(src_path):
                    # Single file update
                    if self._replace_file_safely(src_path, dst_path):
                        updated_files += 1
                        self._log_update(f"✅ Updated: {dst_pattern}")
                    else:
                        failed_files += 1
                        self._log_update(f"❌ Failed: {dst_pattern}")

                elif os.path.isdir(src_path):
                    # Directory update
                    self._log_update(f"📁 Updating directory: {src_pattern}")

                    for root, dirs, files in os.walk(src_path):
                        for file in files:
                            # Skip certain files
                            if file in [".gitignore", ".git", "__pycache__", ".pyc"]:
                                continue

                            src_file = os.path.join(root, file)
                            rel_path = os.path.relpath(src_file, src_path)
                            dst_file = os.path.join(dst_path, rel_path)

                            if self._replace_file_safely(src_file, dst_file):
                                updated_files += 1
                            else:
                                failed_files += 1

            # Update dependencies if requirements.txt changed
            if os.path.exists(os.path.join(self.app_root, "requirements.txt")):
                self._log_update("📦 Updating dependencies...")
                try:
                    result = subprocess.run(
                        ["pip3", "install", "-r", os.path.join(self.app_root, "requirements.txt")],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                    if result.returncode == 0:
                        self._log_update("✅ Dependencies updated successfully")
                    else:
                        self._log_update(f"⚠️ Dependency update warnings: {result.stderr}")
                except Exception as e:
                    self._log_update(f"⚠️ Dependency update failed: {e}")

            # Summary
            total_operations = updated_files + failed_files
            success_rate = (updated_files / total_operations * 100) if total_operations > 0 else 0

            self._log_update(
                f"📊 Update summary: {updated_files} updated, {failed_files} failed ({success_rate:.1f}% success)"
            )

            # Consider update successful if we have at least 80% success rate and core files updated
            if success_rate >= 80 and updated_files > 0:
                self._log_update("✅ Permission-safe update completed successfully")
                return True
            else:
                self._log_update("❌ Update failed - insufficient success rate or no files updated")
                return False

        except Exception as e:
            self._log_update(f"❌ Permission-safe update failed: {e}")
            logger.error(f"Update application failed: {e}")
            return False

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
