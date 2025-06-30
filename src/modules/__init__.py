"""
WhisperS2T Appliance - Modular Components
Enhanced modular architecture preserving all original features
"""

__version__ = "0.8.0"
__author__ = "WhisperS2T Team"

from .admin_panel import AdminPanel
from .api_docs import APIDocs

# Module exports
from .live_speech import LiveSpeechHandler
from .upload_handler import UploadHandler

__all__ = ["LiveSpeechHandler", "UploadHandler", "AdminPanel", "APIDocs"]
