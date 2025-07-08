"""
WhisperAppliance Admin Panel Module
Modular admin interface with enhanced features
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, render_template, send_from_directory

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
            return jsonify(self.model_status.get_model_status())

        # Static file serving for admin assets
        @bp.route('/admin/static/<path:filename>')
        def admin_static(filename):
            # Use the blueprint's static folder
            return send_from_directory(bp.static_folder, filename)

        @bp.route('/api/admin/update-git', methods=['POST'])
        def update_git_repository():
            try:
                # Perform git pull operation
                # Ensure this runs in the correct directory and handles errors
                # This is a simplified example; real implementation needs error handling,
                # security considerations, and potentially asynchronous execution.
                import subprocess
                project_root = Path(__file__).resolve().parent.parent.parent # Adjust if necessary
                result = subprocess.run(['git', 'pull'], cwd=project_root, capture_output=True, text=True, check=False)

                if result.returncode == 0:
                    logger.info("Git repository updated successfully: %s", result.stdout)
                    return jsonify({"success": True, "message": "Repository updated successfully."})
                else:
                    logger.error("Git update failed: %s", result.stderr)
                    return jsonify({"success": False, "message": f"Git update failed: {result.stderr}"}), 500
            except Exception as e:
                logger.exception("Error during Git update:")
                return jsonify({"success": False, "message": str(e)}), 500

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
