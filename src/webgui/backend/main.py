#!/usr/bin/env python3
"""
WhisperS2T Appliance - FastAPI Backend MVP
Minimal viable backend für testing und development
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="WhisperS2T Appliance",
    description="Self-contained Speech-to-Text Appliance",
    version="0.1.0-mvp"
)

# Global state management
class AppState:
    def __init__(self):
        self.whisper_available = False
        self.whisper_module = None
        self.current_model = None
        self.available_models = ["tiny", "base", "small", "medium"]
        self.connected_clients: List[WebSocket] = []
        self.system_status = "initializing"
        
    async def initialize_whisper(self):
        """Initialize WhisperS2T in background"""
        try:
            # Try different import methods
            try:
                from whispers2t import WhisperS2T
                self.whisper_module = WhisperS2T
                self.whisper_available = True
                self.system_status = "ready"
                print("✅ WhisperS2T loaded successfully")
            except ImportError:
                try:
                    import whisper
                    self.whisper_module = whisper
                    self.whisper_available = True
                    self.system_status = "ready_fallback"
                    print("✅ OpenAI Whisper loaded as fallback")
                except ImportError:
                    self.system_status = "whisper_unavailable"
                    print("❌ No Whisper module available")
                    
        except Exception as e:
            self.system_status = f"error: {str(e)}"
            print(f"❌ Whisper initialization failed: {e}")

# Global app state
state = AppState()

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("🚀 Starting WhisperS2T Appliance...")
    await state.initialize_whisper()

@app.get("/")
async def root():
    """Root endpoint - returns simple status page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Appliance</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { padding: 10px; border-radius: 4px; margin: 10px 0; }
            .ready { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .button { display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 WhisperS2T Appliance</h1>
            <p>Self-contained Speech-to-Text System</p>
            
            <div class="status ready">
                <strong>Status:</strong> MVP Running
            </div>
            
            <h3>Quick Actions</h3>
            <a href="/api/status" class="button">API Status</a>
            <a href="/docs" class="button">API Documentation</a>
            <a href="/api/test-websocket" class="button">WebSocket Test</a>
            
            <h3>Next Steps</h3>
            <ul>
                <li>Run <code>make test</code> to validate WhisperS2T</li>
                <li>Test WebSocket connection</li>
                <li>Implement audio pipeline</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def get_status():
    """Get system status and capabilities"""
    import platform
    import psutil
    
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0-mvp",
        "status": state.system_status,
        "whisper": {
            "available": state.whisper_available,
            "current_model": state.current_model,
            "available_models": state.available_models
        },
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 1)
        },
        "websocket": {
            "connected_clients": len(state.connected_clients)
        }
    }

@app.post("/api/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a specific Whisper model"""
    if model_name not in state.available_models:
        raise HTTPException(status_code=400, detail=f"Model {model_name} not available")
    
    if not state.whisper_available:
        raise HTTPException(status_code=503, detail="Whisper not available")
    
    try:
        # Simulate model loading (implement actual loading later)
        await asyncio.sleep(1)  # Simulate loading time
        state.current_model = model_name
        
        # Broadcast to connected clients
        message = {
            "type": "model_changed",
            "model": model_name,
            "timestamp": datetime.now().isoformat()
        }
        await broadcast_to_clients(json.dumps(message))
        
        return {
            "status": "success",
            "model": model_name,
            "message": f"Model {model_name} loaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.websocket("/ws/live-transcription")
async def websocket_live_transcription(websocket: WebSocket):
    """WebSocket endpoint for live transcription"""
    await websocket.accept()
    state.connected_clients.append(websocket)
    
    # Send welcome message
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "WebSocket connected successfully",
        "timestamp": datetime.now().isoformat(),
        "server_status": state.system_status
    }))
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "start":
                # Start transcription simulation
                await websocket.send_text(json.dumps({
                    "type": "transcription_started",
                    "message": "Starting live transcription...",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Simulate some transcription results
                await simulate_transcription(websocket)
                
            elif message.get("action") == "stop":
                await websocket.send_text(json.dumps({
                    "type": "transcription_stopped",
                    "message": "Transcription stopped",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message.get("action") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        state.connected_clients.remove(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in state.connected_clients:
            state.connected_clients.remove(websocket)

async def simulate_transcription(websocket: WebSocket):
    """Simulate transcription results for testing"""
    test_phrases = [
        "Hello, this is a test transcription.",
        "The WhisperS2T appliance is working correctly.",
        "Real-time speech recognition is functional.",
        "Audio processing pipeline is ready.",
        "System integration test completed."
    ]
    
    for i, phrase in enumerate(test_phrases):
        await asyncio.sleep(2)  # Simulate processing time
        
        await websocket.send_text(json.dumps({
            "type": "transcription",
            "text": phrase,
            "confidence": 0.95 - (i * 0.05),  # Simulate decreasing confidence
            "timestamp": datetime.now().isoformat(),
            "segment": i + 1
        }))

async def broadcast_to_clients(message: str):
    """Broadcast message to all connected WebSocket clients"""
    if state.connected_clients:
        disconnected = []
        for client in state.connected_clients:
            try:
                await client.send_text(message)
            except:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            state.connected_clients.remove(client)

@app.get("/api/test-websocket")
async def test_websocket_page():
    """Simple WebSocket test page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 600px; }
            button { padding: 8px 16px; margin: 5px; cursor: pointer; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; background: #f9f9f9; }
            #input { width: 400px; padding: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>WebSocket Test Interface</h2>
            <div>
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="startTranscription()">Start Transcription</button>
                <button onclick="stopTranscription()">Stop Transcription</button>
                <button onclick="ping()">Ping</button>
            </div>
            <div>
                <input type="text" id="input" placeholder="Type a message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
            <div id="messages"></div>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/live-transcription`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    addMessage('Connected to WebSocket');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(`Received: ${JSON.stringify(data, null, 2)}`);
                };
                
                ws.onclose = function() {
                    addMessage('WebSocket connection closed');
                };
                
                ws.onerror = function(error) {
                    addMessage(`WebSocket error: ${error}`);
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                }
            }
            
            function startTranscription() {
                if (ws) {
                    ws.send(JSON.stringify({action: 'start'}));
                }
            }
            
            function stopTranscription() {
                if (ws) {
                    ws.send(JSON.stringify({action: 'stop'}));
                }
            }
            
            function ping() {
                if (ws) {
                    ws.send(JSON.stringify({action: 'ping'}));
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('input');
                if (ws && input.value) {
                    ws.send(input.value);
                    addMessage(`Sent: ${input.value}`);
                    input.value = '';
                }
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            function addMessage(message) {
                const messages = document.getElementById('messages');
                const timestamp = new Date().toLocaleTimeString();
                messages.innerHTML += `<div>[${timestamp}] ${message}</div>`;
                messages.scrollTop = messages.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Appliance MVP Server...")
    print("📱 WebGUI: http://localhost:5000")
    print("📚 API Docs: http://localhost:5000/docs")
    print("🧪 WebSocket Test: http://localhost:5000/api/test-websocket")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
