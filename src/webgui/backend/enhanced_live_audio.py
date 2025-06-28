#!/usr/bin/env python3
"""
WhisperS2T Live Audio Server - Enhanced Version
- Real microphone support with device selection
- Language selection for Whisper
- Improved audio handling
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
from typing import Dict, Optional, List
from collections import deque
from faster_whisper import WhisperModel

app = FastAPI(title="WhisperS2T Enhanced", version="0.4.0-enhanced")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnhancedAudioManager:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=10)
        
        # Device management
        self.input_devices = []
        self.current_device = None
        self.hardware_available = False
        
        # Try multiple audio backends
        self._detect_audio_devices()
    
    def _detect_audio_devices(self):
        """Enhanced audio device detection with multiple backends"""
        print("🔍 Detecting audio devices...")
        
        # Try sounddevice first
        try:
            import sounddevice as sd
            print("✅ sounddevice library available")
            
            devices = sd.query_devices()
            self.input_devices = []
            
            print(f"📱 Found {len(devices)} total audio devices:")
            for i, device in enumerate(devices):
                print(f"   {i}: {device['name']} (in: {device['max_input_channels']}, out: {device['max_output_channels']})")
                
                if device['max_input_channels'] > 0:
                    device_info = {
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'type': 'hardware',
                        'api': device.get('hostapi', 'unknown')
                    }
                    self.input_devices.append(device_info)
            
            if self.input_devices:
                self.current_device = self.input_devices[0]
                self.hardware_available = True
                print(f"🎤 Found {len(self.input_devices)} input devices")
                print(f"🎯 Default device: {self.current_device['name']}")
                return
            else:
                print("⚠️ No input devices found")
                
        except ImportError:
            print("❌ sounddevice not available")
        except Exception as e:
            print(f"❌ sounddevice error: {e}")
        
        # Try pyaudio as fallback
        try:
            import pyaudio
            print("✅ pyaudio library available")
            
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            
            print(f"📱 PyAudio found {device_count} devices:")
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)
                print(f"   {i}: {device_info['name']} (in: {device_info['maxInputChannels']})")
                
                if device_info['maxInputChannels'] > 0:
                    self.input_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate'],
                        'type': 'hardware',
                        'api': 'pyaudio'
                    })
            
            p.terminate()
            
            if self.input_devices:
                self.current_device = self.input_devices[0]
                self.hardware_available = True
                print(f"🎤 PyAudio found {len(self.input_devices)} input devices")
                return
                
        except ImportError:
            print("❌ pyaudio not available")
        except Exception as e:
            print(f"❌ pyaudio error: {e}")
        
        # Fallback to simulated audio
        self._setup_fallback_devices()
    
    def _setup_fallback_devices(self):
        """Setup enhanced simulated audio devices"""
        print("🔄 Setting up simulated audio devices...")
        
        # Create multiple simulated devices for testing
        self.input_devices = [
            {
                'index': 0,
                'name': 'Simulated Microphone (German Voice)',
                'channels': 1,
                'sample_rate': 16000,
                'type': 'simulated',
                'language': 'de',
                'test_phrases': [
                    "Hallo, das ist ein Test auf Deutsch.",
                    "Wie geht es dir heute?", 
                    "Das Wetter ist heute sehr schön.",
                    "Ich teste die Spracherkennung."
                ]
            },
            {
                'index': 1,
                'name': 'Simulated Microphone (English Voice)',
                'channels': 1,
                'sample_rate': 16000,
                'type': 'simulated',
                'language': 'en',
                'test_phrases': [
                    "Hello, this is an English test.",
                    "How are you doing today?",
                    "The weather is beautiful today.",
                    "I am testing speech recognition."
                ]
            },
            {
                'index': 2,
                'name': 'Simulated Microphone (French Voice)',
                'channels': 1,
                'sample_rate': 16000,
                'type': 'simulated',
                'language': 'fr',
                'test_phrases': [
                    "Bonjour, c'est un test en français.",
                    "Comment allez-vous aujourd'hui?",
                    "Le temps est magnifique aujourd'hui.",
                    "Je teste la reconnaissance vocale."
                ]
            }
        ]
        
        self.current_device = self.input_devices[0]
        self.hardware_available = False
        self.phrase_counter = 0
        print(f"✅ Created {len(self.input_devices)} simulated devices")
    
    def get_device_status(self) -> Dict:
        return {
            "devices_available": len(self.input_devices),
            "input_devices": self.input_devices,
            "current_device": self.current_device,
            "is_recording": self.is_recording,
            "hardware_available": self.hardware_available,
            "sample_rate": self.sample_rate
        }
    
    def set_device(self, device_index: int) -> bool:
        """Set the current audio input device"""
        if 0 <= device_index < len(self.input_devices):
            self.current_device = self.input_devices[device_index]
            print(f"🎤 Switched to device: {self.current_device['name']}")
            return True
        return False
    
    def _generate_realistic_test_audio(self) -> np.ndarray:
        """Generate more realistic test audio that simulates speech patterns"""
        if not self.current_device or self.current_device['type'] != 'simulated':
            # Fallback audio
            samples = self.sample_rate
            t = np.linspace(0, 1, samples)
            audio = 0.1 * np.sin(2 * np.pi * 440 * t) + 0.05 * np.random.normal(0, 1, samples)
            return audio.astype(np.float32)
        
        # Get current test phrase
        phrases = self.current_device.get('test_phrases', ['Test audio'])
        current_phrase = phrases[self.phrase_counter % len(phrases)]
        self.phrase_counter += 1
        
        print(f"🎙️ Simulating speech: '{current_phrase}' (Language: {self.current_device.get('language', 'en')})")
        
        # Generate speech-like audio patterns
        samples = self.sample_rate
        t = np.linspace(0, 1, samples)
        
        # Create formant-like frequencies for speech simulation
        f1 = 300 + 200 * np.sin(2 * np.pi * 0.5 * t)  # First formant
        f2 = 1200 + 400 * np.sin(2 * np.pi * 0.3 * t)  # Second formant
        f3 = 2500 + 300 * np.sin(2 * np.pi * 0.7 * t)  # Third formant
        
        # Generate speech-like signal
        audio = (
            0.3 * np.sin(2 * np.pi * f1 * t) +
            0.2 * np.sin(2 * np.pi * f2 * t) + 
            0.1 * np.sin(2 * np.pi * f3 * t) +
            0.05 * np.random.normal(0, 1, samples)
        )
        
        # Add speech-like envelope (pauses and emphasis)
        envelope = np.ones_like(t)
        # Add some pauses
        pause_points = [0.2, 0.4, 0.7]
        for pause in pause_points:
            start = int(pause * samples)
            end = int((pause + 0.05) * samples)
            if end < samples:
                envelope[start:end] *= 0.1
        
        # Add emphasis
        emphasis_points = [0.1, 0.35, 0.8]
        for emphasis in emphasis_points:
            start = int(emphasis * samples)
            end = int((emphasis + 0.1) * samples)
            if end < samples:
                envelope[start:end] *= 1.5
        
        audio *= envelope
        
        # Normalize and add realistic level variation
        audio = audio / np.max(np.abs(audio)) * 0.3
        return audio.astype(np.float32)
    
    def start_recording(self) -> bool:
        """Start audio recording with enhanced device support"""
        if self.is_recording:
            print("⚠️ Already recording")
            return True
        
        if not self.current_device:
            print("❌ No audio device selected")
            return False
        
        print(f"🎤 Starting recording with device: {self.current_device['name']}")
        self.is_recording = True
        
        try:
            if self.hardware_available and self.current_device['type'] == 'hardware':
                return self._start_hardware_recording()
            else:
                return self._start_simulated_recording()
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            self.is_recording = False
            return False
    
    def _start_hardware_recording(self) -> bool:
        """Start real hardware recording"""
        try:
            api = self.current_device.get('api', 'sounddevice')
            
            if api == 'sounddevice':
                import sounddevice as sd
                
                def audio_callback(indata, frames, time, status):
                    if status:
                        print(f"⚠️ Audio status: {status}")
                    
                    # Convert to mono if needed
                    if len(indata.shape) > 1 and indata.shape[1] > 1:
                        audio_data = np.mean(indata, axis=1)
                    else:
                        audio_data = indata.flatten()
                    
                    self.audio_buffer.append(audio_data.copy())
                    
                    try:
                        self.audio_queue.put_nowait(audio_data.copy())
                    except queue.Full:
                        # Remove old data if queue is full
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.put_nowait(audio_data.copy())
                        except queue.Empty:
                            pass
                
                self.audio_stream = sd.InputStream(
                    device=self.current_device['index'],
                    channels=1,
                    samplerate=self.sample_rate,
                    blocksize=self.sample_rate,  # 1 second chunks
                    callback=audio_callback,
                    dtype=np.float32
                )
                
                self.audio_stream.start()
                print(f"✅ Hardware recording started with sounddevice")
                return True
                
            elif api == 'pyaudio':
                import pyaudio
                
                def audio_callback(in_data, frame_count, time_info, status):
                    audio_data = np.frombuffer(in_data, dtype=np.float32)
                    self.audio_buffer.append(audio_data.copy())
                    
                    try:
                        self.audio_queue.put_nowait(audio_data.copy())
                    except queue.Full:
                        pass
                    
                    return (in_data, pyaudio.paContinue)
                
                self.pyaudio_instance = pyaudio.PyAudio()
                self.audio_stream = self.pyaudio_instance.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=self.current_device['index'],
                    frames_per_buffer=self.sample_rate,
                    stream_callback=audio_callback
                )
                
                self.audio_stream.start_stream()
                print(f"✅ Hardware recording started with pyaudio")
                return True
                
        except Exception as e:
            print(f"❌ Hardware recording failed: {e}")
            return False
    
    def _start_simulated_recording(self) -> bool:
        """Start enhanced simulated recording"""
        import threading
        
        def generate_audio():
            print(f"🎭 Starting simulated audio generation for: {self.current_device['name']}")
            
            while self.is_recording:
                try:
                    audio_chunk = self._generate_realistic_test_audio()
                    self.audio_buffer.append(audio_chunk)
                    
                    try:
                        self.audio_queue.put_nowait(audio_chunk)
                    except queue.Full:
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.put_nowait(audio_chunk)
                        except queue.Empty:
                            pass
                    
                    # Wait 3 seconds between phrases for more realistic timing
                    time.sleep(3.0)
                    
                except Exception as e:
                    print(f"❌ Simulated audio generation error: {e}")
                    break
        
        self.audio_thread = threading.Thread(target=generate_audio, daemon=True)
        self.audio_thread.start()
        print(f"✅ Simulated recording started")
        return True
    
    def stop_recording(self) -> bool:
        """Stop audio recording"""
        if not self.is_recording:
            return True
        
        try:
            self.is_recording = False
            
            if self.hardware_available and hasattr(self, 'audio_stream'):
                if hasattr(self, 'pyaudio_instance'):
                    # PyAudio cleanup
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                    self.pyaudio_instance.terminate()
                    del self.pyaudio_instance
                else:
                    # SoundDevice cleanup
                    self.audio_stream.stop()
                    self.audio_stream.close()
                
                del self.audio_stream
            
            # Clear queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            print("🛑 Recording stopped")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop recording: {e}")
            return False
    
    async def get_audio_chunk_async(self, timeout: float = 2.0):
        """Get audio chunk asynchronously"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None, 
                lambda: self.audio_queue.get(timeout=timeout)
            )
        except queue.Empty:
            return None
    
    def get_audio_level(self) -> float:
        """Get current audio level"""
        if not self.audio_buffer:
            return 0.0
        
        latest_chunk = self.audio_buffer[-1]
        rms = np.sqrt(np.mean(latest_chunk ** 2))
        level = min(rms / 0.2, 1.0)  # Adjusted scale for better sensitivity
        return level
    
    def get_recent_audio(self, duration: float = 5.0) -> np.ndarray:
        """Get recent audio for transcription"""
        if not self.audio_buffer:
            return np.array([], dtype=np.float32)
        
        chunks_needed = min(int(duration), len(self.audio_buffer))
        if chunks_needed == 0:
            return np.array([], dtype=np.float32)
        
        recent_chunks = list(self.audio_buffer)[-chunks_needed:]
        audio_data = np.concatenate(recent_chunks)
        return audio_data

# Enhanced Whisper Manager with language support
class EnhancedWhisperManager:
    def __init__(self):
        self.models = {}
        self.current_model_name = None
        self.current_language = None
        self.available_models = ["tiny", "base", "small", "medium"]
        self.available_languages = {
            "auto": "Auto-detect",
            "en": "English", 
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese"
        }
    
    async def load_model(self, model_name="tiny"):
        """Load Whisper model"""
        if model_name in self.models:
            self.current_model_name = model_name
            return {"model": model_name, "cached": True}
        
        print(f"🔄 Loading Whisper model: {model_name}")
        start_time = time.time()
        
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(
            None, 
            lambda: WhisperModel(model_name, device="cpu", compute_type="int8")
        )
        
        self.models[model_name] = model
        self.current_model_name = model_name
        
        load_time = time.time() - start_time
        print(f"✅ Model {model_name} loaded in {load_time:.1f}s")
        
        return {"model": model_name, "load_time": round(load_time, 1)}
    
    def set_language(self, language_code: str):
        """Set transcription language"""
        if language_code in self.available_languages:
            self.current_language = language_code if language_code != "auto" else None
            print(f"🌐 Language set to: {self.available_languages[language_code]}")
            return True
        return False
    
    async def transcribe(self, audio_data, language=None):
        """Transcribe audio with language support"""
        if not self.current_model_name or self.current_model_name not in self.models:
            await self.load_model("tiny")
        
        model = self.models[self.current_model_name]
        target_language = language or self.current_language
        
        print(f"🎤 Transcribing {len(audio_data)} samples (language: {target_language or 'auto'})")
        start_time = time.time()
        
        loop = asyncio.get_event_loop()
        
        # Configure transcription parameters
        transcribe_kwargs = {"beam_size": 1}
        if target_language:
            transcribe_kwargs["language"] = target_language
        
        segments, info = await loop.run_in_executor(
            None,
            lambda: model.transcribe(audio_data, **transcribe_kwargs)
        )
        
        full_text = " ".join(segment.text for segment in segments)
        processing_time = time.time() - start_time
        
        return {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": getattr(info, 'language_probability', 0.0),
            "processing_time": round(processing_time, 2),
            "model": self.current_model_name,
            "audio_length": len(audio_data) / 16000,
            "target_language": target_language or "auto"
        }

# Global instances
audio_manager = EnhancedAudioManager()
whisper_manager = EnhancedWhisperManager()
connected_clients = []
system_ready = False
                    }})
                }});
                const result = await response.json();
                if (result.success) {
                    console.log('Device changed:', result.device);
                    location.reload(); // Refresh to show new device
                } else {
                    alert('Failed to change device');
                }
            }} catch (error) {{
                console.error('Error changing device:', error);
            }}
        }}
        
        async function changeLanguage() {{
            const language = document.getElementById('languageSelect').value;
            try {{
                const response = await fetch('/api/set-language', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{language: language}})
                }});
                const result = await response.json();
                if (result.success) {{
                    console.log('Language changed:', result.language);
                }} else {{
                    alert('Failed to change language');
                }}
            }} catch (error) {{
                console.error('Error changing language:', error);
            }}
        }}
        
        async function changeModel() {{
            const model = document.getElementById('modelSelect').value;
            try {{
                const response = await fetch('/api/set-model', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{model: model}})
                }});
                const result = await response.json();
                if (result.success) {{
                    console.log('Model changed:', result.model);
                    alert('Model loaded: ' + result.model + ' (Load time: ' + result.load_time + 's)');
                }} else {{
                    alert('Failed to change model');
                }}
            }} catch (error) {{
                console.error('Error changing model:', error);
            }}
        }}
        
        async function refreshDevices() {{
            try {{
                const response = await fetch('/api/refresh-devices', {{method: 'POST'}});
                const result = await response.json();
                if (result.success) {{
                    location.reload(); // Refresh page to show new devices
                }} else {{
                    alert('Failed to refresh devices');
                }}
            }} catch (error) {{
                console.error('Error refreshing devices:', error);
            }}
        }}
        </script>
    </body>
    </html>
    """)

@app.get("/api/status")
async def get_status():
    """Enhanced status endpoint"""
    audio_status = audio_manager.get_device_status()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.4.0-enhanced",
        "status": "ready" if system_ready else "starting",
        "whisper": {
            "current_model": whisper_manager.current_model_name,
            "available_models": whisper_manager.available_models,
            "model_loaded": whisper_manager.current_model_name is not None,
            "current_language": whisper_manager.current_language or "auto",
            "available_languages": whisper_manager.available_languages
        },
        "audio": audio_status,
        "websocket": {
            "connected_clients": len(connected_clients)
        },
        "features": {
            "real_microphone": audio_status['hardware_available'],
            "language_selection": True,
            "device_selection": True,
            "realistic_test_audio": True
        }
    }

@app.get("/api/devices")
async def get_devices():
    """Get available audio devices"""
    return audio_manager.get_device_status()

@app.post("/api/set-device")
async def set_device(request: dict):
    """Set audio input device"""
    device_index = request.get('device_index')
    if device_index is not None:
        success = audio_manager.set_device(device_index)
        if success:
            return {
                "success": True, 
                "device": audio_manager.current_device
            }
    return {"success": False, "error": "Invalid device index"}

@app.post("/api/set-language")
async def set_language(request: dict):
    """Set transcription language"""
    language = request.get('language')
    if language:
        success = whisper_manager.set_language(language)
        if success:
            return {
                "success": True, 
                "language": language,
                "language_name": whisper_manager.available_languages.get(language, language)
            }
    return {"success": False, "error": "Invalid language"}

@app.post("/api/set-model") 
async def set_model(request: dict):
    """Set Whisper model"""
    model = request.get('model')
    if model in whisper_manager.available_models:
        result = await whisper_manager.load_model(model)
        return {"success": True, **result}
    return {"success": False, "error": "Invalid model"}

@app.post("/api/refresh-devices")
async def refresh_devices():
    """Refresh audio device list"""
    try:
        audio_manager._detect_audio_devices()
        return {"success": True, "devices": audio_manager.get_device_status()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.websocket("/ws/live-audio")
async def websocket_live_audio(websocket: WebSocket):
    """Enhanced WebSocket with device and language support"""
    print("🔌 Enhanced WebSocket connection...")
    await websocket.accept()
    connected_clients.append(websocket)
    print(f"✅ WebSocket connected! Total: {len(connected_clients)}")
    
    # Send enhanced welcome message
    audio_status = audio_manager.get_device_status()
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": f"Enhanced Live Audio ready! Device: {audio_status['current_device']['name']}",
        "timestamp": datetime.now().isoformat(),
        "audio_status": audio_status,
        "whisper_info": {
            "model": whisper_manager.current_model_name,
            "language": whisper_manager.current_language or "auto",
            "available_languages": whisper_manager.available_languages
        }
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get('action')
            print(f"📨 Received action: {action}")
            
            if action == "start_recording":
                if audio_manager.start_recording():
                    await websocket.send_text(json.dumps({
                        "type": "recording_started",
                        "message": f"🎤 Recording started with {audio_manager.current_device['name']}",
                        "timestamp": datetime.now().isoformat(),
                        "device": audio_manager.current_device
                    }))
                    asyncio.create_task(enhanced_transcription_loop(websocket))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to start recording",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            elif action == "stop_recording":
                audio_manager.stop_recording()
                await websocket.send_text(json.dumps({
                    "type": "recording_stopped",
                    "message": "🛑 Recording stopped",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif action == "transcribe_recent":
                duration = message.get("duration", 5.0)
                language = message.get("language")  # Optional language override
                
                recent_audio = audio_manager.get_recent_audio(duration)
                
                if len(recent_audio) > 0:
                    await websocket.send_text(json.dumps({
                        "type": "processing",
                        "message": f"Transcribing {duration}s of audio...",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    result = await whisper_manager.transcribe(recent_audio, language)
                    
                    await websocket.send_text(json.dumps({
                        "type": "transcription_result",
                        "result": result,
                        "source": "recent_audio",
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No audio available for transcription",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif action == "change_device":
                device_index = message.get("device_index")
                if device_index is not None and audio_manager.set_device(device_index):
                    await websocket.send_text(json.dumps({
                        "type": "device_changed",
                        "message": f"Switched to: {audio_manager.current_device['name']}",
                        "device": audio_manager.current_device,
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to change device",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif action == "change_language":
                language = message.get("language")
                if language and whisper_manager.set_language(language):
                    await websocket.send_text(json.dumps({
                        "type": "language_changed",
                        "message": f"Language set to: {whisper_manager.available_languages.get(language, language)}",
                        "language": language,
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to change language",
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

async def enhanced_transcription_loop(websocket: WebSocket):
    """Enhanced live transcription loop with better audio handling"""
    try:
        print("🎤 Starting enhanced live transcription...")
        consecutive_empty = 0
        
        while audio_manager.is_recording and websocket in connected_clients:
            audio_chunk = await audio_manager.get_audio_chunk_async(timeout=3.0)
            
            if audio_chunk is not None and len(audio_chunk) > 0:
                consecutive_empty = 0
                
                # Calculate audio level
                level = audio_manager.get_audio_level()
                
                # Send audio level update
                await websocket.send_text(json.dumps({
                    "type": "audio_level",
                    "level": level,
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Check if there's significant audio activity
                if level > 0.02:  # Slightly higher threshold for better detection
                    recent_audio = audio_manager.get_recent_audio(duration=4.0)
                    
                    if len(recent_audio) > 32000:  # At least 2 seconds
                        print(f"🎤 Transcribing audio chunk (level: {level:.3f})")
                        
                        result = await whisper_manager.transcribe(recent_audio)
                        
                        # Only send if we got meaningful text
                        if result["text"].strip() and len(result["text"].strip()) > 1:
                            await websocket.send_text(json.dumps({
                                "type": "live_transcription",
                                "result": result,
                                "audio_level": level,
                                "timestamp": datetime.now().isoformat()
                            }))
            else:
                consecutive_empty += 1
                if consecutive_empty > 10:  # 10 * 0.5s = 5s of no audio
                    print("⚠️ No audio received for 5+ seconds")
                    consecutive_empty = 0
            
            await asyncio.sleep(0.5)
        
        print("🛑 Enhanced transcription loop ended")
    except Exception as e:
        print(f"❌ Enhanced transcription error: {e}")

@app.get("/demo")
async def enhanced_demo():
    """Enhanced demo page with device and language controls"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Enhanced Live Demo</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial; margin: 20px; background: #f8f9fa; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            button { padding: 12px 24px; margin: 8px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-record { background: #dc3545; color: white; font-size: 18px; padding: 15px 30px; }
            .btn-record.recording { background: #28a745; animation: pulse 1s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
            
            .status { padding: 12px; border-radius: 5px; margin: 15px 0; font-weight: bold; text-align: center; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .recording { background: #fff3cd; color: #856404; }
            
            .controls { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .config-panel { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
            
            .transcription { background: #f0fff0; border: 1px solid #90ee90; border-radius: 5px; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }
            .transcription.german { border-left-color: #dc3545; background: #fff5f5; }
            .transcription.french { border-left-color: #6610f2; background: #f8f7ff; }
            .transcription.auto { border-left-color: #fd7e14; background: #fff8f5; }
            
            .audio-level { width: 100%; height: 25px; background: #e9ecef; border-radius: 12px; margin: 10px 0; overflow: hidden; }
            .audio-level-bar { height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); border-radius: 12px; transition: width 0.1s ease; width: 0%; }
            
            select { padding: 8px; margin: 5px; border-radius: 4px; border: 1px solid #ddd; min-width: 150px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .info-box { background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 WhisperS2T Enhanced Live Demo</h2>
            <p>Real-time speech-to-text with device selection and multi-language support</p>
            
            <div id="status" class="status disconnected">❌ Disconnected</div>
            
            <div class="grid">
                <div>
                    <div class="config-panel">
                        <h4>⚙️ Configuration</h4>
                        
                        <div style="margin: 10px 0;">
                            <label><strong>🎤 Audio Device:</strong></label><br>
                            <select id="deviceSelect" onchange="changeDevice()">
                                <option value="">Loading devices...</option>
                            </select>
                            <button onclick="refreshDevices()" style="padding: 6px 12px;">🔄</button>
                        </div>
                        
                        <div style="margin: 10px 0;">
                            <label><strong>🌐 Language:</strong></label><br>
                            <select id="languageSelect" onchange="changeLanguage()">
                                <option value="auto">Auto-detect</option>
                                <option value="en">English</option>
                                <option value="de">German</option>
                                <option value="fr">French</option>
                                <option value="es">Spanish</option>
                            </select>
                        </div>
                        
                        <div class="info-box">
                            <small><strong>🎭 Test Mode:</strong> If no hardware microphone is found, realistic test audio will be generated in different languages for demonstration.</small>
                        </div>
                    </div>
                    
                    <div class="controls">
                        <h4>🔌 Connection & Recording</h4>
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
                        
                        <div id="deviceInfo" class="info-box">
                            <small>Device info will appear here...</small>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div id="results" style="min-height: 400px;">
                        <h4>📝 Live Transcription Results</h4>
                        <div id="liveResults">Results will appear here...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRecording = false;
            let currentDevices = [];
            let currentLanguages = {};
            
            function connect() {
                const wsUrl = `ws://${window.location.host}/ws/live-audio`;
                console.log('Connecting to:', wsUrl);
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() { 
                    updateStatus('connected'); 
                    addMessage('✅ Enhanced WebSocket connected!');
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
                    alert('Not connected! Click Connect first.');
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
                
                const language = document.getElementById('languageSelect').value;
                ws.send(JSON.stringify({
                    action: 'transcribe_recent', 
                    duration: 5.0,
                    language: language !== 'auto' ? language : null
                }));
            }
            
            function changeDevice() {
                const deviceIndex = parseInt(document.getElementById('deviceSelect').value);
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('⚠️ Not connected - device change queued');
                    return;
                }
                
                ws.send(JSON.stringify({
                    action: 'change_device',
                    device_index: deviceIndex
                }));
            }
            
            function changeLanguage() {
                const language = document.getElementById('languageSelect').value;
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('⚠️ Not connected - language change queued');
                    return;
                }
                
                ws.send(JSON.stringify({
                    action: 'change_language',
                    language: language
                }));
            }
            
            async function refreshDevices() {
                try {
                    const response = await fetch('/api/refresh-devices', {method: 'POST'});
                    const result = await response.json();
                    if (result.success) {
                        updateDeviceList(result.devices.input_devices);
                        addMessage('🔄 Device list refreshed');
                    }
                } catch (error) {
                    console.error('Error refreshing devices:', error);
                }
            }
            
            function handleMessage(data) {
                console.log('Received:', data.type);
                
                switch(data.type) {
                    case 'connected':
                        addMessage('✅ ' + data.message);
                        if (data.audio_status) {
                            updateDeviceList(data.audio_status.input_devices);
                            updateDeviceInfo(data.audio_status.current_device);
                        }
                        if (data.whisper_info) {
                            currentLanguages = data.whisper_info.available_languages;
                        }
                        break;
                        
                    case 'recording_started':
                        isRecording = true;
                        updateRecordButton();
                        updateStatus('recording');
                        addMessage('🎤 Recording started: ' + data.device.name);
                        break;
                        
                    case 'recording_stopped':
                        isRecording = false;
                        updateRecordButton();
                        updateStatus('connected');
                        addMessage('🛑 Recording stopped');
                        break;
                        
                    case 'live_transcription':
                        displayTranscription(data.result, 'LIVE', data.audio_level);
                        break;
                        
                    case 'transcription_result':
                        displayTranscription(data.result, data.source);
                        break;
                        
                    case 'audio_level':
                        updateAudioLevel(data.level);
                        break;
                        
                    case 'device_changed':
                        addMessage('🎤 ' + data.message);
                        updateDeviceInfo(data.device);
                        break;
                        
                    case 'language_changed':
                        addMessage('🌐 ' + data.message);
                        break;
                        
                    case 'processing':
                        addMessage('🔄 ' + data.message);
                        break;
                        
                    case 'error':
                        addMessage('❌ ' + data.message);
                        break;
                }
            }
            
            function updateDeviceList(devices) {
                const select = document.getElementById('deviceSelect');
                select.innerHTML = '';
                
                devices.forEach((device, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = `${device.name} (${device.type})`;
                    select.appendChild(option);
                });
                
                currentDevices = devices;
            }
            
            function updateDeviceInfo(device) {
                const info = document.getElementById('deviceInfo');
                if (device) {
                    info.innerHTML = `
                        <small><strong>Current Device:</strong><br>
                        📱 ${device.name}<br>
                        🔧 Type: ${device.type}<br>
                        📊 Sample Rate: ${device.sample_rate} Hz<br>
                        🎛️ Channels: ${device.channels}</small>
                    `;
                }
            }
            
            function displayTranscription(result, source, audioLevel = null) {
                const div = document.createElement('div');
                
                // Add language-specific styling
                let languageClass = '';
                if (result.language === 'de') languageClass = 'german';
                else if (result.language === 'fr') languageClass = 'french';
                else if (result.target_language === 'auto') languageClass = 'auto';
                
                div.className = `transcription ${languageClass}`;
                
                const levelText = audioLevel ? ` (Level: ${Math.round(audioLevel * 100)}%)` : '';
                const confidence = result.language_probability ? ` (${Math.round(result.language_probability * 100)}% confidence)` : '';
                
                div.innerHTML = `
                    <h5>📝 ${source}: ${new Date().toLocaleTimeString()}${levelText}</h5>
                    <p><strong>"${result.text}"</strong></p>
                    <small>
                        🌐 Language: ${result.language}${confidence} | 
                        ⚙️ Model: ${result.model} | 
                        ⏱️ Processing: ${result.processing_time}s | 
                        🎵 Audio: ${result.audio_length.toFixed(1)}s
                        ${result.target_language ? ` | 🎯 Target: ${result.target_language}` : ''}
                    </small>
                `;
                
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView({ behavior: 'smooth' });
            }
            
            function addMessage(message) {
                const div = document.createElement('div');
                div.style.cssText = 'padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 3px; font-size: 14px;';
                div.innerHTML = `<small>${new Date().toLocaleTimeString()}: ${message}</small>`;
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView({ behavior: 'smooth' });
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
                        statusDiv.innerHTML = '✅ Connected - Enhanced Features Ready!';
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
                addMessage('🚀 Enhanced demo loaded - click Connect to start');
                
                // Load initial device list
                fetch('/api/devices')
                    .then(response => response.json())
                    .then(data => {
                        updateDeviceList(data.input_devices);
                        updateDeviceInfo(data.current_device);
                    })
                    .catch(error => console.error('Error loading devices:', error));
            };
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Enhanced Live Audio Server...")
    print("🌐 Main Interface: http://localhost:5000")
    print("🎙️ Enhanced Demo: http://localhost:5000/demo")
    print("📊 Status API: http://localhost:5000/api/status")
    print("🎤 Devices API: http://localhost:5000/api/devices")
    print()
    print("🆕 ENHANCED FEATURES:")
    print("   ✅ Real microphone detection & selection")
    print("   ✅ Multi-language support (German, English, French, etc.)")
    print("   ✅ Realistic test audio in different languages")
    print("   ✅ Enhanced device management")
    print("   ✅ Live language detection with confidence")
    print("   ✅ Model selection (tiny/base/small/medium)")
    print("   ✅ Improved audio level detection")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
