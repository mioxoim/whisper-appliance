"""
Shopware-inspired Maintenance Mode Manager
Enterprise-level maintenance mode system for WhisperS2T Appliance

Based on Shopware's MaintenanceModeResolver logic but adapted for Python/Flask
Provides robust maintenance mode handling during updates with IP whitelisting
"""

import ipaddress
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MaintenanceModeManager:
    """
    Shopware-inspired maintenance mode manager

    Features:
    - Automatic maintenance mode during updates
    - IP whitelisting for admin access
    - Graceful maintenance page display
    - Thread-safe operation
    - Enterprise-level robustness
    """

    def __init__(self, app_root: str = None):
        # Auto-detect application root if not provided
        if app_root is None:
            app_root = self._find_app_root()

        self.app_root = app_root
        self.maintenance_file = os.path.join(app_root, ".maintenance_mode")
        self.config_file = os.path.join(app_root, "maintenance_config.json")
        self._lock = threading.Lock()

        # Default configuration (Shopware-inspired)
        self.default_config = {
            "enabled": False,
            "ip_whitelist": ["127.0.0.1", "::1", "localhost"],
            "message": "Our system is currently undergoing maintenance. We'll be back very soon. Sorry for any inconvenience.",
            "title": "Maintenance Mode",
            "auto_mode": False,  # Set by update system
            "started_at": None,
            "estimated_end": None,
            "admin_email": None,
        }

        logger.info(f"MaintenanceModeManager initialized with app_root: {self.app_root}")

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
        """
        Enable maintenance mode (Shopware-style)

        Args:
            message: Custom maintenance message
            ip_whitelist: List of whitelisted IP addresses
            auto_mode: True if enabled by update system
            estimated_duration_minutes: Estimated maintenance duration

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                config = self._load_config()

                # Update configuration
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

                # Save configuration
                self._save_config(config)

                # Create maintenance file (Shopware-style marker)
                with open(self.maintenance_file, "w") as f:
                    f.write(
                        json.dumps(
                            {"enabled_at": datetime.now().isoformat(), "auto_mode": auto_mode, "pid": os.getpid()}, indent=2
                        )
                    )

                logger.info(f"Maintenance mode enabled (auto_mode: {auto_mode})")
                return True

        except Exception as e:
            logger.error(f"Failed to enable maintenance mode: {e}")
            return False

    def disable_maintenance_mode(self) -> bool:
        """
        Disable maintenance mode

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                config = self._load_config()
                config["enabled"] = False
                config["auto_mode"] = False
                config["started_at"] = None
                config["estimated_end"] = None

                self._save_config(config)

                # Remove maintenance file
                if os.path.exists(self.maintenance_file):
                    os.remove(self.maintenance_file)

                logger.info("Maintenance mode disabled")
                return True

        except Exception as e:
            logger.error(f"Failed to disable maintenance mode: {e}")
            return False

    def is_maintenance_mode_active(self) -> bool:
        """
        Check if maintenance mode is active

        Returns:
            bool: True if maintenance mode is active
        """
        try:
            # Fast check: maintenance file exists
            if not os.path.exists(self.maintenance_file):
                return False

            config = self._load_config()
            return config.get("enabled", False)

        except Exception as e:
            logger.error(f"Failed to check maintenance mode status: {e}")
            return False

    def is_maintenance_request(self, client_ip: str, user_agent: str = None) -> bool:
        """
        Shopware-inspired maintenance request check

        Args:
            client_ip: Client IP address
            user_agent: User agent string (optional)

        Returns:
            bool: True if request should see maintenance page
        """
        try:
            # If maintenance mode is not active, allow all requests
            if not self.is_maintenance_mode_active():
                return False

            # Check IP whitelist (case-insensitive for IPv6)
            if self._is_ip_whitelisted(client_ip):
                return False

            # Request should see maintenance page
            return True

        except Exception as e:
            logger.error(f"Failed to check maintenance request: {e}")
            # Fail-safe: if error occurs, don't block access
            return False

    def _is_ip_whitelisted(self, client_ip: str) -> bool:
        """
        Check if IP is whitelisted (Shopware-style with IPv6 case-insensitivity fix)

        Args:
            client_ip: Client IP address to check

        Returns:
            bool: True if IP is whitelisted
        """
        try:
            config = self._load_config()
            whitelist = config.get("ip_whitelist", [])

            # Normalize client IP
            client_ip_normalized = self._normalize_ip(client_ip)

            for whitelisted_ip in whitelist:
                whitelisted_ip_normalized = self._normalize_ip(whitelisted_ip)

                # Direct comparison
                if client_ip_normalized == whitelisted_ip_normalized:
                    return True

                # Check if it's a network range
                try:
                    network = ipaddress.ip_network(whitelisted_ip_normalized, strict=False)
                    if ipaddress.ip_address(client_ip_normalized) in network:
                        return True
                except (ipaddress.AddressValueError, ValueError):
                    continue

            return False

        except Exception as e:
            logger.error(f"IP whitelist check failed: {e}")
            # Fail-safe: if error occurs, deny access
            return False

    def _normalize_ip(self, ip: str) -> str:
        """
        Normalize IP address (fix Shopware's IPv6 case-sensitivity issue)

        Args:
            ip: IP address to normalize

        Returns:
            str: Normalized IP address
        """
        try:
            # Handle common localhost variations
            if ip in ["localhost", "::1", "127.0.0.1"]:
                return "127.0.0.1"

            # Parse and normalize the IP
            ip_obj = ipaddress.ip_address(ip)

            # Return compressed format for IPv6, standard for IPv4
            if isinstance(ip_obj, ipaddress.IPv6Address):
                return str(ip_obj.compressed).lower()
            else:
                return str(ip_obj)

        except ipaddress.AddressValueError:
            # If IP parsing fails, return original (could be hostname)
            return ip.lower()

    def get_maintenance_info(self) -> Dict:
        """
        Get current maintenance mode information

        Returns:
            Dict: Maintenance mode status and configuration
        """
        try:
            config = self._load_config()

            # Calculate duration if maintenance is active
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
            logger.error(f"Failed to get maintenance info: {e}")
            return {"enabled": False, "error": str(e)}

    def add_ip_to_whitelist(self, ip: str) -> bool:
        """
        Add IP to whitelist

        Args:
            ip: IP address to add

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                config = self._load_config()
                whitelist = config.get("ip_whitelist", [])

                normalized_ip = self._normalize_ip(ip)
                if normalized_ip not in [self._normalize_ip(wip) for wip in whitelist]:
                    whitelist.append(ip)
                    config["ip_whitelist"] = whitelist
                    self._save_config(config)
                    logger.info(f"Added IP {ip} to whitelist")
                    return True

                return False  # Already in whitelist

        except Exception as e:
            logger.error(f"Failed to add IP to whitelist: {e}")
            return False

    def remove_ip_from_whitelist(self, ip: str) -> bool:
        """
        Remove IP from whitelist

        Args:
            ip: IP address to remove

        Returns:
            bool: Success status
        """
        try:
            with self._lock:
                config = self._load_config()
                whitelist = config.get("ip_whitelist", [])

                normalized_ip = self._normalize_ip(ip)
                original_length = len(whitelist)

                # Remove matching IPs (normalized comparison)
                whitelist = [wip for wip in whitelist if self._normalize_ip(wip) != normalized_ip]

                if len(whitelist) < original_length:
                    config["ip_whitelist"] = whitelist
                    self._save_config(config)
                    logger.info(f"Removed IP {ip} from whitelist")
                    return True

                return False  # Not found in whitelist

        except Exception as e:
            logger.error(f"Failed to remove IP from whitelist: {e}")
            return False

    def _load_config(self) -> Dict:
        """Load maintenance configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config = json.load(f)

                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                return self.default_config.copy()

        except Exception as e:
            logger.error(f"Failed to load maintenance config: {e}")
            return self.default_config.copy()

    def _save_config(self, config: Dict) -> bool:
        """Save maintenance configuration"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            return True

        except Exception as e:
            logger.error(f"Failed to save maintenance config: {e}")
            return False

    # Context manager support for automatic maintenance mode
    def __enter__(self):
        """Enter maintenance mode context"""
        self.enable_maintenance_mode(auto_mode=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit maintenance mode context"""
        self.disable_maintenance_mode()


# Shopware-inspired Flask middleware for maintenance mode
class MaintenanceModeMiddleware:
    """
    Flask middleware for handling maintenance mode requests

    Usage:
        app.wsgi_app = MaintenanceModeMiddleware(app.wsgi_app, maintenance_manager)
    """

    def __init__(self, wsgi_app, maintenance_manager: MaintenanceModeManager):
        self.wsgi_app = wsgi_app
        self.maintenance_manager = maintenance_manager

    def __call__(self, environ, start_response):
        # Get client IP
        client_ip = self._get_client_ip(environ)
        user_agent = environ.get("HTTP_USER_AGENT", "")

        # Check if request should see maintenance page
        if self.maintenance_manager.is_maintenance_request(client_ip, user_agent):
            return self._maintenance_response(environ, start_response)

        # Continue with normal request
        return self.wsgi_app(environ, start_response)

    def _get_client_ip(self, environ) -> str:
        """Extract client IP from WSGI environ"""
        # Check for forwarded headers (common in proxy setups)
        forwarded_ips = [
            environ.get("HTTP_X_FORWARDED_FOR"),
            environ.get("HTTP_X_REAL_IP"),
            environ.get("HTTP_CF_CONNECTING_IP"),  # Cloudflare
            environ.get("REMOTE_ADDR"),
        ]

        for ip in forwarded_ips:
            if ip:
                # Take first IP if comma-separated
                return ip.split(",")[0].strip()

        return "127.0.0.1"  # Fallback

    def _maintenance_response(self, environ, start_response):
        """Generate maintenance mode response"""
        maintenance_info = self.maintenance_manager.get_maintenance_info()

        # Simple HTML maintenance page (Shopware-inspired)
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{maintenance_info.get('title', 'Maintenance Mode')}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .maintenance-container {{
                    background: white;
                    border-radius: 15px;
                    padding: 60px 40px;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 20px;
                }}
                .maintenance-icon {{
                    font-size: 72px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                    font-size: 28px;
                }}
                p {{
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 30px;
                    font-size: 16px;
                }}
                .eta {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    color: #495057;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="maintenance-container">
                <div class="maintenance-icon">🔧</div>
                <h1>{maintenance_info.get('title', 'Maintenance Mode')}</h1>
                <p>{maintenance_info.get('message', 'Our system is currently undergoing maintenance.')}</p>
                {f'<div class="eta">Estimated completion: {maintenance_info["estimated_end"]}</div>' if maintenance_info.get("estimated_end") else ''}
            </div>
        </body>
        </html>
        """

        response_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(html.encode("utf-8")))),
            ("Cache-Control", "no-cache, no-store, must-revalidate"),
            ("Pragma", "no-cache"),
            ("Expires", "0"),
        ]

        start_response("503 Service Unavailable", response_headers)
        return [html.encode("utf-8")]
