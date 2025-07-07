# 🏗️ System Architecture - OpenAI Whisper Web Interface v1.0.0

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Browser (Client)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Main UI     │  │ Admin Panel │  │ API Docs    │            │
│  │ Port :5001  │  │ /admin      │  │ /docs       │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                           HTTPS (SSL)
                                │
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Application                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Web Routes  │  │ WebSocket   │  │ REST API    │            │
│  │ /           │  │ /admin      │  │ /transcribe │            │
│  │ /admin      │  │ Socket.IO   │  │ /health     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                         Python Modules
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Modular Components                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ ModelManager│  │ LiveSpeech  │  │UploadHandler│            │
│  │ Whisper     │  │ WebSocket   │  │ File Upload │            │
│  │ Management  │  │ Handler     │  │ Processing  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ AdminPanel  │  │ ChatHistory │  │ APIDocs     │            │
│  │ Management  │  │ Database    │  │ Swagger UI  │            │
│  │ Interface   │  │ SQLite      │  │ OpenAPI     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                         AI Processing
                                │
┌─────────────────────────────────────────────────────────────────┐
│                   OpenAI Whisper Engine                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Model Cache │  │ Audio       │  │ Text Output │            │
│  │ ~/.cache/   │  │ Processing  │  │ JSON/Text   │            │
│  │ whisper/    │  │ FFmpeg      │  │ WebSocket   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎤 Audio Processing Pipeline

### **Live Speech Pipeline: Browser → Server → AI**

```
[Microphone] → [getUserMedia] → [MediaRecorder] → [WebM/Opus] 
    ↓
[Base64 Encoding] → [WebSocket] → [Flask-SocketIO] → [Temp File]
    ↓
[OpenAI Whisper] → [Text Response] → [WebSocket Emit] → [Browser Update]
```

### **File Upload Pipeline: Browser → Server → AI**

```
[File Selection] → [FormData] → [HTTP POST /transcribe] 
    ↓
[Flask Upload] → [Secure Filename] → [Temp Storage]
    ↓
[OpenAI Whisper] → [JSON Response] → [Browser Display]
```

---

## 🔧 Technical Stack

### **Frontend Technologies**
- **HTML5 + CSS3**: Modern responsive web interface
- **JavaScript ES6+**: Client-side audio handling and WebSocket communication
- **WebRTC getUserMedia**: Real-time microphone access
- **MediaRecorder API**: Audio capture and encoding
- **Socket.IO Client**: Real-time bidirectional communication
- **Fetch API**: RESTful file upload handling

### **Backend Framework**
- **Flask 3.x**: Core web framework
- **Flask-SocketIO**: WebSocket support for real-time communication
- **Flask-CORS**: Cross-origin resource sharing
- **Flask-Swagger-UI**: API documentation interface
- **Werkzeug**: WSGI utilities and security

### **AI & Audio Processing**
- **OpenAI Whisper**: Core speech-to-text engine
- **LibROSA**: Audio analysis and preprocessing
- **Soundfile**: Audio file I/O operations
- **Pydub**: Audio manipulation and format conversion
- **NumPy**: Numerical computing for audio data

### **System Integration**
- **SQLite**: Chat history and configuration storage
- **SSL/TLS**: HTTPS encryption with auto-generated certificates
- **Systemd**: Service management and auto-restart
- **FFmpeg**: Audio format conversion and processing

---

## 📁 Project Structure

```
whisper-appliance/
├── src/                          # Main application code
│   ├── main.py                   # Flask application entry point
│   ├── main_fallback.py          # Fallback version without Whisper
│   ├── modules/                  # Modular components
│   │   ├── __init__.py          # Module exports
│   │   ├── model_manager.py     # Whisper model management
│   │   ├── live_speech.py       # WebSocket audio handler
│   │   ├── upload_handler.py    # File upload processing
│   │   ├── admin_panel.py       # Management interface
│   │   ├── chat_history.py      # Database operations
│   │   └── api_docs.py          # OpenAPI documentation
│   ├── templates/               # Jinja2 HTML templates
│   │   └── main_interface.html  # Primary web interface
│   ├── static/                  # CSS, JS, images
│   └── requirements.txt         # Python dependencies
├── scripts/                     # Deployment and development
│   ├── proxmox-standalone.sh    # One-line Proxmox deployment
│   ├── dev.sh                   # Development helper
│   ├── debug-container.sh       # Container debugging
│   └── legacy/                  # Deprecated ISO builders
├── ssl/                         # SSL certificates
│   ├── whisper-appliance.crt    # TLS certificate
│   └── whisper-appliance.key    # Private key
├── docs/                        # Documentation
│   ├── legacy/                  # Previous version docs
│   └── *.md                     # Current documentation
└── install-container.sh         # Container installation
```

---

## 🔄 Application Flow

### **1. Application Startup**
```python
# main.py startup sequence
1. Initialize Flask app with CORS and SocketIO
2. Load modular components (ModelManager, ChatHistory, etc.)
3. Attempt to load default Whisper model
4. Register routes and WebSocket handlers
5. Configure SSL certificates if available
6. Start Flask-SocketIO server on port 5001
```

### **2. Web Interface Loading**
```javascript
// Browser-side initialization
1. Load main interface HTML template
2. Initialize WebSocket connection to Flask-SocketIO
3. Request microphone permissions (HTTPS required)
4. Setup file upload drag-and-drop handlers
5. Configure real-time transcription display
```

### **3. Live Speech Recognition**
```python
# WebSocket event flow
@socketio.on('connect')          # Client connects
@socketio.on('start_recording')  # Begin audio capture
@socketio.on('audio_chunk')      # Process audio data
    ↓ OpenAI Whisper Processing
@socketio.emit('transcription_result')  # Send result to client
```

### **4. File Upload Processing**
```python
# HTTP upload flow
@app.route('/transcribe', methods=['POST'])
1. Receive multipart/form-data file
2. Validate file type and size
3. Save to temporary secure location
4. Process with OpenAI Whisper
5. Return JSON response with transcription
6. Cleanup temporary files
```

---

## 🧠 Model Management

### **Whisper Model Lifecycle**
```python
class ModelManager:
    def __init__(self):
        self.current_model = None
        self.available_models = ['tiny', 'base', 'small', 'medium', 'large']
        self.downloaded_models = set()
    
    def load_model(self, model_name):
        # Download if not cached
        # Load into memory
        # Update current_model reference
    
    def get_status(self):
        # Return model info and resource usage
```

### **Model Storage and Caching**
- **Cache Location**: `~/.cache/whisper/`
- **Download Strategy**: Lazy loading on first use
- **Memory Management**: Single model loaded at a time
- **Model Switching**: Graceful unload/reload with status updates

---

## 🔐 Security Architecture

### **SSL/TLS Configuration**
- **Certificate Generation**: Automatic with SAN (Subject Alternative Names)
- **Network Support**: Certificates valid for all local IPs
- **HTTPS Enforcement**: Redirects HTTP to HTTPS
- **Microphone Access**: HTTPS required for WebRTC getUserMedia

### **Input Validation and Sanitization**
```python
# File upload security
- Secure filename generation (Werkzeug)
- File type validation (audio formats only)
- Size limits (100MB default)
- Temporary storage with auto-cleanup

# WebSocket security
- Origin validation
- Data size limits
- Rate limiting per connection
- Automatic disconnect on errors
```

### **System Integration Security**
- **User Isolation**: Runs as dedicated system user
- **Directory Restrictions**: Limited file system access
- **Service Management**: Systemd integration with restart policies
- **Firewall Configuration**: Only necessary ports exposed

---

## 📊 Performance Characteristics

### **Resource Usage by Whisper Model**

| Model  | RAM Usage | VRAM (GPU) | CPU Load | Transcription Speed |
|--------|-----------|------------|----------|-------------------|
| tiny   | ~1GB      | ~1GB       | Low      | 32x realtime     |
| base   | ~1GB      | ~1GB       | Medium   | 16x realtime     |
| small  | ~2GB      | ~2GB       | Medium   | 6x realtime      |
| medium | ~5GB      | ~5GB       | High     | 2x realtime      |
| large  | ~10GB     | ~10GB      | Very High| 1x realtime      |

### **Scalability Considerations**
- **Concurrent Users**: Limited by model memory usage
- **Audio Processing**: Sequential per model instance
- **WebSocket Connections**: Flask-SocketIO handles multiple clients
- **File Storage**: Temporary files cleaned automatically

### **Optimization Strategies**
- **Model Warm-up**: Pre-load model on application start
- **Audio Preprocessing**: Client-side format optimization
- **Result Caching**: Chat history database for repeat requests
- **Resource Monitoring**: Real-time system metrics in admin panel

---

## 🔄 Deployment Architectures

### **1. Proxmox LXC Container (Recommended)**
```
Proxmox Host
└── Ubuntu 22.04 LXC Container
    ├── Systemd Services (whisper-appliance.service)
    ├── Nginx Reverse Proxy (optional)
    ├── SSL Certificates (auto-generated)
    └── Firewall Rules (port 5001)
```

### **2. Docker Container**
```
Docker Host
└── Python 3.11 Container
    ├── Flask Application
    ├── OpenAI Whisper
    ├── Volume Mounts (models, SSL)
    └── Port Mapping (5001:5001)
```

### **3. Local Development**
```
Developer Machine
├── Python Virtual Environment
├── Flask Development Server
├── Local SSL Certificates
└── Direct Model Access
```

---

## 🔧 Configuration Management

### **Environment Variables**
```bash
# Application Configuration
WHISPER_MODEL=base              # Default model to load
FLASK_ENV=production           # Flask environment
MAX_UPLOAD_SIZE=100MB          # File upload limit
DEBUG_MODE=false               # Enable debug logging

# Network Configuration
HTTPS_PORT=5001                # HTTPS port
HTTP_REDIRECT=true             # Redirect HTTP to HTTPS
SSL_CERT_PATH=/path/to/cert    # Custom SSL certificate
SSL_KEY_PATH=/path/to/key      # Custom SSL private key

# Performance Tuning
WORKER_PROCESSES=1             # Flask worker processes
MODEL_CACHE_SIZE=1             # Number of models to cache
AUDIO_CHUNK_SIZE=1024          # WebSocket audio chunk size
```

### **Configuration Files**
- **Flask Config**: Environment variables and defaults
- **SSL Certificates**: Auto-generated or custom provided
- **Systemd Service**: Service definition and startup parameters
- **Chat History**: SQLite database for transcription history

---

## 🔍 Monitoring and Diagnostics

### **Health Check Endpoints**
```python
GET /health                    # Basic service health
GET /api/status               # Detailed system status
GET /admin/check-updates      # Update availability
```

### **Logging Strategy**
- **Application Logs**: Python logging module with timestamps
- **System Logs**: Systemd journal integration
- **Error Tracking**: Structured error logging with context
- **Performance Metrics**: Model loading times and transcription speeds

### **Debugging Tools**
- **Development Helper**: `./scripts/dev.sh` with comprehensive options
- **Container Debug**: `./scripts/debug-container.sh` for system diagnostics
- **Service Status**: Real-time service monitoring in admin panel
- **Model Diagnostics**: Model loading status and memory usage

---

## 🚀 Future Architecture Considerations

### **Scalability Enhancements**
- **GPU Acceleration**: CUDA support for faster transcription
- **Model Serving**: Separate model server for multiple instances
- **Load Balancing**: Multiple container deployment
- **Database Optimization**: PostgreSQL for high-volume chat history

### **Feature Extensions**
- **Multi-language Support**: Dynamic model selection by language
- **User Management**: Authentication and user-specific configurations
- **API Rate Limiting**: Request throttling and usage analytics
- **Batch Processing**: Queue-based bulk audio processing

### **Integration Opportunities**
- **WebRTC Optimization**: Direct peer-to-peer audio streaming
- **Cloud Deployment**: Kubernetes manifest generation
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring Integration**: Prometheus/Grafana metrics export

---

This architecture provides a solid foundation for speech-to-text processing while maintaining flexibility for future enhancements and deployment scenarios.
