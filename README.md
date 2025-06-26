# WhisperS2T Appliance - Self-contained Speech-to-Text System

🎤 **Production-ready Speech-to-Text Appliance** mit WhisperS2T Framework

## 🚀 Quick Start

```bash
# Development Environment Setup
make install

# Run Tests
make test

# Start Development Server
make run
```

## 📁 Project Structure

```
whisper-appliance/
├── src/
│   ├── webgui/
│   │   ├── backend/          # FastAPI Application
│   │   └── frontend/         # Svelte Frontend
│   ├── whisper-service/      # WhisperS2T Integration
│   └── system-config/        # Systemd Services
├── build/                    # ISO Build System
├── docs/                     # Documentation
└── tests/                    # Test Suite
```

## 🎯 Goals

- **100% Local Processing** (DSGVO-compliant)
- **Plug & Play Installation** via ISO
- **Real-time Transcription** with WebSocket
- **4GB RAM Optimized** for embedded systems

## 📊 Status

- [x] Repository Setup
- [ ] WhisperS2T Integration
- [ ] FastAPI Backend
- [ ] Live Transcription
- [ ] ISO Build System

---

*Built with ❤️ for privacy-conscious speech recognition*
