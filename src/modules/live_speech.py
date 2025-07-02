"""
Live Speech Module
Handles WebSocket connections and real-time speech recognition
Preserves all original WebSocket features and enhances with real implementation
"""

import logging
import os
import tempfile
from datetime import datetime

from flask import request
from flask_socketio import emit

logger = logging.getLogger(__name__)


class LiveSpeechHandler:
    """Manages WebSocket connections and live speech transcription"""

    def __init__(self, model_manager, whisper_available, system_stats, connected_clients, chat_history):
        self.model_manager = model_manager
        self.whisper_available = whisper_available
        self.system_stats = system_stats
        self.connected_clients = connected_clients
        self.chat_history = chat_history

    def handle_connect(self):
        """Handle WebSocket connection - Original functionality preserved"""
        self.connected_clients.append(request.sid)
        self.system_stats["active_connections"] = len(self.connected_clients)
        logger.info(f"Client connected: {request.sid}")
        emit(
            "connection_status",
            {
                "status": "connected",
                "message": "WebSocket connected successfully",
                "real_connection": True,  # Now it's real, not simulated!
            },
        )

    def handle_disconnect(self):
        """Handle WebSocket disconnection - Original functionality preserved"""
        if request.sid in self.connected_clients:
            self.connected_clients.remove(request.sid)
        self.system_stats["active_connections"] = len(self.connected_clients)
        logger.info(f"Client disconnected: {request.sid}")

    def handle_transcription_result(self, data):
        """Broadcast transcription result to client - Original functionality + save to history"""
        # Save to chat history
        try:
            self.chat_history.add_transcription(
                text=data.get("text", ""),
                language=data.get("language", "unknown"),
                model_used=self.model_manager.get_current_model_name(),
                source_type="live",
                metadata={"timestamp": datetime.now().isoformat()},
            )
        except Exception as e:
            logger.warning(f"Failed to save live speech to history: {e}")

        emit("transcription_result", data)

    def handle_transcription_error(self, data):
        """Broadcast transcription error to client - Original functionality"""
        emit("transcription_error", data)

    def handle_audio_chunk(self, data):
        """Handle incoming audio chunk for real-time transcription - NEW REAL IMPLEMENTATION"""
        if not self.whisper_available:
            emit("transcription_error", {"error": "Whisper model not available"})
            return

        try:
            # Get audio data and language from WebSocket
            audio_data = data.get("audio_data")
            language = data.get("language", "auto")  # Get language from frontend
            if not audio_data:
                emit("transcription_error", {"error": "No audio data received"})
                return

            # Save audio chunk temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                # Assuming audio_data is base64 encoded or binary
                if isinstance(audio_data, str):
                    import base64

                    audio_bytes = base64.b64decode(audio_data)
                else:
                    audio_bytes = audio_data

                tmp_file.write(audio_bytes)
                tmp_file.flush()

                # Transcribe in real-time using model manager
                logger.info(f"Processing live audio chunk with language: {language}")
                model = self.model_manager.get_model()
                if model is None:
                    emit("transcription_error", {"error": "No model loaded"})
                    return

                # Use language parameter if specified
                transcribe_options = {"fp16": False}
                if language and language != "auto":
                    transcribe_options["language"] = language

                result = model.transcribe(tmp_file.name, **transcribe_options)

                # Clean up
                os.unlink(tmp_file.name)

                # Send result back via WebSocket
                emit(
                    "transcription_result",
                    {
                        "text": result["text"],
                        "language": result.get("language", "unknown"),
                        "timestamp": datetime.now().isoformat(),
                        "confidence": getattr(result, "confidence", 0.0),
                    },
                )

                # Update stats
                self.system_stats["total_transcriptions"] += 1

        except Exception as e:
            logger.error(f"Live transcription error: {e}")
            emit("transcription_error", {"error": str(e), "timestamp": datetime.now().isoformat()})

    def handle_start_recording(self, data):
        """Start live recording session - NEW FEATURE"""
        logger.info(f"Starting live recording session for client: {request.sid}")
        emit(
            "recording_started",
            {"status": "recording", "message": "Live recording started", "timestamp": datetime.now().isoformat()},
        )

    def handle_stop_recording(self, data):
        """Stop live recording session - NEW FEATURE"""
        logger.info(f"Stopping live recording session for client: {request.sid}")
        emit(
            "recording_stopped",
            {"status": "stopped", "message": "Live recording stopped", "timestamp": datetime.now().isoformat()},
        )
