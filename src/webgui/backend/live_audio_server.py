#!/usr/bin/env python3
"""
WhisperS2T Live Audio Server
Simple WebSocket server for audio streaming integration
"""

import asyncio
import json
import logging
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhisperS2T Live Audio Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
connected_clients = []


class AudioManager:
    """Simple audio manager for live recording simulation"""

    def __init__(self):
        self.is_recording = False
        self.current_device = "default"

    def start_recording(self):
        """Start recording simulation"""
        self.is_recording = True
        logger.info("Audio recording started")
        return True

    def stop_recording(self):
        """Stop recording simulation"""
        self.is_recording = False
        logger.info("Audio recording stopped")
        return True

    def get_status(self):
        """Get current recording status"""
        return {
            "is_recording": self.is_recording,
            "device": self.current_device,
            "status": "active" if self.is_recording else "idle",
        }


# Initialize audio manager
audio_manager = AudioManager()


@app.get("/")
async def root():
    """Simple status page"""
    return {"service": "WhisperS2T Live Audio Server", "version": "0.1.0", "status": "running"}


@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    """WebSocket endpoint for live audio communication"""
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info("Client connected to live audio WebSocket")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "start_recording":
                if audio_manager.start_recording():
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "recording_started",
                                "message": "🎤 Recording started!",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

            elif message.get("action") == "stop_recording":
                if audio_manager.stop_recording():
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "recording_stopped",
                                "message": "🛑 Recording stopped!",
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

            elif message.get("action") == "status":
                status = audio_manager.get_status()
                await websocket.send_text(
                    json.dumps({"type": "status", "data": status, "timestamp": datetime.now().isoformat()})
                )

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info("Client disconnected from live audio WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "live_audio_server",
        "connected_clients": len(connected_clients),
        "audio_status": audio_manager.get_status(),
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting WhisperS2T Live Audio Server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
