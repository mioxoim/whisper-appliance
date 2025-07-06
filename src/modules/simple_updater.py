#!/usr/bin/env python3
"""
Simple, Modern Git-Based Update System for WhisperS2T Appliance
==============================================================

Based on modern web application update patterns:
- Git webhook integration
- Simple REST API endpoints
- Automatic service restart
- Zero-downtime deployment ready

Follows best practices from Flask community and modern DevOps patterns.
"""

import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


class SimpleUpdater:
    """
    Modern, webhook-ready update system for Flask applications.

    Features:
    - Git-based updates via webhooks
    - Automatic service restart
    - Version tracking
    - Simple REST API
    - Production-ready error handling
    """

    def __init__(self, app_root: str = None, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.app_root = self._detect_app_root(app_root)
        self.version_file = Path(self.app_root) / "VERSION"

        self.logger.info(f"🔄 SimpleUpdater initialized for: {self.app_root}")

    def _detect_app_root(self, app_root: str = None) -> str:
        """Auto-detect application root directory."""
        if app_root and os.path.exists(app_root):
            return app_root

        # Standard deployment paths in priority order
        possible_paths = [
            "/opt/whisper-appliance",  # Proxmox Standard
            "/app",  # Docker Standard
            "/opt/app",  # Alternative
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),  # Development
        ]

        for path in possible_paths:
            if os.path.exists(os.path.join(path, ".git")):
                return path

        # Fallback to current working directory
        return os.getcwd()

    def get_current_version(self) -> str:
        """Get current application version."""
        try:
            if self.version_file.exists():
                return self.version_file.read_text().strip()

            # Try to get version from git
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception as e:
            self.logger.warning(f"Could not determine version: {e}")

        return "unknown"

    def check_for_updates(self) -> Dict[str, Any]:
        """
        Check if updates are available from git remote.

        Modern approach: Use git fetch + git status to check for updates.
        """
        try:
            self.logger.info("🔍 Checking for updates...")

            # Fetch latest from remote
            fetch_result = subprocess.run(
                ["git", "fetch", "origin"], cwd=self.app_root, capture_output=True, text=True, timeout=30
            )

            if fetch_result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"Failed to fetch from remote: {fetch_result.stderr}",
                    "update_available": False,
                }

            # Check if local is behind remote
            status_result = subprocess.run(
                ["git", "status", "-uno", "--porcelain=v1"], cwd=self.app_root, capture_output=True, text=True, timeout=10
            )

            # Get commit counts
            behind_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            commits_behind = 0
            if behind_result.returncode == 0:
                commits_behind = int(behind_result.stdout.strip() or 0)

            current_version = self.get_current_version()

            return {
                "status": "success",
                "update_available": commits_behind > 0,
                "commits_behind": commits_behind,
                "current_version": current_version,
                "check_time": datetime.now().isoformat(),
                "deployment_type": "simple_git",
                "app_root": self.app_root,
            }

        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Update check timed out", "update_available": False}
        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            return {"status": "error", "message": f"Update check failed: {str(e)}", "update_available": False}

    def perform_update(self) -> Tuple[bool, str]:
        """
        Perform git pull update with service restart.

        Modern approach:
        1. Git pull
        2. Update VERSION file
        3. Restart service (systemd or manual)
        """
        try:
            self.logger.info("🚀 Starting update process...")

            # Store current version for rollback
            current_version = self.get_current_version()

            # Perform git pull
            self.logger.info("📥 Pulling latest changes from git...")
            pull_result = subprocess.run(
                ["git", "pull", "origin", "main"], cwd=self.app_root, capture_output=True, text=True, timeout=60
            )

            if pull_result.returncode != 0:
                error_msg = f"Git pull failed: {pull_result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg

            # Update version file
            new_version = self.get_current_version()
            self.version_file.write_text(f"{new_version}\n")

            self.logger.info(f"✅ Updated from {current_version} to {new_version}")

            # Try to restart service (non-blocking)
            self._restart_service()

            return True, f"Successfully updated from {current_version} to {new_version}"

        except subprocess.TimeoutExpired:
            return False, "Update timed out"
        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _restart_service(self):
        """
        Restart the application service.

        Modern approach: Try systemd first, fallback to graceful restart.
        """
        try:
            # Try systemd restart (Proxmox/production)
            systemd_result = subprocess.run(
                ["systemctl", "restart", "whisper-appliance"], capture_output=True, text=True, timeout=30
            )

            if systemd_result.returncode == 0:
                self.logger.info("🔄 Service restarted via systemd")
                return

        except Exception as e:
            self.logger.debug(f"Systemd restart not available: {e}")

        # Fallback: Log restart requirement
        self.logger.warning("⚠️ Manual restart required - systemd not available")
        self.logger.info("💡 Please restart the application manually to complete the update")


def integrate_simple_updater(app, logger):
    """
    Integrate SimpleUpdater with Flask application.

    Provides modern REST API endpoints:
    - GET /api/updates/check - Check for updates
    - POST /api/updates/apply - Apply updates
    - GET /api/updates/status - Get update status
    """
    updater = SimpleUpdater(logger=logger)

    @app.route("/api/updates/check", methods=["GET"])
    def check_updates():
        """Check for available updates."""
        result = updater.check_for_updates()
        status_code = 200 if result["status"] == "success" else 500
        return result, status_code

    @app.route("/api/updates/apply", methods=["POST"])
    def apply_updates():
        """Apply available updates."""
        try:
            success, message = updater.perform_update()

            if success:
                return {
                    "status": "success",
                    "message": message,
                    "restart_required": True,
                    "update_time": datetime.now().isoformat(),
                }
            else:
                return {"status": "error", "message": message}, 500

        except Exception as e:
            return {"status": "error", "message": f"Update failed: {str(e)}"}, 500

    @app.route("/api/updates/status", methods=["GET"])
    def update_status():
        """Get current update system status."""
        return {
            "status": "active",
            "system": "simple_git_updater",
            "version": updater.get_current_version(),
            "app_root": updater.app_root,
            "features": ["Git-based updates", "Webhook-ready", "Automatic service restart", "Version tracking"],
        }

    logger.info("✅ SimpleUpdater endpoints registered:")
    logger.info("   📋 GET /api/updates/check")
    logger.info("   🚀 POST /api/updates/apply")
    logger.info("   📊 GET /api/updates/status")

    return updater
