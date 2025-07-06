"""
Update Checker
Professional update checking and version management
"""

import json
import logging
import os
import subprocess
import urllib.request
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class UpdateChecker:
    """
    Professional update checking system
    """

    def __init__(self, app_root: str, repo_url: str = "https://github.com/GaboCapo/whisper-appliance.git"):
        self.app_root = app_root
        self.repo_url = repo_url
        self.api_url = self._get_github_api_url(repo_url)

        # Update checking state
        self.check_status = {
            "checking": False,
            "last_check": None,
            "current_version": None,
            "latest_version": None,
            "updates_available": False,
            "commits_behind": 0,
            "error": None,
        }

    def _get_github_api_url(self, repo_url: str) -> str:
        """Extract GitHub API URL from repository URL"""
        if "github.com" in repo_url:
            # Extract owner/repo from URL
            parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

        return "https://api.github.com/repos/GaboCapo/whisper-appliance/releases/latest"

    def get_current_version(self) -> str:
        """
        Get current application version

        Returns:
            str: Current version string
        """
        try:
            # Try git describe first
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.check_status["current_version"] = version
                return version

            # Fallback to commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.check_status["current_version"] = version
                return version

            # Check version file
            version_file = os.path.join(self.app_root, "whisper-appliance_version.txt")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    version = f.read().strip()
                    self.check_status["current_version"] = version
                    return version

        except Exception as e:
            logger.error(f"Failed to get current version: {e}")

        version = "unknown"
        self.check_status["current_version"] = version
        return version

    def check_for_updates(self) -> Dict:
        """
        Check if updates are available

        Returns:
            Dict: Update check results
        """
        if self.check_status["checking"]:
            return {"status": "checking", "message": "Check already in progress"}

        self.check_status["checking"] = True

        try:
            # Get current version
            current_version = self.get_current_version()

            # Check GitHub API for latest release
            with urllib.request.urlopen(self.api_url, timeout=30) as response:
                data = json.loads(response.read().decode())

                latest_version = data["tag_name"].lstrip("v")

                # Update status
                self.check_status["latest_version"] = latest_version
                self.check_status["current_version"] = current_version
                self.check_status["updates_available"] = latest_version != current_version
                self.check_status["last_check"] = datetime.now().isoformat()
                self.check_status["error"] = None

                return {
                    "status": "success",
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "updates_available": latest_version != current_version,
                    "release_notes": data.get("body", "")[:500],
                    "last_check": self.check_status["last_check"],
                    "download_url": data.get("zipball_url", ""),
                }

        except Exception as e:
            error_msg = f"Update check failed: {str(e)}"
            logger.error(error_msg)
            self.check_status["error"] = error_msg

            return {"status": "error", "error": error_msg}

        finally:
            self.check_status["checking"] = False

    def check_commits_behind(self) -> int:
        """
        Check how many commits behind the remote we are

        Returns:
            int: Number of commits behind
        """
        try:
            # Fetch latest changes
            subprocess.run(["git", "fetch", "origin"], cwd=self.app_root, capture_output=True, text=True, timeout=30)

            # Count commits behind
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                commits_behind = int(result.stdout.strip())
                self.check_status["commits_behind"] = commits_behind
                return commits_behind

        except Exception as e:
            logger.warning(f"Failed to check commits behind: {e}")

        return 0

    def get_update_status(self) -> Dict:
        """
        Get comprehensive update status

        Returns:
            Dict: Complete update status
        """
        status = self.check_status.copy()

        # Add current version if not set
        if not status["current_version"]:
            status["current_version"] = self.get_current_version()

        return status

    def get_release_info(self, version: str = None) -> Optional[Dict]:
        """
        Get release information for specific version

        Args:
            version: Version to get info for (latest if None)

        Returns:
            Optional[Dict]: Release information
        """
        try:
            if version:
                api_url = self.api_url.replace("/releases/latest", f"/releases/tags/v{version}")
            else:
                api_url = self.api_url

            with urllib.request.urlopen(api_url, timeout=30) as response:
                data = json.loads(response.read().decode())
                return {
                    "version": data["tag_name"].lstrip("v"),
                    "name": data.get("name", ""),
                    "body": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                    "download_url": data.get("zipball_url", ""),
                    "prerelease": data.get("prerelease", False),
                }

        except Exception as e:
            logger.error(f"Failed to get release info: {e}")
            return None
