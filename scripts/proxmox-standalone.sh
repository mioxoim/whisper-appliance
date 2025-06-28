#!/usr/bin/env bash

# WhisperS2T Proxmox Standalone Installer
# Self-contained installation without GitHub dependency
# Usage: Copy this script to Proxmox and run as root

set -e

# Colors
BL='\033[36m'
RD='\033[0;31m'
GN='\033[1;92m'
YW='\033[33m'
CL='\033[m'

function msg_info() { echo -e "${BL}[INFO]${CL} $1"; }
function msg_ok() { echo -e "${GN}[OK]${CL} $1"; }
function msg_error() { echo -e "${RD}[ERROR]${CL} $1"; }
function msg_warn() { echo -e "${YW}[WARN]${CL} $1"; }

clear
cat <<"EOF"
 __        ___     _                  ____ ____  _____ 
 \ \      / / |__ (_)___ _ __   ___ _ / ___|___ \|_   _|
  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '_\___ \ __) | | |  
   \ V  V / | | | | \__ \ |_) |  __/ |  ___) / __/  | |  
    \_/\_/  |_| |_|_|___/ .__/ \___|_| |____/_____| |_|  
                        |_|                              

WhisperS2T Proxmox LXC Container Creator (Standalone)
===================================================
EOF

# Check if running on Proxmox
if ! command -v pct >/dev/null 2>&1; then
    msg_error "This script must be run on Proxmox VE"
    exit 1
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    msg_error "This script must be run as root"
    exit 1
fi

# Get next available container ID
CTID=$(pvesh get /cluster/nextid)
msg_info "Using Container ID: $CTID"

# Configuration
HOSTNAME="whisper-appliance"
CORES="2"
MEMORY="4096"
DISK_SIZE="20"
TEMPLATE="ubuntu-22.04-standard_22.04-1_amd64.tar.zst"

msg_info "Creating WhisperS2T LXC Container"
msg_info "  ID: $CTID"
msg_info "  Hostname: $HOSTNAME"
msg_info "  CPU: $CORES cores"
msg_info "  RAM: $MEMORY MB"
msg_info "  Disk: $DISK_SIZE GB"

# Download template if needed
TEMPLATE_PATH="/var/lib/vz/template/cache/$TEMPLATE"
if [[ ! -f "$TEMPLATE_PATH" ]]; then
    msg_info "Downloading Ubuntu 22.04 template (this may take a while)..."
    pveam download local $TEMPLATE
    msg_ok "Template downloaded"
fi

# Create container
msg_info "Creating LXC container..."
pct create $CTID $TEMPLATE_PATH \
    --hostname $HOSTNAME \
    --cores $CORES \
    --memory $MEMORY \
    --rootfs local-lvm:$DISK_SIZE \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --features nesting=1,keyctl=1 \
    --unprivileged 1 \
    --onboot 1 \
    --tags "ai,speech,transcription,whisper"

msg_ok "Container created"

# Start container
msg_info "Starting container..."
pct start $CTID
sleep 10
msg_ok "Container started"

# Install WhisperS2T
msg_info "Installing WhisperS2T (this will take 10-15 minutes)..."

# Create installation script inside container
cat > /tmp/install-whisper.sh << 'INSTALL_EOF'
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

export DEBIAN_FRONTEND=noninteractive

print_status "Updating system packages..."
apt-get update >/dev/null 2>&1
apt-get upgrade -y >/dev/null 2>&1

print_status "Installing system dependencies..."
apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release >/dev/null 2>&1

print_status "Installing Python development environment..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel >/dev/null 2>&1

print_status "Installing multimedia libraries..."
apt-get install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libasound2-dev \
    libpulse-dev \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev >/dev/null 2>&1

print_status "Installing web server..."
apt-get install -y nginx >/dev/null 2>&1

print_status "Creating application user..."
if ! id "whisper" &>/dev/null; then
    useradd -m -s /bin/bash whisper
    usermod -aG audio whisper
fi

print_status "Setting up application directories..."
mkdir -p /opt/whisper-appliance/{src,templates,static,models,uploads,logs,config}
chown -R whisper:whisper /opt/whisper-appliance

print_status "Installing Python dependencies..."
sudo -u whisper python3 -m pip install --user --upgrade pip >/dev/null 2>&1
sudo -u whisper python3 -m pip install --user \
    torch torchaudio --index-url https://download.pytorch.org/whl/cpu >/dev/null 2>&1
sudo -u whisper python3 -m pip install --user \
    transformers \
    openai-whisper \
    flask \
    flask-cors \
    gunicorn \
    librosa \
    soundfile \
    pydub \
    requests \
    python-multipart \
    werkzeug \
    psutil \
    sounddevice \
    numpy >/dev/null 2>&1

print_status "Creating WhisperS2T application..."

# Download the enhanced app with live speech from GitHub
curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/src/enhanced_app.py > /opt/whisper-appliance/src/app.py

# Download audio input manager
mkdir -p /opt/whisper-appliance/src/whisper-service
curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/src/whisper-service/audio_input_manager.py > /opt/whisper-appliance/src/whisper-service/audio_input_manager.py

chown -R whisper:whisper /opt/whisper-appliance/src

print_status "Creating systemd service..."
cat > /etc/systemd/system/whisper-appliance.service << "SERVICE_EOF"
[Unit]
Description=WhisperS2T Appliance
After=network.target

[Service]
Type=simple
User=whisper
Group=whisper
WorkingDirectory=/opt/whisper-appliance
Environment=PATH=/home/whisper/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/whisper-appliance
ExecStart=/home/whisper/.local/bin/gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 300 src.app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF

print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/whisper-appliance << "NGINX_EOF"
server {
    listen 5000;
    server_name _;

    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/whisper-appliance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t

print_status "Starting services..."
systemctl daemon-reload
systemctl enable whisper-appliance
systemctl enable nginx

systemctl restart nginx
systemctl start whisper-appliance

if command -v ufw >/dev/null 2>&1; then
    ufw --force enable
    ufw allow 5000/tcp
    ufw allow ssh
fi

print_success "WhisperS2T installation completed!"
INSTALL_EOF

# Copy script to container and make executable
pct push $CTID /tmp/install-whisper.sh /root/install-whisper.sh
pct exec $CTID -- chmod +x /root/install-whisper.sh

# Run installation
msg_info "Executing installation inside container..."
pct exec $CTID -- /root/install-whisper.sh

# Get container IP
msg_info "Getting container IP address..."
sleep 5
CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')

# Success message
clear
cat <<"EOF"
 __        ___     _                  ____ ____  _____ 
 \ \      / / |__ (_)___ _ __   ___ _ / ___|___ \|_   _|
  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '_\___ \ __) | | |  
   \ V  V / | | | | \__ \ |_) |  __/ |  ___) / __/  | |  
    \_/\_/  |_| |_|_|___/ .__/ \___|_| |____/_____| |_|  
                        |_|                              

🎉 INSTALLATION SUCCESSFUL! 🎉
EOF

echo
msg_ok "WhisperS2T LXC Container created successfully!"
msg_ok "Container ID: $CTID"
msg_ok "IP Address: $CONTAINER_IP"
echo
msg_ok "🌐 Web Interface: http://$CONTAINER_IP:5000"
msg_ok "🔧 SSH Access: ssh root@$CONTAINER_IP"
echo
msg_info "Features available:"
msg_info "  • Upload and transcribe audio files"
msg_info "  • Health monitoring endpoint"
msg_info "  • Automatic service management"
echo
msg_warn "Note: First transcription may take longer as Whisper downloads models"
echo
msg_info "Container management commands:"
msg_info "  pct start $CTID    # Start container"
msg_info "  pct stop $CTID     # Stop container"
msg_info "  pct enter $CTID    # Enter container console"
echo