#!/usr/bin/env python3
"""
Enhanced WhisperS2T Appliance - Clean Version with Single Update System
Main entry point with simplified architecture

🎯 SIMPLIFIED UPDATE SYSTEM:
- Single Enterprise Update System (no fallbacks)
- Clean import logic without complexity
- Functional update endpoints

🚨 ALL ORIGINAL FEATURES PRESERVED:
- Purple Gradient UI (Original Enhanced Interface)
- Live Speech WebSocket (now with REAL implementation)
- Upload Transcription
- Admin Panel with Navigation
- API Documentation
- Health Check & Status Endpoints
- Demo Interface

Version: 0.10.0
"""

import logging
import os
import sys
import tempfile
from datetime import datetime

# CRITICAL: Add current directory to Python path for container compatibility
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Flask and extensions
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.utils import secure_filename

# Import our modular components with error handling
try:
    from modules import (
        AdminPanel,
        APIDocs,
        ChatHistoryManager,
        LiveSpeechHandler,
        ModelManager,
        UploadHandler,
    )

    print("✅ Core modules imported successfully")
except ImportError as e:
    print(f"❌ Core module import failed: {e}")
    raise

# Import Maintenance System
try:
    from modules import EnterpriseMaintenanceManager, MaintenanceManager

    MAINTENANCE_MANAGER_AVAILABLE = True
    print("✅ Maintenance System imported successfully")
except ImportError as e:
    MaintenanceManager = None
    EnterpriseMaintenanceManager = None
    MAINTENANCE_MANAGER_AVAILABLE = False
    print(f"⚠️ Maintenance System not available: {e}")

# 🎯 SINGLE UPDATE SYSTEM: Enterprise Update System ONLY
try:
    from modules.update.enterprise import integrate_with_flask_app

    ENTERPRISE_UPDATE_AVAILABLE = True
    print("✅ Enterprise Update System loaded - SINGLE UPDATE SYSTEM")
except ImportError as e:
    ENTERPRISE_UPDATE_AVAILABLE = False
    print(f"❌ CRITICAL: Enterprise Update System not available: {e}")
    print("🚨 UPDATE SYSTEM DISABLED - No update functionality available")

    def integrate_with_flask_app(app, logger=None):
        """Disabled update system - Enterprise Update System not available"""
        if logger:
            logger.error("🚨 UPDATE SYSTEM DISABLED: Enterprise Update System not available")

        @app.route("/api/enterprise/deployment-info", methods=["GET"])
        def api_deployment_info_disabled():
            return {
                "status": "error",
                "message": "Update System Disabled - Enterprise Update System not available",
                "deployment_type": "unknown",
                "update_system": "disabled",
            }, 503

        @app.route("/api/enterprise/check-updates", methods=["GET"])
        def api_check_updates_disabled():
            return {
                "status": "error",
                "message": "Update System Disabled - Enterprise Update System not available",
                "troubleshooting": [
                    "Check that modules.update.enterprise imports correctly",
                    "Verify container deployment completed successfully",
                    "Check application logs for import errors",
                ],
            }, 503

        @app.route("/api/enterprise/start-update", methods=["POST"])
        def api_start_update_disabled():
            return {
                "status": "error",
                "message": "Update System Disabled - Enterprise Update System not available",
                "troubleshooting": [
                    "Check that modules.update.enterprise imports correctly",
                    "Verify container deployment completed successfully",
                    "Check application logs for import errors",
                ],
            }, 503

        @app.route("/api/enterprise/update-status", methods=["GET"])
        def api_update_status_disabled():
            return {
                "status": "error",
                "message": "Update System Disabled - Enterprise Update System not available",
                "update_state": "disabled",
            }, 503


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

# Initialize Enterprise Maintenance System
enterprise_maintenance = None
if MAINTENANCE_MANAGER_AVAILABLE and EnterpriseMaintenanceManager is not None:
    try:
        enterprise_maintenance = EnterpriseMaintenanceManager()
        logger.info("✅ Enterprise Maintenance System initialized")
    except Exception as e:
        logger.warning(f"⚠️ Enterprise Maintenance System initialization failed: {e}")
        enterprise_maintenance = None
else:
    logger.info("ℹ️ Enterprise Maintenance System not available")

# Initialize Model Manager and Chat History
try:
    model_manager = ModelManager()
    chat_history = ChatHistoryManager()
    logger.info("✅ Model Manager and Chat History initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize core components: {e}")
    # Use minimal fallback components
    model_manager = None
    chat_history = None

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

    # AdminPanel initialization without UpdateManager dependency
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
        <p><a href="/admin">Admin Panel</a> | <a href="/docs">API Docs</a></p>
        </body></html>
        """


# ==================== API ROUTES ====================


@app.route("/health")
def health():
    """Health check endpoint - Original functionality preserved"""
    uptime = (datetime.now() - system_stats["uptime_start"]).total_seconds()
    model_status = model_manager.get_status() if model_manager else {"status": "unavailable"}
    return jsonify(
        {
            "status": "healthy",
            "whisper_available": WHISPER_AVAILABLE,
            "version": "0.10.0",
            "uptime_seconds": uptime,
            "total_transcriptions": system_stats["total_transcriptions"],
            "active_connections": len(connected_clients),
            "system_ready": system_ready,
            "timestamp": datetime.now().isoformat(),
            "model_status": model_status,
            "update_system": "enterprise" if ENTERPRISE_UPDATE_AVAILABLE else "disabled",
        }
    )


# ==================== MODULE ROUTES ====================

# Register upload handler routes
if upload_handler:
    upload_handler.register_routes(app)

# Register live speech handler routes and websocket events
if live_speech_handler:
    live_speech_handler.register_routes(app)
    live_speech_handler.register_websocket_events(socketio)

# Register admin panel routes
if admin_panel:
    admin_panel.register_routes(app)

# Register API docs routes
if api_docs:
    api_docs.register_routes(app)


# ==================== MODEL MANAGEMENT ROUTES ====================


@app.route("/api/models", methods=["GET"])
def get_models():
    """Get available Whisper models"""
    if not model_manager:
        return jsonify({"error": "Model manager not available", "status": "error"}), 503

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
    if not model_manager:
        return jsonify({"error": "Model manager not available", "status": "error"}), 503

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


# ==================== CHAT HISTORY ROUTES ====================


@app.route("/api/chat-history", methods=["GET"])
def get_chat_history():
    """Get recent chat history"""
    if not chat_history:
        return jsonify({"error": "Chat history not available", "status": "error"}), 503

    limit = request.args.get("limit", 50, type=int)
    source_type = request.args.get("source", None)

    if source_type:
        transcriptions = chat_history.get_transcriptions_by_source(source_type, limit)
    else:
        transcriptions = chat_history.get_recent_transcriptions(limit)

    return jsonify({"transcriptions": transcriptions, "count": len(transcriptions), "status": "success"})


# Add more chat history routes here if needed...


# ==================== WEBSOCKET EVENTS ====================


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients.append(client_id)
    system_stats["active_connections"] = len(connected_clients)
    logger.info(f"Client connected: {client_id}")
    emit("connection_response", {"status": "connected", "client_id": client_id})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients.remove(client_id)
    system_stats["active_connections"] = len(connected_clients)
    logger.info(f"Client disconnected: {client_id}")


# ==================== STARTUP LOGIC ====================

# Initialize Enterprise Update System - SINGLE INTEGRATION POINT
if ENTERPRISE_UPDATE_AVAILABLE:
    logger.info("🏢 Initializing Enterprise Update System...")
    integrate_with_flask_app(app, logger)
    logger.info("✅ Enterprise Update System integrated - SINGLE UPDATE SYSTEM")
else:
    logger.warning("🚨 UPDATE SYSTEM DISABLED - Enterprise Update System not available")
    integrate_with_flask_app(app, logger)  # This will register disabled endpoints
    logger.warning("❌ Update functionality is not available")

if __name__ == "__main__":
    logger.info("🎤 Starting Enhanced WhisperS2T Appliance v0.10.0...")
    logger.info("🏗️ Architecture: Modular (live_speech, upload_handler, admin_panel, api_docs)")
    logger.info("🌐 SSL: Intelligent network certificate with SAN support")

    if ENTERPRISE_UPDATE_AVAILABLE:
        logger.info("🏢 Enterprise Update System: Single update system - functional")
    else:
        logger.info("🚨 Update System: DISABLED - Enterprise Update System not available")

    # Auto-detect SSL certificates
    ssl_context = None
    ssl_cert_path = os.path.join(current_dir, "..", "ssl", "whisper-appliance.crt")
    ssl_key_path = os.path.join(current_dir, "..", "ssl", "whisper-appliance.key")

    if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        ssl_context = (ssl_cert_path, ssl_key_path)
        logger.info("🔐 SSL certificates found - HTTPS enabled")
    else:
        logger.info("🔓 No SSL certificates found - HTTP mode")

    # Start the application
    try:
        socketio.run(app, host="0.0.0.0", port=5001, debug=False, ssl_context=ssl_context, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)
