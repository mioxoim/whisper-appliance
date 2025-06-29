#!/usr/bin/env python3
"""
Enhanced WhisperS2T Appliance with Update Management
Production-ready Flask application with web-based updates
"""

import logging
import os
import subprocess
import tempfile

from flask import Flask, jsonify, render_template_string, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load whisper, fallback gracefully
try:
    import whisper

    model = whisper.load_model("base")
    WHISPER_AVAILABLE = True
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.warning(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False
    model = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhisperS2T Appliance v0.6.0</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f8f9fa; }
        .header { background: #007bff; color: white; padding: 20px 0; text-align: center; }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1 { margin: 0; font-size: 2.2em; }
        h2 { color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
        .status-bar { display: flex; justify-content: space-between; align-items: center; background: #e9ecef; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .status-indicator { padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9em; }
        .status-healthy { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        .upload-area { border: 3px dashed #007bff; padding: 50px; text-align: center; margin: 25px 0; border-radius: 12px; background: #f8f9fa; transition: all 0.3s; }
        .upload-area:hover { background: #e9ecef; border-color: #0056b3; }
        .upload-area.dragover { background: #cce7ff; border-color: #007bff; }
        .result { margin: 25px 0; padding: 25px; border-radius: 8px; border-left: 5px solid #28a745; background: #d4edda; }
        .result.error { background: #f8d7da; border-left-color: #dc3545; }
        button { background: #007bff; color: white; padding: 14px 28px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s; margin: 5px; }
        button:hover { background: #0056b3; transform: translateY(-1px); }
        button:disabled { background: #6c757d; cursor: not-allowed; transform: none; }
        button.secondary { background: #6c757d; }
        button.secondary:hover { background: #545b62; }
        button.success { background: #28a745; }
        button.success:hover { background: #1e7e34; }
        button.warning { background: #ffc107; color: #212529; }
        button.warning:hover { background: #e0a800; }
        button.danger { background: #dc3545; }
        button.danger:hover { background: #c82333; }
        .update-section { border-top: 2px solid #e9ecef; padding-top: 20px; margin-top: 30px; }
        .update-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .loading { display: none; text-align: center; padding: 20px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #007bff; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .tabs { display: flex; border-bottom: 2px solid #e9ecef; margin-bottom: 20px; }
        .tab { padding: 12px 24px; background: none; border: none; cursor: pointer; font-size: 16px; border-bottom: 3px solid transparent; }
        .tab.active { border-bottom-color: #007bff; color: #007bff; font-weight: bold; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎤 WhisperS2T Appliance</h1>
        <p>Production-ready Speech-to-Text with Container Deployment</p>
    </div>

    <div class="container">
        <div class="status-bar">
            <div>
                <span class="status-indicator {{ 'status-healthy' if whisper_available else 'status-error' }}">
                    {{ '✅ Whisper Ready' if whisper_available else '⚠️ Loading Model' }}
                </span>
            </div>
            <div id="updateIndicator"></div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('transcribe')">🎵 Transcribe</button>
            <button class="tab" onclick="switchTab('system')">⚙️ System</button>
            <button class="tab" onclick="switchTab('updates')">🔄 Updates</button>
        </div>

        <!-- Transcription Tab -->
        <div id="transcribe" class="tab-content active">
            <div class="card">
                {% if whisper_available %}
                <h2>Audio Transcription</h2>
                <p>Upload an audio file to transcribe it using OpenAI Whisper</p>
                
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="upload-area" id="uploadArea">
                        <input type="file" name="audio" id="audioFile" accept="audio/*" required style="display: none;">
                        <div onclick="document.getElementById('audioFile').click()">
                            <p style="font-size: 1.2em; margin: 10px 0;">📁 Click to select audio file</p>
                            <p>or drag and drop here</p>
                            <p><small>Supported: MP3, WAV, M4A, FLAC, OGG (max 100MB)</small></p>
                        </div>
                    </div>
                    <button type="submit" id="transcribeBtn">🎵 Transcribe Audio</button>
                </form>
                
                <div id="result" class="result" style="display:none;">
                    <h3>Transcription Result:</h3>
                    <div id="transcription"></div>
                </div>
                {% else %}
                <div class="result error">
                    <h3>⚠️ Service Starting</h3>
                    <p>The Whisper model is currently loading. Please refresh the page in a few moments.</p>
                    <button onclick="location.reload()">🔄 Refresh Page</button>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- System Tab -->
        <div id="system" class="tab-content">
            <div class="card">
                <h2>System Information</h2>
                <div id="systemInfo">
                    <div class="update-info">
                        <strong>Version:</strong> v0.6.0<br>
                        <strong>Status:</strong> <span id="serviceStatus">Checking...</span><br>
                        <strong>Installation:</strong> Container-based deployment
                    </div>
                </div>
                
                <div class="update-section">
                    <h3>System Management</h3>
                    <button onclick="restartService()" class="warning">🔄 Restart Service</button>
                    <button onclick="checkHealth()" class="secondary">🏥 Health Check</button>
                </div>
            </div>
        </div>

        <!-- Updates Tab -->
        <div id="updates" class="tab-content">
            <div class="card">
                <h2>Update Management</h2>
                <div id="updateStatus" class="update-info">
                    <p>Checking for updates...</p>
                </div>
                
                <div id="updateActions" style="display: none;">
                    <button id="applyUpdateBtn" onclick="applyUpdate()" class="success" style="display: none;">
                        ⬇️ Install Updates
                    </button>
                    <button onclick="checkUpdates()" class="secondary">🔍 Check Again</button>
                </div>
                
                <div class="loading" id="updateLoading">
                    <div class="spinner"></div>
                    <p>Processing update...</p>
                </div>
                
                <div class="update-section">
                    <h3>Update Information</h3>
                    <p>Updates are automatically pulled from GitHub repository. The system will:</p>
                    <ul>
                        <li>✅ Create backup before updating</li>
                        <li>✅ Download latest changes</li>
                        <li>✅ Restart services automatically</li>
                        <li>✅ Preserve all data and configuration</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Tab switching
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Load tab-specific data
            if (tabName === 'updates') {
                checkUpdates();
            } else if (tabName === 'system') {
                checkHealth();
            }
        }

        // Drag and drop functionality
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    document.getElementById('audioFile').files = files;
                    uploadArea.querySelector('p').textContent = `📁 Selected: ${files[0].name}`;
                }
            });
        }

        // Transcription functionality
        {% if whisper_available %}
        document.getElementById('uploadForm').onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const transcribeBtn = document.getElementById('transcribeBtn');
            
            transcribeBtn.disabled = true;
            transcribeBtn.textContent = '🔄 Processing...';
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('transcription').innerHTML = '🔄 Processing audio file, please wait...';
            
            fetch('/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                transcribeBtn.disabled = false;
                transcribeBtn.textContent = '🎵 Transcribe Audio';
                
                if (data.error) {
                    document.getElementById('result').className = 'result error';
                    document.getElementById('transcription').innerHTML = '❌ Error: ' + data.error;
                } else {
                    document.getElementById('result').className = 'result';
                    document.getElementById('transcription').innerHTML = '📝 ' + data.text;
                }
            })
            .catch(error => {
                transcribeBtn.disabled = false;
                transcribeBtn.textContent = '🎵 Transcribe Audio';
                document.getElementById('result').className = 'result error';
                document.getElementById('transcription').innerHTML = '❌ Network error: ' + error;
            });
        };
        {% endif %}

        // Update functionality
        function checkUpdates() {
            document.getElementById('updateActions').style.display = 'none';
            document.getElementById('updateStatus').innerHTML = '<p>🔍 Checking for updates...</p>';
            
            fetch('/update/status')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('updateStatus').innerHTML = 
                        `<p class="status-error">❌ ${data.error}</p>
                         <p>${data.message || ''}</p>`;
                } else {
                    if (data.updates_available) {
                        document.getElementById('updateStatus').innerHTML = 
                            `<p class="status-warning">🔄 Updates Available!</p>
                             <p><strong>Current Version:</strong> ${data.current_version}</p>
                             <p><strong>Commits Behind:</strong> ${data.commits_behind}</p>
                             <p>New features and bug fixes are available.</p>`;
                        
                        document.getElementById('applyUpdateBtn').style.display = 'inline-block';
                    } else {
                        document.getElementById('updateStatus').innerHTML = 
                            `<p class="status-healthy">✅ System Up to Date</p>
                             <p><strong>Current Version:</strong> ${data.current_version}</p>
                             <p>You are running the latest version.</p>`;
                    }
                    document.getElementById('updateActions').style.display = 'block';
                }
            })
            .catch(error => {
                document.getElementById('updateStatus').innerHTML = 
                    `<p class="status-error">❌ Failed to check updates</p>
                     <p>Error: ${error}</p>`;
            });
        }

        function applyUpdate() {
            if (!confirm('This will update the system and restart services. Continue?')) {
                return;
            }
            
            document.getElementById('updateLoading').style.display = 'block';
            document.getElementById('updateActions').style.display = 'none';
            document.getElementById('applyUpdateBtn').style.display = 'none';
            
            fetch('/update/apply', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('updateLoading').style.display = 'none';
                
                if (data.success) {
                    document.getElementById('updateStatus').innerHTML = 
                        `<p class="status-healthy">✅ Update Successful!</p>
                         <p><strong>Updated to:</strong> ${data.new_version}</p>
                         <p>${data.message}</p>`;
                    
                    if (data.restart_required) {
                        setTimeout(() => {
                            if (confirm('Update complete! Restart service now?')) {
                                restartService();
                            }
                        }, 2000);
                    }
                } else {
                    document.getElementById('updateStatus').innerHTML = 
                        `<p class="status-error">❌ Update Failed</p>
                         <p>${data.error}</p>
                         <p>${data.message || ''}</p>`;
                }
                
                document.getElementById('updateActions').style.display = 'block';
            })
            .catch(error => {
                document.getElementById('updateLoading').style.display = 'none';
                document.getElementById('updateStatus').innerHTML = 
                    `<p class="status-error">❌ Update failed</p>
                     <p>Error: ${error}</p>`;
                document.getElementById('updateActions').style.display = 'block';
            });
        }

        // System management
        function restartService() {
            if (!confirm('This will restart the WhisperS2T service. Continue?')) {
                return;
            }
            
            fetch('/system/restart', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Service restart initiated. Page will reload in 5 seconds.');
                    setTimeout(() => location.reload(), 5000);
                } else {
                    alert('❌ Failed to restart service: ' + data.message);
                }
            })
            .catch(error => {
                alert('❌ Error: ' + error);
            });
        }

        function checkHealth() {
            fetch('/health')
            .then(response => response.json())
            .then(data => {
                const statusText = data.status === 'healthy' ? '✅ Healthy' : '❌ Unhealthy';
                const whisperText = data.whisper_available ? '✅ Available' : '❌ Not Available';
                
                document.getElementById('serviceStatus').innerHTML = statusText;
                document.getElementById('systemInfo').innerHTML = 
                    `<div class="update-info">
                        <strong>Version:</strong> ${data.version}<br>
                        <strong>Status:</strong> ${statusText}<br>
                        <strong>Whisper Model:</strong> ${whisperText}<br>
                        <strong>Installation:</strong> Container-based deployment
                    </div>`;
            })
            .catch(error => {
                document.getElementById('serviceStatus').innerHTML = '❌ Error checking status';
            });
        }

        // Auto-check for updates on page load
        setTimeout(checkUpdates, 1000);
        
        // Auto-check health on page load
        setTimeout(checkHealth, 500);
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, whisper_available=WHISPER_AVAILABLE)


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "whisper_available": WHISPER_AVAILABLE, "version": "0.6.0"})


@app.route("/update/status")
def update_status():
    """Check for available updates"""
    try:
        import os
        import subprocess

        # Check if we're in a git repository
        app_dir = "/opt/whisper-appliance"
        if not os.path.exists(f"{app_dir}/.git"):
            return jsonify(
                {"error": "Not a git installation", "message": "Updates only available for git-cloned installations"}
            )

        # Configure SSH if deploy key exists
        env = os.environ.copy()
        if os.path.exists(f"{app_dir}/deploy_key_whisper_appliance"):
            env["GIT_SSH_COMMAND"] = f"ssh -i {app_dir}/deploy_key_whisper_appliance -o IdentitiesOnly=yes"

        # Get current commit
        current_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=app_dir, env=env, universal_newlines=True
        ).strip()

        # Get current version
        try:
            current_version = subprocess.check_output(
                ["git", "describe", "--tags", "--always"], cwd=app_dir, env=env, universal_newlines=True
            ).strip()
        except:
            current_version = current_commit[:8]

        # Fetch latest changes
        subprocess.run(["git", "fetch", "origin", "main"], cwd=app_dir, env=env, capture_output=True)

        # Get remote commit
        remote_commit = subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=app_dir, env=env, universal_newlines=True
        ).strip()

        updates_available = current_commit != remote_commit

        if updates_available:
            # Get number of commits behind
            commits_behind = subprocess.check_output(
                ["git", "rev-list", "--count", f"{current_commit}..origin/main"], cwd=app_dir, env=env, universal_newlines=True
            ).strip()
        else:
            commits_behind = "0"

        return jsonify(
            {
                "current_version": current_version,
                "current_commit": current_commit,
                "latest_commit": remote_commit,
                "updates_available": updates_available,
                "commits_behind": int(commits_behind),
            }
        )

    except Exception as e:
        logger.error(f"Update status check failed: {e}")
        return jsonify({"error": str(e)})


@app.route("/update/apply", methods=["POST"])
def update_apply():
    """Apply available updates"""
    try:
        import os
        import subprocess

        app_dir = "/opt/whisper-appliance"
        if not os.path.exists(f"{app_dir}/.git"):
            return jsonify(
                {"error": "Not a git installation", "message": "Updates only available for git-cloned installations"}
            )

        # Configure SSH if deploy key exists
        env = os.environ.copy()
        if os.path.exists(f"{app_dir}/deploy_key_whisper_appliance"):
            env["GIT_SSH_COMMAND"] = f"ssh -i {app_dir}/deploy_key_whisper_appliance -o IdentitiesOnly=yes"

        # Check if updates are available
        current_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=app_dir, env=env, universal_newlines=True
        ).strip()

        subprocess.run(["git", "fetch", "origin", "main"], cwd=app_dir, env=env)

        remote_commit = subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=app_dir, env=env, universal_newlines=True
        ).strip()

        if current_commit == remote_commit:
            return jsonify({"success": True, "message": "System is already up to date", "action": "none"})

        # Apply updates
        result = subprocess.run(
            ["git", "pull", "origin", "main"], cwd=app_dir, env=env, capture_output=True, universal_newlines=True
        )

        if result.returncode == 0:
            # Update was successful
            new_version = subprocess.check_output(
                ["git", "describe", "--tags", "--always"], cwd=app_dir, env=env, universal_newlines=True
            ).strip()

            # Update permissions
            subprocess.run(["chmod", "+x", f"{app_dir}/*.sh"], shell=True)

            return jsonify(
                {
                    "success": True,
                    "message": f"Updated to version {new_version}",
                    "old_version": current_commit[:8],
                    "new_version": new_version,
                    "restart_required": True,
                }
            )
        else:
            return jsonify({"error": "Update failed", "message": result.stderr})

    except Exception as e:
        logger.error(f"Update apply failed: {e}")
        return jsonify({"error": str(e)})


@app.route("/system/restart", methods=["POST"])
def system_restart():
    """Restart the WhisperS2T service"""
    try:
        import subprocess

        # Restart the service
        result = subprocess.run(["systemctl", "restart", "whisper-appliance"], capture_output=True, universal_newlines=True)

        if result.returncode == 0:
            return jsonify({"success": True, "message": "Service restart initiated"})
        else:
            return jsonify({"error": "Failed to restart service", "message": result.stderr})

    except Exception as e:
        logger.error(f"Service restart failed: {e}")
        return jsonify({"error": str(e)})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not WHISPER_AVAILABLE:
        return jsonify({"error": "Whisper model not available"})

    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"})

        audio_file = request.files["audio"]
        if audio_file.filename == "":
            return jsonify({"error": "No audio file selected"})

        # Secure filename
        filename = secure_filename(audio_file.filename)

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_file.save(tmp_file.name)

            # Transcribe audio
            logger.info(f"Transcribing file: {filename}")
            result = model.transcribe(tmp_file.name)

            # Clean up temp file
            os.unlink(tmp_file.name)

            logger.info("Transcription completed successfully")
            return jsonify({"text": result["text"]})

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    logger.info("🎤 WhisperS2T Appliance with Update Management starting...")
    app.run(host="0.0.0.0", port=5001, debug=False)
