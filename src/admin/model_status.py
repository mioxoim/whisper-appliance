"""
Model Status Manager for WhisperAppliance Admin
Handles model download status and management
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelStatusManager:
    """Manages Whisper model status and information"""
    
    # Available Whisper models with metadata
    AVAILABLE_MODELS = {
        "tiny": {
            "name": "Tiny",
            "size": "39 MB",
            "description": "Fastest, least accurate",
            "parameters": "39M",
            "languages": "Multi",
            "speed": "~32x"
        },
        "base": {
            "name": "Base",
            "size": "74 MB",
            "description": "Fast, good for English",
            "parameters": "74M",
            "languages": "Multi",
            "speed": "~16x"
        },
        "small": {
            "name": "Small",
            "size": "244 MB",
            "description": "Balanced speed/accuracy",
            "parameters": "244M",
            "languages": "Multi",
            "speed": "~6x"
        },
        "medium": {
            "name": "Medium",
            "size": "769 MB",
            "description": "Good accuracy, slower",
            "parameters": "769M",
            "languages": "Multi",
            "speed": "~2x"
        },
        "large": {
            "name": "Large",
            "size": "1550 MB",
            "description": "Best accuracy, slowest",
            "parameters": "1550M",
            "languages": "Multi",
            "speed": "~1x"
        },
        "large-v2": {
            "name": "Large V2",
            "size": "1550 MB",
            "description": "Latest large model",
            "parameters": "1550M",
            "languages": "Multi",
            "speed": "~1x"
        },
        "large-v3": {
            "name": "Large V3",
            "size": "1550 MB",
            "description": "Newest, most accurate",
            "parameters": "1550M",
            "languages": "Multi",
            "speed": "~1x"
        }
    }
    
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.models_dir = Path.home() / ".cache" / "whisper"
        
    def get_downloaded_models(self):
        """Get list of downloaded models"""
        downloaded = []
        
        if self.models_dir.exists():
            for model_id in self.AVAILABLE_MODELS:
                # Check for model file
                model_file = self.models_dir / f"{model_id}.pt"
                if model_file.exists():
                    downloaded.append(model_id)
        
        return downloaded
    
    def get_model_info(self):
        """Get basic model information"""
        downloaded = self.get_downloaded_models()
        current_model = None
        
        if self.model_manager and hasattr(self.model_manager, 'current_model'):
            current_model = self.model_manager.current_model
        
        return {
            "available": self.AVAILABLE_MODELS,
            "downloaded": downloaded,
            "current": current_model,
            "total_available": len(self.AVAILABLE_MODELS),
            "total_downloaded": len(downloaded)
        }
    
    def get_detailed_model_info(self):
        """Get detailed model information with download status"""
        downloaded = self.get_downloaded_models()
        current_model = None
        
        if self.model_manager and hasattr(self.model_manager, 'current_model'):
            current_model = self.model_manager.current_model
        
        models = []
        for model_id, info in self.AVAILABLE_MODELS.items():
            model_data = {
                "id": model_id,
                "is_downloaded": model_id in downloaded,
                "is_current": model_id == current_model,
                **info
            }
            
            # Add file size if downloaded
            if model_data["is_downloaded"]:
                model_file = self.models_dir / f"{model_id}.pt"
                if model_file.exists():
                    size_mb = model_file.stat().st_size / (1024 * 1024)
                    model_data["actual_size"] = f"{size_mb:.1f} MB"
            
            models.append(model_data)
        
        return models
    
    def get_model_status(self):
        """Get model status for API"""
        return {
            "available": self.AVAILABLE_MODELS,
            "downloaded": self.get_downloaded_models(),
            "current": self.model_manager.current_model if self.model_manager else None
        }
