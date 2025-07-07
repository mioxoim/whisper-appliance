"""
Update System Module
Git-based update management for Whisper Appliance
"""

from .api import create_update_endpoints
from .manager import UpdateManager

__all__ = ["UpdateManager", "create_update_endpoints"]
