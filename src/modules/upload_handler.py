"""
Upload Handler Module
Handles file upload transcription functionality
Preserves all original upload features from enhanced_app.py
"""

import os
import tempfile
import logging
from datetime import datetime
from flask import jsonify, request
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class UploadHandler:
    """Handles audio file upload and transcription"""

    def __init__(self, model, whisper_available, system_stats):
        self.model = model
        self.whisper_available = whisper_available
        self.system_stats = system_stats

    def transcribe_upload(self):
        """Transcribe uploaded audio file - Original functionality preserved"""
        if not self.whisper_available:
            return jsonify({"error": "Whisper model not available"})

        try:
            if "audio" not in request.files:
                return jsonify({"error": "No audio file provided"})

            audio_file = request.files["audio"]
            if audio_file.filename == "":
                return jsonify({"error": "No audio file selected"})

            # Secure filename
            filename = secure_filename(audio_file.filename)

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                audio_file.save(tmp_file.name)

                # Transcribe audio
                logger.info(f"Transcribing file: {filename}")
                result = self.model.transcribe(tmp_file.name)

                # Clean up temp file
                os.unlink(tmp_file.name)

                # Update statistics
                self.system_stats["total_transcriptions"] += 1
                logger.info("Transcription completed successfully")

                return jsonify(
                    {
                        "text": result["text"],
                        "language": result.get("language", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return jsonify({"error": str(e)})

    def transcribe_live_api(self):
        """Transcribe live audio recording - Enhanced API version"""
        if not self.whisper_available:
            return jsonify({"error": "Whisper model not available"})

        try:
            if "audio" not in request.files:
                return jsonify({"error": "No audio data provided"})

            audio_file = request.files["audio"]
            language = request.form.get("language", "auto")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                audio_file.save(tmp_file.name)

                logger.info(f"Live transcribing audio (lang: {language})")

                kwargs = {}
                if language != "auto":
                    kwargs["language"] = language

                result = self.model.transcribe(tmp_file.name, **kwargs)
                os.unlink(tmp_file.name)

                self.system_stats["total_transcriptions"] += 1
                return jsonify(
                    {
                        "text": result["text"],
                        "language": result.get("language", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except Exception as e:
            logger.error(f"Live transcription error: {e}")
            return jsonify({"error": str(e)})
