#!/usr/bin/env python3
"""
WhisperS2T Fallback Application
Quick fix when Whisper is not available
"""

import logging
import os
import tempfile
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mock Whisper class
class MockWhisper:
    def __init__(self):
        logger.info("Mock Whisper initialized - Real transcription not available")

    def transcribe(self, audio_file):
        logger.info(f"Mock transcription for file: {audio_file}")
        return {"text": "Mock transcription: Whisper not available. Please install: pip3 install --user openai-whisper"}


# Load mock model
model = MockWhisper()

UPLOAD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhisperS2T - Speech to Text</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.18); }
        h1 { text-align: center; margin-bottom: 30px; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .upload-area { border: 2px dashed rgba(255,255,255,0.5); padding: 40px; text-align: center; border-radius: 10px; margin: 20px 0; transition: all 0.3s ease; }
        .upload-area:hover { border-color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.1); }
        .btn { background: rgba(255,255,255,0.2); color: white; padding: 12px 24px; border: 2px solid rgba(255,255,255,0.3); border-radius: 25px; cursor: pointer; font-size: 16px; transition: all 0.3s ease; }
        .btn:hover { background: rgba(255,255,255,0.3); border-color: rgba(255,255,255,0.5); }
        .result { margin: 20px 0; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 10px; }
        .status { margin: 10px 0; font-weight: bold; text-align: center; }
        .warning { background: rgba(255, 193, 7, 0.2); padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #ffc107; }
        .nav { margin: 20px 0; text-align: center; }
        .nav a { color: rgba(255,255,255,0.8); text-decoration: none; margin: 0 15px; padding: 8px 16px; border-radius: 20px; transition: all 0.3s ease; }
        .nav a:hover { background: rgba(255,255,255,0.1); color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ WhisperS2T Appliance</h1>
        
        <div class="warning">
            <strong>⚠️ Quick Start Mode:</strong> Whisper AI not installed. This is a minimal interface for testing.
            <br><strong>To enable AI transcription:</strong> Run <code>pip3 install --user openai-whisper</code> and restart the service.
        </div>
        
        <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/admin">⚙️ Admin</a>
            <a href="/docs">📚 API Docs</a>
            <a href="/health">🏥 Health</a>
        </div>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <p>📁 Upload audio files for transcription</p>
                <input type="file" id="audioFile" name="audio" accept="audio/*" style="display: none;">
                <button type="button" class="btn" onclick="document.getElementById('audioFile').click()">Select Audio File</button>
            </div>
            <div style="text-align: center;">
                <button type="submit" class="btn">🚀 Test Upload</button>
            </div>
        </form>
        
        <div id="status" class="status"></div>
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        const form = document.getElementById('uploadForm');
        const fileInput = document.getElementById('audioFile');
        const status = document.getElementById('status');
        const result = document.getElementById('result');

        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                document.querySelector('.upload-area p').textContent = `Selected: ${fileName}`;
            }
        });

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!fileInput.files[0]) {
                status.innerHTML = '⚠️ Please select an audio file';
                return;
            }

            const formData = new FormData();
            formData.append('audio', fileInput.files[0]);

            status.innerHTML = '🔄 Processing... (Mock mode)';
            result.style.display = 'none';

            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (data.success) {
                    status.innerHTML = '✅ Mock processing completed!';
                    result.innerHTML = `<h3>Result:</h3><p>${data.transcription}</p>`;
                    result.style.display = 'block';
                } else {
                    status.innerHTML = `❌ Error: ${data.error}`;
                }
            } catch (error) {
                status.innerHTML = `❌ Error: ${error.message}`;
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(UPLOAD_TEMPLATE)


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"})

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})

    try:
        # Mock transcription
        result = model.transcribe(file.filename)
        transcription = result["text"]

        return jsonify(
            {
                "success": True,
                "transcription": transcription,
                "mode": "mock",
                "note": "Install openai-whisper for real AI transcription",
            }
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "mode": "quick-start",
            "whisper_available": False,
            "version": "fallback-1.0",
            "timestamp": datetime.now().isoformat(),
            "note": "Install openai-whisper for full functionality",
        }
    )


@app.route("/admin")
def admin():
    return render_template_string(
        """
    <html>
    <head><title>Admin Panel</title>
    <style>body{font-family:Arial;margin:40px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;}
    .container{max-width:800px;margin:0 auto;background:rgba(255,255,255,0.1);padding:30px;border-radius:15px;}
    .nav a{color:rgba(255,255,255,0.8);text-decoration:none;margin:0 15px;}</style>
    </head>
    <body>
    <div class="container">
        <h1>⚙️ Admin Panel</h1>
        <div class="nav">
            <a href="/">🏠 Home</a> | <a href="/health">🏥 Health</a> | <a href="/docs">📚 API Docs</a>
        </div>
        <p>Status: Quick Start Mode - Install OpenAI Whisper for full functionality</p>
        <p>Service: Running (Fallback)</p>
        <p>To enable full AI transcription: <code>pip3 install --user openai-whisper</code></p>
    </div>
    </body>
    </html>
    """
    )


@app.route("/docs")
def docs():
    return render_template_string(
        """
    <html>
    <head><title>API Documentation</title>
    <style>body{font-family:Arial;margin:40px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;}
    .container{max-width:800px;margin:0 auto;background:rgba(255,255,255,0.1);padding:30px;border-radius:15px;}
    .nav a{color:rgba(255,255,255,0.8);text-decoration:none;margin:0 15px;}</style>
    </head>
    <body>
    <div class="container">
        <h1>📚 API Documentation</h1>
        <div class="nav">
            <a href="/">🏠 Home</a> | <a href="/admin">⚙️ Admin</a> | <a href="/health">🏥 Health</a>
        </div>
        <h3>Available Endpoints:</h3>
        <ul>
            <li><strong>GET /</strong> - Main interface</li>
            <li><strong>POST /transcribe</strong> - Upload audio for transcription</li>
            <li><strong>GET /health</strong> - Health check</li>
            <li><strong>GET /admin</strong> - Admin panel</li>
        </ul>
        <p><strong>Note:</strong> This is a minimal version. Install openai-whisper for full API functionality.</p>
    </div>
    </body>
    </html>
    """
    )


if __name__ == "__main__":
    logger.info("🎤 Starting WhisperS2T Quick Start Appliance...")
    logger.info("⚠️  Mock mode - Install openai-whisper for AI transcription")
    logger.info("🌐 Starting server on https://0.0.0.0:5001")

    # Check for SSL certificates
    ssl_cert_path = None
    ssl_key_path = None

    # Try local development path
    local_ssl_cert = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ssl", "whisper-appliance.crt")
    local_ssl_key = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ssl", "whisper-appliance.key")

    if os.path.exists(local_ssl_cert) and os.path.exists(local_ssl_key):
        ssl_cert_path = local_ssl_cert
        ssl_key_path = local_ssl_key
        logger.info("🔒 SSL certificates found - Starting with HTTPS")
        app.run(host="0.0.0.0", port=5001, debug=False, ssl_context=(ssl_cert_path, ssl_key_path))
    else:
        logger.warning("🔓 No SSL certificates found - Starting HTTP only")
        logger.info("💡 Run ./create-ssl-cert.sh to enable HTTPS")
        app.run(host="0.0.0.0", port=5001, debug=False)
