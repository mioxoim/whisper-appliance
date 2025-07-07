# Whisper Appliance v0.6.0 - Live Speech Integration

## 🎙️ **NEW: Live Speech Recognition**

Whisper Appliance v0.6.0 now includes **real-time speech recognition** alongside the existing file upload functionality!

### ✨ **Dual Interface Features:**

#### 🎙️ **Live Speech Tab**
- **Real-time transcription** using your microphone
- **Audio visualizer** with live level indicators
- **Continuous transcription** updates
- **Copy/Download** transcribed text
- **Hardware or simulated** audio input support

#### 📁 **Upload File Tab** 
- **Drag & drop** or click to upload audio files
- **Multiple formats** supported (MP3, WAV, M4A, FLAC, OGG)
- **Large file support** up to 100MB
- **Instant transcription** results

#### ⚙️ **System Tab**
- **Audio device** management
- **System status** monitoring  
- **Service restart** capabilities
- **Health checks** and diagnostics

### 🚀 **Installation**

The enhanced app with live speech is automatically included in new deployments:

```bash
# One-liner installation (includes live speech)
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

### 🔧 **Technical Details**

#### **Live Speech Architecture**
- **Audio Input Manager**: Handles microphone capture with fallback to simulation
- **Background Transcription**: Non-blocking worker threads for continuous processing
- **WebSocket-like Updates**: Real-time transcription updates via polling
- **Audio Visualization**: Live audio level indicators

#### **Supported Audio Input**
- **Hardware Microphones**: Automatic detection and configuration
- **USB Audio Devices**: Plug-and-play support
- **Built-in Microphones**: Laptop/desktop integrated audio
- **Simulated Audio**: Fallback mode for testing without hardware

#### **Performance Optimizations**
- **Chunked Processing**: 5-second audio segments for responsive transcription
- **Background Workers**: Non-blocking UI during transcription
- **Audio Buffering**: Efficient memory management for continuous recording
- **Model Caching**: Whisper model loaded once and reused

### 🎯 **User Experience**

#### **Live Speech Workflow**
1. **Open Web Interface**: Navigate to the Live Speech tab
2. **Start Recording**: Click "Start Live Transcription"
3. **Speak Naturally**: Real-time audio visualization shows input levels
4. **Watch Transcription**: Text appears and updates continuously
5. **Copy/Save Results**: Download or copy transcribed text
6. **Stop When Done**: Click "Stop Recording" to finish

#### **File Upload Workflow**
1. **Upload Tab**: Switch to Upload File tab
2. **Select File**: Drag & drop or click to choose audio file
3. **Automatic Processing**: Transcription starts immediately
4. **View Results**: Text appears with copy functionality

### 🛡️ **Security & Privacy**

- **Local Processing**: All audio processing happens on your server
- **No Cloud Dependencies**: Whisper runs entirely offline
- **Memory-Only Audio**: Live audio is not saved to disk
- **User Control**: Recording starts/stops only when user initiates

### 🔧 **Troubleshooting**

#### **Live Speech Issues**
```bash
# Test audio system
curl http://your-container-ip:5000/audio/test

# Check audio devices  
curl http://your-container-ip:5000/audio/status

# Restart service
sudo systemctl restart whisper-appliance
```

#### **Common Solutions**
- **No Microphone**: Uses simulated audio for testing
- **Permissions**: Audio group membership handled automatically
- **Dependencies**: All audio libraries installed by default

### 📊 **API Endpoints**

#### **Live Speech API**
```bash
# Start live transcription
POST /live/start

# Get transcription updates
GET /live/update

# Stop recording
POST /live/stop
```

#### **Audio System API**
```bash
# Audio device status
GET /audio/status

# Test microphone
GET /audio/test
```

#### **File Upload API** (Existing)
```bash
# Transcribe uploaded file
POST /transcribe

# Health check
GET /health
```

### 🎉 **Ready to Use!**

The enhanced Whisper Appliance with live speech recognition is production-ready and deployed automatically with the one-liner installation.

**Access your appliance**: `http://your-container-ip:5000`

**Features work immediately** - no additional configuration required!

---

*Whisper Appliance v0.6.0 - Enterprise-ready speech recognition with live microphone input and file upload capabilities.*