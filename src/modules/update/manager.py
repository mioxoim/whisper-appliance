"""
Update Manager
Central management for Git-based updates
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from .git_monitor import GitMonitor
from .installer import UpdateInstaller
from .rollback import UpdateRollback


class UpdateManager:
    """Main update management class"""

    def __init__(self, repo_path: Optional[str] = None):
        # Find repository path
        if repo_path is None:
            repo_path = self._find_repo_path()

        self.repo_path = repo_path
        self.git_monitor = GitMonitor(repo_path)
        self.installer = UpdateInstaller(repo_path)
        self.rollback = UpdateRollback(repo_path)

        # State tracking
        self.last_check = None
        self.update_available = False
        self.update_info = None

    def _find_repo_path(self) -> str:
        """Find the Git repository path"""
        possible_paths = [
            "/opt/whisper-appliance",
            "/app",
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            os.getcwd(),
        ]

        for path in possible_paths:
            if os.path.exists(os.path.join(path, ".git")):
                return path

        # Default fallback
        return "/opt/whisper-appliance"

    def check_for_updates(self) -> Dict[str, any]:
        """Check if updates are available"""
        self.last_check = datetime.now()

        # Fetch latest info
        self.git_monitor.fetch_updates()

        # Check for updates
        has_update, update_info = self.git_monitor.check_for_updates()

        self.update_available = has_update
        self.update_info = update_info

        return {
            "update_available": has_update,
            "current_version": self.git_monitor.get_current_commit(),
            "latest_version": update_info["sha"] if update_info else None,
            "update_info": update_info,
            "last_check": self.last_check.isoformat(),
        }

    def install_update(self) -> Dict[str, any]:
        """Install available updates"""
        if not self.update_available:
            # Re-check first
            self.check_for_updates()

        if not self.update_available:
            return {"success": False, "message": "No updates available"}

        # Install the update
        result = self.installer.install_update()

        # Reset update state if successful
        if result["success"]:
            self.update_available = False
            self.update_info = None

            # Clean up old backups
            self.rollback.cleanup_old_backups()

            if result.get("restart_required", False):
                restart_success = self.restart_application()
                result["restart_attempted"] = True
                result["restart_success"] = restart_success
                if restart_success:
                    result["message"] += " Service restart initiated."
                else:
                    result["message"] += " Service restart failed. Please restart manually."
            else:
                result["restart_attempted"] = False
                result["restart_success"] = None # Or False, depending on desired representation

        return result

    def get_status(self) -> Dict[str, any]:
        """Get current update system status"""
        return {
            "repo_path": self.repo_path,
            "current_commit": self.git_monitor.get_current_commit(),
            "update_available": self.update_available,
            "update_info": self.update_info,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "backups": len(self.rollback.list_backups()),
            "recent_commits": self.git_monitor.get_commit_history(5),
        }

    def get_update_history(self) -> List[Dict]:
        """Get update history from Git log"""
        return self.git_monitor.get_commit_history(20)

    def rollback_to_backup(self, backup_name: str) -> Dict[str, any]:
        """Rollback to a specific backup"""
        return self.rollback.rollback_to(backup_name)

    def list_backups(self) -> List[Dict]:
        """List available backups"""
        return self.rollback.list_backups()

    def restart_application(self) -> bool:
        """Restart the application after update"""
        return self.installer.restart_service()
