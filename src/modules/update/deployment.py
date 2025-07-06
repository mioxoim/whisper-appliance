"""
Deployment Detection
Automatically detect WhisperS2T deployment environment and paths
"""

import logging
import os
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DeploymentType(Enum):
    """Deployment environment types"""

    DEVELOPMENT = "development"
    DOCKER = "docker"
    PROXMOX_LXC = "proxmox_lxc"
    SYSTEMD = "systemd"
    UNKNOWN = "unknown"


class DeploymentDetector:
    """
    Professional deployment environment detection
    """

    def __init__(self):
        self.detection_cache = None

    def detect_deployment_type(self) -> DeploymentType:
        """
        Detect the current deployment environment

        Returns:
            DeploymentType: Detected deployment type
        """
        if self.detection_cache is not None:
            return self.detection_cache

        # Check for Docker environment
        if self._is_docker_environment():
            self.detection_cache = DeploymentType.DOCKER
            return self.detection_cache

        # Check for Proxmox LXC environment
        if self._is_proxmox_lxc_environment():
            self.detection_cache = DeploymentType.PROXMOX_LXC
            return self.detection_cache

        # Check for systemd service environment
        if self._is_systemd_environment():
            self.detection_cache = DeploymentType.SYSTEMD
            return self.detection_cache

        # Check for development environment
        if self._is_development_environment():
            self.detection_cache = DeploymentType.DEVELOPMENT
            return self.detection_cache

        self.detection_cache = DeploymentType.UNKNOWN
        return self.detection_cache

    def find_app_root(self) -> str:
        """
        Find application root directory based on deployment type

        Returns:
            str: Application root path
        """
        # Try to find git repository root first
        try:
            result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                git_root = result.stdout.strip()
                if os.path.exists(os.path.join(git_root, "src", "main.py")):
                    return git_root
        except:
            pass

        # Deployment-specific paths
        deployment_type = self.detect_deployment_type()

        if deployment_type == DeploymentType.DOCKER:
            fallback_paths = ["/app", "/opt/app", "/workspace"]
        elif deployment_type == DeploymentType.PROXMOX_LXC:
            fallback_paths = ["/opt/whisper-appliance", "/opt/app", "/app"]
        elif deployment_type == DeploymentType.SYSTEMD:
            fallback_paths = ["/opt/whisper-appliance", "/usr/local/whisper-appliance", "/app"]
        else:  # DEVELOPMENT or UNKNOWN
            fallback_paths = [
                os.path.expanduser("~/Code/whisper-appliance"),
                "/opt/whisper-appliance",
                "/app",
                "/opt/app",
                os.getcwd(),
            ]

        # Check each path for main.py
        for path in fallback_paths:
            if os.path.exists(os.path.join(path, "src", "main.py")):
                return path

        # Last resort
        return os.getcwd()

    def _is_docker_environment(self) -> bool:
        """Check if running in Docker container"""
        try:
            # Check for .dockerenv file
            if os.path.exists("/.dockerenv"):
                return True

            # Check cgroup for docker
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if "docker" in content:
                    return True
        except:
            pass

        return False

    def _is_proxmox_lxc_environment(self) -> bool:
        """Check if running in Proxmox LXC container"""
        try:
            # Check for LXC-specific indicators
            with open("/proc/1/environ", "rb") as f:
                environ = f.read().decode("utf-8", errors="ignore")
                if "container=lxc" in environ:
                    return True

            # Check for LXC in cgroup
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if "lxc" in content:
                    return True

            # Check for typical LXC mount points
            if os.path.exists("/dev/lxd") or os.path.exists("/run/lxcfs"):
                return True
        except:
            pass

        return False

    def _is_systemd_environment(self) -> bool:
        """Check if running as systemd service"""
        try:
            # Check if systemd is available and we're running as a service
            if os.path.exists("/run/systemd/system"):
                # Check if current process is managed by systemd
                with open("/proc/1/comm", "r") as f:
                    if "systemd" in f.read():
                        return True

                # Check for systemd-specific environment variables
                if "INVOCATION_ID" in os.environ:
                    return True
        except:
            pass

        return False

    def _is_development_environment(self) -> bool:
        """Check if running in development environment"""
        try:
            # Check for development indicators
            current_path = os.getcwd()

            # Check for development paths
            dev_indicators = ["Code/whisper-appliance", "/home/commander", "development", "dev", ".git"]

            for indicator in dev_indicators:
                if indicator in current_path:
                    return True

            # Check for git repository
            if os.path.exists(".git"):
                return True

        except:
            pass

        return False

    def get_deployment_info(self) -> dict:
        """
        Get comprehensive deployment information

        Returns:
            dict: Deployment information
        """
        deployment_type = self.detect_deployment_type()
        app_root = self.find_app_root()

        info = {
            "deployment_type": deployment_type.value,
            "app_root": app_root,
            "detected_at": os.getcwd(),
            "environment_details": {},
        }

        # Add type-specific details
        if deployment_type == DeploymentType.DOCKER:
            info["environment_details"]["container_type"] = "docker"
        elif deployment_type == DeploymentType.PROXMOX_LXC:
            info["environment_details"]["container_type"] = "lxc"
            info["environment_details"]["virtualization"] = "proxmox"
        elif deployment_type == DeploymentType.SYSTEMD:
            info["environment_details"]["service_manager"] = "systemd"
        elif deployment_type == DeploymentType.DEVELOPMENT:
            info["environment_details"]["environment"] = "development"

        return info
