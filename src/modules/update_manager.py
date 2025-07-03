"""
Update Manager Module
Provides web-based update functionality for WhisperS2T Appliance
Integrates with existing auto-update.sh script and provides web interface
"""

import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class UpdateManager:
    """Manages application updates with web interface"""

    def __init__(self, app_root=None):
        # Robust auto-detection of application root
        if app_root is None:
            app_root = self._find_git_repository()

        self.app_root = app_root
        self.auto_update_script = os.path.join(app_root, "auto-update.sh") if app_root else None
        logger.info(f"UpdateManager initialized with app_root: {self.app_root}")
        logger.info(f"Auto-update script path: {self.auto_update_script}")
        self.update_status = {
            "checking": False,
            "updating": False,
            "last_check": None,
            "updates_available": False,
            "current_version": None,
            "latest_version": None,
            "commits_behind": 0,
            "last_update": None,
            "update_log": [],
            "error": None,
        }
        self._update_lock = threading.Lock()

    def _find_git_repository(self) -> Optional[str]:
        """Find the git repository root by checking multiple locations"""
        # First try using git command to find the repository root
        try:
            result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                git_root = result.stdout.strip()
                if os.path.exists(git_root) and os.path.exists(os.path.join(git_root, ".git")):
                    logger.info(f"Found git repository using git command: {git_root}")
                    return git_root
        except Exception as e:
            logger.debug(f"Git command failed: {e}")

        # Fallback to checking possible paths
        possible_paths = [
            # Current application directory (development)
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            # Standard production paths
            "/opt/whisper-appliance",
            "/app",
            "/opt/app",
            # Container paths
            "/workspace",
            "/code",
            # Current working directory and its parents
            os.getcwd(),
        ]

        # Also check parent directories up to root
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        while current_dir != "/" and current_dir:
            possible_paths.append(current_dir)
            current_dir = os.path.dirname(current_dir)

        for path in possible_paths:
            if os.path.exists(os.path.join(path, ".git")):
                logger.info(f"Found git repository at: {path}")
                return path

        logger.warning("No git repository found in any of the checked paths")
        return None

    def get_current_version(self) -> str:
        """Get current application version from git"""
        try:
            if not self.app_root:
                return "unknown - no git repository"

            if os.path.exists(os.path.join(self.app_root, ".git")):
                result = subprocess.run(
                    ["git", "describe", "--tags", "--always"], cwd=self.app_root, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip()

            # Fallback to commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()

        except Exception as e:
            logger.error(f"Failed to get current version: {e}")

        return "unknown"

    def check_for_updates(self, background: bool = False) -> Dict:
        """Check for available updates"""
        if background:
            # Run in background thread
            threading.Thread(target=self._check_updates_background, daemon=True).start()
            return {"status": "checking", "message": "Update check started in background"}
        else:
            return self._check_updates_sync()

    def _check_updates_background(self):
        """Background update check"""
        with self._update_lock:
            self.update_status["checking"] = True
            self.update_status["error"] = None

        try:
            result = self._run_auto_update_script("check")

            with self._update_lock:
                self.update_status["checking"] = False
                self.update_status["last_check"] = datetime.now().isoformat()
                self.update_status["current_version"] = self.get_current_version()

                if result["returncode"] == 2:  # Updates available
                    self.update_status["updates_available"] = True
                    self._parse_update_info(result["output"])
                elif result["returncode"] == 0:  # Up to date
                    self.update_status["updates_available"] = False
                    self.update_status["commits_behind"] = 0
                else:
                    self.update_status["error"] = f"Update check failed: {result['error']}"

        except Exception as e:
            logger.error(f"Background update check failed: {e}")
            with self._update_lock:
                self.update_status["checking"] = False
                self.update_status["error"] = str(e)

    def _check_updates_sync(self) -> Dict:
        """Synchronous update check"""
        with self._update_lock:
            if self.update_status["checking"]:
                return {"status": "busy", "message": "Update check already in progress"}

            self.update_status["checking"] = True
            self.update_status["error"] = None

        try:
            result = self._run_auto_update_script("check")

            response = {
                "status": "success",
                "current_version": self.get_current_version(),
                "last_check": datetime.now().isoformat(),
                "updates_available": False,
                "commits_behind": 0,
            }

            if result["returncode"] == 2:  # Updates available
                response["updates_available"] = True
                update_info = self._parse_update_info(result["output"])
                response.update(update_info)
            elif result["returncode"] == 0:  # Up to date
                response["message"] = "System is up to date"
            else:
                response["status"] = "error"
                response["error"] = f"Update check failed: {result['error']}"

            # Update internal status
            with self._update_lock:
                self.update_status.update(response)
                self.update_status["checking"] = False

            return response

        except Exception as e:
            logger.error(f"Update check failed: {e}")
            with self._update_lock:
                self.update_status["checking"] = False
                self.update_status["error"] = str(e)

            return {"status": "error", "error": str(e)}

    def apply_updates(self) -> Dict:
        """Apply available updates"""
        with self._update_lock:
            if self.update_status["updating"]:
                return {"status": "busy", "message": "Update already in progress"}

            if self.update_status["checking"]:
                return {"status": "busy", "message": "Update check in progress, please wait"}

            self.update_status["updating"] = True
            self.update_status["error"] = None
            self.update_status["update_log"] = []

        # Run update in background
        threading.Thread(target=self._apply_updates_background, daemon=True).start()

        return {"status": "updating", "message": "Update started in background"}

    def _apply_updates_background(self):
        """Background update application"""
        try:
            logger.info("Starting update process...")

            # Add initial log entry
            self._add_update_log("Starting update process...")

            # Run auto-update script
            result = self._run_auto_update_script("apply")

            if result["returncode"] == 0:
                self._add_update_log("Update completed successfully!")
                with self._update_lock:
                    self.update_status["updating"] = False
                    self.update_status["last_update"] = datetime.now().isoformat()
                    self.update_status["current_version"] = self.get_current_version()
                    self.update_status["updates_available"] = False
                    self.update_status["commits_behind"] = 0
            else:
                self._add_update_log(f"Update failed: {result['error']}")
                with self._update_lock:
                    self.update_status["updating"] = False
                    self.update_status["error"] = f"Update failed: {result['error']}"

        except Exception as e:
            logger.error(f"Update process failed: {e}")
            self._add_update_log(f"Update process failed: {str(e)}")
            with self._update_lock:
                self.update_status["updating"] = False
                self.update_status["error"] = str(e)

    def rollback_update(self) -> Dict:
        """Rollback to previous version"""
        with self._update_lock:
            if self.update_status["updating"]:
                return {"status": "busy", "message": "Update in progress, cannot rollback"}

            self.update_status["updating"] = True
            self.update_status["error"] = None

        try:
            result = self._run_auto_update_script("rollback")

            if result["returncode"] == 0:
                with self._update_lock:
                    self.update_status["updating"] = False
                    self.update_status["current_version"] = self.get_current_version()
                    self.update_status["last_update"] = datetime.now().isoformat()

                return {"status": "success", "message": "Rollback completed successfully"}
            else:
                with self._update_lock:
                    self.update_status["updating"] = False
                    self.update_status["error"] = f"Rollback failed: {result['error']}"

                return {"status": "error", "error": f"Rollback failed: {result['error']}"}

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            with self._update_lock:
                self.update_status["updating"] = False
                self.update_status["error"] = str(e)

            return {"status": "error", "error": str(e)}

    def get_update_status(self) -> Dict:
        """Get current update status"""
        with self._update_lock:
            status = self.update_status.copy()

        # Add current version if not set
        if not status["current_version"]:
            status["current_version"] = self.get_current_version()

        return status

    def _run_auto_update_script(self, command: str) -> Dict:
        """Run the auto-update.sh script with specified command"""
        if not self.app_root:
            raise FileNotFoundError("No git repository found - cannot run auto-update script")

        if not self.auto_update_script or not os.path.exists(self.auto_update_script):
            raise FileNotFoundError(f"Auto-update script not found: {self.auto_update_script}")

        try:
            # Make script executable if needed
            os.chmod(self.auto_update_script, 0o755)

            cmd = ["/bin/bash", self.auto_update_script, command]

            logger.info(f"Running update command: {' '.join(cmd)}")

            result = subprocess.run(cmd, cwd=self.app_root, capture_output=True, text=True, timeout=300)  # 5 minute timeout

            return {"returncode": result.returncode, "output": result.stdout, "error": result.stderr}

        except subprocess.TimeoutExpired:
            raise Exception("Update script timed out after 5 minutes")
        except Exception as e:
            raise Exception(f"Failed to run update script: {str(e)}")

    def _parse_update_info(self, output: str) -> Dict:
        """Parse update information from script output"""
        info = {}

        try:
            lines = output.split("\n")
            for line in lines:
                if "Commits behind:" in line:
                    try:
                        commits = int(line.split(":")[-1].strip())
                        info["commits_behind"] = commits
                    except ValueError:
                        pass
                elif "Latest commit:" in line:
                    commit = line.split(":")[-1].strip()
                    info["latest_version"] = commit[:8] if len(commit) >= 8 else commit

        except Exception as e:
            logger.warning(f"Failed to parse update info: {e}")

        return info

    def _add_update_log(self, message: str):
        """Add message to update log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        with self._update_lock:
            self.update_status["update_log"].append(log_entry)
            # Keep only last 50 log entries
            if len(self.update_status["update_log"]) > 50:
                self.update_status["update_log"] = self.update_status["update_log"][-50:]

        logger.info(log_entry)
