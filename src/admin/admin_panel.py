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

logger = logging.getLogger(__name__)

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, 
                    template_folder='templates',
                    static_folder='static',
                    static_url_path='/admin/static')


class AdminPanel:
    """Enhanced Admin Panel with modular architecture"""
    
    def __init__(self, app, model_manager=None, system_stats=None):
        self.app = app
        self.model_manager = model_manager
        self.system_stats = system_stats or {
            "uptime_start": datetime.now(),
            "total_transcriptions": 0,
            "transcriptions_by_source": {"live": 0, "upload": 0, "api": 0}
        }
        
        # Initialize sub-modules
        self.model_status = ModelStatusManager(model_manager)
        self.system_monitor = SystemMonitor(self.system_stats)
        
        # Register routes
        self._register_routes()
        
        logger.info("WhisperAppliance Admin Panel initialized")
    
    def _register_routes(self):
        """Register admin routes"""
        # Main admin page
        @admin_bp.route('/admin')
        def admin_dashboard():
            return render_template('admin-dashboard.html',
                                 system_info=self.system_monitor.get_system_info(),
                                 model_info=self.model_status.get_model_info())
        
        # Model management page
        @admin_bp.route('/admin/models')
        def admin_models():
            return render_template('admin-models.html',
                                 models=self.model_status.get_detailed_model_info())
        
        # Settings page
        @admin_bp.route('/admin/settings')
        def admin_settings():
            return render_template('admin-settings.html')
        
        # API endpoints
        @admin_bp.route('/api/v1/system/status')
        def api_system_status():
            return jsonify(self.system_monitor.get_system_status())
        
        @admin_bp.route('/api/v1/models/status')
        def api_model_status():
            return jsonify(self.model_status.get_model_status())
        
        # Static file serving for admin assets
        @admin_bp.route('/admin/static/<path:filename>')
        def admin_static(filename):
            return send_from_directory(admin_bp.static_folder, filename)
    
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


def init_admin_panel(app, model_manager=None, system_stats=None):
    """Initialize admin panel and register blueprint"""
    admin = AdminPanel(app, model_manager, system_stats)
    app.register_blueprint(admin_bp)
    return admin
