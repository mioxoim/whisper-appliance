"""
WhisperAppliance Admin Panel Module
Modular admin interface with enhanced features
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, render_template, send_from_directory, request

from .model_status import ModelStatusManager
from .system_monitor import SystemMonitor
from .communication_log import CommunicationLog # Added import

logger = logging.getLogger(__name__)

# Function to create the admin blueprint
def create_admin_blueprint():
    return Blueprint('admin', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/admin/static')

# Global admin_bp for non-test scenarios, or tests that don't need isolation.
# For isolated tests, a new blueprint will be created and passed.
admin_bp = create_admin_blueprint()


class AdminPanel:
    """Enhanced Admin Panel with modular architecture"""

    def __init__(self, app, blueprint, model_manager=None, system_stats=None): # Added blueprint parameter
        self.app = app
        self.blueprint = blueprint # Store the blueprint
        self.model_manager = model_manager
        self.system_stats = system_stats or {
            "uptime_start": datetime.now(),
            "total_transcriptions": 0,
            "transcriptions_by_source": {"live": 0, "upload": 0, "api": 0}
        }

        # Initialize sub-modules
        self.model_status = ModelStatusManager(model_manager)
        self.system_monitor = SystemMonitor(self.system_stats)
        self.communication_log = CommunicationLog()

        # Register routes on the provided blueprint
        self._register_routes(self.blueprint)

        logger.info("WhisperAppliance Admin Panel initialized with blueprint: %s", blueprint.name)

    def _register_routes(self, bp): # Takes blueprint as parameter
        """Register admin routes on the given blueprint"""
        # Main admin page
        @bp.route('/admin')
        def admin_dashboard():
            # Ensure self.system_monitor and other necessary components are available
            # This might require passing them or ensuring AdminPanel has them correctly initialized
            return render_template('admin-dashboard.html',
                                 system_info=self.system_monitor.get_system_info(),
                                 model_info=self.model_status.get_model_info(),
                                 communication_logs=self.communication_log.get_logs())

        # Model management page
        @bp.route('/admin/models')
        def admin_models():
            return render_template('admin-models.html',
                                 models=self.model_status.get_detailed_model_info())

        # Settings page
        @bp.route('/admin/settings')
        def admin_settings():
            return render_template('admin-settings.html')

        # API endpoints
        @bp.route('/api/v1/system/status')
        def api_system_status():
            return jsonify(self.system_monitor.get_system_status())

        @bp.route('/api/v1/models/status')
        def api_model_status():
            if not self.model_manager:
                return jsonify({"error": "ModelManager not initialized"}), 500

            status_data = self.model_manager.get_status()
            # Adapt to the structure expected by admin-models.js
            # admin-models.js expects:
            # data.available -> dict of model_id: {name, size, ...}
            # data.downloaded -> list of model_id strings
            # data.current -> string model_id
            js_expected_status = {
                "available": status_data.get("available_models_info", {}),
                "downloaded": status_data.get("downloaded_model_ids", []),
                "current": status_data.get("current_model_name", None)
                # We can include other info if needed, but these are primary for current JS
            }
            return jsonify(js_expected_status)

        @bp.route('/api/v1/models/download/<string:model_id>', methods=['POST'])
        def api_start_model_download(model_id):
            if not self.model_manager:
                return jsonify({"status": "error", "message": "ModelManager not initialized"}), 500
            if model_id not in self.model_manager.get_available_models():
                return jsonify({"status": "error", "message": "Invalid model ID"}), 404

            success = self.model_manager.start_download_model(model_id)
            if success:
                # Check if already downloaded or already in progress to provide specific message
                if self.model_manager.is_model_downloaded(model_id):
                     # Check progress to see if it was just marked as completed by start_download_model
                    progress = self.model_manager.get_download_progress(model_id)
                    if progress and progress.get("status") == "completed":
                        return jsonify({"status": "success", "message": f"Model {model_id} is already downloaded."})

                progress = self.model_manager.get_download_progress(model_id)
                if progress and progress.get("status") == "downloading":
                    return jsonify({"status": "success", "message": f"Download for model {model_id} is already in progress."})

                return jsonify({"status": "success", "message": f"Download started for model {model_id}."})
            else:
                # Attempt to get a more specific error if available
                progress = self.model_manager.get_download_progress(model_id)
                error_message = "Failed to start download."
                if progress and progress.get("error_message"):
                    error_message = progress.get("error_message")
                elif not self.model_manager.whisper_available:
                    error_message = "Whisper library not available to initiate download."
                return jsonify({"status": "error", "message": error_message}), 500

        @bp.route('/api/v1/models/download/<string:model_id>/progress', methods=['GET'])
        def api_get_model_download_progress(model_id):
            if not self.model_manager:
                return jsonify({"status": "error", "message": "ModelManager not initialized"}), 500
            if model_id not in self.model_manager.get_available_models(): # Also check against available models
                # If not an available model, it might be a custom one, or an old entry.
                # However, progress is typically for known models.
                # For now, let's assume we only query progress for models listed in AVAILABLE_MODELS.
                # If model_id is not in download_progress, get_download_progress returns None.
                 pass # Allow querying progress for any model_id that might be in download_progress

            progress_data = self.model_manager.get_download_progress(model_id)
            if progress_data is None:
                # If not actively downloading and not downloaded, it might just not have a progress entry
                if self.model_manager.is_model_downloaded(model_id):
                    # Construct a "completed" status if it's downloaded but not in download_progress dict
                    # This can happen if app restarts and download_progress is in-memory
                    model_info = self.model_manager.get_model_info(model_id)
                    file_path = os.path.join(self.model_manager._get_model_cache_dir(), f"{model_id}.pt")
                    size_bytes = 0
                    if os.path.exists(file_path):
                        size_bytes = os.path.getsize(file_path)

                    progress_data = {
                        "status": "completed", "progress": 100,
                        "downloaded_size": size_bytes,
                        "total_size": size_bytes, # Assuming total size is same as downloaded for completed
                        "error_message": "", "cancel_requested": False
                    }
                    return jsonify({"status": "success", "data": progress_data})
                else:
                    # Not downloaded and no active/failed progress entry
                    return jsonify({"status": "success", "data": {
                        "status": "not_downloaded", "progress": 0,
                        "downloaded_size":0, "total_size":0,
                        "error_message": "", "cancel_requested": False
                    }})
            return jsonify({"status": "success", "data": progress_data})

        @bp.route('/api/v1/models/download/<string:model_id>/cancel', methods=['POST'])
        def api_cancel_model_download(model_id):
            if not self.model_manager:
                return jsonify({"status": "error", "message": "ModelManager not initialized"}), 500
            # No need to check if model_id is in available_models, cancel works on current downloads

            success = self.model_manager.cancel_download_model(model_id)
            if success:
                return jsonify({"status": "success", "message": f"Cancellation requested for model {model_id}."})
            else:
                # More specific message if possible
                prog = self.model_manager.get_download_progress(model_id)
                if not prog or prog.get("status") != "downloading":
                    return jsonify({"status": "error", "message": f"No active download to cancel for model {model_id}."}), 400
                return jsonify({"status": "error", "message": f"Failed to request cancellation for model {model_id}."}), 500

        @bp.route('/api/v1/models/switch', methods=['POST'])
        def api_switch_model():
            if not self.model_manager:
                return jsonify({"status": "error", "message": "ModelManager not initialized"}), 500

            data = request.get_json()
            if not data or 'model' not in data:
                return jsonify({"status": "error", "message": "Missing 'model' in request body"}), 400

            model_id = data['model']
            if model_id not in self.model_manager.get_available_models():
                return jsonify({"status": "error", "message": f"Invalid model ID: {model_id}"}), 404
            if not self.model_manager.is_model_downloaded(model_id):
                return jsonify({"status": "error", "message": f"Model {model_id} is not downloaded."}), 400

            success = self.model_manager.load_model(model_id)
            if success:
                return jsonify({"status": "success", "message": f"Successfully switched to model {model_id}."})
            else:
                return jsonify({"status": "error", "message": f"Failed to switch to model {model_id}."}), 500

        @bp.route('/api/v1/models/<string:model_id>', methods=['DELETE'])
        def api_delete_model(model_id):
            if not self.model_manager:
                return jsonify({"status": "error", "message": "ModelManager not initialized"}), 500
            if model_id not in self.model_manager.get_available_models():
                # Allow deleting models not in the "available" list if they somehow exist?
                # For now, let's stick to known models. User could manually add files.
                # However, model_manager.delete_model_file also checks AVAILABLE_MODELS.
                pass # model_manager.delete_model_file will handle unknown model_id

            success = self.model_manager.delete_model_file(model_id)
            if success:
                return jsonify({"status": "success", "message": f"Model {model_id} deleted successfully."})
            else:
                # Check if it was not downloaded in the first place
                if not self.model_manager.is_model_downloaded(model_id) and \
                   not os.path.exists(os.path.join(self.model_manager._get_model_cache_dir(), f"{model_id}.pt")):
                     # If delete_model_file returned false because it wasn't there to begin with.
                     # This case should ideally be handled by delete_model_file returning True if not found.
                     # Re-checking the logic in delete_model_file, it returns True if not downloaded.
                     # So this path might indicate another error.
                     return jsonify({"status": "error", "message": f"Failed to delete model {model_id}. It might not have been downloaded or another error occurred."}), 500
                return jsonify({"status": "error", "message": f"Failed to delete model {model_id}."}), 500

        # Static file serving for admin assets
        @bp.route('/admin/static/<path:filename>')
        def admin_static(filename):
            # Use the blueprint's static folder
            return send_from_directory(bp.static_folder, filename)

    def get_uptime_formatted(self):
        """Get formatted uptime string"""
        if self.system_stats and "uptime_start" in self.system_stats:
            uptime = datetime.now() - self.system_stats["uptime_start"]
            total_seconds = int(uptime.total_seconds())
            
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            parts.append(f"{seconds}s")
            
            return " ".join(parts)
        return "Unknown"
    
    def increment_transcription_count(self, source="api"):
        """Increment transcription counter"""
        if self.system_stats:
            self.system_stats["total_transcriptions"] += 1
            if source in self.system_stats["transcriptions_by_source"]:
                self.system_stats["transcriptions_by_source"][source] += 1


def init_admin_panel(app, blueprint, model_manager=None, system_stats=None): # Added blueprint parameter
    """Initialize admin panel and register blueprint"""
    admin = AdminPanel(app, blueprint, model_manager, system_stats) # Pass blueprint to AdminPanel
    app.register_blueprint(blueprint) # Register the passed blueprint
    return admin
