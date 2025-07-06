"""
Update Backup Manager
Professional backup management for safe WhisperS2T updates
"""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class UpdateBackupManager:
    """
    Professional backup manager for safe updates
    """

    def __init__(self, app_root: str):
        self.app_root = app_root
        self.backup_dir = os.path.join(app_root, ".update_backups")
        self.max_backups = 5  # Keep last 5 backups

    def create_backup(self, backup_name: str = None) -> Tuple[bool, str]:
        """
        Create backup before update

        Args:
            backup_name: Optional backup name

        Returns:
            Tuple[bool, str]: (success, backup_path)
        """
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            backup_path = os.path.join(self.backup_dir, backup_name)

            # Ensure backup directory exists
            os.makedirs(self.backup_dir, exist_ok=True)

            # Create backup with selective copying (exclude large/unnecessary files)
            self._create_selective_backup(backup_path)

            # Create backup metadata
            self._create_backup_metadata(backup_path)

            # Cleanup old backups
            self._cleanup_old_backups()

            logger.info(f"Backup created successfully: {backup_path}")
            return True, backup_path

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, str(e)

    def _create_selective_backup(self, backup_path: str):
        """Create selective backup excluding unnecessary files"""

        # Files/directories to exclude from backup
        exclude_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            ".github",
            "node_modules",
            "*.log",
            ".update_backups",
            "tmp",
            "temp",
        ]

        def should_exclude(path: str) -> bool:
            for pattern in exclude_patterns:
                if pattern in path or path.endswith(pattern.replace("*", "")):
                    return True
            return False

        # Copy files selectively
        for root, dirs, files in os.walk(self.app_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

            for file in files:
                src_path = os.path.join(root, file)

                if should_exclude(src_path):
                    continue

                # Calculate relative path
                rel_path = os.path.relpath(src_path, self.app_root)
                dst_path = os.path.join(backup_path, rel_path)

                # Ensure destination directory exists
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)

                # Copy file
                shutil.copy2(src_path, dst_path)

    def _create_backup_metadata(self, backup_path: str):
        """Create backup metadata file"""
        try:
            # Get current git info if available
            git_info = self._get_git_info()

            metadata = {
                "created_at": datetime.now().isoformat(),
                "app_root": self.app_root,
                "git_info": git_info,
                "backup_type": "update_backup",
                "size_mb": self._calculate_backup_size(backup_path),
            }

            metadata_file = os.path.join(backup_path, "backup_metadata.json")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to create backup metadata: {e}")

    def _get_git_info(self) -> Dict:
        """Get current git information"""
        git_info = {}

        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                git_info["commit_hash"] = result.stdout.strip()

            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()

        except Exception as e:
            logger.warning(f"Failed to get git info: {e}")

        return git_info

    def _calculate_backup_size(self, backup_path: str) -> float:
        """Calculate backup size in MB"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0

    def _cleanup_old_backups(self):
        """Remove old backups keeping only the latest ones"""
        try:
            if not os.path.exists(self.backup_dir):
                return

            # Get all backup directories
            backups = []
            for item in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(backup_path):
                    # Get creation time
                    stat = os.stat(backup_path)
                    backups.append((backup_path, stat.st_mtime))

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups if we exceed the limit
            if len(backups) > self.max_backups:
                for backup_path, _ in backups[self.max_backups :]:
                    logger.info(f"Removing old backup: {backup_path}")
                    shutil.rmtree(backup_path)

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []

        try:
            if not os.path.exists(self.backup_dir):
                return backups

            for item in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(backup_path):
                    # Load metadata if available
                    metadata_file = os.path.join(backup_path, "backup_metadata.json")
                    metadata = {}

                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, "r") as f:
                                metadata = json.load(f)
                        except:
                            pass

                    # Get basic info
                    stat = os.stat(backup_path)
                    backup_info = {
                        "name": item,
                        "path": backup_path,
                        "created_at": metadata.get("created_at", datetime.fromtimestamp(stat.st_ctime).isoformat()),
                        "size_mb": metadata.get("size_mb", 0),
                        "git_info": metadata.get("git_info", {}),
                        "backup_type": metadata.get("backup_type", "unknown"),
                    }

                    backups.append(backup_info)

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        return backups
