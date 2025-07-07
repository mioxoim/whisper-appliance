"""
Update API Endpoints
REST API for update management
"""

from typing import Optional

from flask import Blueprint, jsonify, request

from .manager import UpdateManager


def create_update_endpoints(app, logger=None):
    """Create and register update API endpoints"""

    # Initialize update manager
    update_manager = UpdateManager()

    # Create blueprint
    update_bp = Blueprint("update", __name__, url_prefix="/api/update")

    @update_bp.route("/check", methods=["GET"])
    def check_updates():
        """Check for available updates"""
        try:
            result = update_manager.check_for_updates()
            return jsonify(result)
        except Exception as e:
            if logger:
                logger.error(f"Update check failed: {e}")
            return jsonify({"error": str(e)}), 500

    @update_bp.route("/install", methods=["POST"])
    def install_update():
        """Install available updates"""
        try:
            result = update_manager.install_update()
            return jsonify(result)
        except Exception as e:
            if logger:
                logger.error(f"Update installation failed: {e}")
            return jsonify({"error": str(e)}), 500

    @update_bp.route("/status", methods=["GET"])
    def update_status():
        """Get update system status"""
        try:
            status = update_manager.get_status()
            return jsonify(status)
        except Exception as e:
            if logger:
                logger.error(f"Status check failed: {e}")
            return jsonify({"error": str(e)}), 500

    @update_bp.route("/history", methods=["GET"])
    def update_history():
        """Get update history"""
        try:
            history = update_manager.get_update_history()
            return jsonify({"commits": history})
        except Exception as e:
            if logger:
                logger.error(f"History fetch failed: {e}")
            return jsonify({"error": str(e)}), 500

    @update_bp.route("/backups", methods=["GET"])
    def list_backups():
        """List available backups"""
        try:
            backups = update_manager.list_backups()
            return jsonify({"backups": backups})
        except Exception as e:
            if logger:
                logger.error(f"Backup list failed: {e}")
            return jsonify({"error": str(e)}), 500

    @update_bp.route("/rollback", methods=["POST"])
    def rollback_update():
        """Rollback to a previous backup"""
        try:
            data = request.get_json()
            backup_name = data.get("backup_name")

            if not backup_name:
                return jsonify({"error": "backup_name required"}), 400

            result = update_manager.rollback_to_backup(backup_name)
            return jsonify(result)
        except Exception as e:
            if logger:
                logger.error(f"Rollback failed: {e}")
            return jsonify({"error": str(e)}), 500

    @update_bp.route("/restart", methods=["POST"])
    def restart_application():
        """Restart the application"""
        try:
            success = update_manager.restart_application()
            return jsonify({"success": success})
        except Exception as e:
            if logger:
                logger.error(f"Restart failed: {e}")
            return jsonify({"error": str(e)}), 500

    # Register blueprint
    app.register_blueprint(update_bp)

    if logger:
        logger.info("✅ Update API endpoints registered at /api/update/*")
        logger.info(f"✅ Registered routes: /api/update/check, /api/update/install, /api/update/status, etc.")

    # Debug: List all registered routes
    for rule in app.url_map.iter_rules():
        if "/api/update" in rule.rule:
            if logger:
                logger.info(f"  - {rule.rule} [{', '.join(rule.methods)}]")

    return update_manager
