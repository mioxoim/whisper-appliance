#!/usr/bin/env python3
"""
Enhanced WhisperS2T Appliance - Modular Version
Main entry point with preserved functionality and enhanced architecture

🚨 ALL ORIGINAL FEATURES PRESERVED:
- Purple Gradient UI (Original Enhanced Interface)
- Live Speech WebSocket (now with REAL implementation)
- Upload Transcription
- Admin Panel with Navigation
- API Documentation
- Health Check & Status Endpoints
- Demo Interface

🆕 NEW ENHANCEMENTS:
- Modular architecture (live_speech, upload_handler, admin_panel, api_docs)
- Enhanced WebSocket with real audio processing
- Comprehensive navigation between interfaces
- Improved error handling and logging
"""

import logging
import os
import tempfile
from datetime import datetime

# Flask and extensions
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# Import our modular components
from modules import AdminPanel, APIDocs, LiveSpeechHandler, UploadHandler

# Initialize Flask app
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size
app.config["SECRET_KEY"] = "whisper-s2t-enhanced-secret-key"
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# System statistics and state
system_stats = {"uptime_start": datetime.now(), "total_transcriptions": 0, "active_connections": 0}
connected_clients = []
system_ready = True

# Try to load Whisper model
try:
    import whisper

    logger.info("Loading Whisper model...")
    model = whisper.load_model("base")
    WHISPER_AVAILABLE = True
    logger.info("✅ Whisper model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load Whisper model: {e}")
    model = None
    WHISPER_AVAILABLE = False

# Initialize module handlers
upload_handler = UploadHandler(model, WHISPER_AVAILABLE, system_stats)
live_speech_handler = LiveSpeechHandler(model, WHISPER_AVAILABLE, system_stats, connected_clients)
admin_panel = AdminPanel(WHISPER_AVAILABLE, system_stats, connected_clients, model)
api_docs = APIDocs(version="0.7.0")


# ==================== MAIN ROUTES ====================


@app.route("/")
def index():
    """Enhanced Purple Gradient Interface - Original UI Preserved"""
    status_text = "🟢 System Ready" if WHISPER_AVAILABLE else "🔴 Whisper Unavailable"

    try:
        with open("/home/commander/Code/whisper-appliance/src/templates/main_interface.html", "r") as f:
            template = f.read()

        # Inject status and enhanced JavaScript
        enhanced_js = """
        <script>
        // WebSocket connection and audio handling
        let socket = null;
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        
        // Initialize WebSocket connection
        function initWebSocket() {
            socket = io();
            
            socket.on('connect', function() {
                document.getElementById('ws-status').textContent = 'Connected ✅';
                document.getElementById('ws-indicator').classList.add('connected');
                console.log('WebSocket connected');
            });
            
            socket.on('disconnect', function() {
                document.getElementById('ws-status').textContent = 'Disconnected ❌';
                document.getElementById('ws-indicator').classList.remove('connected');
                console.log('WebSocket disconnected');
            });
            
            socket.on('connection_status', function(data) {
                console.log('Connection status:', data);
                if (data.real_connection) {
                    document.getElementById('ws-status').textContent = 'Connected (Real) ✅';
                }
            });
            
            socket.on('transcription_result', function(data) {
                document.getElementById('liveResult').innerHTML = 
                    '<strong>📝 ' + new Date().toLocaleTimeString() + ':</strong><br>' + 
                    data.text + '<br><small>Language: ' + data.language + '</small>';
            });
            
            socket.on('transcription_error', function(data) {
                document.getElementById('liveResult').innerHTML = 
                    '<span style="color: #ff6b6b;">❌ Error: ' + data.error + '</span>';
            });
        }
        
        // Initialize audio devices
        async function initAudioDevices() {
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const audioDevices = devices.filter(device => device.kind === 'audioinput');
                const select = document.getElementById('deviceSelect');
                
                audioDevices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.deviceId;
                    option.textContent = device.label || `Microphone ${select.children.length}`;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error accessing audio devices:', error);
            }
        }
        
        // Start recording function
        async function startRecording() {
            try {
                const deviceId = document.getElementById('deviceSelect').value;
                const constraints = {
                    audio: deviceId ? { deviceId: { exact: deviceId } } : true
                };
                
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    sendAudioToServer(audioBlob);
                };
                
                mediaRecorder.start();
                isRecording = true;
                
                // Update UI
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('recordingIndicator').style.display = 'block';
                
                // Emit start recording event
                if (socket) {
                    socket.emit('start_recording', {
                        language: document.getElementById('languageSelect').value
                    });
                }
                
            } catch (error) {
                console.error('Error starting recording:', error);
                alert('Error accessing microphone: ' + error.message);
            }
        }
        
        // Stop recording function
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                // Stop all tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                
                // Update UI
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('recordingIndicator').style.display = 'none';
                
                // Emit stop recording event
                if (socket) {
                    socket.emit('stop_recording', {});
                }
            }
        }
        
        // Send audio to server via WebSocket
        function sendAudioToServer(audioBlob) {
            const reader = new FileReader();
            reader.onload = function() {
                const base64Data = reader.result.split(',')[1];
                if (socket) {
                    socket.emit('audio_chunk', {
                        audio_data: base64Data,
                        language: document.getElementById('languageSelect').value
                    });
                }
            };
            reader.readAsDataURL(audioBlob);
        }
        
        // File upload functionality
        function uploadFile() {
            const fileInput = document.getElementById('audioFile');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select an audio file first!');
                return;
            }
            
            const formData = new FormData();
            formData.append('audio', file);
            
            document.getElementById('uploadResult').innerHTML = '🔄 Processing...';
            document.getElementById('uploadBtn').disabled = true;
            
            fetch('/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('uploadResult').innerHTML = 
                        '<span style="color: #ff6b6b;">❌ Error: ' + data.error + '</span>';
                } else {
                    document.getElementById('uploadResult').innerHTML = 
                        '<strong>📝 Transcription:</strong><br>' + data.text + 
                        '<br><small>Language: ' + (data.language || 'unknown') + '</small>';
                }
                document.getElementById('uploadBtn').disabled = false;
            })
            .catch(error => {
                document.getElementById('uploadResult').innerHTML = 
                    '<span style="color: #ff6b6b;">❌ Error: ' + error.message + '</span>';
                document.getElementById('uploadBtn').disabled = false;
            });
        }
        
        // Clear upload
        function clearUpload() {
            document.getElementById('audioFile').value = '';
            document.getElementById('uploadResult').innerHTML = 'No file uploaded yet...';
            document.getElementById('uploadBtn').disabled = true;
        }
        
        // File input change handler
        document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.getElementById('audioFile');
            const uploadBtn = document.getElementById('uploadBtn');
            
            fileInput.addEventListener('change', function() {
                uploadBtn.disabled = !this.files[0];
            });
            
            // Drag and drop functionality
            const uploadArea = document.getElementById('uploadArea');
            
            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    uploadBtn.disabled = false;
                }
            });
            
            // Initialize everything
            initWebSocket();
            initAudioDevices();
        });
        </script>
        """

        # Replace placeholder and inject JavaScript
        template = template.replace("{{ status_text }}", status_text)
        template = template.replace("</body>", enhanced_js + "</body>")

        return template

    except Exception as e:
        logger.error(f"Error loading main interface: {e}")
        # Fallback simple interface
        return f"""
        <html><body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🎤 WhisperS2T Appliance</h1>
        <p>Status: {status_text}</p>
        <p><a href="/admin">Admin Panel</a> | <a href="/docs">API Docs</a> | <a href="/demo">Demo</a></p>
        </body></html>
        """


# ==================== API ROUTES ====================


@app.route("/health")
def health():
    """Health check endpoint - Original functionality preserved"""
    uptime = (datetime.now() - system_stats["uptime_start"]).total_seconds()
    return jsonify(
        {
            "status": "healthy",
            "whisper_available": WHISPER_AVAILABLE,
            "version": "0.7.0",
            "uptime_seconds": uptime,
            "total_transcriptions": system_stats["total_transcriptions"],
            "active_connections": len(connected_clients),
            "system_ready": system_ready,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Upload transcription - Delegated to UploadHandler"""
    return upload_handler.transcribe_upload()


@app.route("/api/transcribe-live", methods=["POST"])
def transcribe_live():
    """Live transcription API - Delegated to UploadHandler"""
    return upload_handler.transcribe_live_api()


@app.route("/api/status")
def api_status():
    """Detailed API status - Enhanced version"""
    uptime = (datetime.now() - system_stats["uptime_start"]).total_seconds()
    return jsonify(
        {
            "service": "WhisperS2T Enhanced Appliance",
            "version": "0.7.0",
            "status": "running",
            "whisper": {
                "available": WHISPER_AVAILABLE,
                "model_loaded": model is not None,
                "model_type": "base" if model else None,
            },
            "statistics": {
                "uptime_seconds": uptime,
                "total_transcriptions": system_stats["total_transcriptions"],
                "active_websocket_connections": len(connected_clients),
                "system_ready": system_ready,
            },
            "endpoints": {
                "main_interface": "/",
                "health_check": "/health",
                "upload_transcription": "/transcribe",
                "live_transcription": "/api/transcribe-live",
                "api_documentation": "/docs",
                "admin_panel": "/admin",
                "demo_interface": "/demo",
            },
            "architecture": {
                "framework": "Flask + SocketIO",
                "modules": ["live_speech", "upload_handler", "admin_panel", "api_docs"],
                "features": ["Purple Gradient UI", "Real WebSocket", "Navigation", "Modular"],
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


# ==================== INTERFACE ROUTES ====================


@app.route("/admin")
def admin():
    """Admin Panel - Delegated to AdminPanel"""
    return admin_panel.get_admin_interface()


@app.route("/demo")
def demo():
    """Demo Interface - Delegated to AdminPanel"""
    return admin_panel.get_demo_interface()


@app.route("/docs")
def docs():
    """API Documentation - Delegated to APIDocs"""
    return api_docs.get_docs_interface()


# ==================== WEBSOCKET HANDLERS ====================


@socketio.on("connect")
def handle_connect():
    """WebSocket connect - Delegated to LiveSpeechHandler"""
    return live_speech_handler.handle_connect()


@socketio.on("disconnect")
def handle_disconnect():
    """WebSocket disconnect - Delegated to LiveSpeechHandler"""
    return live_speech_handler.handle_disconnect()


@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    """Audio chunk processing - NEW REAL IMPLEMENTATION"""
    return live_speech_handler.handle_audio_chunk(data)


@socketio.on("start_recording")
def handle_start_recording(data):
    """Start recording - NEW FEATURE"""
    return live_speech_handler.handle_start_recording(data)


@socketio.on("stop_recording")
def handle_stop_recording(data):
    """Stop recording - NEW FEATURE"""
    return live_speech_handler.handle_stop_recording(data)


@socketio.on("transcription_result")
def handle_transcription_result(data):
    """Transcription result - Original functionality preserved"""
    return live_speech_handler.handle_transcription_result(data)


@socketio.on("transcription_error")
def handle_transcription_error(data):
    """Transcription error - Original functionality preserved"""
    return live_speech_handler.handle_transcription_error(data)


# ==================== STARTUP ====================

if __name__ == "__main__":
    logger.info("🎤 Starting Enhanced WhisperS2T Appliance v0.7.0...")
    logger.info("🏗️ Architecture: Modular (live_speech, upload_handler, admin_panel, api_docs)")
    logger.info("🌐 Main Interface: http://0.0.0.0:5001")
    logger.info("⚙️ Admin Panel: http://0.0.0.0:5001/admin")
    logger.info("📚 API Docs: http://0.0.0.0:5001/docs")
    logger.info("🎯 Demo Interface: http://0.0.0.0:5001/demo")
    logger.info("🏥 Health Check: http://0.0.0.0:5001/health")
    logger.info("✨ Features: Purple Gradient UI + REAL Live Speech + Upload + Full Navigation")

    # Run with SocketIO
    socketio.run(app, host="0.0.0.0", port=5001, debug=False, allow_unsafe_werkzeug=True)
