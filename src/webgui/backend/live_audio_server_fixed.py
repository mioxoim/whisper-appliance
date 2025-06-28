#!/usr/bin/env python3
"""
WhisperS2T Appliance - Live Audio Server (Standalone)
Complete implementation with integrated AudioInputManager + CORS Support
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
from typing import Dict, Optional, Callable
from collections import deque

# Import faster-whisper
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

# ============================================================================
# INTEGRATED AUDIO INPUT MANAGER
# ============================================================================

class AudioInputManager:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_duration: float = 1.0):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
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
                    device_info = {
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'type': 'hardware'
                    }
                    self.input_devices.append(device_info)
            
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
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_duration": self.chunk_duration
        }
    
    def has_microphone(self) -> bool:
        return len(self.input_devices) > 0
    
    def _generate_test_audio(self, duration: float = 1.0) -> np.ndarray:
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Generate speech-like audio
        audio = (
            0.3 * np.sin(2 * np.pi * 220 * t) +
            0.2 * np.sin(2 * np.pi * 440 * t) +
            0.1 * np.sin(2 * np.pi * 880 * t) +
            0.05 * np.random.normal(0, 1, samples)
        )
        
        envelope = np.exp(-t * 0.5) * (1 + 0.5 * np.sin(2 * np.pi * 3 * t))
        audio *= envelope
        audio = audio / np.max(np.abs(audio)) * 0.3
        
        return audio.astype(np.float32)
    
    def start_recording(self) -> bool:
        if self.is_recording:
            print("⚠️ Already recording")
            return True
        
        if not self.has_microphone():
            print("❌ No audio input available")
            return False
        
        try:
            if self.hardware_available:
                return self._start_hardware_recording()
            else:
                return self._start_simulated_recording()
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            return False
    
    def _start_hardware_recording(self) -> bool:
        try:
            import sounddevice as sd
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"⚠️ Audio callback status: {status}")
                
                if indata.shape[1] > 1:
                    audio_data = np.mean(indata, axis=1)
                else:
                    audio_data = indata[:, 0]
                
                self.audio_buffer.append(audio_data.copy())
                
                try:
                    self.audio_queue.put_nowait(audio_data.copy())
                except queue.Full:
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put_nowait(audio_data.copy())
                    except queue.Empty:
                        pass
            
            self.audio_stream = sd.InputStream(
                device=self.current_device['index'],
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback,
                dtype=np.float32
            )
            
            self.audio_stream.start()
            self.is_recording = True
            print(f"🎤 Started hardware recording: {self.current_device['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Hardware recording failed: {e}")
            return False
    
    def _start_simulated_recording(self) -> bool:
        self.is_recording = True
        
        import threading
        
        def generate_audio():
            while self.is_recording:
                audio_chunk = self._generate_test_audio(self.chunk_duration)
                self.audio_buffer.append(audio_chunk)
                
                try:
                    self.audio_queue.put_nowait(audio_chunk)
                except queue.Full:
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put_nowait(audio_chunk)
                    except queue.Empty:
                        pass
                
                time.sleep(self.chunk_duration)
        
        self.audio_thread = threading.Thread(target=generate_audio, daemon=True)
        self.audio_thread.start()
        print(f"🎤 Started simulated recording: {self.current_device['name']}")
        return True
    
    def stop_recording(self) -> bool:
        if not self.is_recording:
            return True
        
        try:
            self.is_recording = False
            
            if self.hardware_available and hasattr(self, 'audio_stream'):
                self.audio_stream.stop()
                self.audio_stream.close()
                del self.audio_stream
            
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            print("🛑 Stopped recording")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop recording: {e}")
            return False
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    async def get_audio_chunk_async(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None, 
                lambda: self.audio_queue.get(timeout=timeout)
            )
        except queue.Empty:
            return None
    
    def get_audio_level(self) -> float:
        if not self.audio_buffer:
            return 0.0
        
        latest_chunk = self.audio_buffer[-1]
        rms = np.sqrt(np.mean(latest_chunk ** 2))
        level = min(rms / 0.1, 1.0)
        return level
    
    def get_recent_audio(self, duration: float = 5.0) -> np.ndarray:
        if not self.audio_buffer:
            return np.array([], dtype=np.float32)
        
        chunks_needed = int(duration / self.chunk_duration)
        chunks_needed = min(chunks_needed, len(self.audio_buffer))
        
        if chunks_needed == 0:
            return np.array([], dtype=np.float32)
        
        recent_chunks = list(self.audio_buffer)[-chunks_needed:]
        audio_data = np.concatenate(recent_chunks)
        return audio_data


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

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

# Use lifespan instead of deprecated on_event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global system_ready
    print("🚀 Starting WhisperS2T Appliance with LIVE AUDIO...")
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
    
    yield
    
    # Shutdown
    print("🛑 Shutting down WhisperS2T Live Audio...")

app.router.lifespan_context = lifespan

@app.get("/")
async def root():
    status = "✅ Ready for live transcription!" if system_ready else "🔄 Starting up..."
    model = current_model_name or "Loading..."
    audio_status = audio_manager.get_device_status()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T - Live Audio</title>
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
            <h1>🎤 WhisperS2T Live Audio (CORS Fixed)</h1>
            <p><strong>Real-time Speech-to-Text with Live Audio Input</strong></p>
            
            <div class="status">{status}</div>
            
            <div class="audio-status">
                <h4>🎙️ Audio System</h4>
                <p><strong>Devices:</strong> {audio_status['devices_available']}</p>
                <p><strong>Hardware:</strong> {'✅ Available' if audio_status['hardware_available'] else '🔄 Simulated'}</p>
                <p><strong>Device:</strong> {audio_status['current_device']['name'] if audio_status['current_device'] else 'None'}</p>
            </div>
            
            <div class="highlight">
                <h3>🔥 LIVE AUDIO TRANSCRIPTION!</h3>
                <p>Real-time microphone → Whisper transcription</p>
                <p><strong>CORS Support enabled for WebSocket connections</strong></p>
            </div>
            
            <h3>🎯 Try It Now</h3>
            <a href="/demo" class="button">🎙️ Live Demo</a>
            <a href="/api/status" class="button">📊 Status</a>
            <a href="/docs" class="button">📚 API Docs</a>
            
            <div class="feature">
                <h3>🔧 Configuration</h3>
                <p><strong>Model:</strong> {model}</p>
                <p><strong>Sample Rate:</strong> {audio_status['sample_rate']} Hz</p>
                <p><strong>Connected Clients:</strong> {len(connected_clients)}</p>
                <p><strong>Version:</strong> 0.3.1-cors (WebSocket Fixed)</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/api/status")
async def get_status():
    import platform
    import psutil
    
    audio_status = audio_manager.get_device_status()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.3.1-cors",
        "status": "ready" if system_ready else "starting",
        "websocket_fix": "CORS enabled for WebSocket connections",
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
    print("🔌 New WebSocket connection attempt...")
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"✅ WebSocket connected! Total clients: {len(connected_clients)}")
    
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
            print(f"📨 Received WebSocket message: {message.get('action', 'unknown')}")
            
            if message.get("action") == "start_recording":
                if audio_manager.start_recording():
                    await websocket.send_text(json.dumps({
                        "type": "recording_started",
                        "message": "🎤 Live recording started - speak now!",
                        "timestamp": datetime.now().isoformat()
                    }))
                    asyncio.create_task(live_transcription_loop(websocket))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to start audio recording",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            elif message.get("action") == "stop_recording":
                audio_manager.stop_recording()
                await websocket.send_text(json.dumps({
                    "type": "recording_stopped",
                    "message": "🛑 Live recording stopped",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif message.get("action") == "transcribe_recent":
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
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        audio_manager.stop_recording()
        print(f"🔌 WebSocket disconnected. Remaining clients: {len(connected_clients)}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def live_transcription_loop(websocket: WebSocket):
    try:
        print("🎤 Starting live transcription loop...")
        while audio_manager.is_recording and websocket in connected_clients:
            audio_chunk = await audio_manager.get_audio_chunk_async(timeout=2.0)
            
            if audio_chunk is not None and len(audio_chunk) > 0:
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
        print(f"❌ Live transcription loop error: {e}")
            }
            
            .audio-level-bar {
                height: 100%;
                background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
                border-radius: 15px;
                transition: width 0.1s ease;
                width: 0%;
            }
            
            .debug-info {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin: 10px 0;
                font-family: monospace;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 WhisperS2T - LIVE AUDIO Demo (CORS Fixed)</h2>
            <p>Real-time microphone → Whisper transcription</p>
            
            <div id="status" class="status disconnected">
                ❌ Disconnected - Click Connect to start
            </div>
            
            <div class="controls">
                <h4>🔌 Connection & Recording</h4>
                <button onclick="connect()" class="btn-primary">🔌 Connect to WebSocket</button>
                <br><br>
                
                <button id="recordBtn" onclick="toggleRecording()" class="btn-record">
                    🎙️ START LIVE RECORDING
                </button>
                <br><br>
                
                <button onclick="transcribeRecent()" class="btn-success">📝 Transcribe Last 5s</button>
                
                <h4>🎛️ Audio Level</h4>
                <div class="audio-level">
                    <div id="audioLevelBar" class="audio-level-bar"></div>
                </div>
                <span id="audioLevelText">Level: 0%</span>
                
                <div class="debug-info">
                    <strong>WebSocket Debug:</strong><br>
                    <div id="debugInfo">Ready to connect...</div>
                </div>
            </div>
            
            <div id="transcription-display" style="min-height: 200px; margin: 20px 0;">
                <h4>📝 Live Transcription Results</h4>
                <div id="liveResults">Results will appear here...</div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRecording = false;
            
            function addDebugInfo(message) {
                const debugDiv = document.getElementById('debugInfo');
                const timestamp = new Date().toLocaleTimeString();
                debugDiv.innerHTML = `${timestamp}: ${message}<br>` + debugDiv.innerHTML;
            }
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/live-audio`;
                
                addDebugInfo(`Attempting WebSocket connection to: ${wsUrl}`);
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() { 
                    updateStatus('connected'); 
                    addDebugInfo('✅ WebSocket connection successful!');
                };
                
                ws.onmessage = function(event) { 
                    const data = JSON.parse(event.data);
                    addDebugInfo(`📨 Received: ${data.type}`);
                    handleMessage(data); 
                };
                
                ws.onclose = function() { 
                    updateStatus('disconnected'); 
                    isRecording = false; 
                    updateRecordButton(); 
                    addDebugInfo('❌ WebSocket connection closed');
                };
                
                ws.onerror = function(error) { 
                    console.error('WebSocket error:', error); 
                    updateStatus('disconnected'); 
                    addDebugInfo(`❌ WebSocket error: ${error.type || 'Connection failed'}`);
                };
            }
            
            function toggleRecording() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected! Click Connect first.');
                    addDebugInfo('⚠️ Recording attempted but not connected');
                    return;
                }
                
                if (!isRecording) {
                    addDebugInfo('🎤 Sending start_recording command...');
                    ws.send(JSON.stringify({action: 'start_recording'}));
                } else {
                    addDebugInfo('🛑 Sending stop_recording command...');
                    ws.send(JSON.stringify({action: 'stop_recording'}));
                }
            }
            
            function transcribeRecent() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected!');
                    return;
                }
                
                addDebugInfo('📝 Sending transcribe_recent command...');
                ws.send(JSON.stringify({action: 'transcribe_recent', duration: 5.0}));
            }
            
            function handleMessage(data) {
                console.log('Received:', data.type, data);
                
                switch(data.type) {
                    case 'connected':
                        addLogMessage('✅ ' + data.message);
                        addDebugInfo(`✅ Connected! Model: ${data.current_model}`);
                        break;
                    case 'recording_started':
                        isRecording = true;
                        updateRecordButton();
                        updateStatus('recording');
                        addLogMessage('🎤 Recording started - speak now!');
                        addDebugInfo('🎤 Recording started successfully');
                        break;
                    case 'recording_stopped':
                        isRecording = false;
                        updateRecordButton();
                        updateStatus('connected');
                        addLogMessage('🛑 Recording stopped');
                        addDebugInfo('🛑 Recording stopped');
                        break;
                    case 'live_transcription':
                        displayLiveTranscription(data.result);
                        addDebugInfo(`📝 Live transcription: "${data.result.text.substring(0, 30)}..."`);
                        break;
                    case 'transcription_result':
                        displayTranscriptionResult(data.result, data.source);
                        addDebugInfo(`📝 Transcription result from ${data.source}`);
                        break;
                    case 'audio_level':
                        updateAudioLevel(data.level);
                        break;
                    case 'processing':
                        addLogMessage('🔄 ' + data.message);
                        break;
                    case 'error':
                        addLogMessage('❌ ' + data.message);
                        addDebugInfo(`❌ Error: ${data.message}`);
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
                    <small>Language: ${result.language} | Processing: ${result.processing_time}s | Model: ${result.model}</small>
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
                    <small>Language: ${result.language} | Processing: ${result.processing_time}s | Audio: ${result.audio_length.toFixed(1)}s</small>
                `;
                liveResults.appendChild(div);
                liveResults.scrollTop = liveResults.scrollHeight;
            }
            
            function addLogMessage(message) {
                const liveResults = document.getElementById('liveResults');
                const div = document.createElement('div');
                div.style.cssText = 'padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 3px; font-size: 14px;';
                div.innerHTML = `<small>${new Date().toLocaleTimeString()}: ${message}</small>`;
                liveResults.appendChild(div);
                liveResults.scrollTop = liveResults.scrollHeight;
            }
            
            function updateAudioLevel(level) {
                const bar = document.getElementById('audioLevelBar');
                const text = document.getElementById('audioLevelText');
                const percentage = Math.round(level * 100);
                
                bar.style.width = percentage + '%';
                text.textContent = `Level: ${percentage}%`;
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
                addLogMessage('Demo interface loaded - click Connect to start');
                addDebugInfo('Demo page loaded successfully');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Live Audio Server (CORS Fixed)...")
    print("🌐 Main Interface: http://localhost:5000")
    print("🎙️ Live Audio Demo: http://localhost:5000/demo")
    print("📊 API Status: http://localhost:5000/api/status")
    print()
    print("🔧 FIXES APPLIED:")
    print("   - CORS middleware enabled for WebSocket support")
    print("   - Detailed WebSocket debugging")
    print("   - Improved error handling")
    print()
    print("🎤 LIVE FEATURES:")
    print("   - Real microphone input (or simulated if no hardware)")
    print("   - Live audio level monitoring")
    print("   - Real-time transcription")
    print("   - WebSocket live communication")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
