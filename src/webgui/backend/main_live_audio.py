#!/usr/bin/env python3
"""
WhisperS2T Appliance - FastAPI Backend mit LIVE AUDIO INPUT
Real microphone-to-text transcription
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import asyncio
import json
from datetime import datetime
import numpy as np
import time
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

# Import faster-whisper and our audio manager
from faster_whisper import WhisperModel
import logging

# Import our audio input manager
sys.path.append(os.path.join(parent_dir, 'src'))
from whisper_service.audio_input_manager import AudioInputManager

app = FastAPI(title="WhisperS2T Appliance", version="0.3.0-live-audio")

# Global state with audio input
whisper_model = None
current_model_name = None
connected_clients = []
system_ready = False
audio_manager = AudioInputManager()

async def load_whisper_model(model_name="tiny"):
    """Load Whisper model asynchronously"""
    global whisper_model, current_model_name
    
    print(f"🔄 Loading {model_name} model...")
    start_time = time.time()
    
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
    
    loop = asyncio.get_event_loop()
    segments, info = await loop.run_in_executor(
        None,
        lambda: whisper_model.transcribe(audio_data, beam_size=1)
    )
    
    full_text = " ".join(segment.text for segment in segments)
    processing_time = time.time() - start_time
    
    return {
        "text": full_text.strip(),
        "language": info.language,
        "processing_time": round(processing_time, 2),
        "model": current_model_name,
        "audio_length": len(audio_data) / 16000
    }

@app.on_event("startup")
async def startup_event():
    """Initialize Whisper and Audio on startup"""
    global system_ready
    
    print("🚀 Starting WhisperS2T Appliance with LIVE AUDIO...")
    try:
        await load_whisper_model("tiny")
        
        # Test audio system
        audio_status = audio_manager.get_device_status()
        print(f"🎤 Audio devices: {audio_status['devices_available']}")
        print(f"🔧 Hardware available: {audio_status['hardware_available']}")
        
        system_ready = True
        print("✅ WhisperS2T Appliance with Live Audio ready!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        system_ready = False

@app.get("/")
async def root():
    """Main landing page with audio features"""
    status = "✅ Ready for live transcription!" if system_ready else "🔄 Starting up..."
    model = current_model_name or "Loading..."
    audio_status = audio_manager.get_device_status()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Appliance - Live Audio</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ padding: 15px; background: #d4edda; color: #155724; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
            .audio-status {{ padding: 15px; background: #e2e3e5; color: #383d41; border-radius: 5px; margin: 20px 0; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; font-weight: bold; }}
            .button:hover {{ background: #0056b3; }}
            .feature {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #007bff; }}
            .highlight {{ background: #fff3cd; padding: 15px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 WhisperS2T Appliance</h1>
            <p><strong>Self-contained Speech-to-Text System with Live Audio Input</strong></p>
            
            <div class="status">{status}</div>
            
            <div class="audio-status">
                <h4>🎙️ Audio System Status</h4>
                <p><strong>Devices Available:</strong> {audio_status['devices_available']}</p>
                <p><strong>Hardware Audio:</strong> {'✅ Available' if audio_status['hardware_available'] else '🔄 Simulated Mode'}</p>
                <p><strong>Current Device:</strong> {audio_status['current_device']['name'] if audio_status['current_device'] else 'None'}</p>
            </div>
            
            <div class="highlight">
                <h3>🔥 NEW: Live Audio Transcription!</h3>
                <p>Real-time microphone input → Whisper transcription</p>
                <p><strong>Features:</strong> Automatic device detection, live audio processing, real-time results</p>
            </div>
            
            <h3>🎯 Try Live Audio</h3>
            <a href="/api/live-demo" class="button">🎙️ Live Audio Demo</a>
            <a href="/api/status" class="button">📊 System Status</a>
            <a href="/docs" class="button">📚 API Documentation</a>
            
            <div class="feature">
                <h3>🔧 Current Configuration</h3>
                <p><strong>Whisper Model:</strong> {model}</p>
                <p><strong>Audio Device:</strong> {audio_status['current_device']['name'] if audio_status['current_device'] else 'None'}</p>
                <p><strong>Sample Rate:</strong> {audio_status['sample_rate']} Hz</p>
                <p><strong>Connected Clients:</strong> {len(connected_clients)}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/api/status")
async def get_status():
    """Get comprehensive system status including audio"""
    import platform
    import psutil
    
    audio_status = audio_manager.get_device_status()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.3.0-live-audio",
        "status": "ready" if system_ready else "starting",
        "whisper": {
            "current_model": current_model_name,
            "available_models": ["tiny", "base", "small", "medium"],
            "model_loaded": whisper_model is not None
        },
        "audio": audio_status,
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

@app.websocket("/ws/live-audio")
async def websocket_live_audio(websocket: WebSocket):
    """WebSocket for LIVE AUDIO transcription"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Send welcome message
    audio_status = audio_manager.get_device_status()
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": f"Live Audio ready! Device: {audio_status['current_device']['name']}",
        "timestamp": datetime.now().isoformat(),
        "current_model": current_model_name,
        "audio_status": audio_status
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "start_live_recording":
                # Start live audio recording
                if audio_manager.start_recording():
                    await websocket.send_text(json.dumps({
                        "type": "recording_started",
                        "message": "Live recording started - speak now!",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Start live transcription loop
                    asyncio.create_task(live_transcription_loop(websocket))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to start audio recording",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            elif message.get("action") == "stop_live_recording":
                # Stop live audio recording
                audio_manager.stop_recording()
                await websocket.send_text(json.dumps({
                    "type": "recording_stopped",
                    "message": "Live recording stopped",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message.get("action") == "transcribe_recent":
                # Transcribe recent audio buffer
                duration = message.get("duration", 5.0)
                recent_audio = audio_manager.get_recent_audio(duration)
                
                if len(recent_audio) > 0:
                    await websocket.send_text(json.dumps({
                        "type": "processing",
                        "message": f"Transcribing {duration}s of recent audio...",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    result = await transcribe_audio(recent_audio)
                    
                    await websocket.send_text(json.dumps({
                        "type": "transcription_result",
                        "result": result,
                        "source": "recent_audio",
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No recent audio available",
                        "timestamp": datetime.now().isoformat()
                    }))
                
            elif message.get("action") == "get_audio_level":
                # Get current audio input level
                level = audio_manager.get_audio_level()
                await websocket.send_text(json.dumps({
                    "type": "audio_level",
                    "level": level,
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        audio_manager.stop_recording()  # Stop recording if client disconnects
        print("🔌 Live audio client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def live_transcription_loop(websocket: WebSocket):
    """Background loop for continuous live transcription"""
    try:
        while audio_manager.is_recording and websocket in connected_clients:
            # Get audio chunk with timeout
            audio_chunk = await audio_manager.get_audio_chunk_async(timeout=2.0)
            
            if audio_chunk is not None and len(audio_chunk) > 0:
                # Send audio level update
                level = np.sqrt(np.mean(audio_chunk ** 2))
                await websocket.send_text(json.dumps({
                    "type": "audio_level",
                    "level": min(level / 0.1, 1.0),
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Check if there's enough audio energy to transcribe
                if level > 0.01:  # Threshold for speech detection
                    # Get recent audio for context
                    recent_audio = audio_manager.get_recent_audio(duration=3.0)
                    
                    if len(recent_audio) > 16000:  # At least 1 second
                        result = await transcribe_audio(recent_audio)
                        
                        # Only send if we got actual text
                        if result["text"].strip():
                            await websocket.send_text(json.dumps({
                                "type": "live_transcription",
                                "result": result,
                                "timestamp": datetime.now().isoformat()
                            }))
            
            await asyncio.sleep(0.5)  # Check every 500ms
            
    except Exception as e:
        print(f"Live transcription loop error: {e}")

@app.get("/api/live-demo")
async def live_demo_page():
    """Live audio demo interface"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T - LIVE AUDIO Demo</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            button { padding: 12px 24px; margin: 8px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .btn-record { background: #dc3545; color: white; font-size: 18px; padding: 15px 30px; }
            .btn-record.recording { background: #28a745; animation: pulse 1s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
            
            .status { 
                padding: 12px; 
                border-radius: 5px; 
                margin: 15px 0; 
                font-weight: bold; 
                text-align: center;
            }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .recording { background: #fff3cd; color: #856404; }
            
            .controls { 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 5px; 
                margin: 20px 0;
                text-align: center;
            }
            
            .live-transcription {
                background: #f0fff0;
                border: 1px solid #90ee90;
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #28a745;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 WhisperS2T - LIVE AUDIO Transcription Demo</h2>
            <p>Real-time microphone → Whisper transcription</p>
            
            <div id="status" class="status disconnected">
                ❌ Disconnected - Click Connect to start
            </div>
            
            <div class="controls">
                <h4>Connection & Recording</h4>
                <button onclick="connect()" class="btn-primary">🔌 Connect to Audio System</button>
                <br><br>
                
                <button id="recordBtn" onclick="toggleRecording()" class="btn-record">
                    🎙️ START LIVE RECORDING
                </button>
                <br><br>
                
                <button onclick="transcribeRecent()" class="btn-success">📝 Transcribe Last 5 Seconds</button>
            </div>
            
            <div id="transcription-display" style="min-height: 100px; margin: 20px 0;">
                <h4>📝 Live Transcription Results</h4>
                <div id="liveResults">Transcription results will appear here...</div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRecording = false;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/live-audio`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    updateStatus('connected');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    updateStatus('disconnected');
                    isRecording = false;
                    updateRecordButton();
                };
            }
            
            function toggleRecording() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected! Click Connect first.');
                    return;
                }
                
                if (!isRecording) {
                    ws.send(JSON.stringify({action: 'start_live_recording'}));
                } else {
                    ws.send(JSON.stringify({action: 'stop_live_recording'}));
                }
            }
            
            function transcribeRecent() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected!');
                    return;
                }
                
                ws.send(JSON.stringify({
                    action: 'transcribe_recent',
                    duration: 5.0
                }));
            }
            
            function handleMessage(data) {
                switch(data.type) {
                    case 'connected':
                        console.log('Connected:', data.message);
                        break;
                        
                    case 'recording_started':
                        isRecording = true;
                        updateRecordButton();
                        updateStatus('recording');
                        break;
                        
                    case 'recording_stopped':
                        isRecording = false;
                        updateRecordButton();
                        updateStatus('connected');
                        break;
                        
                    case 'live_transcription':
                        displayLiveTranscription(data.result);
                        break;
                        
                    case 'transcription_result':
                        displayTranscriptionResult(data.result, data.source);
                        break;
                }
            }
            
            function displayLiveTranscription(result) {
                const liveResults = document.getElementById('liveResults');
                const div = document.createElement('div');
                div.className = 'live-transcription';
                div.innerHTML = `
                    <h5>🔴 LIVE: ${new Date().toLocaleTimeString()}</h5>
                    <p><strong>"${result.text}"</strong></p>
                    <small>Language: ${result.language} | Processing: ${result.processing_time}s</small>
                `;
                liveResults.appendChild(div);
                liveResults.scrollTop = liveResults.scrollHeight;
            }
            
            function displayTranscriptionResult(result, source) {
                const liveResults = document.getElementById('liveResults');
                const div = document.createElement('div');
                div.className = 'live-transcription';
                div.innerHTML = `
                    <h5>📝 ${source}: ${new Date().toLocaleTimeString()}</h5>
                    <p><strong>"${result.text}"</strong></p>
                    <small>Language: ${result.language} | Processing: ${result.processing_time}s</small>
                `;
                liveResults.appendChild(div);
                liveResults.scrollTop = liveResults.scrollHeight;
            }
            
            function updateRecordButton() {
                const btn = document.getElementById('recordBtn');
                if (isRecording) {
                    btn.innerHTML = '⏹️ STOP RECORDING';
                    btn.className = 'btn-record recording';
                } else {
                    btn.innerHTML = '🎙️ START LIVE RECORDING';
                    btn.className = 'btn-record';
                }
            }
            
            function updateStatus(status) {
                const statusDiv = document.getElementById('status');
                switch(status) {
                    case 'connected':
                        statusDiv.className = 'status connected';
                        statusDiv.innerHTML = '✅ Connected - Ready for Live Audio';
                        break;
                    case 'recording':
                        statusDiv.className = 'status recording';
                        statusDiv.innerHTML = '🔴 RECORDING - Speak now!';
                        break;
                    case 'disconnected':
                        statusDiv.className = 'status disconnected';
                        statusDiv.innerHTML = '❌ Disconnected';
                        break;
                }
            }
            
            window.onload = function() {
                console.log('WhisperS2T Live Audio Demo Ready!');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Appliance with LIVE AUDIO INPUT...")
    print("🌐 Main Interface: http://localhost:5000")
    print("🎙️ Live Audio Demo: http://localhost:5000/api/live-demo")
    print("📊 API Status: http://localhost:5000/api/status")
    print()
    print("🎤 LIVE FEATURES:")
    print("   - Real microphone input (or simulated if no hardware)")
    print("   - Live audio level monitoring")
    print("   - Real-time transcription")
    print("   - WebSocket live communication")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
