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
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.utils import secure_filename

# Import our modular components
from modules import (
    UPDATE_MANAGER_AVAILABLE,
    AdminPanel,
    APIDocs,
    ChatHistoryManager,
    LiveSpeechHandler,
    ModelManager,
    UpdateManager,
    UploadHandler,
)

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

# Initialize Model Manager and Chat History
try:
    model_manager = ModelManager()
    chat_history = ChatHistoryManager()
    if UPDATE_MANAGER_AVAILABLE:
        update_manager = UpdateManager()
        logger.info("✅ Model Manager, Chat History, and Update Manager initialized")
    else:
        update_manager = None
        logger.warning("⚠️ Update Manager not available (backward compatibility mode)")
        logger.info("✅ Model Manager and Chat History initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize core components: {e}")
    # Use minimal fallback components
    model_manager = None
    chat_history = None
    update_manager = None

# Try to load default Whisper model
WHISPER_AVAILABLE = False
if model_manager:
    try:
        logger.info("Loading default Whisper model...")
        if model_manager.load_model("base"):
            WHISPER_AVAILABLE = True
            logger.info("✅ Whisper model loaded successfully")
        else:
            WHISPER_AVAILABLE = False
            logger.warning("⚠️ Failed to load default model, will try on-demand")
    except Exception as e:
        logger.error(f"❌ Failed to load Whisper model: {e}")
        WHISPER_AVAILABLE = False
else:
    logger.warning("⚠️ Model Manager not available")

# Initialize module handlers with proper fallback handling
try:
    upload_handler = UploadHandler(model_manager, WHISPER_AVAILABLE, system_stats, chat_history)
    live_speech_handler = LiveSpeechHandler(model_manager, WHISPER_AVAILABLE, system_stats, connected_clients, chat_history)

    # AdminPanel initialization with optional UpdateManager
    if update_manager:
        admin_panel = AdminPanel(
            WHISPER_AVAILABLE, system_stats, connected_clients, model_manager, chat_history, update_manager
        )
    else:
        # Fallback AdminPanel initialization without UpdateManager
        admin_panel = AdminPanel(WHISPER_AVAILABLE, system_stats, connected_clients, model_manager, chat_history)

    api_docs = APIDocs(version="0.10.0")
    logger.info("✅ All module handlers initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize module handlers: {e}")
    # Create minimal fallback handlers
    upload_handler = None
    live_speech_handler = None
    admin_panel = None
    api_docs = None

# Configure SwaggerUI
SWAGGER_URL = "/docs"
API_URL = "/api/openapi.json"
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "WhisperS2T API Documentation", "deepLinking": True}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# ==================== MAIN ROUTES ====================


@app.route("/")
def index():
    """Enhanced Purple Gradient Interface - Original UI Preserved"""
    status_text = "🟢 System Ready" if WHISPER_AVAILABLE else "🔴 Whisper Unavailable"

    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "templates", "main_interface.html")

        with open(template_path, "r") as f:
            template = f.read()

        # Replace status placeholder
        template = template.replace("{{ status_text }}", status_text)

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
    model_status = model_manager.get_status()
    return jsonify(
        {
            "status": "healthy",
            "whisper_available": WHISPER_AVAILABLE,
            "version": "0.9.0",
            "uptime_seconds": uptime,
            "total_transcriptions": system_stats["total_transcriptions"],
            "active_connections": len(connected_clients),
            "system_ready": system_ready,
            "timestamp": datetime.now().isoformat(),
            "model_status": model_status,
        }
    )


# ==================== MODEL MANAGEMENT ROUTES ====================


@app.route("/api/models", methods=["GET"])
def get_models():
    """Get available Whisper models"""
    return jsonify(
        {
            "available_models": model_manager.get_available_models(),
            "current_model": model_manager.get_current_model_name(),
            "model_loading": model_manager.is_model_loading(),
            "status": "success",
        }
    )


@app.route("/api/models/<model_name>", methods=["POST"])
def switch_model(model_name):
    """Switch to a different Whisper model"""
    if model_manager.is_model_loading():
        return jsonify({"error": "Model loading already in progress", "status": "error"}), 429

    if model_name not in model_manager.get_available_models():
        return jsonify({"error": f"Invalid model: {model_name}", "status": "error"}), 400

    # Load model in background to avoid blocking
    import threading

    def load_model():
        success = model_manager.load_model(model_name)
        if success:
            logger.info(f"Model switched to: {model_name}")
        else:
            logger.error(f"Failed to switch to model: {model_name}")

    thread = threading.Thread(target=load_model, daemon=True)
    thread.start()

    return jsonify({"message": f"Loading model: {model_name}", "target_model": model_name, "status": "loading"})


@app.route("/api/models/download-status", methods=["GET"])
def get_model_download_status():
    """Get detailed download status for all models"""
    return jsonify(
        {
            "download_status": model_manager.get_download_status(),
            "summary": {
                "total_models": len(model_manager.get_available_models()),
                "downloaded_count": len(model_manager.downloaded_models),
                "pending_count": len(
                    [m for m in model_manager.get_available_models() if m not in model_manager.downloaded_models]
                ),
            },
            "status": "success",
        }
    )


# ==================== CHAT HISTORY ROUTES ====================


@app.route("/api/chat-history", methods=["GET"])
def get_chat_history():
    """Get recent chat history"""
    limit = request.args.get("limit", 50, type=int)
    source_type = request.args.get("source", None)

    if source_type:
        transcriptions = chat_history.get_transcriptions_by_source(source_type, limit)
    else:
        transcriptions = chat_history.get_recent_transcriptions(limit)

    return jsonify({"transcriptions": transcriptions, "count": len(transcriptions), "status": "success"})


@app.route("/api/chat-history/search", methods=["GET"])
def search_chat_history():
    """Search chat history"""
    query = request.args.get("q", "")
    limit = request.args.get("limit", 50, type=int)

    if not query:
        return jsonify({"error": "Search query required", "status": "error"}), 400

    results = chat_history.search_transcriptions(query, limit)
    return jsonify({"results": results, "count": len(results), "query": query, "status": "success"})


@app.route("/api/chat-history/stats", methods=["GET"])
def get_chat_history_stats():
    """Get chat history statistics"""
    stats = chat_history.get_statistics()
    return jsonify({"statistics": stats, "status": "success"})


@app.route("/api/chat-history/export", methods=["GET"])
def export_chat_history():
    """Export chat history"""
    format = request.args.get("format", "json")

    if format not in ["json", "csv"]:
        return jsonify({"error": "Invalid format. Use 'json' or 'csv'", "status": "error"}), 400

    exported_data = chat_history.export_history(format)

    if format == "csv":
        from flask import Response

        return Response(
            exported_data, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=chat_history.csv"}
        )
    else:
        return jsonify({"data": exported_data, "format": format, "status": "success"})


# ==================== UPDATE MANAGEMENT ROUTES ====================


@app.route("/api/updates/check", methods=["POST"])
def check_updates():
    """Check for available updates"""
    if not update_manager:
        return jsonify({"error": "Update manager not available", "status": "error"}), 503

    try:
        background = request.json.get("background", False) if request.is_json else False
        result = update_manager.check_for_updates(background=background)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Update check failed: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/updates/apply", methods=["POST"])
def apply_updates():
    """Apply available updates"""
    if not update_manager:
        return jsonify({"error": "Update manager not available", "status": "error"}), 503

    try:
        result = update_manager.apply_updates()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Update apply failed: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/updates/rollback", methods=["POST"])
def rollback_updates():
    """Rollback to previous version"""
    if not update_manager:
        return jsonify({"error": "Update manager not available", "status": "error"}), 503

    try:
        result = update_manager.rollback_update()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Update rollback failed: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/updates/status", methods=["GET"])
def get_update_status():
    """Get current update status"""
    if not update_manager:
        return jsonify({"error": "Update manager not available", "status": "error"}), 503

    try:
        status = update_manager.get_update_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Update status check failed: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/transcribe", methods=["POST"])
def transcribe():
    """Upload transcription - Delegated to UploadHandler"""
    if not upload_handler:
        return jsonify({"error": "Upload handler not available"}), 503
    return upload_handler.transcribe_upload()


@app.route("/api/transcribe-live", methods=["POST"])
def transcribe_live():
    """Live transcription API - Delegated to UploadHandler"""
    if not upload_handler:
        return jsonify({"error": "Upload handler not available"}), 503
    return upload_handler.transcribe_live_api()


@app.route("/api/status")
def api_status():
    """Detailed API status - Enhanced version"""
    uptime = (datetime.now() - system_stats["uptime_start"]).total_seconds()
    return jsonify(
        {
            "service": "WhisperS2T Enhanced Appliance",
            "version": "0.9.0",
            "status": "running",
            "whisper": {
                "available": WHISPER_AVAILABLE,
                "model_loaded": model_manager.get_current_model() is not None,
                "model_type": model_manager.get_current_model_name() if model_manager.get_current_model() else None,
                "model_loading": model_manager.is_model_loading(),
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


@app.route("/api/openapi.json")
def openapi_spec():
    """OpenAPI 3.0 specification for SwaggerUI"""
    return jsonify(api_docs.get_openapi_spec(request))


# ==================== INTERFACE ROUTES ====================


@app.route("/admin")
def admin():
    """Admin Panel - Delegated to AdminPanel"""
    return admin_panel.get_admin_interface()


@app.route("/demo")
def demo():
    """Demo Interface - Delegated to AdminPanel"""
    return admin_panel.get_demo_interface()


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
    logger.info("🎤 Starting Enhanced WhisperS2T Appliance v0.9.0...")
    logger.info("🏗️ Architecture: Modular (live_speech, upload_handler, admin_panel, api_docs)")
    logger.info("🌐 SSL: Intelligent network certificate with SAN support")

    # Check for SSL certificates (support both local dev and container paths)
    ssl_cert_path = None
    ssl_key_path = None

    # Try container path first (Proxmox deployment)
    container_ssl_cert = "/opt/whisper-appliance/ssl/whisper-appliance.crt"
    container_ssl_key = "/opt/whisper-appliance/ssl/whisper-appliance.key"

    if os.path.exists(container_ssl_cert) and os.path.exists(container_ssl_key):
        ssl_cert_path = container_ssl_cert
        ssl_key_path = container_ssl_key
    else:
        # Try local development path
        local_ssl_cert = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ssl", "whisper-appliance.crt")
        local_ssl_key = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ssl", "whisper-appliance.key")

        if os.path.exists(local_ssl_cert) and os.path.exists(local_ssl_key):
            ssl_cert_path = local_ssl_cert
            ssl_key_path = local_ssl_key

    if ssl_cert_path and ssl_key_path:
        logger.info("🔒 SSL certificates found - Starting with HTTPS support")
        logger.info("🌐 Main Interface: https://localhost:5001")
        logger.info("⚙️ Admin Panel: https://localhost:5001/admin")
        logger.info("📚 API Docs: https://localhost:5001/docs")
        logger.info("🎯 Demo Interface: https://localhost:5001/demo")
        logger.info("🏥 Health Check: https://localhost:5001/health")
        logger.info("🎙️ Microphone Access: ✅ Enabled via HTTPS")
        logger.info("⚠️  Browser Security Warning: Click 'Advanced' → 'Continue to localhost'")

        # Run with SSL
        socketio.run(
            app, host="0.0.0.0", port=5001, debug=False, allow_unsafe_werkzeug=True, ssl_context=(ssl_cert_path, ssl_key_path)
        )
    else:
        logger.warning("🔓 No SSL certificates found - Starting without HTTPS")
        logger.warning("🎙️ Microphone Access: ❌ Limited (HTTPS required for production)")
        logger.info("💡 To enable HTTPS: Run './create-ssl-cert.sh' in project root")
        logger.info("🌐 Main Interface: http://0.0.0.0:5001")
        logger.info("⚙️ Admin Panel: http://0.0.0.0:5001/admin")
        logger.info("📚 API Docs: http://0.0.0.0:5001/docs")
        logger.info("🎯 Demo Interface: http://0.0.0.0:5001/demo")
        logger.info("🏥 Health Check: http://0.0.0.0:5001/health")

        # Run without SSL
        socketio.run(app, host="0.0.0.0", port=5001, debug=False, allow_unsafe_werkzeug=True)

    logger.info("✨ Features: Purple Gradient UI + REAL Live Speech + Upload + Full Navigation + HTTPS Support")


@app.route("/api/chat-history/update/<int:transcription_id>", methods=["PUT"])
def update_chat_history(transcription_id):
    """Update transcription text"""
    if not chat_history:
        return jsonify({"error": "Chat history not available"}), 503

    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Text field required", "status": "error"}), 400

    success = chat_history.update_transcription(transcription_id, data["text"])
    if success:
        return jsonify({"message": "Transcription updated", "status": "success"})
    else:
        return jsonify({"error": "Failed to update transcription", "status": "error"}), 400


@app.route("/api/chat-history/delete/<int:transcription_id>", methods=["DELETE"])
def delete_chat_history(transcription_id):
    """Delete transcription"""
    if not chat_history:
        return jsonify({"error": "Chat history not available"}), 503

    success = chat_history.delete_transcription(transcription_id)
    if success:
        return jsonify({"message": "Transcription deleted", "status": "success"})
    else:
        return jsonify({"error": "Failed to delete transcription", "status": "error"}), 400


@app.route("/api/chat-history/filter", methods=["GET"])
def filter_chat_history():
    """Get chat history filtered by date range"""
    if not chat_history:
        return jsonify({"error": "Chat history not available"}), 503

    start_date = request.args.get("start_date", None)
    end_date = request.args.get("end_date", None)
    limit = request.args.get("limit", 100, type=int)

    transcriptions = chat_history.get_transcriptions_by_date_range(start_date, end_date, limit)
    return jsonify({"transcriptions": transcriptions, "count": len(transcriptions), "status": "success"})
