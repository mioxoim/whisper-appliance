# 🏗️ Technische Architektur - Enhanced WhisperS2T v0.4.0

## 📊 System-Übersicht

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Browser       │    │   FastAPI        │    │   Whisper       │
│                 │    │   Backend        │    │   Engine        │
│ ┌─────────────┐ │    │                  │    │                 │
│ │getUserMedia │ │◄──►│ enhanced_final_  │◄──►│ faster-whisper  │
│ │    API      │ │    │   working.py     │    │ + openai-whisper│
│ └─────────────┘ │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │MediaRecorder│ │    │ │WebSocket API │ │    │ │Model Cache  │ │
│ │    API      │ │    │ │      /ws     │ │    │ │~/.cache/    │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │                 │
│ │WebSocket    │ │    │ │HTTP REST API │ │    │                 │
│ │   Client    │ │    │ │   /api/*     │ │    │                 │
│ └─────────────┘ │    │ └──────────────┘ │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 🎤 Audio-Pipeline

### **Input-Pipeline: Browser → Server**

```
[Mikrofon] → [getUserMedia] → [MediaRecorder] → [WebM/Opus] 
    ↓
[Base64 Encoding] → [WebSocket] → [Server Decode] → [Temp File]
    ↓
[Whisper Processing] → [Text Output] → [WebSocket Response]
```

### **Detaillierte Audio-Verarbeitung**

```python
# 1. Browser: Audio Capture
navigator.mediaDevices.getUserMedia({
    audio: {
        deviceId: selectedMicrophone,
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
    }
})

# 2. Browser: Recording & Encoding
mediaRecorder = new MediaRecorder(audioStream, {
    mimeType: 'audio/webm;codecs=opus',
    audioBitsPerSecond: 16000
})

# 3. Server: Audio Processing
async def process_real_audio(audio_data_base64, language):
    audio_bytes = base64.b64decode(audio_data_base64)
    
    with tempfile.NamedTemporaryFile(suffix='.webm') as temp_file:
        temp_file.write(audio_bytes)
        
        # Faster-Whisper Processing
        segments, info = current_model.transcribe(
            temp_file.name,
            language=language_code,
            beam_size=5,
            word_timestamps=False
        )
        
        transcript = ''.join([segment.text for segment in segments])
        return transcript.strip()
```

---

## 🧠 Whisper-Integration

### **Model-Management Architecture**

```
Model Loading Strategy:
├── 1. Primary: faster-whisper (CPU optimized)
│   ├── WhisperModel(model_name, device="cpu", compute_type="int8")
│   ├── Cache: ~/.cache/huggingface/transformers/
│   └── API: segments, info = model.transcribe(audio, language)
│
├── 2. Fallback: openai-whisper (compatibility)
│   ├── whisper.load_model(model_name)
│   ├── Cache: ~/.cache/whisper/
│   └── API: result = model.transcribe(audio, language, fp16=False)
│
└── 3. Detection: Automatic model type recognition
    ├── hasattr(model, 'model') → faster-whisper
    ├── hasattr(model, 'dims') → openai-whisper
    └── model.model_type attribute for explicit marking
```

### **Model-Sizes & Performance**

| Model | Size | RAM | CPU Time | Quality | Use Case |
|-------|------|-----|----------|---------|----------|
| tiny  | 39MB | ~150MB | ~1s | Basic | Development/Testing |
| base  | 74MB | ~300MB | ~2s | Good | Real-time Applications |
| small | 244MB | ~800MB | ~5s | Better | Quality Applications |
| medium| 769MB | ~2GB | ~12s | High | Professional Use |
| large | 1550MB | ~4GB | ~25s | Best | Maximum Accuracy |

---

## 🌐 WebSocket-API

### **Message Protocol**

```json
// Client → Server Commands
{
  "command": "start_real_recording",
  "device_id": "microphone-device-id",
  "language": "de",
  "mode": "real_microphone"
}

{
  "command": "process_audio",
  "audio_data": "UklGRnoGAABXQVZFZm10IBAAAAABAAEA...",
  "language": "de",
  "format": "webm"
}

{
  "command": "load_model",
  "model_name": "base"
}

// Server → Client Responses
{
  "type": "transcript",
  "transcript": "Das ist ein Test der Spracherkennung.",
  "language": "de",
  "source": "real_microphone",
  "timestamp": "2025-06-26T23:30:00Z"
}

{
  "type": "status",
  "message": "Recording started",
  "recording": true,
  "model": "base"
}

{
  "type": "model_loaded",
  "message": "Whisper base model loaded successfully",
  "model": "base",
  "load_time": 2.3
}
```

### **Connection Lifecycle**

```python
# Server-side WebSocket Handler
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Command Routing
            if command == 'start_real_recording':
                # Setup recording session
            elif command == 'process_audio':
                # Process audio with Whisper
            elif command == 'load_model':
                # Load new Whisper model
                
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
```

---

## 🗂️ File-System-Layout

### **Project Structure**

```
whisper-appliance/
├── src/
│   └── webgui/
│       └── backend/
│           ├── enhanced_final_working.py    # Main Server
│           ├── enhanced_clean.py            # Legacy Version
│           └── enhanced_*.py                # Development Versions
├── models/                                  # Local Model Cache
├── docs/                                    # Documentation
├── tests/                                   # Test Suite
├── requirements.txt                         # Python Dependencies
├── README.md                               # Main Documentation
├── QUICKSTART.md                           # Getting Started
├── CHANGELOG.md                            # Version History
└── ARCHITECTURE.md                         # This File
```

### **Runtime Directories**

```
~/.cache/
├── huggingface/transformers/               # Faster-Whisper Models
│   ├── models--guillaumekln--faster-whisper-tiny/
│   ├── models--guillaumekln--faster-whisper-base/
│   ├── models--guillaumekln--faster-whisper-small/
│   ├── models--guillaumekln--faster-whisper-medium/
│   └── models--guillaumekln--faster-whisper-large/
│
└── whisper/                                # OpenAI-Whisper Models
    ├── tiny.pt
    ├── base.pt
    ├── small.pt
    ├── medium.pt
    └── large.pt

/tmp/                                       # Temporary Audio Files
├── tmpXXXXXX.webm                         # Processing Audio
└── (auto-cleanup after processing)
```

---

## 🔧 Code-Architecture

### **Main Server Components**

```python
# enhanced_final_working.py - Architecture Overview

# 1. Global State Management
current_model = None                        # Loaded Whisper Model
current_model_name = "tiny"                # Active Model Name
connected_clients = set()                  # WebSocket Connections
system_ready = False                       # System Status

# 2. Core Classes
class EnhancedAudioManager:
    """Manages audio devices and test voices"""
    def get_enhanced_audio_devices(self)    # List available devices
    def simulate_enhanced_audio(self)       # Generate test audio
    def set_device(self, index)             # Select audio input

class EnhancedWhisperManager:
    """Manages Whisper models and languages"""
    def load_model(self, name)              # Load Whisper model
    def set_language(self, lang)            # Set recognition language
    def get_languages(self)                 # List supported languages

# 3. Core Functions
def load_whisper_model(model_name)          # Global model loading
async def process_real_audio(audio_data)   # Audio → Text processing
async def websocket_endpoint(websocket)    # WebSocket handler

# 4. HTTP Routes
@app.get("/")                              # Landing page
@app.get("/demo")                          # Interactive demo
@app.get("/api/status")                    # System status
@app.post("/api/load-model")               # HTTP model loading

# 5. WebSocket Routes  
@app.websocket("/ws")                      # Real-time communication
```

### **Frontend Architecture**

```javascript
// Demo Interface Components

// 1. Audio Management
async function loadMicrophones()           // Enumerate audio devices
async function testMicrophone()            // Audio level testing
async function startRecording()            // Begin audio capture
async function stopRecording()             // End audio capture

// 2. WebSocket Communication
function connectWebSocket()                // Establish connection
function sendAudioToServer(audioBlob)      // Transmit audio data
function handleWebSocketMessage(event)     // Process server responses

// 3. Model Management
async function loadWhisperModel()          // Request model loading
function updateModelStatus(status)        // Display loading progress

// 4. UI State Management
function updateStatus(connection, device)  // Update status display
function handleRecordingState(recording)   // Manage recording UI
```

---

## 🔒 Security-Architecture

### **Privacy-by-Design**

```
Data Flow Security:
├── Audio Capture: Browser → Local Server only
├── Processing: 100% local Whisper models
├── Storage: Temporary files, immediate cleanup
├── Network: No external API calls
└── DSGVO: Full compliance, no data leaving system
```

### **Input Validation**

```python
# Audio Data Validation
def validate_audio_input(audio_data, format):
    if not audio_data or len(audio_data) == 0:
        raise ValueError("Empty audio data")
    
    if len(audio_data) > MAX_AUDIO_SIZE:  # 10MB limit
        raise ValueError("Audio too large")
        
    if format not in ['webm', 'wav', 'mp3']:
        raise ValueError("Unsupported format")

# WebSocket Message Validation  
def validate_websocket_message(message):
    required_fields = ['command']
    if not all(field in message for field in required_fields):
        raise ValueError("Missing required fields")
```

### **Resource Protection**

```python
# Model Loading Limits
MAX_CONCURRENT_MODELS = 1
MODEL_LOAD_TIMEOUT = 300  # 5 minutes

# Audio Processing Limits
MAX_AUDIO_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PROCESSING_TIME = 60  # 1 minute
MAX_CONCURRENT_PROCESSES = 5

# WebSocket Limits
MAX_CONNECTED_CLIENTS = 50
MESSAGE_RATE_LIMIT = 100  # per minute
```

---

## ⚡ Performance-Optimierungen

### **Audio Processing**

```python
# Optimized Audio Settings
OPTIMAL_SETTINGS = {
    'sample_rate': 16000,      # Whisper-optimized
    'channels': 1,             # Mono for better performance
    'chunk_duration': 3,       # 3-second chunks
    'encoding': 'opus',        # Efficient compression
    'bitrate': 16000          # Balanced quality/size
}

# Async Processing Pipeline
async def process_audio_pipeline(audio_data):
    # 1. Decode in background thread
    audio_bytes = await asyncio.to_thread(
        base64.b64decode, audio_data
    )
    
    # 2. Whisper processing (CPU-intensive)
    transcript = await asyncio.to_thread(
        whisper_transcribe, audio_bytes
    )
    
    # 3. Cleanup in background
    asyncio.create_task(cleanup_temp_files())
    
    return transcript
```

### **Memory Management**

```python
# Model Caching Strategy
class ModelCache:
    def __init__(self, max_models=2):
        self.cache = {}
        self.max_models = max_models
        
    def get_model(self, name):
        if name in self.cache:
            return self.cache[name]
            
        # Load new model
        if len(self.cache) >= self.max_models:
            # Evict least recently used
            oldest = min(self.cache.keys(), 
                        key=lambda x: self.cache[x].last_used)
            del self.cache[oldest]
            
        model = load_whisper_model(name)
        self.cache[name] = model
        return model
```

### **WebSocket Optimierung**

```python
# Connection Pooling
class WebSocketManager:
    def __init__(self):
        self.connections = set()
        self.message_queue = asyncio.Queue()
        
    async def broadcast(self, message):
        """Efficient broadcast to all clients"""
        if not self.connections:
            return
            
        # Serialize once, send to all
        serialized = json.dumps(message)
        await asyncio.gather(
            *[ws.send_text(serialized) for ws in self.connections],
            return_exceptions=True
        )
```

---

## 🧪 Testing-Architecture

### **Test-Kategorien**

```
tests/
├── unit/
│   ├── test_audio_processing.py          # Audio pipeline tests
│   ├── test_whisper_integration.py       # Model loading tests
│   └── test_websocket_api.py             # WebSocket protocol tests
├── integration/
│   ├── test_full_pipeline.py             # End-to-end tests
│   └── test_model_switching.py           # Model management tests
├── performance/
│   ├── test_load_testing.py              # Concurrent user tests
│   └── test_memory_usage.py              # Resource consumption tests
└── fixtures/
    ├── sample_audio/                     # Test audio files
    └── mock_responses/                   # Mocked API responses
```

### **Test-Setup**

```python
# Test Configuration
@pytest.fixture
def test_audio_data():
    """Provide sample audio for testing"""
    return base64.b64encode(
        open('tests/fixtures/sample_audio/test.webm', 'rb').read()
    ).decode()

@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model for unit tests"""
    mock_model = Mock()
    mock_model.transcribe.return_value = (
        [Mock(text="Test transcript")], 
        Mock(language="en")
    )
    return mock_model

# Performance Tests
def test_audio_processing_latency():
    """Ensure audio processing under 5 seconds"""
    start_time = time.time()
    result = process_audio(test_audio_data)
    latency = time.time() - start_time
    
    assert latency < 5.0
    assert result is not None
```

---

## 🔮 Skalierungsarchitektur

### **Horizontal Scaling (Geplant v0.7.0)**

```
Load Balancer (nginx)
├── WhisperS2T Instance 1 (Port 5000)
├── WhisperS2T Instance 2 (Port 5001)  
├── WhisperS2T Instance 3 (Port 5002)
└── Redis Session Store (WebSocket state)
```

### **Microservices-Migration (Geplant v0.8.0)**

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   API Gateway   │   │  Audio Service  │   │ Whisper Service │
│   (FastAPI)     │◄─►│   (Processing)  │◄─►│   (ML Models)   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  WebSocket      │   │  Queue System   │   │  Model Cache    │
│   Service       │   │    (Redis)      │   │   (Shared)      │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 📊 Monitoring & Observability

### **Metriken (Geplant v0.6.0)**

```python
# Performance Metrics
METRICS = {
    'audio_processing_time': histogram,
    'model_loading_time': histogram,
    'websocket_connections': gauge,
    'transcription_accuracy': gauge,
    'memory_usage': gauge,
    'cpu_usage': gauge
}

# Health Checks
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "whisper_model": current_model_name,
        "connected_clients": len(connected_clients),
        "memory_usage": get_memory_usage(),
        "uptime": get_uptime()
    }
```

### **Logging-Architecture**

```python
# Structured Logging
import structlog

logger = structlog.get_logger()

# Audio Processing Events
logger.info("audio_processing_started", 
           device_id=device_id,
           language=language,
           audio_size=len(audio_data))

logger.info("transcription_completed",
           transcript_length=len(transcript),
           processing_time=duration,
           model=current_model_name)
```

---

## 🔧 Deployment-Optionen

### **Development (Current)**
```bash
# Local Development Server
cd src/webgui/backend
python enhanced_final_working.py
```

### **Docker (Geplant v0.7.0)**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY src/ /app/src/
WORKDIR /app/src/webgui/backend

# Expose port
EXPOSE 5000

# Start server
CMD ["python", "enhanced_final_working.py"]
```

### **Production (Geplant v1.0.0)**
```bash
# Systemd Service
sudo systemctl enable whisper-s2t
sudo systemctl start whisper-s2t

# Nginx Reverse Proxy
upstream whisper_backend {
    server 127.0.0.1:5000;
}

server {
    listen 443 ssl;
    server_name whisper.example.com;
    
    location / {
        proxy_pass http://whisper_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

*Diese Architektur-Dokumentation wird kontinuierlich mit neuen Features und Verbesserungen aktualisiert.*
