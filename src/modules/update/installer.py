"""
Update Installation
Handles the actual update process
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class UpdateInstaller:
    """Handles update installation"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.backup_dir = os.path.join(repo_path, ".update_backups")
        self.log_file = os.path.join(repo_path, "logs", "update.log")

    def create_backup(self) -> Optional[str]:
        """Create backup before update"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")

            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)

            # Backup critical files
            critical_paths = ["src", "requirements.txt", "config", "templates", "static"]

            for path in critical_paths:
                source = os.path.join(self.repo_path, path)
                if os.path.exists(source):
                    dest = os.path.join(backup_path, path)
                    if os.path.isdir(source):
                        shutil.copytree(source, dest)
                    else:
                        shutil.copy2(source, dest)

            return backup_path
        except Exception as e:
            self._log(f"Backup failed: {e}")
            return None

    def install_update(self) -> Dict[str, any]:
        """Install updates from Git"""
        result = {"success": False, "message": "", "backup_path": None, "restart_required": False}

        # Create backup first
        backup_path = self.create_backup()
        if not backup_path:
            result["message"] = "Failed to create backup"
            return result

        result["backup_path"] = backup_path

        try:
            # Pull latest changes
            # Ensure a writable HOME directory for git, using the repo_path itself.
            git_env = os.environ.copy()
            git_env["HOME"] = self.repo_path

            pull_result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60,
                env=git_env
            )

            if pull_result.returncode != 0:
                result["message"] = f"Git pull failed: {pull_result.stderr}"
                return result

            # Check if requirements changed
            req_changed = "requirements.txt" in pull_result.stdout

            # Install new requirements if needed
            if req_changed:
                pip_result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=300,
                )
                if pip_result.returncode != 0:
                    result["message"] = "Failed to install requirements"
                    return result

            # Check if Python files changed
            if ".py" in pull_result.stdout:
                result["restart_required"] = True

            result["success"] = True
            result["message"] = "Update installed successfully"
            self._log(f"Update installed successfully. Backup: {backup_path}")

            return result

        except Exception as e:
            result["message"] = f"Update failed: {str(e)}"
            self._log(f"Update failed: {e}")
            return result

    def _log(self, message: str):
        """Log update activities"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def restart_service(self) -> bool:
        """Restart the application service"""
        try:
            # Try systemd first (production)
            result = subprocess.run(["systemctl", "restart", "whisper-appliance"], capture_output=True)
            if result.returncode == 0:
                self._log("Service restarted via systemd")
                return True

            # Try docker restart (container environment)
            result = subprocess.run(["docker", "restart", "whisper-appliance"], capture_output=True)
            if result.returncode == 0:
                self._log("Service restarted via docker")
                return True

            # Development environment - just log
            self._log("Development environment - manual restart required")
            return True

        except Exception as e:
            self._log(f"Service restart failed: {e}")
            return False
