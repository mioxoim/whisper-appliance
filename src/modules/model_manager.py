"""
Model Manager Module
Handles Whisper model selection and management
Provides model switching functionality for Live Speech and Admin Panel
"""

import logging
import os
import threading
import hashlib # Added for SHA256 checksum
import requests # Added for downloading files
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
            "url": "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
            "sha256": "65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9"
        },
        "base": {
            "name": "Base",
            "size": "~74 MB",
            "speed": "Fast",
            "quality": "Good",
            "description": "Balanced speed and accuracy (recommended)",
            "url": "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
            "sha256": "ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e"
        },
        "small": {
            "name": "Small",
            "size": "~244 MB",
            "speed": "Medium",
            "quality": "Better",
            "description": "Better accuracy, moderate speed",
            "url": "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
            "sha256": "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794"
        },
        "medium": {
            "name": "Medium",
            "size": "~769 MB",
            "speed": "Slow",
            "quality": "High",
            "description": "High accuracy, slower processing",
            "url": "https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt",
            "sha256": "345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1"
        },
        "large": { # This corresponds to large-v3 in openai-whisper
            "name": "Large",
            "size": "~1550 MB",
            "speed": "Very Slow",
            "quality": "Excellent",
            "description": "Best accuracy, slowest processing (uses large-v3)",
            "url": "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt",
            "sha256": "e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb"
        },
        # TODO: Consider adding large-v1 and large-v2 if differentiation is needed
        # "large-v1": {
        #     "name": "Large v1",
        #     "size": "~1550 MB",
        #     "speed": "Very Slow",
        #     "quality": "Excellent",
        #     "description": "Original large model",
        #     "url": "https://openaipublic.azureedge.net/main/whisper/models/e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a/large-v1.pt",
        #     "sha256": "e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a"
        # },
        # "large-v2": {
        #     "name": "Large v2",
        #     "size": "~1550 MB",
        #     "speed": "Very Slow",
        #     "quality": "Excellent",
        #     "description": "Improved large model",
        #     "url": "https://openaipublic.azureedge.net/main/whisper/models/81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/large-v2.pt",
        #     "sha256": "81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524"
        # }
    }

    def __init__(self):
        self.current_model = None
        self.current_model_name = "base"  # Default model
        self.model_loading = False
        self.model_load_lock = threading.Lock()
        self.whisper_available = False
        self.downloaded_models = set()  # Track which models are actually downloaded
        self.download_progress = {}  # Stores progress of ongoing downloads

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

    def get_model(self):
        """Get the current loaded model instance"""
        return self.current_model

    def get_status(self) -> Dict:
        """Get current model manager status, including detailed available models."""
        # This structure is more aligned with what admin-models.js expects for availableModels
        return {
            "whisper_available": self.whisper_available,
            "current_model_name": self.get_current_model_name(), # Changed from current_model to current_model_name for clarity
            "model_loaded": self.current_model is not None,
            "model_loading": self.model_loading,
            "available_models_info": self.get_available_models(), # Provides full details
            "downloaded_model_ids": list(self.downloaded_models), # List of IDs
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

    def _get_model_cache_dir(self):
        """Gets the Whisper model cache directory."""
        return os.path.join(os.path.expanduser("~"), ".cache", "whisper")

    def _perform_download(self, model_id: str):
        """Performs the actual download of a model file."""
        if model_id not in self.AVAILABLE_MODELS:
            logger.error(f"Attempted to download unknown model: {model_id}")
            self.download_progress[model_id] = {
                "status": "failed",
                "error_message": "Unknown model ID",
                "progress": 0,
                "downloaded_size": 0,
                "total_size": 0,
                "cancel_requested": False,
            }
            return

        model_info = self.AVAILABLE_MODELS[model_id]
        url = model_info["url"]
        expected_sha256 = model_info["sha256"]

        models_dir = self._get_model_cache_dir()
        os.makedirs(models_dir, exist_ok=True)

        # Use a temporary filename during download
        base_filename = f"{model_id}.pt"
        download_target_path = os.path.join(models_dir, base_filename)
        temp_download_path = download_target_path + ".tmp"

        self.download_progress[model_id] = {
            "status": "downloading",
            "error_message": "",
            "progress": 0,
            "downloaded_size": 0,
            "total_size": 0, # Will be updated once headers are received
            "cancel_requested": False,
        }

        try:
            logger.info(f"Starting download for model {model_id} from {url}")
            response = requests.get(url, stream=True, timeout=30) # Increased timeout
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            self.download_progress[model_id]["total_size"] = total_size
            downloaded_size = 0

            hasher = hashlib.sha256()

            with open(temp_download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.download_progress[model_id].get("cancel_requested", False):
                        logger.info(f"Download cancelled for model {model_id}")
                        self.download_progress[model_id]["status"] = "cancelled"
                        if os.path.exists(temp_download_path):
                            os.remove(temp_download_path)
                        return

                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded_size += len(chunk)
                    self.download_progress[model_id]["downloaded_size"] = downloaded_size
                    if total_size > 0:
                        self.download_progress[model_id]["progress"] = int((downloaded_size / total_size) * 100)

            calculated_sha256 = hasher.hexdigest()
            if calculated_sha256 != expected_sha256:
                self.download_progress[model_id]["status"] = "failed"
                self.download_progress[model_id]["error_message"] = f"SHA256 checksum mismatch. Expected {expected_sha256}, got {calculated_sha256}"
                logger.error(self.download_progress[model_id]["error_message"])
                if os.path.exists(temp_download_path):
                    os.remove(temp_download_path)
                return

            # Download successful and checksum matches, move temp file to final destination
            os.rename(temp_download_path, download_target_path)
            self.download_progress[model_id]["status"] = "completed"
            self.download_progress[model_id]["progress"] = 100
            self.downloaded_models.add(model_id)
            logger.info(f"Model {model_id} downloaded and verified successfully.")

        except requests.exceptions.RequestException as e:
            error_msg = f"Download failed for model {model_id}: {str(e)}"
            logger.error(error_msg)
            self.download_progress[model_id]["status"] = "failed"
            self.download_progress[model_id]["error_message"] = str(e)
            if os.path.exists(temp_download_path):
                os.remove(temp_download_path)
        except Exception as e:
            error_msg = f"An unexpected error occurred during download of {model_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.download_progress[model_id]["status"] = "failed"
            self.download_progress[model_id]["error_message"] = "An unexpected error occurred."
            if os.path.exists(temp_download_path):
                os.remove(temp_download_path)
        finally:
            # If download was successful, the entry in download_progress will be 'completed'.
            # If failed or cancelled, it will reflect that.
            # We might want to remove completed/failed entries after some time or leave them for history.
            pass


    def start_download_model(self, model_id: str) -> bool:
        """Initiates download of a model in a background thread."""
        if model_id not in self.AVAILABLE_MODELS:
            logger.error(f"Attempted to download unknown model: {model_id}")
            return False

        if self.is_model_downloaded(model_id):
            logger.info(f"Model {model_id} is already downloaded.")
            # Optionally update progress to completed if it's not already reflected
            self.download_progress[model_id] = {
                "status": "completed", "progress": 100,
                "downloaded_size": os.path.getsize(os.path.join(self._get_model_cache_dir(), f"{model_id}.pt")) if os.path.exists(os.path.join(self._get_model_cache_dir(), f"{model_id}.pt")) else 0,
                "total_size": os.path.getsize(os.path.join(self._get_model_cache_dir(), f"{model_id}.pt")) if os.path.exists(os.path.join(self._get_model_cache_dir(), f"{model_id}.pt")) else 0,
                "error_message": "", "cancel_requested": False
            }
            return True

        if model_id in self.download_progress and self.download_progress[model_id]["status"] == "downloading":
            logger.warning(f"Download for model {model_id} is already in progress.")
            return True # Indicate that the process is active

        # Initialize or reset progress for a new download
        self.download_progress[model_id] = {
            "status": "pending",
            "progress": 0,
            "downloaded_size": 0,
            "total_size": 0,
            "error_message": "",
            "cancel_requested": False
        }

        logger.info(f"Queuing download for model {model_id}")
        download_thread = threading.Thread(target=self._perform_download, args=(model_id,))
        download_thread.daemon = True  # Allow main program to exit even if threads are running
        download_thread.start()
        return True

    def get_download_progress(self, model_id: str) -> Optional[Dict]:
        """Returns the download progress for a given model_id."""
        return self.download_progress.get(model_id)

    def cancel_download_model(self, model_id: str) -> bool:
        """Requests cancellation of an ongoing download for model_id."""
        if model_id in self.download_progress and self.download_progress[model_id]["status"] == "downloading":
            self.download_progress[model_id]["cancel_requested"] = True
            logger.info(f"Cancellation requested for model {model_id} download.")
            return True
        logger.warning(f"No active download to cancel for model {model_id} or download not in cancellable state.")
        return False

    def delete_model_file(self, model_id: str) -> bool:
        """Deletes the model file from the cache and updates internal state."""
        if model_id not in self.AVAILABLE_MODELS:
            logger.error(f"Attempted to delete unknown model: {model_id}")
            return False

        if not self.is_model_downloaded(model_id):
            logger.info(f"Model {model_id} is not downloaded, nothing to delete.")
            # Consider if this should return True or False. True if "delete succeeded" means "it's not there".
            return True

        model_cache_dir = self._get_model_cache_dir()
        model_filename = f"{model_id}.pt" # Assuming .pt extension, align with _perform_download
        model_path = os.path.join(model_cache_dir, model_filename)

        try:
            if os.path.exists(model_path):
                os.remove(model_path)
                logger.info(f"Successfully deleted model file: {model_path}")
            else:
                logger.warning(f"Model file not found at {model_path}, though it was marked as downloaded.")

            # Update internal state
            if model_id in self.downloaded_models:
                self.downloaded_models.remove(model_id)

            # Clean up progress state if any
            if model_id in self.download_progress:
                self.download_progress[model_id]["status"] = "deleted" # Or remove entry: del self.download_progress[model_id]
                # If keeping the entry, ensure progress reflects deletion
                self.download_progress[model_id]["progress"] = 0
                self.download_progress[model_id]["downloaded_size"] = 0


            # If the deleted model was the current model, unload it
            if self.current_model_name == model_id:
                self.current_model = None
                self.current_model_name = None # Or set to a default like "base" if one must always be "current"
                logger.info(f"Unloaded model {model_id} as it was deleted.")

            return True
        except OSError as e:
            logger.error(f"Error deleting model file {model_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting model {model_id}: {e}")
            return False
