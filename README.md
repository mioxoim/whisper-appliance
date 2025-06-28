# 🎤 Enhanced WhisperS2T Appliance v0.6.0

**Advanced Speech-to-Text Appliance powered by OpenAI Whisper**

## ⚠️ **DEVELOPMENT STATUS WARNING**

> **🚧 ACTIVE DEVELOPMENT - NOT PRODUCTION READY**  
> This project is under heavy development and should **NOT** be used in production environments without thorough testing and security auditing. 
> 
> **🔍 SECURITY NOTICE:**  
> - **Code Audit Required:** Please audit all code before production deployment
> - **Test Environment Only:** Use only in isolated, non-critical environments  
> - **No Warranty:** See [LICENSE](LICENSE) for complete disclaimer
> - **Changes Tracked:** See [CHANGELOG.md](CHANGELOG.md) for all modifications
> 
> **📊 Current Status:** Container deployment functional, but expect breaking changes

---

## 🎯 **NEW: Container-First Deployment**

**Priority Focus:** Proxmox LXC Container deployment for immediate production use

### ⚡ One-Liner Installation (Easiest)

**For Proxmox VE users - Working Standalone Version:**
```bash
# One command setup - run on Proxmox host as root:
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```
**⏱️ Total time: 10-15 minutes** - Creates container, installs everything, ready to use!

### 🔧 Manual Container Setup (More Control)

```bash
# 1. Create Ubuntu 22.04 LXC container in Proxmox
# 2. SSH into container
ssh root@container-ip

# 3. Clone and install  
git clone https://github.com/GaboCapo/whisper-appliance.git
cd whisper-appliance
./install-container.sh

# 4. Access web interface
# http://container-ip:5000
```

**📖 Detailed Guides:** 
- **[One-Liner Method](PROXMOX-HELPER-SCRIPTS.md)** - Easiest deployment
- **[Manual Method](PROXMOX-QUICKSTART.md)** - Step-by-step guide

---

## 🔄 **Strategy Change in v0.6.0**

### **Why Container-First?**

**Previous Approach (v0.5.0):** Fedora ISO builds with livemedia-creator
- ❌ 15+ hour build times
- ❌ Complex library conflicts  
- ❌ Unreliable Mock environments
- ❌ Difficult to test and iterate

**New Approach (v0.6.0):** Proxmox LXC Containers
- ✅ 10-minute deployment
- ✅ Easy testing and updates
- ✅ Resource efficient
- ✅ Production-ready reliability
- ✅ Git-based deployment workflow

### **Deployment Strategy**
1. **Phase 1 (Current):** Proxmox LXC Container - ✅ **READY**
2. **Phase 2 (Future):** Debian-based Live ISO  
3. **Phase 3 (Future):** Dedicated hardware appliance

---

## 🏗️ System Architecture

### **Container-Based Stack**
```
┌─────────────────────────────────────────┐
│     Web Interface (Port 5000)          │  ← Upload & Transcription UI
├─────────────────────────────────────────┤
│        Nginx Reverse Proxy             │  ← SSL termination & routing
├─────────────────────────────────────────┤
│        Flask Application               │  ← Core application logic
├─────────────────────────────────────────┤
│        Whisper Model Engine            │  ← OpenAI Whisper processing
├─────────────────────────────────────────┤
│        System Services                 │  ← Systemd integration
└─────────────────────────────────────────┘
```

### **Features in v0.6.0**
- ✅ **Web File Upload Interface** - Drag & drop audio transcription
- ✅ **Health Check Endpoints** - `/health` for monitoring
- ✅ **Systemd Service Integration** - Auto-start and management
- ✅ **Nginx Reverse Proxy** - Production-grade web serving
- ✅ **Security Configuration** - Firewall setup and user isolation
- ✅ **Resource Optimization** - Memory and CPU tuning
- ✅ **Logging & Monitoring** - Structured logs and service status

---

## 📦 Container Requirements

### **Proxmox Host**
- Proxmox VE 7.0+
- Bridge network interface (vmbr0)

### **Container Specs**
- **Base:** Ubuntu 22.04 LTS (recommended) or Debian 12
- **CPU:** 2 cores minimum
- **RAM:** 4GB minimum (8GB for large models)
- **Storage:** 20GB minimum (50GB recommended)
- **Features:** Nesting enabled

### **Automatic Dependencies**
- Python 3.10+ with pip
- FFmpeg and audio libraries
- Build tools and development headers
- Nginx web server
- Systemd service management

---

## 🚀 Deployment Options

### **1. Proxmox LXC Container (Recommended)**
```bash
# Quick deployment in existing container
./install-container.sh
```
**Time:** ~10 minutes  
**Guide:** [PROXMOX-QUICKSTART.md](PROXMOX-QUICKSTART.md)

### **2. Docker Container**
```bash
# Alternative for non-Proxmox environments
docker build -t whisper-appliance .
docker run -p 5000:5000 whisper-appliance
```

### **3. Manual Installation**
```bash
# Development setup
./dev.sh dev start
```

---

## 🎤 Usage

### **Web Interface**
1. **Access:** `http://container-ip:5000`
2. **Upload:** Drag & drop audio file (MP3, WAV, M4A, etc.)
3. **Transcribe:** Automatic processing with OpenAI Whisper
4. **Result:** Text transcription displayed in browser

### **API Endpoint**
```bash
# Direct API access
curl -X POST -F "audio=@file.wav" http://container-ip:5000/transcribe
```

### **Health Monitoring**
```bash
# Service status
curl http://container-ip:5000/health

# System status
systemctl status whisper-appliance
journalctl -u whisper-appliance -f
```

---

## 🔧 Configuration

### **Environment Variables**
```bash
# Model selection
export WHISPER_MODEL=base  # base, small, medium, large

# Performance tuning  
export WORKER_PROCESSES=2
export MAX_UPLOAD_SIZE=100MB
```

### **System Service**
```bash
# Service management
systemctl start whisper-appliance
systemctl stop whisper-appliance
systemctl restart whisper-appliance
systemctl enable whisper-appliance
```

---

## 📊 Resource Requirements by Model

| Model | RAM Usage | CPU Load | Transcription Speed |
|-------|-----------|----------|-------------------|
| base  | ~1GB      | Medium   | 1x realtime      |
| small | ~2GB      | Medium   | 2x realtime      |
| medium| ~5GB      | High     | 3x realtime      |
| large | ~10GB     | High     | 5x realtime      |

---

## 🛠 Troubleshooting

### **Service Issues**
```bash
# Check service status
systemctl status whisper-appliance

# View logs
journalctl -u whisper-appliance -n 50

# Restart service
systemctl restart whisper-appliance
```

### **Model Loading Issues**
```bash
# Test Whisper installation
sudo -u whisper python3 -c "import whisper; print('OK')"

# Manually load model
sudo -u whisper python3 -c "import whisper; whisper.load_model('base')"
```

### **Network Issues**
```bash
# Check port binding
netstat -tlnp | grep 5000

# Test connectivity
curl -I http://localhost:5000/health
```

---

## 📚 Documentation

- **[One-Liner Deployment](PROXMOX-HELPER-SCRIPTS.md)** - Single command installation
- **[Manual Setup Guide](PROXMOX-QUICKSTART.md)** - Step-by-step deployment
- **[Container Deployment](CONTAINER-DEPLOYMENT.md)** - Detailed setup guide
- **[Update Management](UPDATE-MANAGEMENT.md)** - Automated updates and rollbacks
- **[CI/CD Pipeline](CI-CD-DOCUMENTATION.md)** - Quality assurance and testing
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Development](QUICKSTART.md)** - Development environment setup
- **[Changelog](CHANGELOG.md)** - Version history and changes

---

## 🎯 Future Roadmap

### **v0.6.x - Container Optimization**
- [ ] Multi-model support (base, small, medium, large)
- [ ] GPU acceleration support
- [ ] Container template packaging
- [ ] Performance monitoring dashboard

### **v0.7.x - Debian ISO Build**
- [ ] Switch to Debian stable base
- [ ] Standard live-build toolchain  
- [ ] Reliable ISO generation
- [ ] Hardware compatibility testing

### **v0.8.x - Production Features**
- [ ] HTTPS/TLS support
- [ ] User authentication
- [ ] Batch processing queues
- [ ] API rate limiting
- [ ] Backup and restore

---

## 🤖 Continuous Integration & Quality Assurance

WhisperS2T uses **GitHub Actions** for automated testing and quality assurance to ensure reliable, professional-grade code:

### 🔍 **Why GitHub Actions?**
- **Automated Quality Checks**: Every code change is automatically tested
- **Prevent Breaking Changes**: Catch issues before they reach production
- **Community Contributions**: Ensure all pull requests meet quality standards
- **Professional Standards**: Maintain enterprise-grade code quality

### ⚙️ **CI/CD Pipeline Jobs**

| Job | Purpose | What it Checks |
|-----|---------|----------------|
| **🐍 Lint** | Code Quality | Python syntax, PEP 8 compliance, import sorting |
| **🔧 ShellCheck** | Script Quality | Shell script best practices, syntax validation |
| **📦 Container Test** | Deployment | Installation scripts, file completeness |
| **📚 Documentation** | Completeness | Required docs exist, version consistency |
| **🛡️ Security** | Safety | No secrets committed, secure configurations |

### 🎯 **Benefits for WhisperS2T**
- **🚀 Reliable Deployments**: Installation scripts are tested before release
- **🔒 Security**: Automatic scanning for potential security issues
- **📝 Documentation**: Ensures guides stay up-to-date with code changes
- **🤝 Community-Ready**: Contributors get immediate feedback on code quality
- **⚡ Fast Feedback**: Know within minutes if changes break anything

### 🏆 **Quality Standards Enforced**
- **Python Code**: Black formatting, flake8 linting, import sorting
- **Shell Scripts**: ShellCheck validation for all .sh files
- **Documentation**: Version consistency, completeness checks
- **Security**: No hardcoded secrets, safe file permissions
- **Dependencies**: Proper package management and compatibility

The green ✅ badges you see on GitHub mean all quality checks pass - your deployment will be reliable!

**📖 Detailed Guide:** [CI/CD Documentation](CI-CD-DOCUMENTATION.md)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

**🎉 Ready to deploy? Start with the [Proxmox Quick Start](PROXMOX-QUICKSTART.md)!**