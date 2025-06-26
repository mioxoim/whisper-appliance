#!/usr/bin/env python3
"""
WhisperS2T Appliance - FastAPI Backend mit echter Whisper Integration
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import asyncio
import json
from datetime import datetime
import numpy as np
import time

# Import faster-whisper
from faster_whisper import WhisperModel

app = FastAPI(title="WhisperS2T Appliance", version="0.2.0")

# Global state
whisper_model = None
current_model_name = None
connected_clients = []
system_ready = False

async def load_whisper_model(model_name="tiny"):
    """Load Whisper model asynchronously"""
    global whisper_model, current_model_name
    
    print(f"🔄 Loading {model_name} model...")
    start_time = time.time()
    
    # Load in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    whisper_model = await loop.run_in_executor(
        None, 
        lambda: WhisperModel(model_name, device="cpu", compute_type="int8")
    )
    
    load_time = time.time() - start_time
    current_model_name = model_name
    
    print(f"✅ Model {model_name} loaded in {load_time:.1f}s")
    return {"model": model_name, "load_time": round(load_time, 1)}

async def transcribe_audio(audio_data):
    """Transcribe audio using loaded model"""
    global whisper_model
    
    if not whisper_model:
        await load_whisper_model("tiny")
    
    print(f"🎤 Transcribing {len(audio_data)} audio samples...")
    start_time = time.time()
    
    # Run transcription in thread pool
    loop = asyncio.get_event_loop()
    segments, info = await loop.run_in_executor(
        None,
        lambda: whisper_model.transcribe(audio_data, beam_size=1)
    )
    
    # Collect all text
    full_text = " ".join(segment.text for segment in segments)
    processing_time = time.time() - start_time
    
    return {
        "text": full_text.strip(),
        "language": info.language,
        "processing_time": round(processing_time, 2),
        "model": current_model_name
    }

def generate_test_audio(duration=2.0):
    """Generate simple test audio (sine wave)"""
    sample_rate = 16000
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples)
    
    # Create a decaying sine wave
    audio = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.5)
    return audio.astype(np.float32)

@app.on_event("startup")
async def startup_event():
    """Initialize Whisper on startup"""
    global system_ready
    
    print("🚀 Starting WhisperS2T Appliance...")
    try:
        await load_whisper_model("tiny")
        system_ready = True
        print("✅ WhisperS2T Appliance ready for transcription!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        system_ready = False

@app.get("/")
async def root():
    """Main landing page"""
    status = "✅ Ready for transcription!" if system_ready else "🔄 Starting up..."
    model = current_model_name or "Loading..."
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Appliance</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ padding: 15px; background: #d4edda; color: #155724; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; font-weight: bold; }}
            .button:hover {{ background: #0056b3; }}
            .feature {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #007bff; }}
            .code {{ background: #e9ecef; padding: 8px; border-radius: 4px; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 WhisperS2T Appliance</h1>
            <p><strong>Self-contained Speech-to-Text System</strong></p>
            
            <div class="status">{status}</div>
            
            <div class="feature">
                <h3>🚀 Real Whisper Features</h3>
                <ul>
                    <li><strong>Real-time transcription</strong> with faster-whisper</li>
                    <li><strong>Multiple models:</strong> tiny, base, small, medium</li>
                    <li><strong>WebSocket live demo</strong> for real-time testing</li>
                    <li><strong>100% local processing</strong> - no cloud required</li>
                </ul>
            </div>
            
            <h3>🎯 Try It Now</h3>
            <a href="/api/status" class="button">📊 System Status</a>
            <a href="/api/test-websocket" class="button">🧪 Live Demo</a>
            <a href="/docs" class="button">📚 API Documentation</a>
            
            <div class="feature">
                <h3>🔧 Current Configuration</h3>
                <p><strong>Active Model:</strong> {model}</p>
                <p><strong>Device:</strong> CPU (INT8 optimized)</p>
                <p><strong>Connected Clients:</strong> {len(connected_clients)}</p>
            </div>
            
            <div class="feature">
                <h3>🎙️ Quick API Test</h3>
                <p>Test the transcription pipeline:</p>
                <div class="code">curl -X POST "http://localhost:5000/api/transcribe-test"</div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/api/status")
async def get_status():
    """Get system status"""
    import platform
    import psutil
    
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0-whisper",
        "status": "ready" if system_ready else "starting",
        "whisper": {
            "current_model": current_model_name,
            "available_models": ["tiny", "base", "small", "medium"],
            "model_loaded": whisper_model is not None
        },
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "cpu_cores": psutil.cpu_count()
        },
        "websocket": {
            "connected_clients": len(connected_clients)
        }
    }

@app.post("/api/transcribe-test")
async def transcribe_test():
    """Quick transcription test with generated audio"""
    try:
        # Generate 2 seconds of test audio
        test_audio = generate_test_audio(duration=2.0)
        
        # Transcribe it
        result = await transcribe_audio(test_audio)
        
        return {
            "success": True,
            "test_audio_duration": 2.0,
            "result": result,
            "note": "Empty text is expected for sine wave - this validates the pipeline works!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.websocket("/ws/live-transcription")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live transcription demo"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Send welcome message
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": f"WhisperS2T ready! Model: {current_model_name}",
        "timestamp": datetime.now().isoformat(),
        "current_model": current_model_name
    }))
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "demo_transcription":
                # Demo transcription
                await websocket.send_text(json.dumps({
                    "type": "processing",
                    "message": "Generating test audio and transcribing...",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Generate and transcribe test audio
                test_audio = generate_test_audio(duration=3.0)
                result = await transcribe_audio(test_audio)
                
                # Send result
                await websocket.send_text(json.dumps({
                    "type": "transcription_result",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message.get("action") == "change_model":
                # Change Whisper model
                model_name = message.get("model", "tiny")
                
                try:
                    await websocket.send_text(json.dumps({
                        "type": "model_loading",
                        "model": model_name,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Load new model
                    result = await load_whisper_model(model_name)
                    
                    await websocket.send_text(json.dumps({
                        "type": "model_loaded",
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Failed to load model: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            elif message.get("action") == "ping":
                # Simple ping/pong
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "server_time": datetime.now().isoformat(),
                    "model": current_model_name
                }))
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("🔌 Client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/api/test-websocket")
async def websocket_test_page():
    """WebSocket test interface"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Live Demo</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            button { padding: 12px 24px; margin: 8px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background-color 0.2s; }
            .btn-primary { background: #007bff; color: white; }
            .btn-primary:hover { background: #0056b3; }
            .btn-success { background: #28a745; color: white; }
            .btn-success:hover { background: #1e7e34; }
            .btn-danger { background: #dc3545; color: white; }
            .btn-danger:hover { background: #c82333; }
            .btn-warning { background: #ffc107; color: #212529; }
            .btn-warning:hover { background: #e0a800; }
            #messages { 
                border: 1px solid #ddd; 
                height: 400px; 
                overflow-y: scroll; 
                padding: 15px; 
                background: #f8f9fa; 
                border-radius: 5px; 
                font-family: 'Consolas', 'Monaco', monospace; 
                font-size: 14px;
                margin: 20px 0;
            }
            .status { 
                padding: 12px; 
                border-radius: 5px; 
                margin: 15px 0; 
                font-weight: bold; 
                text-align: center;
            }
            .connected { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .disconnected { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            select { 
                padding: 8px; 
                margin: 8px; 
                border-radius: 4px; 
                border: 1px solid #ddd;
                font-size: 14px;
            }
            .controls { 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 5px; 
                margin: 20px 0;
            }
            .model-section {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 WhisperS2T Live Demo</h2>
            <p>Real-time speech-to-text demonstration with WebSocket connection</p>
            
            <div id="status" class="status disconnected">
                ❌ Disconnected - Click Connect to start
            </div>
            
            <div class="controls">
                <h4>Connection Controls</h4>
                <button onclick="connect()" class="btn-primary">🔌 Connect</button>
                <button onclick="disconnect()" class="btn-danger">❌ Disconnect</button>
                <button onclick="ping()" class="btn-warning">📡 Ping Server</button>
                
                <div class="model-section">
                    <h4>Demo & Model Controls</h4>
                    <button onclick="demoTranscription()" class="btn-success">🎙️ Run Demo Transcription</button>
                    
                    <br><br>
                    <label><strong>Select Whisper Model:</strong></label>
                    <select id="modelSelect">
                        <option value="tiny">Tiny (Fastest, ~60MB)</option>
                        <option value="base">Base (Good balance, ~140MB)</option>
                        <option value="small">Small (Better quality, ~460MB)</option>
                        <option value="medium">Medium (Best quality, ~1.5GB)</option>
                    </select>
                    <button onclick="changeModel()" class="btn-primary">🔄 Change Model</button>
                </div>
            </div>
            
            <h4>Live Messages</h4>
            <div id="messages"></div>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    addMessage('⚠️ Already connected!', 'warning');
                    return;
                }
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/live-transcription`;
                
                addMessage('🔄 Connecting to WhisperS2T...', 'info');
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    addMessage('🟢 Connected to WhisperS2T!', 'success');
                    updateStatus(true);
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    addMessage('🔴 Connection closed', 'error');
                    updateStatus(false);
                };
                
                ws.onerror = function(error) {
                    addMessage('❌ WebSocket error occurred', 'error');
                    updateStatus(false);
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    addMessage('👋 Disconnecting...', 'info');
                } else {
                    addMessage('⚠️ Not connected!', 'warning');
                }
            }
            
            function demoTranscription() {
                if (!checkConnection()) return;
                
                addMessage('🎙️ Starting demo transcription...', 'info');
                ws.send(JSON.stringify({action: 'demo_transcription'}));
            }
            
            function changeModel() {
                if (!checkConnection()) return;
                
                const model = document.getElementById('modelSelect').value;
                addMessage(`🔄 Requesting model change to: ${model}`, 'info');
                ws.send(JSON.stringify({action: 'change_model', model: model}));
            }
            
            function ping() {
                if (!checkConnection()) return;
                
                addMessage('📡 Sending ping...', 'info');
                ws.send(JSON.stringify({action: 'ping'}));
            }
            
            function checkConnection() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('❌ Not connected! Click "Connect" first.', 'error');
                    return false;
                }
                return true;
            }
            
            function handleMessage(data) {
                switch(data.type) {
                    case 'connected':
                        addMessage('✅ ' + data.message, 'success');
                        break;
                        
                    case 'transcription_result':
                        addMessage('🎯 ===== TRANSCRIPTION RESULT =====', 'result');
                        addMessage(`📝 Text: "${data.result.text}"`, 'result');
                        addMessage(`🌍 Language: ${data.result.language}`, 'result');
                        addMessage(`⏱️ Processing Time: ${data.result.processing_time}s`, 'result');
                        addMessage(`🤖 Model: ${data.result.model}`, 'result');
                        addMessage('==================================', 'result');
                        break;
                        
                    case 'processing':
                        addMessage('🔄 ' + data.message, 'info');
                        break;
                        
                    case 'model_loading':
                        addMessage('📦 Loading model: ' + data.model + '...', 'warning');
                        addMessage('⏳ This may take a few seconds...', 'warning');
                        break;
                        
                    case 'model_loaded':
                        addMessage(`✅ Model loaded successfully!`, 'success');
                        addMessage(`🤖 Active model: ${data.result.model}`, 'success');
                        addMessage(`⏱️ Load time: ${data.result.load_time}s`, 'success');
                        break;
                        
                    case 'pong':
                        addMessage('🏓 Pong received - Server is responsive!', 'success');
                        addMessage(`🕐 Server time: ${data.server_time}`, 'info');
                        break;
                        
                    case 'error':
                        addMessage('❌ Error: ' + data.message, 'error');
                        break;
                        
                    default:
                        addMessage('📨 Raw message: ' + JSON.stringify(data), 'raw');
                }
            }
            
            function addMessage(message, type = 'info') {
                const messages = document.getElementById('messages');
                const timestamp = new Date().toLocaleTimeString();
                
                const colors = {
                    'success': '#28a745',
                    'error': '#dc3545',
                    'warning': '#fd7e14',
                    'info': '#17a2b8',
                    'result': '#6f42c1',
                    'raw': '#6c757d'
                };
                
                const color = colors[type] || '#333';
                
                const div = document.createElement('div');
                div.style.cssText = `
                    color: ${color}; 
                    margin: 4px 0; 
                    padding: 2px 0;
                    border-left: 3px solid ${color};
                    padding-left: 8px;
                `;
                div.innerHTML = `[${timestamp}] ${message}`;
                
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function updateStatus(connected) {
                const status = document.getElementById('status');
                if (connected) {
                    status.className = 'status connected';
                    status.innerHTML = '✅ Connected - WhisperS2T Ready for Action!';
                } else {
                    status.className = 'status disconnected';
                    status.innerHTML = '❌ Disconnected - Click Connect to start';
                }
            }
            
            // Initialize on page load
            window.onload = function() {
                addMessage('🚀 WhisperS2T Live Demo Interface Ready!', 'info');
                addMessage('💡 Click "Connect" to establish WebSocket connection', 'info');
                addMessage('🎙️ Then try "Run Demo Transcription" to test the system', 'info');
                addMessage('🔧 You can also change models and test different sizes', 'info');
                addMessage('───────────────────────────────────────────', 'raw');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Appliance...")
    print("🌐 Main Interface: http://localhost:5000")
    print("🧪 Live Demo: http://localhost:5000/api/test-websocket")
    print("📊 API Status: http://localhost:5000/api/status")
    print("📚 API Docs: http://localhost:5000/docs")
    print()
    print("⚡ Loading Whisper tiny model on startup...")
    print("🔄 This may take 10-15 seconds...")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
