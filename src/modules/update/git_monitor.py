"""
Git-based Update Detection
Monitors Git repository for new commits on main branch
"""

import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests


class GitMonitor:
    """Monitors Git repository for updates"""

    def __init__(self, repo_path: str = "/opt/whisper-appliance"):
        self.repo_path = self._find_repo_path(repo_path)
        self.github_api = "https://api.github.com/repos/GaboCapo/whisper-appliance"

    def _find_repo_path(self, default: str) -> str:
        """Find the Git repository path"""
        possible_paths = [
            default,
            "/opt/whisper-appliance",
            "/app",
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            os.getcwd(),
        ]

        for path in possible_paths:
            if os.path.exists(os.path.join(path, ".git")):
                return path

        return default

    def get_current_commit(self) -> Optional[str]:
        """Get current commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def get_latest_remote_commit(self) -> Optional[Dict]:
        """Get latest commit from GitHub"""
        try:
            response = requests.get(f"{self.github_api}/commits/main", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "sha": data["sha"],
                    "message": data["commit"]["message"],
                    "author": data["commit"]["author"]["name"],
                    "date": data["commit"]["author"]["date"],
                }
        except Exception:
            pass
        return None

    def check_for_updates(self) -> Tuple[bool, Optional[Dict]]:
        """Check if updates are available"""
        current = self.get_current_commit()
        latest = self.get_latest_remote_commit()

        if not current or not latest:
            return False, None

        if current != latest["sha"]:
            return True, latest

        return False, None

    def get_commit_history(self, limit: int = 10) -> List[Dict]:
        """Get recent commit history"""
        try:
            response = requests.get(f"{self.github_api}/commits?per_page={limit}", timeout=10)
            if response.status_code == 200:
                commits = []
                for commit in response.json():
                    commits.append(
                        {
                            "sha": commit["sha"][:7],
                            "message": commit["commit"]["message"].split("\n")[0],
                            "author": commit["commit"]["author"]["name"],
                            "date": commit["commit"]["author"]["date"],
                        }
                    )
                return commits
        except Exception:
            pass
        return []

    def fetch_updates(self) -> bool:
        """Fetch updates from remote repository"""
        try:
            # First fetch
            result = subprocess.run(["git", "fetch", "origin", "main"], cwd=self.repo_path, capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception:
            return False
