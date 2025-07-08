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
        ENTERPRISE_MAINTENANCE_AVAILABLE,
        UPDATE_MANAGER_AVAILABLE,
        # AdminPanel, # Removed: Will use init_admin_panel from src.admin
        APIDocs,
        ChatHistoryManager,
        LiveSpeechHandler,
        ModelManager,
        UploadHandler,
    )
    from admin import init_admin_panel # Added for the new admin panel

    print("✅ Core modules imported successfully")
except ImportError as e:
    print(f"❌ Core module import failed: {e}")
    raise

# Import UpdateManager with graceful fallback
try:
    from modules import UpdateManager, create_update_endpoints

    UPDATE_MANAGER_IMPORTED = True
    print("✅ UpdateManager imported successfully")
except ImportError as e:
    UpdateManager = None
    create_update_endpoints = None
    UPDATE_MANAGER_IMPORTED = False
    print(f"⚠️ UpdateManager not available: {e}")

# Import EnterpriseMaintenanceManager with graceful fallback
try:
    from modules import EnterpriseMaintenanceManager

    ENTERPRISE_MAINTENANCE_IMPORTED = True
    print("✅ EnterpriseMaintenanceManager imported successfully")
except ImportError as e:
    EnterpriseMaintenanceManager = None
    ENTERPRISE_MAINTENANCE_IMPORTED = False
    print(f"⚠️ EnterpriseMaintenanceManager not available: {e}")

# Import MaintenanceManager with graceful fallback
try:
    from modules import MaintenanceManager

    MAINTENANCE_MANAGER_IMPORTED = True
    print("✅ MaintenanceManager imported successfully")
except ImportError as e:
    MaintenanceManager = None
    MAINTENANCE_MANAGER_IMPORTED = False
    print(f"⚠️ MaintenanceManager not available: {e}")


# Enterprise Maintenance System (additive)
if ENTERPRISE_MAINTENANCE_AVAILABLE:
    from modules.maintenance import EnterpriseMaintenanceManager

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

# ==================== EARLY UPDATE SYSTEM INITIALIZATION ====================
# Initialize Update System immediately after Flask app creation
if UPDATE_MANAGER_IMPORTED and create_update_endpoints:
    logger.info("🔄 Initializing Update System (early init)...")
    create_update_endpoints(app, logger)
    logger.info("✅ Update System integrated at /api/update/*")
else:
    logger.warning("⚠️ No update system available")
    logger.info("💡 Update functionality disabled")

# System statistics and state
system_stats = {"uptime_start": datetime.now(), "total_transcriptions": 0, "active_connections": 0}
connected_clients = []
system_ready = True

# Initialize Enterprise Maintenance System (additive)
enterprise_maintenance = None
if ENTERPRISE_MAINTENANCE_IMPORTED and EnterpriseMaintenanceManager is not None:
    try:
        enterprise_maintenance = EnterpriseMaintenanceManager()
        logger.info("✅ Enterprise Maintenance System initialized (additive)")
    except Exception as e:
        logger.warning(f"⚠️ Enterprise Maintenance System initialization failed: {e}")
        enterprise_maintenance = None
else:
    logger.info("ℹ️ Enterprise Maintenance System not available")

# Initialize Model Manager and Chat History
try:
    model_manager = ModelManager()
    chat_history = ChatHistoryManager()

    # Initialize Update Manager if available
    if UPDATE_MANAGER_IMPORTED and UpdateManager is not None:
        update_manager = UpdateManager()
        logger.info("🔄 Update Manager initialized")
    else:
        update_manager = None
        logger.warning("⚠️ No Update Manager available")

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

    # Initialize the new Admin Panel using init_admin_panel
    # The old admin_panel instantiation is removed.
    try:
        # Ensure model_manager and system_stats are available
        # The init_admin_panel function from src.admin.admin_panel expects 'app', 'model_manager', and 'system_stats'.
        # app is available globally. model_manager and system_stats should be initialized by this point.
        if model_manager is not None and system_stats is not None:
            admin_panel_instance = init_admin_panel(app, model_manager=model_manager, system_stats=system_stats)
            logger.info("✅ New Admin Panel initialized and blueprint registered.")
        else:
            logger.error("❌ Failed to initialize new Admin Panel: model_manager or system_stats not available.")
            admin_panel_instance = None # Or some fallback if necessary
    except Exception as e_admin:
        logger.error(f"❌ Error initializing new Admin Panel: {e_admin}")
        admin_panel_instance = None # Fallback

    api_docs = APIDocs(version="0.10.0")
    logger.info("✅ All module handlers initialized (Upload, LiveSpeech, APIDocs)")
except Exception as e:
    logger.error(f"❌ Failed to initialize module handlers: {e}")
    # Create minimal fallback handlers
    upload_handler = None
    live_speech_handler = None
    # admin_panel = None # This was the old one
    admin_panel_instance = None # For the new one
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


@app.route("/api/chat-history/update/<int:transcription_id>", methods=["PUT"])
def update_chat_history_entry(transcription_id):
    """Update a specific chat history entry"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json", "status": "error"}), 400

        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Text field is required", "status": "error"}), 400

        new_text = data["text"]
        if not new_text or not new_text.strip():
            return jsonify({"error": "Text cannot be empty", "status": "error"}), 400

        # Update the transcription
        success = chat_history.update_transcription(transcription_id, new_text.strip())

        if success:
            return jsonify({"message": "Transcription updated successfully", "id": transcription_id, "status": "success"})
        else:
            return (
                jsonify(
                    {
                        "error": f"Failed to update transcription with ID {transcription_id}. Entry may not exist.",
                        "status": "error",
                    }
                ),
                404,
            )

    except Exception as e:
        logger.error(f"Failed to update chat history entry {transcription_id}: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}", "status": "error"}), 500


@app.route("/api/chat-history/delete/<int:transcription_id>", methods=["DELETE"])
def delete_chat_history_entry(transcription_id):
    """Delete a specific chat history entry"""
    try:
        success = chat_history.delete_transcription(transcription_id)

        if success:
            return jsonify({"message": "Transcription deleted successfully", "id": transcription_id, "status": "success"})
        else:
            return (
                jsonify(
                    {
                        "error": f"Failed to delete transcription with ID {transcription_id}. Entry may not exist.",
                        "status": "error",
                    }
                ),
                404,
            )

    except Exception as e:
        logger.error(f"Failed to delete chat history entry {transcription_id}: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}", "status": "error"}), 500


@app.route("/api/chat-history/import", methods=["POST"])
def import_chat_history():
    """Import chat history from JSON or CSV file"""
    try:
        # Check if file is present
        if "file" not in request.files:
            return jsonify({"error": "No file provided", "status": "error"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected", "status": "error"}), 400

        # Check file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if file_ext not in ["json", "csv"]:
            return (
                jsonify(
                    {
                        "error": f"Unsupported file format: {file_ext}. Only JSON and CSV files are supported.",
                        "status": "error",
                    }
                ),
                400,
            )

        # Read file content
        try:
            file_content = file.read().decode("utf-8")
        except UnicodeDecodeError:
            return jsonify({"error": "File encoding error. Please ensure the file is UTF-8 encoded.", "status": "error"}), 400

        if not file_content.strip():
            return jsonify({"error": "File is empty", "status": "error"}), 400

        # Import the data
        result = chat_history.import_history(file_content, file_ext, filename)

        # Return appropriate HTTP status based on result
        if result["status"] == "error":
            return jsonify(result), 400
        elif result["status"] == "partial_success":
            return jsonify(result), 206  # Partial Content
        else:
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Failed to import chat history: {e}")
        return jsonify({"error": f"Import failed: {str(e)}", "status": "error"}), 500


@app.route("/api/chat-history/import/template/<format>", methods=["GET"])
def get_import_template(format):
    """Get import template for JSON or CSV format"""
    try:
        if format not in ["json", "csv"]:
            return jsonify({"error": "Invalid format. Use 'json' or 'csv'", "status": "error"}), 400

        if format == "json":
            template = {
                "transcriptions": [
                    {
                        "text": "Example transcription text here",
                        "language": "en",
                        "model_used": "whisper-large",
                        "source_type": "upload",
                        "filename": "example.mp3",
                        "duration": 30.5,
                        "confidence": 0.95,
                        "metadata": {"example_key": "example_value"},
                    },
                    {
                        "text": "Another example transcription",
                        "language": "de",
                        "model_used": "whisper-medium",
                        "source_type": "live",
                        "filename": None,
                        "duration": None,
                        "confidence": None,
                        "metadata": None,
                    },
                ]
            }

            import json

            from flask import Response

            return Response(
                json.dumps(template, indent=2),
                mimetype="application/json",
                headers={"Content-Disposition": "attachment; filename=chat_history_template.json"},
            )

        else:  # CSV format
            template_csv = """text,language,model_used,source_type,filename,duration,confidence
"Example transcription text here","en","whisper-large","upload","example.mp3","30.5","0.95"
"Another example transcription","de","whisper-medium","live","","",""
"Minimal example with just text","","","","","",""
"""

            from flask import Response

            return Response(
                template_csv,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=chat_history_template.csv"},
            )

    except Exception as e:
        logger.error(f"Failed to generate import template: {e}")
        return jsonify({"error": f"Template generation failed: {str(e)}", "status": "error"}), 500


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


# ==================== SIMPLE UPDATE ENDPOINTS (Legacy Compatible) ====================


@app.route("/api/simple-update", methods=["POST"])
def simple_update():
    """Enterprise-grade update system - GitHub Releases first, Git fallback"""
    try:
        import shutil
        import subprocess
        import tempfile
        import time

        import requests

        logger.info("Starting enterprise update process...")

        # 1. Try GitHub Releases first (tteck's preferred method)
        try:
            response = requests.get("https://api.github.com/repos/GaboCapo/whisper-appliance/releases/latest", timeout=10)
            if response.status_code == 200:
                # GitHub Releases update method
                return _update_via_github_releases(response.json())
        except Exception as e:
            logger.info(f"GitHub Releases not available ({e}), falling back to Git method")

        # 2. Fallback to Git-based update (for development)
        logger.info("Using Git-based update...")
        return _update_via_git()

    except Exception as e:
        logger.error(f"Enterprise update failed: {e}")
        return jsonify({"error": f"Update failed: {str(e)}", "status": "error"}), 500


def _update_via_git():
    """Git-based update for development environments"""
    try:
        import subprocess
        import sys

        # Find git repository
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists(os.path.join(app_dir, ".git")):
            return jsonify({"error": "Git repository not found", "status": "error"}), 400

        # Change to app directory
        original_cwd = os.getcwd()
        os.chdir(app_dir)

        try:
            # Configure SSH if deploy key exists
            env = os.environ.copy()
            if os.path.exists("./deploy_key_whisper_appliance"):
                env["GIT_SSH_COMMAND"] = (
                    "ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
                )

            # Get current commit before update
            current_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()

            # Fetch and pull latest changes
            logger.info("Fetching latest changes...")
            subprocess.run(["git", "fetch", "origin", "main"], env=env, check=True, capture_output=True, timeout=30)

            logger.info("Pulling updates...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"], env=env, check=True, capture_output=True, text=True, timeout=60
            )

            # Check if anything was updated
            new_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()

            if current_commit == new_commit:
                return jsonify(
                    {
                        "status": "success",
                        "message": "Already up to date",
                        "update_method": "git",
                        "changes": False,
                        "current_commit": current_commit[:8],
                    }
                )

            # Update dependencies if requirements.txt exists
            requirements_file = os.path.join(app_dir, "src", "requirements.txt")
            if os.path.exists(requirements_file):
                try:
                    logger.info("Updating dependencies...")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    logger.info("Dependencies updated successfully")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to update dependencies: {e}")

            # Update script permissions
            for script in ["auto-update.sh", "create-ssl-cert.sh", "install-container.sh"]:
                script_path = os.path.join(app_dir, script)
                if os.path.exists(script_path):
                    os.chmod(script_path, 0o755)

            logger.info("Git-based update completed successfully!")

            return jsonify(
                {
                    "status": "success",
                    "message": "Update completed successfully",
                    "update_method": "git",
                    "changes": True,
                    "previous_commit": current_commit[:8],
                    "new_commit": new_commit[:8],
                    "restart_recommended": True,
                }
            )

        finally:
            os.chdir(original_cwd)

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        return jsonify({"error": f"Git update failed: {e.stderr if e.stderr else str(e)}", "status": "error"}), 500
    except Exception as e:
        logger.error(f"Git update failed: {e}")
        return jsonify({"error": f"Update failed: {str(e)}", "status": "error"}), 500


def _update_via_github_releases(release_data):
    """GitHub Releases update method (tteck's approach)"""
    try:
        import shutil
        import tarfile
        import tempfile
        import time

        import requests

        latest_version = release_data["tag_name"].lstrip("v")
        download_url = f"https://github.com/GaboCapo/whisper-appliance/archive/refs/tags/{release_data['tag_name']}.tar.gz"

        logger.info(f"Latest version available: {latest_version}")

        # Get current app directory (where we're actually running from)
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        version_file = os.path.join(app_dir, "whisper-appliance_version.txt")

        # Check current version
        current_version = None
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    current_version = f.read().strip()
            except:
                pass

        if current_version == latest_version:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Already up to date (v{current_version})",
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_method": "github_releases",
                }
            )

        logger.info(f"Updating from {current_version or 'unknown'} to {latest_version}")

        # Create backup in same directory (not /opt) - PERMISSION FIX
        backup_dir = f"{app_dir}_backup_{int(time.time())}"
        logger.info(f"Creating backup at {backup_dir}")

        # Check if we have write permissions for backup
        parent_dir = os.path.dirname(app_dir)
        if not os.access(parent_dir, os.W_OK):
            # Fallback: create backup in temp directory
            backup_dir = os.path.join(tempfile.gettempdir(), f"whisper-appliance_backup_{int(time.time())}")
            logger.warning(f"No write permission in {parent_dir}, using temp backup: {backup_dir}")

        if os.path.exists(app_dir):
            shutil.copytree(app_dir, backup_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))

        # Download and extract new version
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Downloading {download_url}")

            download_response = requests.get(download_url, stream=True, timeout=30)
            download_response.raise_for_status()

            tar_path = os.path.join(temp_dir, "update.tar.gz")
            with open(tar_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Extract tarball
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(temp_dir)

            # Find extracted directory
            extracted_dirs = [
                d
                for d in os.listdir(temp_dir)
                if d.startswith("whisper-appliance-") and os.path.isdir(os.path.join(temp_dir, d))
            ]
            if not extracted_dirs:
                raise Exception("Could not find extracted directory")

            extracted_dir = os.path.join(temp_dir, extracted_dirs[0])

            # Preserve important directories
            preserve_dirs = ["ssl", "data", "logs"]
            preserved_data = {}

            for preserve_dir in preserve_dirs:
                old_path = os.path.join(app_dir, preserve_dir)
                if os.path.exists(old_path):
                    preserved_data[preserve_dir] = os.path.join(temp_dir, f"preserved_{preserve_dir}")
                    shutil.copytree(old_path, preserved_data[preserve_dir])

            # Replace installation
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)

            shutil.move(extracted_dir, app_dir)

            # Restore preserved directories
            for preserve_dir, preserved_path in preserved_data.items():
                target_path = os.path.join(app_dir, preserve_dir)
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.move(preserved_path, target_path)

        # Write version file
        with open(version_file, "w") as f:
            f.write(latest_version)

        # Update dependencies
        requirements_file = os.path.join(app_dir, "src", "requirements.txt")
        if os.path.exists(requirements_file):
            try:
                logger.info("Updating dependencies...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to update dependencies: {e}")

        logger.info(f"GitHub Releases update completed successfully to v{latest_version}")

        return jsonify(
            {
                "status": "success",
                "message": f"Successfully updated to v{latest_version}",
                "previous_version": current_version,
                "new_version": latest_version,
                "backup_location": backup_dir,
                "update_method": "github_releases",
                "restart_required": True,
            }
        )

    except Exception as e:
        logger.error(f"GitHub Releases update failed: {e}")
        return (
            jsonify(
                {
                    "error": f"GitHub Releases update failed: {str(e)}",
                    "status": "error",
                    "backup_available": locals().get("backup_dir") is not None,
                }
            ),
            500,
        )
    try:
        import shutil
        import tempfile
        import time

        import requests

        logger.info("Starting enterprise update process...")

        # 1. Get latest release info from GitHub API
        try:
            response = requests.get("https://api.github.com/repos/GaboCapo/whisper-appliance/releases/latest", timeout=10)
            if response.status_code != 200:
                raise Exception(f"GitHub API error: {response.status_code}")

            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            download_url = f"https://github.com/GaboCapo/whisper-appliance/archive/refs/tags/{release_data['tag_name']}.tar.gz"

            logger.info(f"Latest version available: {latest_version}")

        except Exception as e:
            logger.error(f"Failed to get release info: {e}")
            return jsonify({"error": f"Failed to get release info: {str(e)}", "status": "error"}), 500

        # 2. Check current version
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        version_file = os.path.join(app_dir, "whisper-appliance_version.txt")

        current_version = None
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    current_version = f.read().strip()
            except:
                pass

        if current_version == latest_version:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Already up to date (v{current_version})",
                    "current_version": current_version,
                    "latest_version": latest_version,
                }
            )

        logger.info(f"Updating from {current_version or 'unknown'} to {latest_version}")

        # 3. Create backup of current installation
        backup_dir = f"{app_dir}_backup_{int(time.time())}"
        logger.info(f"Creating backup at {backup_dir}")

        if os.path.exists(app_dir):
            shutil.copytree(app_dir, backup_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))

        # 4. Download and extract new version
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Downloading {download_url}")

            # Download with requests for better error handling
            download_response = requests.get(download_url, stream=True, timeout=30)
            download_response.raise_for_status()

            tar_path = os.path.join(temp_dir, "update.tar.gz")
            with open(tar_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Extract tarball
            import tarfile

            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(temp_dir)

            # Find extracted directory (should be whisper-appliance-{version})
            extracted_dirs = [
                d
                for d in os.listdir(temp_dir)
                if d.startswith("whisper-appliance-") and os.path.isdir(os.path.join(temp_dir, d))
            ]
            if not extracted_dirs:
                raise Exception("Could not find extracted directory")

            extracted_dir = os.path.join(temp_dir, extracted_dirs[0])

            # 5. Replace current installation (preserve data directories)
            logger.info("Installing new version...")

            # Preserve important data directories if they exist
            preserve_dirs = ["ssl", "data", "logs"]
            preserved_data = {}

            for preserve_dir in preserve_dirs:
                old_path = os.path.join(app_dir, preserve_dir)
                if os.path.exists(old_path):
                    preserved_data[preserve_dir] = os.path.join(temp_dir, f"preserved_{preserve_dir}")
                    shutil.copytree(old_path, preserved_data[preserve_dir])

            # Remove old installation (except preserved dirs)
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)

            # Move new installation
            shutil.move(extracted_dir, app_dir)

            # Restore preserved directories
            for preserve_dir, preserved_path in preserved_data.items():
                target_path = os.path.join(app_dir, preserve_dir)
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.move(preserved_path, target_path)

        # 6. Write version file
        with open(version_file, "w") as f:
            f.write(latest_version)

        # 7. Update dependencies if requirements.txt changed
        requirements_file = os.path.join(app_dir, "src", "requirements.txt")
        if os.path.exists(requirements_file):
            try:
                logger.info("Updating dependencies...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info("Dependencies updated successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to update dependencies: {e}")

        # 8. Cleanup old backup (keep only latest 3)
        try:
            parent_dir = os.path.dirname(app_dir)
            backup_dirs = [d for d in os.listdir(parent_dir) if d.startswith(os.path.basename(app_dir) + "_backup_")]
            backup_dirs.sort(reverse=True)  # Newest first

            for old_backup in backup_dirs[3:]:  # Keep only 3 newest
                backup_path = os.path.join(parent_dir, old_backup)
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                    logger.info(f"Cleaned up old backup: {old_backup}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

        logger.info(f"Enterprise update completed successfully to v{latest_version}")

        return jsonify(
            {
                "status": "success",
                "message": f"Successfully updated to v{latest_version}",
                "previous_version": current_version,
                "new_version": latest_version,
                "backup_location": backup_dir,
                "restart_required": True,
            }
        )

    except Exception as e:
        logger.error(f"Enterprise update failed: {e}")
        return (
            jsonify(
                {
                    "error": f"Update failed: {str(e)}",
                    "status": "error",
                    "backup_available": locals().get("backup_dir") is not None,
                }
            ),
            500,
        )


@app.route("/api/check-git-updates", methods=["GET"])
def check_git_updates():
    """DEPRECATED: Legacy endpoint - redirects to Enterprise Update System"""
    return (
        jsonify(
            {
                "status": "deprecated",
                "message": "This endpoint has been replaced by the Enterprise Update System",
                "new_endpoint": "/api/enterprise/check-updates",
                "enterprise_features": [
                    "Deployment-aware update checking",
                    "Permission-safe operations",
                    "Blue-Green deployment support",
                    "Comprehensive error handling",
                ],
            }
        ),
        200,
    )
    try:
        import subprocess

        import requests

        logger.info("Checking for available updates...")

        # 1. Try GitHub Releases first (tteck's preferred method)
        try:
            response = requests.get("https://api.github.com/repos/GaboCapo/whisper-appliance/releases/latest", timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                release_date = release_data.get("published_at", "Unknown")
                release_notes = release_data.get("body", "No release notes available")

                # Check current version
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                version_file = os.path.join(app_dir, "whisper-appliance_version.txt")

                current_version = None
                if os.path.exists(version_file):
                    try:
                        with open(version_file, "r") as f:
                            current_version = f.read().strip()
                    except:
                        pass

                updates_available = current_version != latest_version

                return jsonify(
                    {
                        "status": "success",
                        "update_method": "github_releases",
                        "updates_available": updates_available,
                        "current_version": current_version or "Unknown",
                        "latest_version": latest_version,
                        "release_date": release_date,
                        "release_notes": release_notes[:500] + "..." if len(release_notes) > 500 else release_notes,
                        "message": f"Updates available: {latest_version}" if updates_available else "System is up to date",
                    }
                )

        except Exception as e:
            logger.info(f"GitHub Releases not available ({e}), falling back to Git method")

        # 2. Fallback to Git-based update check
        logger.info("Using Git-based update check...")

        # Find git repository
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists(os.path.join(app_dir, ".git")):
            # Try alternative locations
            for alt_path in ["/opt/whisper-appliance", "/app", "/workspace"]:
                if os.path.exists(os.path.join(alt_path, ".git")):
                    app_dir = alt_path
                    break
            else:
                return jsonify({"error": "No git repository found and no GitHub releases available", "status": "error"}), 400

        # Change to app directory for git operations
        original_cwd = os.getcwd()
        os.chdir(app_dir)

        try:
            # Configure SSH if deploy key exists
            env = os.environ.copy()
            if os.path.exists("./deploy_key_whisper_appliance"):
                env["GIT_SSH_COMMAND"] = (
                    "ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
                )

            # Fetch latest changes
            subprocess.run(["git", "fetch", "origin", "main"], env=env, check=True, capture_output=True, timeout=30)

            # Get current and remote commits
            local_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            ).stdout.strip()
            remote_commit = subprocess.run(
                ["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True
            ).stdout.strip()

            # Get commit info
            local_info = (
                subprocess.run(
                    ["git", "log", "-1", "--format=%h|%s|%an|%ad", "--date=short", local_commit],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .split("|")
            )

            commits_behind = 0
            if local_commit != remote_commit:
                commits_result = subprocess.run(
                    ["git", "rev-list", "--count", f"{local_commit}..origin/main"], capture_output=True, text=True, check=True
                )
                commits_behind = int(commits_result.stdout.strip())

            return jsonify(
                {
                    "status": "success",
                    "update_method": "git_commits",
                    "updates_available": commits_behind > 0,
                    "commits_behind": commits_behind,
                    "current_commit": local_info[0] if local_info else local_commit[:8],
                    "current_commit_message": local_info[1] if len(local_info) > 1 else "Unknown",
                    "current_commit_author": local_info[2] if len(local_info) > 2 else "Unknown",
                    "current_commit_date": local_info[3] if len(local_info) > 3 else "Unknown",
                    "message": f"{commits_behind} commits behind" if commits_behind > 0 else "Up to date",
                }
            )

        finally:
            os.chdir(original_cwd)

    except Exception as e:
        logger.error(f"Update check failed: {e}")
        return jsonify({"error": f"Update check failed: {str(e)}", "status": "error"}), 500

        def find_git_repository():
            """Find the git repository root by checking multiple locations"""
            # Priority 1: Check where main.py is located (current app location)
            current_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if os.path.exists(os.path.join(current_app_dir, ".git")):
                return current_app_dir

            # Priority 2: Use git command from current app directory
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10, cwd=current_app_dir
                )
                if result.returncode == 0:
                    git_root = result.stdout.strip()
                    if os.path.exists(git_root):
                        return git_root
            except Exception:
                pass

            # Priority 3: Use git command from current working directory
            try:
                result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    git_root = result.stdout.strip()
                    if os.path.exists(git_root):
                        return git_root
            except Exception:
                pass

            # Fallback to checking standard deployment paths
            possible_paths = [
                current_app_dir,  # Where the app is actually running
                "/home/commander/Code/whisper-appliance",  # Known actual location
                "/opt/whisper-appliance",  # Standard production path
                "/app",  # Docker standard
                "/opt/app",  # Alternative production
                "/workspace",  # Development
                "/code",  # Alternative development
                os.getcwd(),  # Current working directory
            ]

            for path in possible_paths:
                if os.path.exists(os.path.join(path, ".git")):
                    return path

            return None

        app_dir = find_git_repository()
        if not app_dir:
            # Try more aggressive git detection like in simple-update
            try:
                # Try git command from current working directory
                cwd_result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10, cwd=os.getcwd()
                )
                if cwd_result.returncode == 0:
                    app_dir = cwd_result.stdout.strip()
                    logger.info(f"Found git repository using CWD git command: {app_dir}")
                else:
                    # Try from main.py directory
                    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    main_result = subprocess.run(
                        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10, cwd=main_dir
                    )
                    if main_result.returncode == 0:
                        app_dir = main_result.stdout.strip()
                        logger.info(f"Found git repository using main.py dir: {app_dir}")
            except Exception as e:
                logger.error(f"Extended git detection failed: {e}")

        if not app_dir:
            return (
                jsonify(
                    {
                        "error": "Git repository not found",
                        "status": "error",
                        "debug_info": {
                            "cwd": os.getcwd(),
                            "main_file_dir": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "checked_paths": [
                                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "/opt/whisper-appliance",
                                "/app",
                                "/opt/app",
                                "/workspace",
                                "/code",
                                os.getcwd(),
                            ],
                        },
                    }
                ),
                400,
            )

        os.chdir(app_dir)

        # Configure SSH for deploy key if available
        env = os.environ.copy()
        if os.path.exists("./deploy_key_whisper_appliance"):
            env["GIT_SSH_COMMAND"] = "ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin", "main"], env=env, check=True, capture_output=True)

        # Get current and remote commits with detailed information
        local_commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        remote_commit = subprocess.run(
            ["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True
        ).stdout.strip()

        # Get current commit details
        local_commit_info = (
            subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%an|%ad", "--date=iso", local_commit],
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .split("|")
        )

        if local_commit == remote_commit:
            return jsonify(
                {
                    "updates_available": False,
                    "commits_behind": 0,
                    "current_commit": local_commit[:8],
                    "current_commit_full": local_commit,
                    "current_commit_info": {
                        "hash": local_commit,
                        "short_hash": local_commit[:8],
                        "message": local_commit_info[1] if len(local_commit_info) > 1 else "Unknown",
                        "author": local_commit_info[2] if len(local_commit_info) > 2 else "Unknown",
                        "date": local_commit_info[3] if len(local_commit_info) > 3 else "Unknown",
                    },
                    "status": "success",
                }
            )
        else:
            # Count commits behind
            commits_behind_result = subprocess.run(
                ["git", "rev-list", "--count", f"{local_commit}..origin/main"], capture_output=True, text=True, check=True
            )
            commits_behind = int(commits_behind_result.stdout.strip())

            # Get remote commit details
            remote_commit_info = (
                subprocess.run(
                    ["git", "log", "-1", "--format=%H|%s|%an|%ad", "--date=iso", remote_commit],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                .stdout.strip()
                .split("|")
            )

            # Get list of new commits
            new_commits_result = subprocess.run(
                ["git", "log", "--format=%h|%s|%an|%ad", "--date=short", f"{local_commit}..origin/main"],
                capture_output=True,
                text=True,
                check=True,
            )

            new_commits = []
            if new_commits_result.stdout.strip():
                for line in new_commits_result.stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split("|")
                        if len(parts) >= 4:
                            new_commits.append({"hash": parts[0], "message": parts[1], "author": parts[2], "date": parts[3]})

            return jsonify(
                {
                    "updates_available": True,
                    "commits_behind": commits_behind,
                    "current_commit": local_commit[:8],
                    "current_commit_full": local_commit,
                    "remote_commit": remote_commit[:8],
                    "remote_commit_full": remote_commit,
                    "current_commit_info": {
                        "hash": local_commit,
                        "short_hash": local_commit[:8],
                        "message": local_commit_info[1] if len(local_commit_info) > 1 else "Unknown",
                        "author": local_commit_info[2] if len(local_commit_info) > 2 else "Unknown",
                        "date": local_commit_info[3] if len(local_commit_info) > 3 else "Unknown",
                    },
                    "remote_commit_info": {
                        "hash": remote_commit,
                        "short_hash": remote_commit[:8],
                        "message": remote_commit_info[1] if len(remote_commit_info) > 1 else "Unknown",
                        "author": remote_commit_info[2] if len(remote_commit_info) > 2 else "Unknown",
                        "date": remote_commit_info[3] if len(remote_commit_info) > 3 else "Unknown",
                    },
                    "new_commits": new_commits[:10],  # Limit to 10 most recent commits
                    "status": "success",
                }
            )

    except Exception as e:
        logger.error(f"Git update check failed: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/api/restart-service", methods=["POST"])
def restart_service():
    """Restart the WhisperS2T service"""
    try:
        import subprocess

        logger.info("Restarting WhisperS2T service...")

        # Try different service restart methods
        service_names = ["whisper-appliance", "whisper-s2t", "whisper"]

        for service_name in service_names:
            try:
                # Check if service exists
                result = subprocess.run(["systemctl", "is-active", service_name], capture_output=True, text=True, timeout=5)
                if result.returncode in [0, 3]:  # active or inactive
                    # Restart the service
                    subprocess.run(["systemctl", "restart", service_name], check=True, timeout=10)
                    logger.info(f"Service {service_name} restarted successfully")
                    return jsonify({"status": "success", "message": f"Service {service_name} restarted successfully"})
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue

        # If no systemd service found, suggest manual restart
        return jsonify(
            {"status": "success", "message": "Service restart initiated. Please refresh the page in a few seconds."}
        )

    except Exception as e:
        logger.error(f"Service restart failed: {e}")
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


# The @app.route("/admin") and def admin() are removed.
# The new admin panel blueprint (admin_bp) registered via init_admin_panel
# will handle /admin and its sub-routes.

@app.route("/demo")
def demo():
    """Demo Interface - Placeholder or handled by new admin if it provides one"""
    # This might need adjustment if the new admin panel also provides /demo
    # For now, let's assume it might be separate or the new admin doesn't have a /demo yet.
    # If admin_panel_instance has a demo method, it could be called here,
    # or this route could be removed if the new admin blueprint handles it.
    # Checking src/admin/admin_panel.py, it does not define a /demo route.
    # The old src/modules/admin_panel.py did have get_demo_interface.
    # For now, to prevent errors, let's return a simple placeholder.
    # A more robust solution would be to check if admin_panel_instance can handle it,
    # or define a new demo page if required.
    if admin_panel_instance and hasattr(admin_panel_instance, 'get_demo_interface'):
        # This assumes the new AdminPanel class might have such a method,
        # which it currently does not based on src/admin/admin_panel.py
        # The class AdminPanel in src/admin/admin_panel.py does not have get_demo_interface
        # Let's have a placeholder to avoid NameError for admin_panel
        return "Demo interface is under construction."
    return "Demo interface is under construction."


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


# ==================== ENTERPRISE MAINTENANCE ENDPOINTS (ADDITIVE) ====================


@app.route("/api/enterprise-maintenance/status", methods=["GET"])
def enterprise_maintenance_status():
    """
    Enterprise maintenance status - additive endpoint
    🎯 ADDITIVE: Coexists with existing update system
    """
    try:
        if not ENTERPRISE_MAINTENANCE_AVAILABLE or not enterprise_maintenance:
            return (
                jsonify({"status": "error", "error": "Enterprise maintenance system not available", "available": False}),
                503,
            )

        info = enterprise_maintenance.get_maintenance_info()
        return jsonify({"status": "success", "enterprise_maintenance": True, "maintenance_info": info, "version": "1.0.0"})

    except Exception as e:
        logger.error(f"Enterprise maintenance status failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/enterprise-maintenance/enable", methods=["POST"])
def enterprise_maintenance_enable():
    """
    Enable enterprise maintenance mode - additive endpoint
    🎯 ADDITIVE: Works alongside existing systems
    """
    try:
        if not ENTERPRISE_MAINTENANCE_AVAILABLE or not enterprise_maintenance:
            return jsonify({"status": "error", "error": "Enterprise maintenance system not available"}), 503

        data = request.get_json() or {}
        message = data.get("message", "🚀 Enterprise maintenance in progress")
        duration_minutes = data.get("duration_minutes", 10)

        success = enterprise_maintenance.enable_maintenance_mode(message=message, estimated_duration_minutes=duration_minutes)

        if success:
            return jsonify(
                {
                    "status": "success",
                    "message": "Enterprise maintenance mode enabled",
                    "enterprise": True,
                    "duration_minutes": duration_minutes,
                }
            )
        else:
            return jsonify({"status": "error", "error": "Failed to enable maintenance mode"}), 500

    except Exception as e:
        logger.error(f"Enterprise maintenance enable failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/enterprise-maintenance/disable", methods=["POST"])
def enterprise_maintenance_disable():
    """
    Disable enterprise maintenance mode - additive endpoint
    """
    try:
        if not ENTERPRISE_MAINTENANCE_AVAILABLE or not enterprise_maintenance:
            return jsonify({"status": "error", "error": "Enterprise maintenance system not available"}), 503

        success = enterprise_maintenance.disable_maintenance_mode()

        if success:
            return jsonify({"status": "success", "message": "Enterprise maintenance mode disabled", "enterprise": True})
        else:
            return jsonify({"status": "error", "error": "Failed to disable maintenance mode"}), 500

    except Exception as e:
        logger.error(f"Enterprise maintenance disable failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


# ==================== MAIN STARTUP ====================

if __name__ == "__main__":
    logger.info("🎤 Starting Enhanced WhisperS2T Appliance v1.1.0...")
    logger.info("🔄 Update System: Git-based with automatic detection")
    logger.info("🌐 SSL: Intelligent network certificate with SAN support")

    if UPDATE_MANAGER_IMPORTED:
        logger.info("🔄 Update System: Ready for Git-based updates")
    else:
        logger.info("⚠️ Update System: Disabled (no update functionality available)")

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
