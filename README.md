# 🎤 Enhanced WhisperS2T Appliance v1.0.0

## ⚠️ DEVELOPMENT STATUS

**🚧 This project is currently under active development and NOT production-ready.**

- Features may change without notice
- Breaking changes possible between versions  
- Use for testing and development purposes only
- No stability guarantees for current release

---

**Modern web interface for OpenAI Whisper speech-to-text with Docker and Proxmox support**

[![Docker Support](https://img.shields.io/badge/docker-supported-blue)](https://docs.docker.com/)
[![Proxmox Ready](https://img.shields.io/badge/proxmox-ready-green)](https://www.proxmox.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ⚡ Quick Start

### 🚀 One-Line Proxmox Deployment (Recommended)

Deploy a complete LXC container with web interface in 10-15 minutes:

```bash
# Run on Proxmox host as root:
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

**What this does:**
- ✅ Creates Ubuntu 22.04 LXC container automatically
- ✅ Installs OpenAI Whisper + web interface
- ✅ Configures HTTPS with SSL certificates
- ✅ Sets up systemd services
- ✅ Provides web interface URL

### 🐳 Docker Deployment

**Quick Start:**
```bash
# Clone repository
git clone https://github.com/GaboCapo/whisper-appliance.git
cd whisper-appliance

# Start with Docker Compose
docker-compose up -d

# Access web interface
open https://localhost:5001
```

**Development Mode:**
```bash
# Start development container with hot-reload
docker-compose -f docker-compose.dev.yml up -d

# Test fallback mode
docker-compose -f docker-compose.dev.yml --profile fallback up -d

# Access development interface
open https://localhost:5001
```

**Testing & Management:**
```bash
# Quick test all features
./scripts/docker-test.sh test

# View container logs
./scripts/docker-test.sh logs

# Stop containers
./scripts/docker-test.sh stop

# Complete cleanup
./scripts/docker-test.sh clean
```

### 💻 Local Development

**Full Development Setup:**
```bash
# Clone and setup
git clone https://github.com/GaboCapo/whisper-appliance.git
cd whisper-appliance

# Install full development dependencies
pip3 install -r requirements-dev.txt

# Start development server
cd src && python3 main.py
```

**Lightweight Development (without ML dependencies):**
```bash
# For quick web interface testing
pip3 install -r requirements-lite.txt

# Start fallback server (no AI transcription)
cd src && python3 main_fallback.py
```

**Requirements Files:**
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development with testing tools
- `requirements-lite.txt` - Web interface only (no Whisper)
- `requirements-container.txt` - Container-optimized versions

## 🎯 Features

- **🎙️ Live Speech Recognition** - Real-time microphone transcription via WebSocket
- **📁 File Upload Support** - Drag & drop audio files (MP3, WAV, M4A, etc.)
- **🔒 HTTPS Ready** - Built-in SSL certificate generation
- **🌐 Network Access** - Works across your local network
- **⚙️ Admin Panel** - Model management and system monitoring
- **📚 API Documentation** - RESTful API with Swagger UI
- **🔄 Auto-Updates** - GitHub-based update system
- **📊 Health Monitoring** - Service status and diagnostics

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│     Web Interface (HTTPS:5001)         │  ← Upload & Live Speech UI
├─────────────────────────────────────────┤
│        Flask Application               │  ← Core application logic
├─────────────────────────────────────────┤
│        OpenAI Whisper Engine           │  ← AI transcription processing
├─────────────────────────────────────────┤
│        Systemd Services                │  ← Auto-start and management
└─────────────────────────────────────────┘
```

## 📋 Requirements

### **Proxmox LXC (Recommended)**
- Proxmox VE 7.0+
- 2 CPU cores, 4GB RAM, 20GB storage
- Ubuntu 22.04 LXC template

### **Docker**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM available

### **Local Installation**
- Python 3.8+
- FFmpeg
- 4GB RAM

## 🎤 Usage

### **Web Interface**
1. **Access:** Navigate to `https://your-ip:5001`
2. **Live Speech:** Click microphone button, speak naturally
3. **File Upload:** Drag & drop audio files
4. **Real-time Results:** See transcription appear instantly

### **API Access**
```bash
# Transcribe audio file
curl -X POST -F "audio=@file.wav" https://your-ip:5001/transcribe

# Health check
curl https://your-ip:5001/health

# API documentation
open https://your-ip:5001/docs
```

## ⚙️ Model Management

The interface supports multiple OpenAI Whisper models:

| Model | RAM Usage | Speed | Quality |
|-------|-----------|-------|---------|
| tiny  | ~1GB      | 32x   | Good    |
| base  | ~1GB      | 16x   | Better  |
| small | ~2GB      | 6x    | Better  |
| medium| ~5GB      | 2x    | Best    |
| large | ~10GB     | 1x    | Best    |

Models are downloaded automatically on first use or can be pre-installed via the admin panel.

## 🔧 Configuration

### **Environment Variables**
```bash
# Model selection
WHISPER_MODEL=base

# Performance tuning
MAX_UPLOAD_SIZE=100MB
WORKER_PROCESSES=2

# Network configuration
HTTPS_PORT=5001
HTTP_REDIRECT=true
```

### **SSL Certificates**
```bash
# Generate certificates for network access
./create-ssl-cert.sh

# Certificates support multiple IPs automatically
# Includes localhost, hostname, and all network IPs
```

## 🛠️ Development

### **Development Server**
```bash
# Start development environment
./scripts/dev.sh dev start

# Run tests
./scripts/dev.sh test

# Build container
./scripts/dev.sh container build
```

### **Project Structure**
```
whisper-appliance/
├── src/                    # Main application
│   ├── main.py            # Flask application
│   ├── modules/           # Modular components
│   └── templates/         # Web interface
├── scripts/               # Deployment & development
│   ├── proxmox-standalone.sh
│   ├── dev.sh
│   └── debug-container.sh
├── docs/                  # Documentation
└── ssl/                   # SSL certificates
```

## 📊 Monitoring

### **Service Status**
```bash
# Check service health
systemctl status whisper-appliance

# View logs
journalctl -u whisper-appliance -f

# Web health check
curl https://localhost:5001/health
```

### **Performance Monitoring**
- CPU and memory usage in admin panel
- Transcription speed metrics
- Service uptime tracking
- Error rate monitoring

## 🔄 Updates

### **Automatic Updates**
```bash
# Check for updates
curl https://your-ip:5001/admin/check-updates

# Perform update (via web interface)
# Or manually:
./auto-update.sh
```

### **Manual Updates**
```bash
cd whisper-appliance
git pull origin main
pip3 install -r requirements.txt
systemctl restart whisper-appliance
```

## 🚨 Troubleshooting

### **Service Issues**
```bash
# Restart service
systemctl restart whisper-appliance

# Check logs
journalctl -u whisper-appliance -n 50

# Test dependencies
python3 -c "import whisper; print('OK')"
```

### **Network Access Issues**
```bash
# Check SSL certificates
openssl x509 -in ssl/whisper-appliance.crt -text -noout

# Test connectivity
curl -k https://localhost:5001/health

# Regenerate certificates
./create-ssl-cert.sh
```

### **Model Loading Issues**
```bash
# Clear model cache
rm -rf ~/.cache/whisper/

# Manually download model
python3 -c "import whisper; whisper.load_model('base')"
```

## 📚 Documentation

- **[Proxmox Deployment Guide](PROXMOX-QUICKSTART.md)** - Step-by-step container setup
- **[Container Installation](CONTAINER-DEPLOYMENT.md)** - Manual container deployment
- **[Update Management](UPDATE-MANAGEMENT.md)** - Automated updates and rollbacks
- **[API Documentation](docs/api.md)** - RESTful API reference
- **[Contributing Guide](CONTRIBUTING.md)** - Development guidelines
- **[Legacy Documentation](docs/legacy/)** - Previous version docs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Fork and clone
git clone https://github.com/yourusername/whisper-appliance.git
cd whisper-appliance

# Install development dependencies
pip3 install -r requirements-dev.txt

# Start development server
./scripts/dev.sh dev start
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for the Whisper speech recognition model
- **tteck/community-scripts** for Proxmox deployment inspiration
- **Flask & SocketIO** for the web framework
- **Contributors** who help improve this project

---

**🎉 Ready to start? Try the [one-line Proxmox deployment](#-one-line-proxmox-deployment-recommended)!**
# 🎤 OpenAI Whisper Web Interface v0.10.0

**Modern web interface for OpenAI Whisper speech-to-text with Docker and Proxmox support**