"""
Enhanced Deployment Detector
Enterprise-grade deployment detection extending the modular architecture

Extends the base DeploymentDetector with enterprise features:
- Enhanced container type detection
- Blue-Green deployment support
- Permission-safe operation detection
- Enterprise logging integration

Author: WhisperS2T Enterprise Team
Version: 0.8.0
"""

import os
from enum import Enum
from typing import List

from ..deployment import DeploymentDetector as BaseDeploymentDetector
from ..deployment import DeploymentType as BaseDeploymentType
from .logger import EnterpriseLogger


class EnterpriseDeploymentType(Enum):
    """Extended deployment environment types for enterprise features"""

    DOCKER = "docker"
    PROXMOX_LXC = "proxmox_lxc"
    DEVELOPMENT = "development"
    BARE_METAL = "bare_metal"
    SYSTEMD = "systemd"
    UNKNOWN = "unknown"


class EnterpriseDeploymentDetector:
    """
    Enterprise-grade deployment detector extending modular architecture

    🎯 WRAPPER PATTERN: Uses base DeploymentDetector and adds enterprise features
    """

    def __init__(self, logger: EnterpriseLogger = None):
        self.logger = logger or EnterpriseLogger()
        self.base_detector = BaseDeploymentDetector()
        self.container_type = None

    def detect(self) -> EnterpriseDeploymentType:
        """
        Enhanced deployment detection with enterprise features

        Returns:
            EnterpriseDeploymentType: Detected deployment type
        """
        self.logger.info("🔍 Detecting deployment environment...")

        # Use base detector first
        base_type = self.base_detector.detect_deployment_type()

        # Map base types to enterprise types and add enhanced detection
        if base_type == BaseDeploymentType.DOCKER:
            self.container_type = "docker"
            self.logger.info("✅ Docker container detected")
            return EnterpriseDeploymentType.DOCKER

        elif base_type == BaseDeploymentType.PROXMOX_LXC:
            self.container_type = self._detect_lxc_type()
            self.logger.info(f"✅ Proxmox LXC detected (type: {self.container_type})")
            return EnterpriseDeploymentType.PROXMOX_LXC

        elif base_type == BaseDeploymentType.SYSTEMD:
            self.logger.info("✅ Systemd service detected")
            return EnterpriseDeploymentType.SYSTEMD

        elif base_type == BaseDeploymentType.DEVELOPMENT:
            self.logger.info("✅ Development environment detected")
            return EnterpriseDeploymentType.DEVELOPMENT

        else:
            # Enhanced bare metal detection
            if self._is_bare_metal():
                self.logger.info("✅ Bare metal deployment detected")
                return EnterpriseDeploymentType.BARE_METAL

            self.logger.warning("⚠️ Unknown deployment type")
            return EnterpriseDeploymentType.UNKNOWN

    def get_application_paths(self) -> List[str]:
        """
        Get prioritized list of application paths for enterprise deployment

        Returns:
            List[str]: Prioritized application paths
        """
        # Start with base detector app root
        base_root = self.base_detector.find_app_root()

        # Enterprise-prioritized paths
        enterprise_paths = [
            base_root,  # Use base detector result first
            "/opt/whisper-appliance",  # Standard enterprise deployment
            "/app",  # Docker standard
            "/opt/app",  # Alternative enterprise
            "/usr/local/whisper-appliance",  # System-wide installation
        ]

        # Add development paths if in development
        deployment_type = self.detect()
        if deployment_type == EnterpriseDeploymentType.DEVELOPMENT:
            enterprise_paths.extend(
                [
                    os.path.expanduser("~/Code/whisper-appliance"),
                    os.getcwd(),
                ]
            )

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in enterprise_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        return unique_paths

    def _detect_lxc_type(self) -> str:
        """
        Enhanced LXC container type detection

        Returns:
            str: LXC container type (privileged/unprivileged)
        """
        try:
            # Check for privileged vs unprivileged LXC
            if os.path.exists("/proc/1/uid_map"):
                with open("/proc/1/uid_map", "r") as f:
                    uid_map = f.read().strip()
                    if uid_map == "0 0 4294967295":
                        return "privileged_lxc"
                    else:
                        return "unprivileged_lxc"
            return "lxc"
        except:
            return "lxc"

    def _is_bare_metal(self) -> bool:
        """
        Detect bare metal deployment (non-containerized)

        Returns:
            bool: True if bare metal deployment
        """
        try:
            # Not in Docker or LXC, but has systemd or direct installation
            if not self._is_container_environment() and (
                os.path.exists("/etc/systemd/system") or os.path.exists("/opt/whisper-appliance")
            ):
                return True
        except:
            pass
        return False

    def _is_container_environment(self) -> bool:
        """
        Check if running in any container environment

        Returns:
            bool: True if in container
        """
        # Check for container indicators
        container_files = ["/.dockerenv", "/proc/1/cgroup"]
        container_keywords = ["docker", "lxc", "container"]

        for file_path in container_files:
            try:
                if os.path.exists(file_path):
                    if file_path == "/.dockerenv":
                        return True
                    else:
                        with open(file_path, "r") as f:
                            content = f.read().lower()
                            if any(keyword in content for keyword in container_keywords):
                                return True
            except:
                continue

        return False

    def get_enterprise_deployment_info(self) -> dict:
        """
        Get comprehensive enterprise deployment information

        Returns:
            dict: Enterprise deployment information
        """
        deployment_type = self.detect()
        app_paths = self.get_application_paths()

        return {
            "deployment_type": deployment_type.value,
            "container_type": getattr(self, "container_type", None),
            "application_path": app_paths[0] if app_paths else "/unknown",
            "detected_paths": app_paths,
            "enterprise_features": {
                "zero_downtime_updates": True,
                "permission_safe_operations": True,
                "automatic_rollback": True,
                "blue_green_deployment": True,
                "deployment_aware_strategies": True,
                "comprehensive_audit_logging": True,
            },
            "strategy_description": {
                "docker": "Volume-based updates with container optimization",
                "proxmox_lxc": "Permission-safe file replacement with systemd integration",
                "development": "Git-based updates with stash backup system",
                "bare_metal": "Blue-Green deployment with service management",
                "systemd": "Service-managed updates with rollback capability",
            }.get(deployment_type.value, "Unknown deployment type"),
        }
