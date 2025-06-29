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

    def __init__(self, model, whisper_available, system_stats, connected_clients):
        self.model = model
        self.whisper_available = whisper_available
        self.system_stats = system_stats
        self.connected_clients = connected_clients

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
        """Broadcast transcription result to client - Original functionality"""
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
            # Get audio data from WebSocket
            audio_data = data.get("audio_data")
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

                # Transcribe in real-time
                logger.info("Processing live audio chunk...")
                result = self.model.transcribe(tmp_file.name, fp16=False)

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
