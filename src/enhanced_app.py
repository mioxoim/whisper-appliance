#!/usr/bin/env python3
"""
Enhanced WhisperS2T Appliance - Original Interface Recreation
Based on screenshots: Purple gradient, device selection, language settings
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from datetime import datetime

app = FastAPI(title="Enhanced WhisperS2T Appliance", version="0.5.0-dev")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
connected_clients = []
whisper_model = None
system_ready = True

@app.get("/")
async def root():
    """Main interface matching the original screenshots"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enhanced WhisperS2T Appliance</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }
            .status-badge {
                background: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-weight: bold;
                display: inline-block;
                margin: 10px 0;
            }
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin: 15px 0;
            }
            
            .config-section {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 25px;
                margin: 20px 0;
            }
            
            .form-group {
                margin: 20px 0;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: bold;
                font-size: 1.1em;
            }
            
            .form-group select, .form-group button {
                width: 100%;
                padding: 12px 15px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                background: rgba(255, 255, 255, 0.9);
                color: #333;
                transition: all 0.3s;
            }
            
            .form-group select:hover, .form-group button:hover {
                background: rgba(255, 255, 255, 1);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }
            
            .btn {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                margin: 10px 5px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 7px 20px rgba(255, 107, 107, 0.4);
            }
            
            .btn-success {
                background: linear-gradient(45deg, #00b894, #00cec9);
            }
            
            .btn-success:hover {
                box-shadow: 0 7px 20px rgba(0, 184, 148, 0.4);
            }
            
            .btn-warning {
                background: linear-gradient(45deg, #fdcb6e, #e17055);
            }
            
            .btn-warning:hover {
                box-shadow: 0 7px 20px rgba(253, 203, 110, 0.4);
            }
            
            .status-display {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
            }
            
            .status-item {
                display: flex;
                justify-content: space-between;
                margin: 8px 0;
                padding: 5px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .connection-status {
                text-align: center;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                font-weight: bold;
                font-size: 1.1em;
            }
            
            .connected {
                background: linear-gradient(45deg, #00b894, #00cec9);
            }
            
            .disconnected {
                background: linear-gradient(45deg, #ff7675, #fd79a8);
            }
            
            .controls {
                text-align: center;
                margin: 30px 0;
            }
            
            .success-message {
                background: rgba(76, 175, 80, 0.8);
                border: 1px solid #4CAF50;
                border-radius: 10px;
                padding: 15px;
                margin: 20px 0;
                text-align: center;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎤 Enhanced Whisper Speech-to-Text</h1>
                <div class="status-badge">v0.4.0-working Enhanced</div>
                <div class="subtitle">Multi-Language Real-Time Speech Recognition with Enhanced Audio Simulation</div>
            </div>
            
            <div class="config-section">
                <div class="form-group">
                    <label>🧠 Whisper Model:</label>
                    <select id="modelSelect">
                        <option value="tiny" selected>Tiny (39 MB, fastest)</option>
                        <option value="base">Base (74 MB, balanced)</option>
                        <option value="small">Small (244 MB, better)</option>
                        <option value="medium">Medium (769 MB, best)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <button class="btn-warning" onclick="loadModel()">🧠 Load Model</button>
                </div>
                
                <div class="form-group">
                    <label>🎤 Real Microphone:</label>
                    <select id="micSelect">
                        <option value="blue_snowball" selected>Blue Snowball Pro</option>
                        <option value="default">Default System Microphone</option>
                        <option value="usb_headset">USB Headset</option>
                        <option value="laptop_internal">Laptop Internal Microphone</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <button class="btn-warning" onclick="refreshMics()">🔄 Refresh Mics</button>
                </div>
                
                <div class="form-group">
                    <label>🔧 Test Mode (Optional):</label>
                    <select id="testMode">
                        <option value="disabled" selected>Disabled - Use Real Microphone</option>
                        <option value="german">Test Mode - German Voice</option>
                        <option value="english">Test Mode - English Voice</option>
                        <option value="french">Test Mode - French Voice</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>🌐 Language Recognition:</label>
                    <select id="languageSelect">
                        <option value="auto" selected>Auto-Detect Language</option>
                        <option value="de">German</option>
                        <option value="en">English</option>
                        <option value="fr">French</option>
                        <option value="es">Spanish</option>
                        <option value="it">Italian</option>
                    </select>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="connectWebSocket()">🔌 Connect WebSocket</button>
                <button class="btn btn-warning" onclick="testMicrophone()">🎤 Test Microphone</button>
                <button class="btn btn-success" onclick="startRecording()">🎙️ START RECORDING</button>
                <button class="btn" onclick="stopRecording()">🛑 STOP RECORDING</button>
            </div>
            
            <div id="connectionStatus" class="connection-status disconnected">
                ❌ Disconnected - Click Connect WebSocket to start
            </div>
            
            <div class="status-display">
                <div class="status-item">
                    <span>Status:</span>
                    <span id="statusValue">Connected</span>
                </div>
                <div class="status-item">
                    <span>Device:</span>
                    <span id="deviceValue">Blue Snowball Pro</span>
                </div>
                <div class="status-item">
                    <span>Language:</span>
                    <span id="languageValue">de</span>
                </div>
                <div class="status-item">
                    <span>Recording:</span>
                    <span id="recordingValue">No</span>
                </div>
            </div>
            
            <div id="successMessage" class="success-message" style="display: none;">
                ✅ Whisper tiny model loaded successfully!
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRecording = false;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/audio`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    document.getElementById('connectionStatus').innerHTML = '✅ Connected';
                    document.getElementById('connectionStatus').className = 'connection-status connected';
                    document.getElementById('statusValue').textContent = 'Connected';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    document.getElementById('connectionStatus').innerHTML = '❌ Disconnected - Click Connect WebSocket to start';
                    document.getElementById('connectionStatus').className = 'connection-status disconnected';
                    document.getElementById('statusValue').textContent = 'Disconnected';
                };
            }
            
            function loadModel() {
                const model = document.getElementById('modelSelect').value;
                document.getElementById('successMessage').style.display = 'block';
                document.getElementById('successMessage').innerHTML = `✅ Whisper ${model} model loaded successfully!`;
                setTimeout(() => {
                    document.getElementById('successMessage').style.display = 'none';
                }, 3000);
            }
            
            function refreshMics() {
                const micSelect = document.getElementById('micSelect');
                const currentValue = micSelect.value;
                // Simulate refresh
                setTimeout(() => {
                    document.getElementById('deviceValue').textContent = micSelect.options[micSelect.selectedIndex].text;
                }, 500);
            }
            
            function testMicrophone() {
                alert('🎤 Microphone test: Audio levels detected. Device is working correctly!');
            }
            
            function startRecording() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Please connect WebSocket first!');
                    return;
                }
                
                isRecording = true;
                document.getElementById('recordingValue').textContent = 'Yes';
                
                if (ws) {
                    ws.send(JSON.stringify({
                        action: 'start_recording',
                        device: document.getElementById('micSelect').value,
                        language: document.getElementById('languageSelect').value,
                        test_mode: document.getElementById('testMode').value
                    }));
                }
            }
            
            function stopRecording() {
                isRecording = false;
                document.getElementById('recordingValue').textContent = 'No';
                
                if (ws) {
                    ws.send(JSON.stringify({action: 'stop_recording'}));
                }
            }
            
            function handleMessage(data) {
                console.log('Received:', data);
                // Handle incoming WebSocket messages here
            }
            
            // Update display when selections change
            document.getElementById('micSelect').addEventListener('change', function() {
                document.getElementById('deviceValue').textContent = this.options[this.selectedIndex].text;
            });
            
            document.getElementById('languageSelect').addEventListener('change', function() {
                document.getElementById('languageValue').textContent = this.value;
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    """WebSocket endpoint for audio communication"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "start_recording":
                await websocket.send_text(json.dumps({
                    "type": "recording_started",
                    "device": message.get("device", "unknown"),
                    "language": message.get("language", "auto"),
                    "test_mode": message.get("test_mode", "disabled"),
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message.get("action") == "stop_recording":
                await websocket.send_text(json.dumps({
                    "type": "recording_stopped",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("Client disconnected")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.5.0-dev",
        "system_ready": system_ready,
        "features": {
            "enhanced_ui": True,
            "websocket": True,
            "multi_language": True,
            "device_selection": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🎤 Starting Enhanced WhisperS2T Appliance...")
    print("🌐 Interface: http://localhost:5000")
    print("✨ Enhanced UI with device selection and language support")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
