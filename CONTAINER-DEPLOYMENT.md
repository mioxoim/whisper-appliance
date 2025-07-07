# Whisper Appliance Appliance - Proxmox Container Deployment

## 🎯 Container-First Approach

This repository is optimized for **Proxmox LXC Container** deployment, providing a fast and reliable way to run the Whisper Appliance Appliance.

## 📋 Prerequisites

### Proxmox Host Requirements
- **Proxmox VE 7.0+**
- **Minimum Resources per Container:**
  - CPU: 2 cores
  - RAM: 4GB (8GB recommended for larger models)
  - Storage: 20GB (50GB recommended)
  - Network: Bridge interface

### Base Container Requirements
- **Ubuntu 22.04 LTS** or **Debian 12** LXC template
- **Privileged container** (required for GPU access if needed)
- **SSH access enabled**

## 🚀 Quick Deployment

### Step 1: Create Proxmox Container

```bash
# In Proxmox web interface or CLI:
# 1. Download Ubuntu 22.04 LTS template
# 2. Create new container with:
#    - Template: Ubuntu 22.04
#    - CPU: 2 cores  
#    - Memory: 4096MB
#    - Storage: 20GB
#    - Network: vmbr0
#    - Enable SSH
```

### Step 2: Deploy Whisper Appliance

```bash
# SSH into the container
ssh root@your-container-ip

# Clone and install
git clone https://github.com/yourusername/whisper-appliance.git
cd whisper-appliance
./install-container.sh

# Start the application
./dev.sh dev start
```

### Step 3: Access Web Interface

- **Web UI:** `http://your-container-ip:5000`
- **API:** `http://your-container-ip:5000/api`

## 📦 System Dependencies

### Core System Packages
```bash
# Build tools
build-essential
cmake
git
curl
wget

# Python ecosystem
python3
python3-pip
python3-venv
python3-dev

# Audio/Video processing
ffmpeg
libavcodec-dev
libavformat-dev
libavutil-dev
libswscale-dev
libswresample-dev

# Audio libraries
libasound2-dev
libpulse-dev
libsndfile1-dev

# Web server
nginx
```

### Python Dependencies
```bash
# AI/ML Core
torch>=2.0.0
torchaudio>=2.0.0
transformers>=4.30.0
openai-whisper>=20230314

# Web Framework
flask>=2.3.0
flask-cors>=4.0.0
gunicorn>=20.1.0

# Audio Processing
librosa>=0.10.0
soundfile>=0.12.0
pydub>=0.25.0

# Utilities
requests>=2.30.0
python-multipart>=0.0.6
```

## 🛠 Container Optimization

### Resource Limits
```bash
# /etc/pve/lxc/CTID.conf additions:
cores: 2
memory: 4096
swap: 2048

# Optional: GPU passthrough for acceleration
# lxc.cgroup2.devices.allow: c 226:* rwm
# lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
```

### Performance Tuning
```bash
# CPU Governor
echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Memory optimization
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
```

## 📁 Directory Structure

```
whisper-appliance/
├── src/                    # Application source code
├── templates/             # HTML templates
├── static/               # CSS, JS, assets
├── models/               # Whisper model cache
├── uploads/              # Temporary audio files
├── logs/                 # Application logs
├── config/               # Configuration files
├── scripts/              # Deployment scripts
├── container/            # Container-specific files
│   ├── install-container.sh
│   ├── nginx.conf
│   ├── systemd/
│   └── requirements.txt
└── dev.sh               # Main development script
```

## 🔧 Configuration

### Environment Variables
```bash
# /etc/environment or ~/.bashrc
export WHISPER_MODEL=base
export WHISPER_DEVICE=cpu
export FLASK_ENV=production
export WORKER_PROCESSES=2
export MAX_UPLOAD_SIZE=100MB
```

### Service Configuration
```bash
# Systemd service for auto-start
/etc/systemd/system/whisper-appliance.service

# Nginx reverse proxy
/etc/nginx/sites-available/whisper-appliance
```

## 🐳 Alternative: Docker Deployment

For non-Proxmox environments:

```bash
# Build and run with Docker
docker build -t whisper-appliance .
docker run -p 5000:5000 -v whisper-models:/app/models whisper-appliance
```

## 📊 Monitoring

### Health Checks
- **Endpoint:** `http://container-ip:5000/health`
- **Metrics:** `http://container-ip:5000/metrics`
- **Logs:** `journalctl -u whisper-appliance -f`

### Resource Monitoring
```bash
# Container resource usage
pct list
pct status CTID

# Application monitoring
htop
iotop
nethogs
```

## 🔐 Security

### Container Security
- Regular security updates: `apt update && apt upgrade`
- Firewall configuration: `ufw enable && ufw allow 5000`
- SSH key authentication recommended
- Regular backup of configuration

### Application Security
- Rate limiting on API endpoints
- File upload validation
- Secure temporary file handling
- HTTPS termination at proxy level

## 🧪 Testing

```bash
# Quick functionality test
curl -X POST -F "audio=@test.wav" http://container-ip:5000/transcribe

# Load testing
./scripts/load-test.sh

# Health monitoring
./scripts/monitor.sh
```

## 📚 Documentation

- **API Documentation:** `/docs` endpoint
- **Configuration Guide:** `docs/configuration.md`
- **Troubleshooting:** `docs/troubleshooting.md`
- **Performance Tuning:** `docs/performance.md`

## 🎯 Future: Debian ISO Build

Once container deployment is stable, we'll create a dedicated Debian-based Live ISO:

- **Base:** Debian 12 stable
- **Tools:** Standard `live-build` instead of Fedora's complex livemedia-creator
- **Target:** Dedicated hardware appliances
- **Benefits:** More reliable than Fedora Rawhide approach

---

**Ready to deploy? Start with the container approach for immediate results!** 🚀
