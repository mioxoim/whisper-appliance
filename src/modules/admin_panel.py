"""
Admin Panel Module
Provides comprehensive admin interface with navigation and system monitoring
Preserves all original admin features and enhances with navigation
"""

import logging
from datetime import datetime

from flask import render_template_string

logger = logging.getLogger(__name__)


class AdminPanel:
    """Manages admin interface and system monitoring"""

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

    def get_admin_interface(self):
        """Enhanced Admin Panel with Navigation - Preserving original + adding navigation"""
        uptime = (datetime.now() - self.system_stats["uptime_start"]).total_seconds()
        uptime_formatted = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"

        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhisperS2T Admin Panel</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="30">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; }}
                
                /* Navigation Header */
                .nav-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .nav-container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 20px;
                }}
                .nav-title {{
                    font-size: 1.5em;
                    font-weight: bold;
                }}
                .nav-links {{
                    display: flex;
                    gap: 20px;
                }}
                .nav-links a {{
                    color: white;
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                .nav-links a:hover {{
                    background: rgba(255,255,255,0.2);
                }}
                .nav-links a.active {{
                    background: rgba(255,255,255,0.3);
                }}
                
                /* Main Content */
                .container {{ 
                    max-width: 1400px; 
                    margin: 0 auto; 
                    padding: 20px;
                }}
                .header {{ 
                    background: white;
                    color: #333;
                    padding: 20px; 
                    border-radius: 10px; 
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                    margin-bottom: 20px; 
                }}
                .stat-card {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                }}
                .stat-value {{ 
                    font-size: 2em; 
                    font-weight: bold; 
                    color: #667eea; 
                }}
                .stat-label {{ 
                    color: #666; 
                    margin-top: 5px; 
                }}
                .status-good {{ color: #28a745; }}
                .status-warning {{ color: #ffc107; }}
                .status-error {{ color: #dc3545; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin-top: 10px; 
                }}
                th, td {{ 
                    padding: 10px; 
                    text-align: left; 
                    border-bottom: 1px solid #ddd; 
                }}
                th {{ background: #f8f9fa; }}
                
                /* Quick Actions */
                .quick-actions {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .action-buttons {{
                    display: flex;
                    gap: 15px;
                    margin-top: 15px;
                }}
                .btn {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    transition: all 0.3s;
                }}
                .btn-primary {{ background: #667eea; color: white; }}
                .btn-success {{ background: #28a745; color: white; }}
                .btn-info {{ background: #17a2b8; color: white; }}
                .btn-warning {{ background: #ffc107; color: black; }}
                .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
            </style>
        </head>
        <body>
            <!-- Navigation Header -->
            <div class="nav-header">
                <div class="nav-container">
                    <div class="nav-title">🎤 WhisperS2T Control Center</div>
                    <div class="nav-links">
                        <a href="/" class="nav-link">🏠 Home</a>
                        <a href="/admin" class="nav-link active">⚙️ Admin</a>
                        <a href="/docs" class="nav-link">📚 API Docs</a>
                        <a href="/demo" class="nav-link">🎯 Demo</a>
                        <a href="/health" class="nav-link">🏥 Health</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="header">
                    <h1>⚙️ System Administration Dashboard</h1>
                    <p>Real-time monitoring and system control interface</p>
                </div>
                
                <!-- Quick Actions -->
                <div class="quick-actions">
                    <h3>🚀 Quick Actions</h3>
                    <div class="action-buttons">
                        <a href="/health" class="btn btn-success">🏥 Health Check</a>
                        <a href="/api/status" class="btn btn-info">📊 API Status</a>
                        <a href="/docs" class="btn btn-primary">📚 API Documentation</a>
                        <a href="/demo" class="btn btn-warning">🎯 Test Interface</a>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value status-good">{"✅ Online" if self.whisper_available else "❌ Offline"}</div>
                        <div class="stat-label">Whisper Service Status</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{uptime_formatted}</div>
                        <div class="stat-label">System Uptime</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{self.system_stats['total_transcriptions']}</div>
                        <div class="stat-label">Total Transcriptions</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{len(self.connected_clients)}</div>
                        <div class="stat-label">Active WebSocket Connections</div>
                    </div>
                </div>
                
                <!-- Model Management Section -->
                <div class="stat-card">
                    <h3>🧠 Whisper Model Management</h3>
                    <div class="model-management">
                        <div class="current-model">
                            <strong>Current Model:</strong> 
                            <span id="current-model-name">{self._safe_get_current_model()}</span>
                            <span id="model-loading-indicator" style="color: #007bff; font-style: italic;">
                                {("(Loading...)" if self._safe_is_loading() else "")}
                            </span>
                        </div>
                        
                        <div class="model-selector" style="margin: 15px 0;">
                            <label for="admin-model-select"><strong>Switch Model:</strong></label>
                            <select id="admin-model-select" style="margin-left: 10px; padding: 5px;">
                                {"".join([f'<option value="{model_id}" {"selected" if model_id == self._safe_get_current_model() else ""}>{model_info["name"]} - {model_info["description"]}</option>' for model_id, model_info in self._safe_get_available_models().items()]) if self._safe_get_available_models() else '<option>No models available</option>'}
                            </select>
                            <button onclick="switchAdminModel()" style="margin-left: 10px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                Switch Model
                            </button>
                        </div>
                        
                        <div id="admin-model-status" style="margin-top: 10px; font-size: 0.9em;"></div>
                        
                        <div class="model-details" style="margin-top: 15px;">
                            <h4>Available Models:</h4>
                            <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                                <tr style="background: #f8f9fa;">
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Model</th>
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Size</th>
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Speed</th>
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Quality</th>
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
                                </tr>
                                {"".join([f'''
                                <tr style="{'background: #e8f5e8;' if model_id == self._safe_get_current_model() else ''}">
                                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{model_info["name"]}</strong> {"✅" if model_id == self._safe_get_current_model() else ""}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{model_info.get("size", "Unknown")}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{model_info.get("speed", "Unknown")}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{model_info.get("quality", "Unknown")}</td>
                                    <td style="padding: 8px; border: 1px solid #ddd;">{model_info.get("description", "No description")}</td>
                                </tr>''' for model_id, model_info in self._safe_get_available_models().items()]) if self._safe_get_available_models() else '<tr><td colspan="5" style="padding: 8px; border: 1px solid #ddd; text-align: center;">No models available</td></tr>'}
                            </table>
                        </div>
                    </div>
                </div>
                
                {self._get_update_management_html()}
                
                <div class="stat-card">
                    <h3>🔧 System Information</h3>
                    <table>
                        <tr><th>Property</th><th>Value</th></tr>
                        <tr><td>Service Name</td><td>WhisperS2T Enhanced Appliance</td></tr>
                        <tr><td>Version</td><td>0.10.0</td></tr>
                        <tr><td>Framework</td><td>Flask + SocketIO + SQLite</td></tr>
                        <tr><td>Whisper Available</td><td>{"Yes" if self.whisper_available else "No"}</td></tr>
                        <tr><td>Model Type</td><td>{self.model_manager.get_current_model_name()}</td></tr>
                        <tr><td>Architecture</td><td>Modular (live_speech, upload_handler, admin_panel, api_docs, chat_history)</td></tr>
                        <tr><td>Features</td><td>Live Speech, Upload Transcription, WebSocket, API Docs, Chat History</td></tr>
                    </table>
                </div>
                
                <!-- Chat History & Model Download Status Section -->
                <div class="stat-card">
                    <h3>📊 Model Download Status</h3>
                    <div class="model-download-status">
                        <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Model</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Status</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Size</th>
                                <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
                            </tr>
                            {"".join([f'''
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;"><strong>{model_info["name"]}</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">
                                    {"📦 Downloaded" if model_id in self.model_manager.downloaded_models else "⬇️ Need Download"}
                                </td>
                                <td style="padding: 8px; border: 1px solid #ddd;">{model_info["size"]}</td>
                                <td style="padding: 8px; border: 1px solid #ddd;">{model_info["description"]}</td>
                            </tr>''' for model_id, model_info in self.model_manager.get_available_models().items()])}
                        </table>
                    </div>
                </div>
                
                <div class="stat-card">
                    <h3>💬 Chat History Statistics</h3>
                    <div class="chat-history-stats">
                        {self._get_chat_history_stats_html()}
                        <div style="margin-top: 15px;">
                            <button onclick="loadChatHistory()" style="margin-right: 10px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                📜 View Recent History
                            </button>
                            <button onclick="exportChatHistory('json')" style="margin-right: 10px; padding: 5px 10px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                📤 Export JSON
                            </button>
                            <button onclick="exportChatHistory('csv')" style="padding: 5px 10px; background: #ffc107; color: black; border: none; border-radius: 3px; cursor: pointer;">
                                📤 Export CSV
                            </button>
                        </div>
                        <div id="chat-history-content" style="margin-top: 15px; max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f8f9fa; display: none;">
                            <!-- Chat history will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # JavaScript for model management (separate to avoid Black parsing issues)
        js_script = """
            <script>
                async function switchAdminModel() {
                    const modelSelect = document.getElementById('admin-model-select');
                    const statusDiv = document.getElementById('admin-model-status');
                    const loadingIndicator = document.getElementById('model-loading-indicator');
                    const currentModelName = document.getElementById('current-model-name');
                    
                    const selectedModel = modelSelect.value;
                    
                    try {
                        statusDiv.innerHTML = '<span style="color: #007bff;">Loading ' + selectedModel + ' model...</span>';
                        loadingIndicator.textContent = '(Loading...)';
                        loadingIndicator.style.display = 'inline';
                        
                        const response = await fetch('/api/models/' + selectedModel, {{
                            method: 'POST'
                        }});
                        const data = await response.json();
                        
                        if (data.status === 'loading') {
                            const pollInterval = setInterval(async () => {
                                try {
                                    const statusResponse = await fetch('/api/models');
                                    const statusData = await statusResponse.json();
                                    
                                    if (!statusData.model_loading) {
                                        clearInterval(pollInterval);
                                        loadingIndicator.style.display = 'none';
                                        
                                        if (statusData.current_model === selectedModel) {
                                            statusDiv.innerHTML = '<span style="color: #28a745;">Successfully switched to ' + selectedModel + ' model</span>';
                                            currentModelName.textContent = selectedModel;
                                            setTimeout(() => location.reload(), 2000);
                                        } else {
                                            statusDiv.innerHTML = '<span style="color: #dc3545;">Failed to load ' + selectedModel + ' model</span>';
                                        }
                                    }
                                } catch (error) {
                                    clearInterval(pollInterval);
                                    statusDiv.innerHTML = '<span style="color: #dc3545;">Error checking model status</span>';
                                }
                            }, 2000);
                        }
                    } catch (error) {
                        statusDiv.innerHTML = '<span style="color: #dc3545;">Network error</span>';
                    }
                }
                
                setInterval(async () => {
                    try {
                        const response = await fetch('/api/models');
                        const data = await response.json();
                        
                        const currentModelName = document.getElementById('current-model-name');
                        const loadingIndicator = document.getElementById('model-loading-indicator');
                        
                        if (currentModelName) {
                            currentModelName.textContent = data.current_model;
                        }
                        
                        if (loadingIndicator) {
                            loadingIndicator.textContent = data.model_loading ? '(Loading...)' : '';
                            loadingIndicator.style.display = data.model_loading ? 'inline' : 'none';
                        }
                    } catch (error) {
                        console.error('Model status update failed:', error);
                    }
                }, 30000);
                
                // Chat History Functions
                async function loadChatHistory() {
                    const chatContent = document.getElementById('chat-history-content');
                    
                    try {
                        chatContent.innerHTML = '<p>Loading chat history...</p>';
                        chatContent.style.display = 'block';
                        
                        const response = await fetch('/api/chat-history?limit=20');
                        const data = await response.json();
                        
                        if (data.status === 'success' && data.transcriptions.length > 0) {
                            let historyHtml = '<h4>Recent Transcriptions:</h4>';
                            
                            data.transcriptions.forEach(trans => {
                                const date = new Date(trans.timestamp).toLocaleString();
                                historyHtml += `
                                    <div style="border-bottom: 1px solid #ddd; padding: 10px; margin: 5px 0;">
                                        <div style="font-size: 0.9em; color: #666;">
                                            ${date} | ${trans.source_type} | ${trans.model_used || 'unknown'}
                                        </div>
                                        <div style="margin-top: 5px;">${trans.text}</div>
                                    </div>
                                `;
                            });
                            
                            chatContent.innerHTML = historyHtml;
                        } else {
                            chatContent.innerHTML = '<p>No chat history found.</p>';
                        }
                    } catch (error) {
                        chatContent.innerHTML = '<p>Error loading chat history: ' + error.message + '</p>';
                    }
                }
                
                async function exportChatHistory(format) {
                    try {
                        const response = await fetch('/api/chat-history/export?format=' + format);
                        
                        if (format === 'csv') {
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'chat_history.csv';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            window.URL.revokeObjectURL(url);
                        } else {
                            const data = await response.json();
                            const blob = new Blob([data.data], { type: 'application/json' });
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'chat_history.json';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            window.URL.revokeObjectURL(url);
                        }
                        
                        alert('Chat history exported successfully!');
                    } catch (error) {
                        alert('Export failed: ' + error.message);
                    }
                }
            </script>
        """

        # JavaScript for update management
        update_js = """
        <script>
        let currentUpdateInfo = null;
        
        async function checkForUpdates() {
            const checkBtn = document.getElementById('check-updates-btn');
            const statusText = document.getElementById('update-status-text');
            const applyBtn = document.getElementById('apply-updates-btn');
            
            try {
                checkBtn.disabled = true;
                checkBtn.innerHTML = '&#x1F504; Checking...';
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
                    
                    infoContent.innerHTML = `
                        <p><strong>Current:</strong> ${data.current_version.substring(0, 7)}</p>
                        <p><strong>Latest:</strong> ${data.latest_version.substring(0, 7)}</p>
                        <p><strong>Message:</strong> ${data.update_info.message}</p>
                        <p><strong>Author:</strong> ${data.update_info.author}</p>
                        <p><strong>Date:</strong> ${new Date(data.update_info.date).toLocaleString()}</p>
                    `;
                } else {
                    statusText.innerHTML = '✓ System is up to date';
                    applyBtn.disabled = true;
                }
                
                // Update version display
                document.getElementById('current-version-display').innerHTML = 
                    `${data.current_version.substring(0, 7)}`;
                
            } catch (error) {
                statusText.innerHTML = '❌ Check failed: ' + error.message;
            } finally {
                checkBtn.disabled = false;
                checkBtn.innerHTML = '&#x1F50D; Check for Updates';
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
                applyBtn.innerHTML = '&#x1F504; Installing...';
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
                applyBtn.innerHTML = '&#x2B07; Install Updates';
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
        
        // Auto-check for updates on page load
        window.addEventListener('load', () => {
            setTimeout(checkForUpdates, 1000);
        });
        </script>
        """

        # Insert both JavaScript blocks before closing body tag
        admin_html = admin_html.replace("</body>", js_script + update_js + "</body>")

        return admin_html

    def _get_update_management_html(self):
        """Generate HTML for update management section - supports both SimpleUpdater and Legacy systems"""
        return f"""
        <!-- Update Management Section -->
        <div class="stat-card">
            <h3>&#x1F504; System Updates</h3>
            <div class="update-management">
                <div class="current-version" style="margin-bottom: 15px;">
                    <strong>Current Version:</strong> 
                    <span id="current-version-display">v1.0.0</span>
                    <span id="update-status-indicator" style="margin-left: 10px; font-style: italic; color: #666;"></span>
                </div>
                
                <div class="update-controls" style="margin: 15px 0;">
                    <button id="check-updates-btn" onclick="checkForUpdates()" 
                            style="margin-right: 10px; padding: 12px 20px; background: #17a2b8; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        &#x1F50D; Check for Updates
                    </button>
                    <button id="apply-updates-btn" onclick="applyUpdates()" 
                            style="margin-right: 10px; padding: 12px 20px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer;" 
                            disabled>
                        &#x2B07; Install Updates
                    </button>
                    <button id="rollback-btn" onclick="rollbackUpdate()" 
                            style="padding: 12px 20px; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer;">
                        &#x21A9; Rollback
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
                    <strong>🔄 Simple Update System:</strong><br>
                    &bull; Git-based updates with automatic detection<br>
                    &bull; Backup and rollback support<br>
                    &bull; Version tracking and commit history<br>
                    &bull; Production-ready deployment<br>
                    &bull; Automatic service restart<br>
                    &bull; Modular architecture
                </div>
            </div>
        </div>
        """

        return update_html

    def _get_chat_history_stats_html(self):
        """Generate HTML for chat history statistics"""
        try:
            stats = self.chat_history.get_statistics()

            stats_html = f"""
                <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 15px 0;">
                    <div style="padding: 10px; background: #e8f5e8; border-radius: 5px;">
                        <div style="font-size: 1.5em; font-weight: bold;">{stats.get('total_transcriptions', 0)}</div>
                        <div style="font-size: 0.9em; color: #666;">Total Transcriptions</div>
                    </div>
                    <div style="padding: 10px; background: #e8f4fd; border-radius: 5px;">
                        <div style="font-size: 1.5em; font-weight: bold;">{stats.get('last_24h', 0)}</div>
                        <div style="font-size: 0.9em; color: #666;">Last 24 Hours</div>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <h4>By Source Type:</h4>
                    <ul style="margin: 5px 0;">
                        {"".join([f"<li>{source}: {count} transcriptions</li>" for source, count in stats.get('source_breakdown', {}).items()])}
                    </ul>
                    
                    <h4>By Model:</h4>
                    <ul style="margin: 5px 0;">
                        {"".join([f"<li>{model}: {count} transcriptions</li>" for model, count in stats.get('model_breakdown', {}).items()])}
                    </ul>
                </div>
            """
            return stats_html
        except Exception as e:
            return f"<p>Error loading statistics: {e}</p>"

    def get_demo_interface(self):
        """Enhanced Demo Interface - Preserving original functionality"""
        demo_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhisperS2T Demo Interface</title>
            <meta charset="utf-8">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                /* CSS Variables for theming */
                :root {
                    --bg-primary: #f8f9fa;
                    --bg-secondary: white;
                    --text-primary: #333;
                    --text-secondary: #666;
                    --border-color: rgba(0,0,0,0.1);
                    --card-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    --result-bg: #e8f5e8;
                    --result-border: #28a745;
                    --error-bg: #f8d7da;
                    --error-border: #dc3545;
                }
                
                /* Dark mode variables */
                [data-theme="dark"] {
                    --bg-primary: #1a1a1a;
                    --bg-secondary: #2d2d2d;
                    --text-primary: #e0e0e0;
                    --text-secondary: #b0b0b0;
                    --border-color: rgba(255,255,255,0.1);
                    --card-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    --result-bg: #1e3a1e;
                    --result-border: #4caf50;
                    --error-bg: #3a1e1e;
                    --error-border: #f44336;
                }
                
                body { 
                    font-family: Arial, sans-serif; 
                    background: var(--bg-primary); 
                    margin: 0;
                    color: var(--text-primary);
                    transition: background 0.3s, color 0.3s;
                }
                
                /* Navigation */
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
                .nav-title { font-size: 1.5em; font-weight: bold; }
                .nav-links { display: flex; gap: 20px; }
                .nav-links a {
                    color: white;
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    transition: background 0.3s;
                }
                .nav-links a:hover { background: rgba(255,255,255,0.2); }
                .nav-links a.active { background: rgba(255,255,255,0.3); }
                
                .container { 
                    max-width: 800px; 
                    margin: 20px auto; 
                    background: var(--bg-secondary); 
                    padding: 30px; 
                    border-radius: 10px; 
                    box-shadow: var(--card-shadow);
                    transition: background 0.3s, box-shadow 0.3s;
                }
                .header { text-align: center; margin-bottom: 30px; }
                .demo-section { 
                    background: var(--bg-primary); 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin: 20px 0;
                    transition: background 0.3s;
                }
                button { 
                    background: #667eea; 
                    color: white; 
                    border: none; 
                    padding: 12px 24px; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    margin: 10px;
                    transition: background 0.3s;
                }
                button:hover { background: #5a67d8; }
                .result { 
                    background: var(--result-bg); 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 10px 0; 
                    border-left: 4px solid var(--result-border);
                    transition: background 0.3s, border-color 0.3s;
                }
                .error { 
                    background: var(--error-bg); 
                    border-left-color: var(--error-border); 
                }
                input[type="file"], select { 
                    margin: 10px 0; 
                    padding: 8px;
                    background: var(--bg-secondary);
                    color: var(--text-primary);
                    border: 1px solid var(--border-color);
                    border-radius: 4px;
                    transition: background 0.3s, color 0.3s, border-color 0.3s;
                }
                
                /* Dark mode toggle */
                .theme-toggle {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 50px;
                    cursor: pointer;
                    font-size: 16px;
                    z-index: 1000;
                    transition: background 0.3s;
                }
                .theme-toggle:hover { background: #5a67d8; }
            </style>
        </head>
        <body>
            <!-- Dark Mode Toggle -->
            <button class="theme-toggle" onclick="toggleTheme()" id="themeToggle">🌙</button>
            
            <!-- Navigation -->
            <div class="nav-header">
                <div class="nav-container">
                    <div class="nav-title">🎤 WhisperS2T Control Center</div>
                    <div class="nav-links">
                        <a href="/" class="nav-link">🏠 Home</a>
                        <a href="/admin" class="nav-link">⚙️ Admin</a>
                        <a href="/docs" class="nav-link">📚 API Docs</a>
                        <a href="/demo" class="nav-link active">🎯 Demo</a>
                        <a href="/health" class="nav-link">🏥 Health</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="header">
                    <h1>🎯 WhisperS2T Demo Interface</h1>
                    <p>Quick testing interface for API functionality</p>
                </div>

                <div class="demo-section">
                    <h3>🏥 System Health Check</h3>
                    <button onclick="checkHealth()">Check System Health</button>
                    <div id="healthResult"></div>
                </div>
                
                <div class="demo-section">
                    <h3>📁 File Upload Transcription</h3>
                    <input type="file" id="audioFile" accept="audio/*">
                    <button onclick="uploadFile()">Upload & Transcribe</button>
                    <div id="uploadResult"></div>
                </div>
                
                <div class="demo-section">
                    <h3>🎙️ Live Speech Recording Demo</h3>
                    <p>Test real-time speech-to-text with your microphone</p>
                    
                    <div style="margin: 15px 0;">
                        <label for="demoLanguage">🌍 Language:</label>
                        <select id="demoLanguage" style="margin: 5px; padding: 5px;">
                            <option value="auto">Auto-detect</option>
                            <option value="de">German (Deutsch)</option>
                            <option value="en">English</option>
                            <option value="fr">French (Français)</option>
                            <option value="es">Spanish (Español)</option>
                            <option value="it">Italian (Italiano)</option>
                        </select>
                    </div>
                    
                    <div>
                        <button id="startRecordingDemo" onclick="startLiveRecording()">🎙️ Start Recording</button>
                        <button id="stopRecordingDemo" onclick="stopLiveRecording()" disabled>⏹️ Stop Recording</button>
                        <span id="recordingStatus" style="margin-left: 15px; color: #666;">Ready to record</span>
                    </div>
                    
                    <div id="liveSpeechResult" style="margin-top: 15px; min-height: 60px; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea;">
                        Click "Start Recording" to test live speech recognition...
                    </div>
                </div>
                
                <div class="demo-section">
                    <h3>🔗 WebSocket Connection Test</h3>
                    <button onclick="testWebSocket()">Test WebSocket Connection</button>
                    <div id="websocketResult"></div>
                </div>
            </div>
            
            <script>
                async function checkHealth() {
                    try {
                        const response = await fetch('/health');
                        const data = await response.json();
                        document.getElementById('healthResult').innerHTML = 
                            '<div class="result"><strong>Health Status:</strong><br>' + 
                            JSON.stringify(data, null, 2) + '</div>';
                    } catch (error) {
                        document.getElementById('healthResult').innerHTML = 
                            '<div class="result error"><strong>Error:</strong> ' + error.message + '</div>';
                    }
                }
                
                async function uploadFile() {
                    const fileInput = document.getElementById('audioFile');
                    if (!fileInput.files[0]) {
                        alert('Please select an audio file first!');
                        return;
                    }
                    
                    const formData = new FormData();
                    formData.append('audio', fileInput.files[0]);
                    
                    try {
                        document.getElementById('uploadResult').innerHTML = '<div class="result">🔄 Processing...</div>';
                        
                        const response = await fetch('/transcribe', {{
                            method: 'POST',
                            body: formData
                        }});
                        const data = await response.json();
                        
                        if (data.error) {
                            document.getElementById('uploadResult').innerHTML = 
                                '<div class="result error"><strong>Error:</strong> ' + data.error + '</div>';
                        } else {
                            document.getElementById('uploadResult').innerHTML = 
                                '<div class="result"><strong>Transcription:</strong><br>"' + data.text + '"</div>';
                        }
                    } catch (error) {
                        document.getElementById('uploadResult').innerHTML = 
                            '<div class="result error"><strong>Error:</strong> ' + error.message + '</div>';
                    }
                }
                
                // Live Speech Recording Demo
                let demoSocket = null;
                let demoMediaRecorder = null;
                let demoAudioChunks = [];
                let isDemoRecording = false;
                
                function initDemoWebSocket() {
                    if (!demoSocket) {
                        demoSocket = io();
                        
                        demoSocket.on('connect', function() {
                            console.log('Demo WebSocket connected');
                        });
                        
                        demoSocket.on('transcription_result', function(data) {
                            document.getElementById('liveSpeechResult').innerHTML = 
                                '<div class="result"><strong>📝 Transcription Result:</strong><br>"' + 
                                data.text + '"<br><small>Language: ' + data.language + 
                                ' | Time: ' + new Date().toLocaleTimeString() + '</small></div>';
                        });
                        
                        demoSocket.on('transcription_error', function(data) {
                            document.getElementById('liveSpeechResult').innerHTML = 
                                '<div class="result error"><strong>❌ Error:</strong> ' + data.error + '</div>';
                        });
                    }
                }
                
                async function startLiveRecording() {
                    try {
                        // Initialize WebSocket if needed
                        initDemoWebSocket();
                        
                        // Get microphone access
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        demoMediaRecorder = new MediaRecorder(stream);
                        demoAudioChunks = [];
                        
                        demoMediaRecorder.ondataavailable = function(event) {
                            if (event.data.size > 0) {
                                demoAudioChunks.push(event.data);
                            }
                        };
                        
                        demoMediaRecorder.onstop = function() {
                            const audioBlob = new Blob(demoAudioChunks, { type: 'audio/wav' });
                            sendDemoAudioToServer(audioBlob);
                        };
                        
                        demoMediaRecorder.start();
                        isDemoRecording = true;
                        
                        // Update UI
                        document.getElementById('startRecordingDemo').disabled = true;
                        document.getElementById('stopRecordingDemo').disabled = false;
                        document.getElementById('recordingStatus').innerHTML = '🔴 Recording...';
                        document.getElementById('recordingStatus').style.color = '#dc3545';
                        document.getElementById('liveSpeechResult').innerHTML = '🎙️ Recording in progress... Speak now!';
                        
                        // Emit start recording event
                        if (demoSocket) {
                            demoSocket.emit('start_recording', {
                                language: document.getElementById('demoLanguage').value
                            });
                        }
                        
                    } catch (error) {
                        console.error('Error starting demo recording:', error);
                        document.getElementById('liveSpeechResult').innerHTML = 
                            '<div class="result error"><strong>❌ Microphone Error:</strong> ' + error.message + 
                            '<br><small>Please allow microphone access and try again.</small></div>';
                    }
                }
                
                function stopLiveRecording() {
                    if (demoMediaRecorder && isDemoRecording) {
                        demoMediaRecorder.stop();
                        isDemoRecording = false;
                        
                        // Stop all tracks
                        demoMediaRecorder.stream.getTracks().forEach(track => track.stop());
                        
                        // Update UI
                        document.getElementById('startRecordingDemo').disabled = false;
                        document.getElementById('stopRecordingDemo').disabled = true;
                        document.getElementById('recordingStatus').innerHTML = '🔄 Processing...';
                        document.getElementById('recordingStatus').style.color = '#667eea';
                        document.getElementById('liveSpeechResult').innerHTML = '🔄 Processing audio for transcription...';
                        
                        // Emit stop recording event
                        if (demoSocket) {
                            demoSocket.emit('stop_recording', {});
                        }
                    }
                }
                
                function sendDemoAudioToServer(audioBlob) {
                    const reader = new FileReader();
                    reader.onload = function() {
                        const base64Data = reader.result.split(',')[1];
                        if (demoSocket) {
                            demoSocket.emit('audio_chunk', {
                                audio_data: base64Data,
                                language: document.getElementById('demoLanguage').value
                            });
                        }
                        
                        // Reset status
                        document.getElementById('recordingStatus').innerHTML = 'Ready to record';
                        document.getElementById('recordingStatus').style.color = '#666';
                    };
                    reader.readAsDataURL(audioBlob);
                }
                
                function testWebSocket() {
                    try {
                        const socket = io();
                        document.getElementById('websocketResult').innerHTML = '<div class="result">🔄 Connecting...</div>';
                        
                        socket.on('connection_status', function(data) {
                            document.getElementById('websocketResult').innerHTML = 
                                '<div class="result"><strong>WebSocket Status:</strong><br>' + 
                                JSON.stringify(data, null, 2) + '</div>';
                        });
                        
                        socket.on('connect_error', function(error) {
                            document.getElementById('websocketResult').innerHTML = 
                                '<div class="result error"><strong>Connection Error:</strong> ' + error + '</div>';
                        });
                        
                    } catch (error) {
                        document.getElementById('websocketResult').innerHTML = 
                            '<div class="result error"><strong>Error:</strong> ' + error.message + '</div>';
                    }
                }
                
                // Dark mode functionality
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
            </script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
        </body>
        </html>
        """
        return demo_html
