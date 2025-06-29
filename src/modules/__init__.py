"""
WhisperS2T Appliance - Modular Components
Enhanced modular architecture preserving all original features
"""

__version__ = "0.7.0"
__author__ = "WhisperS2T Team"

# Module exports
from .live_speech import LiveSpeechHandler
from .upload_handler import UploadHandler  
from .admin_panel import AdminPanel
from .api_docs import APIDocs

__all__ = [
    'LiveSpeechHandler',
    'UploadHandler', 
    'AdminPanel',
    'APIDocs'
]
