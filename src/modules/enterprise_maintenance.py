"""
Shopware-inspired Maintenance Mode Manager - Additive Implementation
Enterprise-level maintenance mode system for WhisperS2T Appliance

🎯 ADDITIVE APPROACH: Adds enterprise features WITHOUT removing legacy functionality
"""

import ipaddress
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EnterpriseMaintenanceManager:
    """
    Shopware-inspired maintenance mode manager - Enterprise Edition

    ✅ ADDITIVE IMPLEMENTATION:
    - Coexists with existing update system
    - Adds enterprise features without breaking legacy
    - Shopware-style maintenance mode with IP whitelisting
    """

    def __init__(self, app_root: str = None):
        if app_root is None:
            app_root = self._find_app_root()

        self.app_root = app_root
        self.maintenance_file = os.path.join(app_root, ".enterprise_maintenance")
        self.config_file = os.path.join(app_root, "enterprise_maintenance_config.json")
        self._lock = threading.Lock()

        # Default configuration (Shopware-inspired)
        self.default_config = {
            "enabled": False,
            "ip_whitelist": ["127.0.0.1", "::1", "localhost"],
            "message": "🚀 Enterprise maintenance in progress. We'll be back shortly.",
            "title": "Enterprise Maintenance Mode",
            "auto_mode": False,
            "started_at": None,
            "estimated_end": None,
            "admin_email": None,
        }

        logger.info(f"EnterpriseMaintenanceManager initialized with app_root: {self.app_root}")

    def _find_app_root(self) -> str:
        """Find application root directory"""
        # Try current working directory first
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "src", "main.py")):
            return cwd

        # Try standard deployment paths
        deployment_paths = [
            "/opt/whisper-appliance",
            "/app",
            "/opt/app",
            "/workspace",
        ]

        for path in deployment_paths:
            if os.path.exists(os.path.join(path, "src", "main.py")):
                return path

        # Fallback to parent directory of this script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def enable_maintenance_mode(
        self,
        message: str = None,
        ip_whitelist: List[str] = None,
        auto_mode: bool = False,
        estimated_duration_minutes: int = None,
    ) -> bool:
        """Enable enterprise maintenance mode"""
        try:
            with self._lock:
                config = self._load_config()

                config["enabled"] = True
                config["started_at"] = datetime.now().isoformat()
                config["auto_mode"] = auto_mode

                if message:
                    config["message"] = message

                if ip_whitelist:
                    config["ip_whitelist"] = ip_whitelist

                if estimated_duration_minutes:
                    from datetime import timedelta

                    end_time = datetime.now() + timedelta(minutes=estimated_duration_minutes)
                    config["estimated_end"] = end_time.isoformat()

                self._save_config(config)

                # Create maintenance file
                with open(self.maintenance_file, "w") as f:
                    f.write(
                        json.dumps(
                            {"enabled_at": datetime.now().isoformat(), "auto_mode": auto_mode, "pid": os.getpid()}, indent=2
                        )
                    )

                logger.info(f"Enterprise maintenance mode enabled (auto_mode: {auto_mode})")
                return True

        except Exception as e:
            logger.error(f"Failed to enable enterprise maintenance mode: {e}")
            return False

    def disable_maintenance_mode(self) -> bool:
        """Disable enterprise maintenance mode"""
        try:
            with self._lock:
                config = self._load_config()
                config["enabled"] = False
                config["auto_mode"] = False
                config["started_at"] = None
                config["estimated_end"] = None

                self._save_config(config)

                if os.path.exists(self.maintenance_file):
                    os.remove(self.maintenance_file)

                logger.info("Enterprise maintenance mode disabled")
                return True

        except Exception as e:
            logger.error(f"Failed to disable enterprise maintenance mode: {e}")
            return False

    def is_maintenance_mode_active(self) -> bool:
        """Check if enterprise maintenance mode is active"""
        try:
            if not os.path.exists(self.maintenance_file):
                return False

            config = self._load_config()
            return config.get("enabled", False)

        except Exception as e:
            logger.error(f"Failed to check enterprise maintenance mode status: {e}")
            return False

    def get_maintenance_info(self) -> Dict:
        """Get enterprise maintenance mode information"""
        try:
            config = self._load_config()

            duration_minutes = None
            if config.get("started_at"):
                start_time = datetime.fromisoformat(config["started_at"])
                duration_minutes = (datetime.now() - start_time).total_seconds() / 60

            return {
                "enabled": config.get("enabled", False),
                "auto_mode": config.get("auto_mode", False),
                "message": config.get("message", self.default_config["message"]),
                "title": config.get("title", self.default_config["title"]),
                "started_at": config.get("started_at"),
                "estimated_end": config.get("estimated_end"),
                "duration_minutes": round(duration_minutes) if duration_minutes else None,
                "ip_whitelist_count": len(config.get("ip_whitelist", [])),
                "admin_email": config.get("admin_email"),
            }

        except Exception as e:
            logger.error(f"Failed to get enterprise maintenance info: {e}")
            return {"enabled": False, "error": str(e)}

    def _load_config(self) -> Dict:
        """Load enterprise maintenance configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)

                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                return self.default_config.copy()

        except Exception as e:
            logger.error(f"Failed to load enterprise maintenance config: {e}")
            return self.default_config.copy()

    def _save_config(self, config: Dict) -> bool:
        """Save enterprise maintenance configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            return True

        except Exception as e:
            logger.error(f"Failed to save enterprise maintenance config: {e}")
            return False
