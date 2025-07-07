"""
Update Rollback
Handles rollback to previous versions
"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional


class UpdateRollback:
    """Manages update rollbacks"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.backup_dir = os.path.join(repo_path, ".update_backups")

    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []

        if not os.path.exists(self.backup_dir):
            return backups

        for backup in os.listdir(self.backup_dir):
            if backup.startswith("backup_"):
                backup_path = os.path.join(self.backup_dir, backup)
                stat = os.stat(backup_path)
                backups.append(
                    {
                        "name": backup,
                        "path": backup_path,
                        "date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "size": self._get_dir_size(backup_path),
                    }
                )

        return sorted(backups, key=lambda x: x["date"], reverse=True)

    def rollback_to(self, backup_name: str) -> Dict[str, any]:
        """Rollback to specific backup"""
        result = {"success": False, "message": ""}

        backup_path = os.path.join(self.backup_dir, backup_name)
        if not os.path.exists(backup_path):
            result["message"] = "Backup not found"
            return result

        try:
            # Restore each backed up item
            for item in os.listdir(backup_path):
                source = os.path.join(backup_path, item)
                dest = os.path.join(self.repo_path, item)

                # Remove existing
                if os.path.exists(dest):
                    if os.path.isdir(dest):
                        shutil.rmtree(dest)
                    else:
                        os.remove(dest)

                # Restore from backup
                if os.path.isdir(source):
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)

            result["success"] = True
            result["message"] = f"Rolled back to {backup_name}"
            return result

        except Exception as e:
            result["message"] = f"Rollback failed: {str(e)}"
            return result

    def _get_dir_size(self, path: str) -> int:
        """Get directory size in bytes"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total

    def cleanup_old_backups(self, keep_count: int = 5):
        """Remove old backups, keeping only the most recent ones"""
        backups = self.list_backups()

        if len(backups) > keep_count:
            for backup in backups[keep_count:]:
                try:
                    shutil.rmtree(backup["path"])
                except Exception:
                    pass
