#!/usr/bin/env python3
"""
WhisperS2T Appliance - Live Audio Server (Fixed CORS + Clean)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
import numpy as np
import time
import queue
from typing import Dict, Optional
from collections import deque
from faster_whisper import WhisperModel

app = FastAPI(title="WhisperS2T Live Audio", version="0.3.1-cors")

# Add CORS middleware for WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AudioInputManager:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=10)
        self.input_devices = []
        self.current_device = None
        self.hardware_available = False
        self._detect_audio_devices()
    
    def _detect_audio_devices(self):
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            self.input_devices = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    self.input_devices.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'type': 'hardware'
                    })
            
            if self.input_devices:
                self.current_device = self.input_devices[0]
                self.hardware_available = True
                print(f"🎤 Found {len(self.input_devices)} hardware audio devices")
            else:
                self._setup_fallback_devices()
        except (ImportError, OSError) as e:
            print(f"⚠️ Hardware audio not available: {e}")
            self._setup_fallback_devices()
    
    def _setup_fallback_devices(self):
        self.input_devices = [{
            'index': 0,
            'name': 'Simulated Microphone (Test Mode)',
            'channels': 1,
            'sample_rate': 16000,
            'type': 'simulated'
        }]
        self.current_device = self.input_devices[0]
        self.hardware_available = False
        print("🔄 Using simulated audio devices")
    
    def get_device_status(self) -> Dict:
        return {
            "devices_available": len(self.input_devices),
            "input_devices": self.input_devices,
            "current_device": self.current_device,
            "is_recording": self.is_recording,
            "hardware_available": self.hardware_available,
            "sample_rate": self.sample_rate
        }
    
    def _generate_test_audio(self) -> np.ndarray:
        samples = self.sample_rate
        t = np.linspace(0, 1, samples)
        audio = (
            0.3 * np.sin(2 * np.pi * 220 * t) +
            0.2 * np.sin(2 * np.pi * 440 * t) +
            0.05 * np.random.normal(0, 1, samples)
        )
        envelope = np.exp(-t * 0.5)
        audio *= envelope
        return (audio / np.max(np.abs(audio)) * 0.3).astype(np.float32)
    
    def start_recording(self) -> bool:
        if self.is_recording:
            return True
        
        self.is_recording = True
        
        if self.hardware_available:
            try:
                import sounddevice as sd
                
                def audio_callback(indata, frames, time, status):
                    audio_data = np.mean(indata, axis=1) if indata.shape[1] > 1 else indata[:, 0]
                    self.audio_buffer.append(audio_data.copy())
                    try:
                        self.audio_queue.put_nowait(audio_data.copy())
                    except queue.Full:
                        pass
                
                self.audio_stream = sd.InputStream(
                    device=self.current_device['index'],
                    channels=1,
                    samplerate=self.sample_rate,
                    callback=audio_callback,
                    dtype=np.float32
                )
                self.audio_stream.start()
                print(f"🎤 Started hardware recording")
                return True
            except Exception as e:
                print(f"❌ Hardware recording failed: {e}")
        
        # Fallback to simulated
        import threading
        
        def generate_audio():
            while self.is_recording:
                audio_chunk = self._generate_test_audio()
                self.audio_buffer.append(audio_chunk)
                try:
                    self.audio_queue.put_nowait(audio_chunk)
                except queue.Full:
                    pass
                time.sleep(1.0)
        
        self.audio_thread = threading.Thread(target=generate_audio, daemon=True)
        self.audio_thread.start()
        print("🎤 Started simulated recording")
        return True
    
    def stop_recording(self) -> bool:
        self.is_recording = False
        
        if self.hardware_available and hasattr(self, 'audio_stream'):
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except:
                pass
        
        print("🛑 Stopped recording")
        return True
    
    async def get_audio_chunk_async(self, timeout: float = 1.0):
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self.audio_queue.get(timeout=timeout))
        except queue.Empty:
            return None
    
    def get_audio_level(self) -> float:
        if not self.audio_buffer:
            return 0.0
        latest_chunk = self.audio_buffer[-1]
        rms = np.sqrt(np.mean(latest_chunk ** 2))
        return min(rms / 0.1, 1.0)
    
    def get_recent_audio(self, duration: float = 5.0) -> np.ndarray:
        if not self.audio_buffer:
            return np.array([], dtype=np.float32)
        
        chunks_needed = min(int(duration), len(self.audio_buffer))
        if chunks_needed == 0:
            return np.array([], dtype=np.float32)
        
        recent_chunks = list(self.audio_buffer)[-chunks_needed:]
        return np.concatenate(recent_chunks)

# Global state
whisper_model = None
current_model_name = None
connected_clients = []
system_ready = False
audio_manager = AudioInputManager()

async def load_whisper_model(model_name="tiny"):
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
    global system_ready
    
    print("🚀 Starting WhisperS2T Live Audio...")
    try:
        await load_whisper_model("tiny")
        
        audio_status = audio_manager.get_device_status()
        print(f"🎤 Audio devices: {audio_status['devices_available']}")
        print(f"🔧 Hardware available: {audio_status['hardware_available']}")
        
        system_ready = True
        print("✅ WhisperS2T Live Audio ready!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        system_ready = False

@app.get("/")
async def root():
    status = "✅ Ready" if system_ready else "🔄 Starting..."
    audio_status = audio_manager.get_device_status()
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head><title>WhisperS2T Live Audio (Fixed)</title></head>
    <body style="font-family: Arial; margin: 40px; background: #f5f5f5;">
        <div style="max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
            <h1>🎤 WhisperS2T Live Audio (CORS Fixed)</h1>
            <div style="padding: 15px; background: #d4edda; color: #155724; border-radius: 5px; margin: 20px 0;">
                {status}
            </div>
            <p><strong>Audio Device:</strong> {audio_status['current_device']['name'] if audio_status['current_device'] else 'None'}</p>
            <p><strong>Hardware Available:</strong> {'✅ Yes' if audio_status['hardware_available'] else '🔄 Simulated'}</p>
            <a href="/demo" style="display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px;">🎙️ Live Demo</a>
            <a href="/api/status" style="display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 10px;">📊 Status</a>
        </div>
    </body>
    </html>
    """)

@app.get("/api/status")
async def get_status():
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.3.1-clean",
        "status": "ready" if system_ready else "starting",
        "whisper": {
            "current_model": current_model_name,
            "model_loaded": whisper_model is not None
        },
        "audio": audio_manager.get_device_status(),
        "websocket": {
            "connected_clients": len(connected_clients)
        }
    }

@app.websocket("/ws/live-audio")
async def websocket_live_audio(websocket: WebSocket):
    print("🔌 New WebSocket connection...")
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"✅ WebSocket connected! Total: {len(connected_clients)}")
    
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "Live Audio ready!",
        "timestamp": datetime.now().isoformat(),
        "current_model": current_model_name
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"📨 Received: {message.get('action', 'unknown')}")
            
            if message.get("action") == "start_recording":
                if audio_manager.start_recording():
                    await websocket.send_text(json.dumps({
                        "type": "recording_started",
                        "message": "🎤 Recording started!",
                        "timestamp": datetime.now().isoformat()
                    }))
                    asyncio.create_task(live_transcription_loop(websocket))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to start recording",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            elif message.get("action") == "stop_recording":
                audio_manager.stop_recording()
                await websocket.send_text(json.dumps({
                    "type": "recording_stopped",
                    "message": "🛑 Recording stopped",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message.get("action") == "transcribe_recent":
                duration = message.get("duration", 5.0)
                recent_audio = audio_manager.get_recent_audio(duration)
                
                if len(recent_audio) > 0:
                    await websocket.send_text(json.dumps({
                        "type": "processing",
                        "message": f"Transcribing {duration}s of audio...",
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
                        "message": "No audio available",
                        "timestamp": datetime.now().isoformat()
                    }))
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        audio_manager.stop_recording()
        print(f"🔌 WebSocket disconnected. Remaining: {len(connected_clients)}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def live_transcription_loop(websocket: WebSocket):
    try:
        print("🎤 Starting live transcription...")
        while audio_manager.is_recording and websocket in connected_clients:
            audio_chunk = await audio_manager.get_audio_chunk_async(timeout=2.0)
            
            if audio_chunk is not None:
                level = np.sqrt(np.mean(audio_chunk ** 2))
                await websocket.send_text(json.dumps({
                    "type": "audio_level",
                    "level": min(level / 0.1, 1.0),
                    "timestamp": datetime.now().isoformat()
                }))
                
                if level > 0.01:
                    recent_audio = audio_manager.get_recent_audio(duration=3.0)
                    
                    if len(recent_audio) > 16000:
                        result = await transcribe_audio(recent_audio)
                        
                        if result["text"].strip():
                            await websocket.send_text(json.dumps({
                                "type": "live_transcription",
                                "result": result,
                                "timestamp": datetime.now().isoformat()
                            }))
            
            await asyncio.sleep(0.5)
        
        print("🛑 Live transcription loop ended")
    except Exception as e:
        print(f"❌ Live transcription error: {e}")

@app.get("/demo")
async def demo():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Live Demo (Fixed)</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f8f9fa; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
            button { padding: 12px 24px; margin: 8px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-record { background: #dc3545; color: white; font-size: 18px; padding: 15px 30px; }
            .btn-record.recording { background: #28a745; animation: pulse 1s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
            .status { padding: 12px; border-radius: 5px; margin: 15px 0; font-weight: bold; text-align: center; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .recording { background: #fff3cd; color: #856404; }
            .controls { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; }
            .transcription { background: #f0fff0; border: 1px solid #90ee90; border-radius: 5px; padding: 15px; margin: 10px 0; }
            .audio-level { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; margin: 10px 0; overflow: hidden; }
            .audio-level-bar { height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); border-radius: 10px; transition: width 0.1s ease; width: 0%; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 WhisperS2T Live Demo (CORS Fixed)</h2>
            
            <div id="status" class="status disconnected">❌ Disconnected</div>
            
            <div class="controls">
                <h4>🔌 Connection</h4>
                <button onclick="connect()" class="btn-primary">🔌 Connect WebSocket</button>
                <br><br>
                
                <button id="recordBtn" onclick="toggleRecording()" class="btn-record">🎙️ START RECORDING</button>
                <br><br>
                
                <button onclick="transcribeRecent()" class="btn-success">📝 Transcribe Last 5s</button>
                
                <h4>🎛️ Audio Level</h4>
                <div class="audio-level">
                    <div id="audioLevelBar" class="audio-level-bar"></div>
                </div>
                <span id="audioLevelText">Level: 0%</span>
            </div>
            
            <div id="results" style="min-height: 200px; margin: 20px 0;">
                <h4>📝 Results</h4>
                <div id="liveResults">Results will appear here...</div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRecording = false;
            
            function connect() {
                const wsUrl = `ws://${window.location.host}/ws/live-audio`;
                console.log('Connecting to:', wsUrl);
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() { 
                    updateStatus('connected'); 
                    addMessage('✅ Connected successfully!');
                };
                
                ws.onmessage = function(event) { 
                    const data = JSON.parse(event.data);
                    handleMessage(data); 
                };
                
                ws.onclose = function() { 
                    updateStatus('disconnected'); 
                    isRecording = false; 
                    updateRecordButton(); 
                    addMessage('❌ Connection closed');
                };
                
                ws.onerror = function(error) { 
                    console.error('WebSocket error:', error); 
                    updateStatus('disconnected'); 
                    addMessage('❌ Connection error');
                };
            }
            
            function toggleRecording() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected!');
                    return;
                }
                
                if (!isRecording) {
                    ws.send(JSON.stringify({action: 'start_recording'}));
                } else {
                    ws.send(JSON.stringify({action: 'stop_recording'}));
                }
            }
            
            function transcribeRecent() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected!');
                    return;
                }
                ws.send(JSON.stringify({action: 'transcribe_recent', duration: 5.0}));
            }
            
            function handleMessage(data) {
                console.log('Received:', data.type);
                
                switch(data.type) {
                    case 'connected':
                        addMessage('✅ ' + data.message);
                        break;
                    case 'recording_started':
                        isRecording = true;
                        updateRecordButton();
                        updateStatus('recording');
                        addMessage('🎤 Recording started!');
                        break;
                    case 'recording_stopped':
                        isRecording = false;
                        updateRecordButton();
                        updateStatus('connected');
                        addMessage('🛑 Recording stopped');
                        break;
                    case 'live_transcription':
                        displayTranscription(data.result, 'LIVE');
                        break;
                    case 'transcription_result':
                        displayTranscription(data.result, data.source);
                        break;
                    case 'audio_level':
                        updateAudioLevel(data.level);
                        break;
                    case 'processing':
                        addMessage('🔄 ' + data.message);
                        break;
                    case 'error':
                        addMessage('❌ ' + data.message);
                        break;
                }
            }
            
            function displayTranscription(result, source) {
                const div = document.createElement('div');
                div.className = 'transcription';
                div.innerHTML = `
                    <h5>📝 ${source}: ${new Date().toLocaleTimeString()}</h5>
                    <p><strong>"${result.text}"</strong></p>
                    <small>Language: ${result.language} | Processing: ${result.processing_time}s</small>
                `;
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView();
            }
            
            function addMessage(message) {
                const div = document.createElement('div');
                div.style.cssText = 'padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 3px; font-size: 14px;';
                div.innerHTML = `<small>${new Date().toLocaleTimeString()}: ${message}</small>`;
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView();
            }
            
            function updateAudioLevel(level) {
                const percentage = Math.round(level * 100);
                document.getElementById('audioLevelBar').style.width = percentage + '%';
                document.getElementById('audioLevelText').textContent = `Level: ${percentage}%`;
            }
            
            function updateRecordButton() {
                const btn = document.getElementById('recordBtn');
                if (isRecording) {
                    btn.innerHTML = '⏹️ STOP RECORDING';
                    btn.className = 'btn-record recording';
                } else {
                    btn.innerHTML = '🎙️ START RECORDING';
                    btn.className = 'btn-record';
                }
            }
            
            function updateStatus(status) {
                const statusDiv = document.getElementById('status');
                switch(status) {
                    case 'connected':
                        statusDiv.className = 'status connected';
                        statusDiv.innerHTML = '✅ Connected - Ready!';
                        break;
                    case 'recording':
                        statusDiv.className = 'status recording';
                        statusDiv.innerHTML = '🔴 RECORDING';
                        break;
                    case 'disconnected':
                        statusDiv.className = 'status disconnected';
                        statusDiv.innerHTML = '❌ Disconnected';
                        break;
                }
            }
            
            window.onload = function() {
                addMessage('Demo loaded - click Connect to start');
            };
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Live Audio Server (Clean + CORS Fixed)...")
    print("🌐 Main Interface: http://localhost:5000")
    print("🎙️ Live Demo: http://localhost:5000/demo")
    print("📊 Status: http://localhost:5000/api/status")
    print()
    print("🔧 FIXES:")
    print("   ✅ CORS middleware enabled")
    print("   ✅ Clean code without syntax errors") 
    print("   ✅ Simplified demo interface")
    print("   ✅ Detailed WebSocket logging")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
