#!/usr/bin/env python3
"""
Enhanced WhisperS2T Appliance - Complete System Management
v0.5.0 - Full Appliance Edition

Complete Speech-to-Text Appliance with:
- Real-time microphone integration
- Advanced system resource management
- ISO-deployment ready configuration
- Comprehensive admin interface
- RAM/CPU monitoring and limits
- Model management with size controls
- Multi-user session management
- Network appliance features
"""

import asyncio
import base64
import gc
import json
import logging
import os

# System imports for appliance functionality
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import psutil
import uvicorn

# Core Framework
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/var/log/whisper-appliance.log"), logging.StreamHandler()],
)
logger = logging.getLogger("WhisperS2T-Appliance")


# Global state management
class ApplianceState:
    def __init__(self):
        self.current_model = None
        self.current_model_name = "tiny"
        self.model_loading = False
        self.connected_clients: Set[WebSocket] = set()
        self.active_sessions: Dict[str, dict] = {}
        self.system_ready = False
        self.max_ram_usage = 3.0  # GB
        self.max_cpu_usage = 80  # Percentage
        self.model_cache = {}
        self.processing_queue = asyncio.Queue()
        self.stats = {
            "total_transcriptions": 0,
            "total_audio_minutes": 0.0,
            "uptime_start": datetime.now(),
            "last_model_load": None,
        }


state = ApplianceState()


# Enhanced System Resource Manager
class SystemResourceManager:
    """Advanced system resource monitoring and management"""

    def __init__(self):
        self.cpu_history = []
        self.ram_history = []
        self.monitoring = False
        self.alerts = []

    def start_monitoring(self):
        """Start continuous system monitoring"""
        self.monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        logger.info("System resource monitoring started")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                # Keep history (last 100 measurements)
                self.cpu_history.append(cpu_percent)
                self.ram_history.append(memory.percent)

                if len(self.cpu_history) > 100:
                    self.cpu_history.pop(0)
                if len(self.ram_history) > 100:
                    self.ram_history.pop(0)

                # Check thresholds
                if cpu_percent > state.max_cpu_usage:
                    self._add_alert(f"High CPU usage: {cpu_percent:.1f}%")

                if memory.percent > (state.max_ram_usage / memory.total * 100) * 100:
                    self._add_alert(f"High RAM usage: {memory.percent:.1f}%")

            except Exception as e:
                logger.error(f"Monitoring error: {e}")

            time.sleep(5)

    def _add_alert(self, message):
        """Add system alert"""
        alert = {"timestamp": datetime.now().isoformat(), "message": message, "level": "warning"}
        self.alerts.append(alert)
        if len(self.alerts) > 50:  # Keep last 50 alerts
            self.alerts.pop(0)
        logger.warning(message)

    def get_system_info(self):
        """Get comprehensive system information"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_count = psutil.cpu_count()

        # Network info
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "127.0.0.1"

        # Uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time

        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "cpu": {
                "count": cpu_count,
                "current_usage": psutil.cpu_percent(),
                "history": self.cpu_history[-20:],  # Last 20 measurements
                "max_threshold": state.max_cpu_usage,
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 1),
                "used_gb": round(memory.used / (1024**3), 1),
                "available_gb": round(memory.available / (1024**3), 1),
                "percent": memory.percent,
                "history": self.ram_history[-20:],
                "max_threshold_gb": state.max_ram_usage,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 1),
                "used_gb": round(disk.used / (1024**3), 1),
                "free_gb": round(disk.free / (1024**3), 1),
                "percent": round((disk.used / disk.total) * 100, 1),
            },
            "uptime": {"seconds": int(uptime_seconds), "formatted": self._format_uptime(uptime_seconds)},
            "alerts": self.alerts,
            "whisper_model": {
                "current": state.current_model_name,
                "ram_usage_mb": self._get_model_ram_usage(),
                "loading": state.model_loading,
            },
            "sessions": {"active_connections": len(state.connected_clients), "total_sessions": len(state.active_sessions)},
        }

    def _format_uptime(self, seconds):
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"

    def _get_model_ram_usage(self):
        """Estimate RAM usage of current Whisper model"""
        if not state.current_model:
            return 0

        model_sizes = {"tiny": 150, "base": 300, "small": 800, "medium": 2000, "large": 4000}  # MB
        return model_sizes.get(state.current_model_name, 0)


# Initialize resource manager
resource_manager = SystemResourceManager()


# Enhanced Whisper Model Manager with Resource Limits
class EnhancedWhisperModelManager:
    """Advanced Whisper model management with resource constraints"""

    def __init__(self):
        self.model_info = {
            "tiny": {"size_mb": 39, "ram_mb": 150, "description": "Fastest, minimal accuracy"},
            "base": {"size_mb": 74, "ram_mb": 300, "description": "Good balance"},
            "small": {"size_mb": 244, "ram_mb": 800, "description": "Better accuracy"},
            "medium": {"size_mb": 769, "ram_mb": 2000, "description": "High accuracy"},
            "large": {"size_mb": 1550, "ram_mb": 4000, "description": "Best accuracy"},
        }

    async def load_model_with_limits(self, model_name: str):
        """Load model with resource limit checking"""
        if state.model_loading:
            raise HTTPException(status_code=409, detail="Another model is currently loading")

        # Check RAM availability
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        required_gb = self.model_info[model_name]["ram_mb"] / 1024

        if required_gb > available_gb:
            raise HTTPException(
                status_code=507, detail=f"Insufficient RAM: {required_gb:.1f}GB required, {available_gb:.1f}GB available"
            )

        # Check if loading would exceed limits
        if required_gb > state.max_ram_usage:
            raise HTTPException(
                status_code=507, detail=f"Model exceeds RAM limit: {required_gb:.1f}GB > {state.max_ram_usage:.1f}GB"
            )

        # Unload current model to free memory
        if state.current_model:
            logger.info(f"Unloading current model: {state.current_model_name}")
            del state.current_model
            state.current_model = None
            gc.collect()

        state.model_loading = True

        try:
            logger.info(f"Loading Whisper model: {model_name}")

            # Try Faster-Whisper first
            try:
                from faster_whisper import WhisperModel

                state.current_model = WhisperModel(model_name, device="cpu", compute_type="int8")
                state.current_model.model_type = "faster-whisper"
                logger.info(f"Faster-Whisper {model_name} loaded successfully")

            except Exception as e:
                logger.warning(f"Faster-Whisper failed: {e}, trying OpenAI-Whisper")
                import whisper

                state.current_model = whisper.load_model(model_name)
                state.current_model.model_type = "openai-whisper"
                logger.info(f"OpenAI-Whisper {model_name} loaded successfully")

            state.current_model_name = model_name
            state.stats["last_model_load"] = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")
        finally:
            state.model_loading = False

    def get_model_recommendations(self):
        """Get model recommendations based on system resources"""
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)

        recommendations = []
        for model, info in self.model_info.items():
            required_gb = info["ram_mb"] / 1024
            can_load = required_gb <= available_gb and required_gb <= state.max_ram_usage

            recommendations.append(
                {
                    "model": model,
                    "size_mb": info["size_mb"],
                    "ram_mb": info["ram_mb"],
                    "description": info["description"],
                    "can_load": can_load,
                    "reason": "OK" if can_load else f"Requires {required_gb:.1f}GB RAM",
                }
            )

        return recommendations


model_manager = EnhancedWhisperModelManager()


# Audio processing with resource management
async def process_real_audio_managed(audio_data_base64: str, language: str = "auto", audio_format: str = "webm"):
    """Process audio with resource monitoring"""
    start_time = time.time()

    try:
        # Check system load before processing
        cpu_usage = psutil.cpu_percent()
        if cpu_usage > state.max_cpu_usage:
            logger.warning(f"High CPU usage ({cpu_usage}%), queuing request")
            await state.processing_queue.put((audio_data_base64, language, audio_format))
            return "Audio queued due to high system load"

        # Process audio
        audio_bytes = base64.b64decode(audio_data_base64)

        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_audio_path = temp_file.name

        try:
            if not state.current_model:
                return "No Whisper model loaded"

            language_code = None if language == "auto" else language

            # Check model type and process accordingly
            model_type = getattr(state.current_model, "model_type", "unknown")

            if model_type == "faster-whisper" or hasattr(state.current_model, "model"):
                segments, info = state.current_model.transcribe(
                    temp_audio_path, language=language_code, beam_size=5, word_timestamps=False
                )

                transcript_parts = []
                for segment in segments:
                    transcript_parts.append(segment.text)

                transcript = "".join(transcript_parts).strip()
                detected_language = info.language if hasattr(info, "language") else "unknown"

            else:
                # OpenAI Whisper
                result = state.current_model.transcribe(temp_audio_path, language=language_code, fp16=False, verbose=False)
                transcript = result.get("text", "").strip()
                detected_language = result.get("language", "unknown")

            # Update statistics
            processing_time = time.time() - start_time
            state.stats["total_transcriptions"] += 1
            state.stats["total_audio_minutes"] += len(audio_bytes) / (16000 * 2 * 60)  # Rough estimate

            logger.info(f"Audio processed in {processing_time:.2f}s: {transcript[:50]}...")

            return transcript if transcript else "No speech detected"

        finally:
            try:
                os.unlink(temp_audio_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        return f"Error processing audio: {str(e)}"


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    logger.info("🚀 Starting Enhanced WhisperS2T Appliance v0.5.0")

    # Start system monitoring
    resource_manager.start_monitoring()

    # Load default model if possible
    try:
        await model_manager.load_model_with_limits("tiny")
        logger.info("✅ Default model loaded successfully")
    except Exception as e:
        logger.warning(f"Default model loading failed: {e}")

    state.system_ready = True
    logger.info("✅ Enhanced WhisperS2T Appliance ready!")

    yield

    # Cleanup
    resource_manager.monitoring = False
    logger.info("🔄 Appliance shutdown complete")


# FastAPI app with lifespan
app = FastAPI(
    title="Enhanced WhisperS2T Appliance",
    description="Production-ready Speech-to-Text Appliance with advanced system management",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (will be created)
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Start the enhanced appliance
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info", access_log=True)
