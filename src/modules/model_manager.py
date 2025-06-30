"""
Model Manager Module
Handles Whisper model selection and management
Provides model switching functionality for Live Speech and Admin Panel
"""

import logging
import os
import threading
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages Whisper model loading and switching"""

    AVAILABLE_MODELS = {
        "tiny": {
            "name": "Tiny",
            "size": "~39 MB",
            "speed": "Fast",
            "quality": "Basic",
            "description": "Fastest processing, good for testing",
        },
        "base": {
            "name": "Base",
            "size": "~74 MB",
            "speed": "Fast",
            "quality": "Good",
            "description": "Balanced speed and accuracy (recommended)",
        },
        "small": {
            "name": "Small",
            "size": "~244 MB",
            "speed": "Medium",
            "quality": "Better",
            "description": "Better accuracy, moderate speed",
        },
        "medium": {
            "name": "Medium",
            "size": "~769 MB",
            "speed": "Slow",
            "quality": "High",
            "description": "High accuracy, slower processing",
        },
        "large": {
            "name": "Large",
            "size": "~1550 MB",
            "speed": "Very Slow",
            "quality": "Excellent",
            "description": "Best accuracy, slowest processing",
        },
    }

    def __init__(self):
        self.current_model = None
        self.current_model_name = "base"  # Default model
        self.model_loading = False
        self.model_load_lock = threading.Lock()
        self.whisper_available = False
        self.downloaded_models = set()  # Track which models are actually downloaded

        # Try to import whisper
        try:
            import whisper

            self.whisper = whisper
            self.whisper_available = True
            logger.info("✅ Whisper library available")

            # Check which models are already downloaded
            self._check_downloaded_models()
        except ImportError:
            self.whisper = None
            self.whisper_available = False
            logger.warning("⚠️ Whisper library not available - install with: pip install openai-whisper")

    def _check_downloaded_models(self):
        """Check which models are already downloaded to avoid re-downloading"""
        if not self.whisper_available:
            return

        import os

        try:
            # Whisper stores models in ~/.cache/whisper/
            whisper_cache = os.path.expanduser("~/.cache/whisper/")
            if os.path.exists(whisper_cache):
                for model_name in self.AVAILABLE_MODELS.keys():
                    # Check for .pt files that match model names
                    model_files = [f for f in os.listdir(whisper_cache) if f.startswith(model_name) and f.endswith(".pt")]
                    if model_files:
                        self.downloaded_models.add(model_name)
                        logger.info(f"📦 Found downloaded model: {model_name}")

            logger.info(f"📊 Downloaded models: {list(self.downloaded_models) if self.downloaded_models else 'None'}")
        except Exception as e:
            logger.warning(f"Could not check downloaded models: {e}")

    def load_model(self, model_name: str = "base") -> bool:
        """Load a Whisper model"""
        if not self.whisper_available:
            logger.error("Whisper library not available")
            return False

        if model_name not in self.AVAILABLE_MODELS:
            logger.error(f"Invalid model name: {model_name}")
            return False

        with self.model_load_lock:
            if self.model_loading:
                logger.warning("Model loading already in progress")
                return False

            try:
                self.model_loading = True
                logger.info(f"Loading Whisper model: {model_name}")

                # Load the model
                self.current_model = self.whisper.load_model(model_name)
                self.current_model_name = model_name

                logger.info(f"Successfully loaded model: {model_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                return False
            finally:
                self.model_loading = False

    def get_current_model(self):
        """Get the currently loaded model"""
        return self.current_model

    def get_current_model_name(self) -> str:
        """Get the name of the currently loaded model"""
        return self.current_model_name

    def get_available_models(self) -> Dict:
        """Get list of available models with metadata"""
        return self.AVAILABLE_MODELS

    def is_model_loading(self) -> bool:
        """Check if a model is currently being loaded"""
        return self.model_loading

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model"""
        return self.AVAILABLE_MODELS.get(model_name)

    def transcribe(self, audio_path: str, **kwargs) -> Optional[Dict]:
        """Transcribe audio using the current model"""
        if not self.current_model:
            logger.error("No model loaded")
            return None

        try:
            logger.info(f"Transcribing with model: {self.current_model_name}")
            result = self.current_model.transcribe(audio_path, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    def get_status(self) -> Dict:
        """Get current model manager status"""
        return {
            "whisper_available": self.whisper_available,
            "current_model": self.current_model_name,
            "model_loaded": self.current_model is not None,
            "model_loading": self.model_loading,
            "available_models": list(self.AVAILABLE_MODELS.keys()),
            "downloaded_models": list(self.downloaded_models),
            "models_needing_download": [m for m in self.AVAILABLE_MODELS.keys() if m not in self.downloaded_models],
        }

    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if a specific model is downloaded"""
        return model_name in self.downloaded_models

    def get_download_status(self) -> Dict:
        """Get detailed download status for all models"""
        status = {}
        for model_name, model_info in self.AVAILABLE_MODELS.items():
            status[model_name] = {
                "downloaded": model_name in self.downloaded_models,
                "info": model_info,
                "status": "Downloaded" if model_name in self.downloaded_models else "Needs Download",
            }
        return status
