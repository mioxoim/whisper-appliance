#!/usr/bin/env python3
"""
Enhanced WhisperS2T Appliance v0.6.0 with Live Speech Recognition
Basic working version with upload functionality and live speech stub
"""

import logging
import os
import tempfile
import threading
import time
from datetime import datetime

import whisper
from flask import Flask, jsonify, render_template_string, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
model = None
transcription_active = False
current_transcription = ""

def load_whisper_model():
    """Load Whisper model in background"""
    global model
    try:
        model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")

# Load model in background
threading.Thread(target=load_whisper_model, daemon=True).start()

ENHANCED_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>WhisperS2T v0.6.0 - Speech to Text</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { flex: 1; padding: 15px; text-align: center; cursor: pointer; border: 1px solid #ddd; background: #f8f9fa; }
        .tab.active { background: #007bff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 10px; margin: 20px 0; cursor: pointer; }
        .upload-area:hover { border-color: #007bff; }
        .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .result { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }
        .status { margin: 10px 0; font-weight: bold; }
        .error { color: #dc3545; }
        .success { color: #28a745; }
        .warning { color: #ffc107; background: #fff3cd; padding: 10px; border-radius: 5px; margin: 20px 0; }
        .transcription-output { background: #f8f9fa; border: 2px solid #e9ecef; border-radius: 10px; padding: 20px; min-height: 200px; font-family: monospace; white-space: pre-wrap; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ WhisperS2T v0.6.0</h1>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('live')">🎙️ Live Speech</div>
            <div class="tab" onclick="showTab('upload')">📁 Upload File</div>
            <div class="tab" onclick="showTab('system')">⚙️ System</div>
        </div>
        
        <!-- Live Speech Tab -->
        <div id="live" class="tab-content active">
            <h2>🎙️ Live Speech Recognition</h2>
            <div class="warning">
                <strong>⚠️ Live Speech Feature:</strong> Currently in development. Use Upload tab for transcription.
            </div>
            
            <button class="btn" onclick="startLive()" disabled>🎙️ Start Recording (Coming Soon)</button>
            <button class="btn" onclick="stopLive()" disabled>⏹️ Stop Recording</button>
            
            <div class="transcription-output" id="liveOutput">
                Live transcription will appear here when feature is complete...
            </div>
        </div>
        
        <!-- Upload Tab -->
        <div id="upload" class="tab-content">
            <h2>📁 Upload Audio File</h2>
            
            <div class="upload-area" onclick="document.getElementById('audioFile').click()">
                <p>📁 Drag & drop audio files here or click to select</p>
                <p>Supports MP3, WAV, M4A, FLAC, OGG (max 100MB)</p>
                <input type="file" id="audioFile" name="audio" accept="audio/*" style="display: none;" onchange="handleFileSelect(event)">
            </div>
            
            <button class="btn" onclick="document.getElementById('audioFile').click()">Select Audio File</button>
            
            <div id="uploadStatus" class="status"></div>
            <div id="uploadResult" class="result" style="display: none;"></div>
        </div>
        
        <!-- System Tab -->
        <div id="system" class="tab-content">
            <h2>⚙️ System Information</h2>
            
            <div class="result">
                <h3>Service Status</h3>
                <p><strong>Version:</strong> 0.6.0</p>
                <p><strong>Model:</strong> <span id="modelStatus">Loading...</span></p>
                <p><strong>Features:</strong> File Upload ✅, Live Speech 🚧</p>
                
                <button class="btn" onclick="checkHealth()">Check Health</button>
            </div>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                transcribeFile(file);
            }
        }
        
        async function transcribeFile(file) {
            const formData = new FormData();
            formData.append('audio', file);
            
            document.getElementById('uploadStatus').innerHTML = '<span class="success">Transcribing... Please wait.</span>';
            document.getElementById('uploadResult').style.display = 'none';
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('uploadStatus').innerHTML = '<span class="success">✅ Transcription completed!</span>';
                    document.getElementById('uploadResult').innerHTML = 
                        '<h3>Result:</h3><p>' + data.transcription + '</p>' +
                        '<button class="btn" onclick="copyText(\'' + data.transcription.replace(/'/g, "\\\\'") + '\')">Copy Text</button>';
                    document.getElementById('uploadResult').style.display = 'block';
                } else {
                    document.getElementById('uploadStatus').innerHTML = '<span class="error">❌ Error: ' + data.error + '</span>';
                }
            } catch (error) {
                document.getElementById('uploadStatus').innerHTML = '<span class="error">❌ Error: ' + error.message + '</span>';
            }
        }
        
        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                document.getElementById('uploadStatus').innerHTML = '<span class="success">Text copied to clipboard!</span>';
            });
        }
        
        async function checkHealth() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                document.getElementById('modelStatus').textContent = data.model_loaded ? 'Loaded ✅' : 'Loading...';
            } catch (error) {
                document.getElementById('modelStatus').textContent = 'Error ❌';
            }
        }
        
        function startLive() {
            alert('Live speech feature is coming soon! Please use the Upload tab for now.');
        }
        
        function stopLive() {
            alert('Live speech feature is coming soon!');
        }
        
        // Initialize
        window.addEventListener('load', checkHealth);
        
        // Drag and Drop
        const uploadArea = document.querySelector('.upload-area');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#007bff';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#ccc';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#ccc';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                transcribeFile(files[0]);
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(ENHANCED_TEMPLATE)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe uploaded audio file"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'})
    
    if model is None:
        return jsonify({'success': False, 'error': 'Whisper model not loaded yet. Please wait and try again.'})
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            file.save(tmp_file.name)
            
            # Transcribe
            result = model.transcribe(tmp_file.name)
            transcription = result['text'].strip()
            
            # Clean up
            os.unlink(tmp_file.name)
            
            logger.info(f"Transcribed file: {filename}")
            return jsonify({
                'success': True,
                'transcription': transcription,
                'filename': filename
            })
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/live/start', methods=['POST'])
def start_live():
    """Placeholder for live transcription"""
    return jsonify({'success': False, 'error': 'Live speech feature coming soon'})

@app.route('/live/stop', methods=['POST'])
def stop_live():
    """Placeholder for stopping live transcription"""
    return jsonify({'success': False, 'error': 'Live speech feature coming soon'})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'version': '0.6.0',
        'features': {
            'file_upload': True,
            'live_speech': False,
            'whisper_model': 'base'
        }
    })

if __name__ == '__main__':
    logger.info("Starting WhisperS2T v0.6.0")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
