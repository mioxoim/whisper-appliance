"""
Admin Panel Module - Fixed Version
"""

import logging
from datetime import datetime
from flask import render_template_string

logger = logging.getLogger(__name__)

# CSS als separate Konstante
ADMIN_CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; }
    
    /* Navigation Header */
    .nav-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .nav-container {
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 20px;
    }
    .nav-title {
        font-size: 1.5em;
        font-weight: bold;
    }
    .nav-links {
        display: flex;
        gap: 20px;
    }
    .nav-links a {
        color: white;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 5px;
        transition: background 0.3s;
    }
    .nav-links a:hover {
        background: rgba(255,255,255,0.2);
    }
    .nav-links a.active {
        background: rgba(255,255,255,0.3);
    }
    
    /* Main Content */
    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
    }
    h1 {
        background: white;
        color: #333;
        padding: 20px;
        margin: -20px -20px 20px -20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin-bottom: 20px;
    }
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 2em;
        font-weight: bold;
        color: #667eea;
    }
    .stat-label {
        color: #666;
        margin-top: 5px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    th, td {
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    
    /* Quick Actions */
    .actions-section {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .actions-grid {
        display: flex;
        gap: 15px;
        margin-top: 15px;
    }
    button {
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        background: #667eea;
        color: white;
        cursor: pointer;
        transition: all 0.3s;
    }
    button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(102,126,234,0.4); }
    button:disabled { background: #ccc; cursor: not-allowed; transform: none; }
    
    /* Dark mode support */
    [data-theme="dark"] body { background: #1a1a1a; color: #e0e0e0; }
    [data-theme="dark"] .stat-card,
    [data-theme="dark"] .actions-section,
    [data-theme="dark"] h1 { background: #2d2d2d; color: #e0e0e0; }
    [data-theme="dark"] th,
    [data-theme="dark"] td { border-color: #444; }
    
    /* Theme toggle */
    #themeToggle {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #667eea;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 1.5em;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        transition: all 0.3s;
    }
    #themeToggle:hover {
        transform: scale(1.1);
    }
"""


class AdminPanel:
    """Fixed Admin Panel"""
    
    def __init__(self, whisper_available, system_stats, connected_clients, model_manager, chat_history, update_manager=None):
        self.whisper_available = whisper_available
        self.system_stats = system_stats
        self.connected_clients = connected_clients
        self.model_manager = model_manager
        self.chat_history = chat_history
        self.update_manager = update_manager
        self.update_available = update_manager is not None

    def _safe_get_current_model(self):
        """Safely get current model name with fallback"""
        if self.model_manager:
            try:
                return self.model_manager.get_current_model_name()
            except Exception:
                return "Error loading model"
        return "Model Manager unavailable"

    def _safe_get_available_models(self):
        """Safely get available models with fallback"""
        if self.model_manager:
            try:
                return self.model_manager.get_available_models()
            except Exception:
                return {}
        return {}

    def _safe_is_loading(self):
        """Safely check if model is loading"""
        if self.model_manager:
            try:
                return self.model_manager.is_model_loading()
            except Exception:
                return False
        return False

    def get_demo_interface(self):
        """Demo interface stub"""
        return "<h1>Demo Interface - Coming Soon</h1>"

    def get_admin_interface(self):
        """Generate admin interface without f-string CSS issues"""
        uptime = (datetime.now() - self.system_stats["uptime_start"]).total_seconds()
        uptime_formatted = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
        
        # Generate HTML without problematic f-string CSS
        html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>WhisperS2T Admin Panel</title>
    <meta charset="utf-8">
    <style>
''' + ADMIN_CSS + '''
    </style>
</head>
<body>
    <nav class="nav-header">
        <div class="nav-container">
            <div class="nav-title">🎤 WhisperS2T Admin Panel</div>
            <div class="nav-links">
                <a href="/" title="Main Interface">🏠 Home</a>
                <a href="/admin" class="active" title="Admin Panel">⚙️ Admin</a>
                <a href="/docs" title="API Documentation">📚 API Docs</a>
                <a href="/demo" title="Demo Interface">🎯 Demo</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        <h1>🎛️ System Administration</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 System Status</h3>
                <div class="stat-value">''' + ("✅ ONLINE" if self.whisper_available else "❌ OFFLINE") + '''</div>
                <div class="stat-label">Whisper Model Status</div>
                <table>
                    <tr><td>Uptime:</td><td>''' + uptime_formatted + '''</td></tr>
                    <tr><td>Total Transcriptions:</td><td>''' + str(self.system_stats.get("total_transcriptions", 0)) + '''</td></tr>
                    <tr><td>Active Connections:</td><td>''' + str(len(self.connected_clients)) + '''</td></tr>
                </table>
            </div>
            
            <div class="stat-card">
                <h3>🔄 System Updates</h3>
                <div class="update-management">
                    <div class="current-version" style="margin-bottom: 15px;">
                        <strong>Current Version:</strong> 
                        <span id="current-version-display">v1.1.0</span>
                        <span id="update-status-indicator" style="margin-left: 10px; font-style: italic; color: #666;"></span>
                    </div>
                    
                    <div class="update-controls" style="margin: 15px 0;">
                        <button id="check-updates-btn" onclick="checkForUpdates()" 
                                style="margin-right: 10px; padding: 12px 20px; background: #17a2b8; color: white; border: none; border-radius: 6px; cursor: pointer;">
                            🔍 Check for Updates
                        </button>
                        <button id="apply-updates-btn" onclick="applyUpdates()" 
                                style="margin-right: 10px; padding: 12px 20px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer;" 
                                disabled>
                            ⬇ Install Updates
                        </button>
                        <button id="rollback-btn" onclick="rollbackUpdate()" 
                                style="padding: 12px 20px; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer;">
                            ↩ Rollback
                        </button>
                    </div>
                    
                    <div id="update-status" style="margin: 15px 0;">
                        <span id="update-status-text">Click "Check for Updates" to see if updates are available</span>
                    </div>
                    
                    <div id="update-progress" style="margin-top: 15px; display: none;">
                        <div style="background: #f0f0f0; border-radius: 4px; padding: 2px;">
                            <div id="update-progress-bar" style="background: #007bff; height: 20px; border-radius: 2px; width: 0%; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    
                    <div id="update-details" style="margin-top: 15px; display: none;">
                        <h4>Update Information:</h4>
                        <div id="update-info-content"></div>
                    </div>
                    
                    <div id="update-log" style="margin-top: 15px; display: none;">
                        <h4>Update Log:</h4>
                        <div id="update-log-content" style="max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 0.9em;">
                        </div>
                    </div>
                    
                    <div class="update-info" style="margin-top: 15px; padding: 12px; background: #e8f5e8; border-radius: 4px; font-size: 14px;">
                        <strong>🔄 Update System:</strong><br>
                        • Git-based updates with automatic detection<br>
                        • Backup and rollback support<br>
                        • Version tracking and commit history<br>
                        • Production-ready deployment<br>
                        • Automatic service restart<br>
                        • Modular architecture
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <button id="themeToggle" onclick="toggleTheme()">🌙</button>
    
    <script>
    let currentUpdateInfo = null;
    
    async function checkForUpdates() {
        const checkBtn = document.getElementById('check-updates-btn');
        const statusText = document.getElementById('update-status-text');
        const applyBtn = document.getElementById('apply-updates-btn');
        
        try {
            checkBtn.disabled = true;
            checkBtn.innerHTML = '🔄 Checking...';
            statusText.innerHTML = 'Checking for updates...';
            
            const response = await fetch('/api/update/check');
            const data = await response.json();
            
            if (data.update_available) {
                statusText.innerHTML = '✅ Update available!';
                currentUpdateInfo = data;
                applyBtn.disabled = false;
                
                // Show update details
                const detailsDiv = document.getElementById('update-details');
                const infoContent = document.getElementById('update-info-content');
                detailsDiv.style.display = 'block';
                
                infoContent.innerHTML = '<p><strong>Current:</strong> ' + data.current_version.substring(0, 7) + '</p>' +
                    '<p><strong>Latest:</strong> ' + data.latest_version.substring(0, 7) + '</p>' +
                    '<p><strong>Message:</strong> ' + data.update_info.message + '</p>' +
                    '<p><strong>Author:</strong> ' + data.update_info.author + '</p>' +
                    '<p><strong>Date:</strong> ' + new Date(data.update_info.date).toLocaleString() + '</p>';
            } else {
                statusText.innerHTML = '✓ System is up to date';
                applyBtn.disabled = true;
            }
            
            // Update version display
            document.getElementById('current-version-display').innerHTML = 
                data.current_version.substring(0, 7);
            
        } catch (error) {
            statusText.innerHTML = '❌ Check failed: ' + error.message;
        } finally {
            checkBtn.disabled = false;
            checkBtn.innerHTML = '🔍 Check for Updates';
        }
    }
    
    async function applyUpdates() {
        if (!currentUpdateInfo || !currentUpdateInfo.update_available) {
            alert('No updates available');
            return;
        }
        
        if (!confirm('Apply update now?\\n\\nThis will:\\n• Create a backup\\n• Install the update\\n• Restart the service if needed\\n\\nContinue?')) {
            return;
        }
        
        const applyBtn = document.getElementById('apply-updates-btn');
        const statusText = document.getElementById('update-status-text');
        const progressDiv = document.getElementById('update-progress');
        const progressBar = document.getElementById('update-progress-bar');
        const logDiv = document.getElementById('update-log');
        const logContent = document.getElementById('update-log-content');
        
        try {
            applyBtn.disabled = true;
            applyBtn.innerHTML = '🔄 Installing...';
            progressDiv.style.display = 'block';
            logDiv.style.display = 'block';
            
            progressBar.style.width = '20%';
            statusText.innerHTML = 'Creating backup...';
            logContent.innerHTML += '[' + new Date().toLocaleTimeString() + '] Starting update process...\\n';
            
            const response = await fetch('/api/update/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            progressBar.style.width = '60%';
            statusText.innerHTML = 'Installing update...';
            logContent.innerHTML += '[' + new Date().toLocaleTimeString() + '] Installing updates...\\n';
            
            const data = await response.json();
            
            if (data.success) {
                progressBar.style.width = '100%';
                statusText.innerHTML = '✅ Update installed successfully!';
                logContent.innerHTML += '[' + new Date().toLocaleTimeString() + '] ' + data.message + '\\n';
                
                if (data.restart_required) {
                    logContent.innerHTML += '[' + new Date().toLocaleTimeString() + '] Service restart required\\n';
                    setTimeout(() => {
                        alert('Update completed! The service will restart now.');
                        location.reload();
                    }, 2000);
                }
            } else {
                throw new Error(data.message || 'Update failed');
            }
            
        } catch (error) {
            progressBar.style.width = '0%';
            statusText.innerHTML = '❌ Update failed: ' + error.message;
            logContent.innerHTML += '[' + new Date().toLocaleTimeString() + '] ERROR: ' + error.message + '\\n';
            alert('Update failed: ' + error.message);
        } finally {
            applyBtn.disabled = false;
            applyBtn.innerHTML = '⬇ Install Updates';
        }
    }
    
    async function rollbackUpdate() {
        const response = await fetch('/api/update/backups');
        const data = await response.json();
        
        if (!data.backups || data.backups.length === 0) {
            alert('No backups available');
            return;
        }
        
        const backup = prompt('Enter backup name to rollback to:\\n\\n' + 
            data.backups.map(b => b.name + ' (' + new Date(b.date).toLocaleString() + ')').join('\\n'));
        
        if (!backup) return;
        
        if (!confirm('Rollback to ' + backup + '?\\n\\nThis will restore the previous version.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/update/rollback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ backup_name: backup })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Rollback successful! The page will reload.');
                location.reload();
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            alert('Rollback failed: ' + error.message);
        }
    }
    
    function toggleTheme() {
        const body = document.body;
        const toggle = document.getElementById('themeToggle');
        
        if (body.getAttribute('data-theme') === 'dark') {
            body.removeAttribute('data-theme');
            toggle.textContent = '🌙';
            localStorage.setItem('theme', 'light');
        } else {
            body.setAttribute('data-theme', 'dark');
            toggle.textContent = '☀️';
            localStorage.setItem('theme', 'dark');
        }
    }
    
    // Load saved theme on page load
    document.addEventListener('DOMContentLoaded', function() {
        const savedTheme = localStorage.getItem('theme');
        const toggle = document.getElementById('themeToggle');
        
        if (savedTheme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
            toggle.textContent = '☀️';
        } else {
            toggle.textContent = '🌙';
        }
    });
    
    // Auto-check for updates on page load
    window.addEventListener('load', () => {
        setTimeout(checkForUpdates, 1000);
    });
    </script>
</body>
</html>
'''
        
        return html_template
