#!/usr/bin/env bash

# WhisperS2T Proxmox Standalone Installer - Git-based Version
# Installs WhisperS2T as a Git repository for update support

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
 __    __ _     _                      _               _ _                      
/ / /\ \ \ |__ (_)___ _ __   ___ _ __ /_\  _ __  _ __ | (_) __ _ _ __   ___ ___ 
\ \/  \/ / '_ \| / __| '_ \ / _ \ '__//_\\| '_ \| '_ \| | |/ _` | '_ \ / __/ _ \
 \  /\  /| | | | \__ \ |_) |  __/ | /  _  \ |_) | |_) | | | (_| | | | | (_|  __/
  \/  \/ |_| |_|_|___/ .__/ \___|_| \_/ \_/ .__/| .__/|_|_|\__,_|_| |_|\___\___|
                     |_|                  |_|   |_|                             


WhisperS2T Proxmox LXC Container Creator (Git-based)
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
    msg_info "Downloading Ubuntu 22.04 template..."
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

# Colors for nested script
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

print_status() { echo -e "${GREEN}[*]${NC} $1"; }
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
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    libsndfile1-dev \
    openssl >/dev/null 2>&1

print_status "Creating application user..."
if ! id "whisper" &>/dev/null; then
    useradd -m -s /bin/bash whisper
    usermod -aG audio whisper
fi

print_status "Cloning WhisperS2T repository..."
cd /opt
git clone https://github.com/GaboCapo/whisper-appliance.git
# Add /opt/whisper-appliance to safe directories
git config --global --add safe.directory /opt/whisper-appliance
chown -R whisper:whisper /opt/whisper-appliance

print_status "Installing Python dependencies..."
cd /opt/whisper-appliance
sudo -u whisper python3 -m pip install --user --upgrade pip >/dev/null 2>&1
sudo -u whisper python3 -m pip install --user -r requirements.txt >/dev/null 2>&1

print_status "Creating SSL certificates..."
mkdir -p /opt/whisper-appliance/ssl
cd /opt/whisper-appliance/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout whisper-appliance.key \
    -out whisper-appliance.crt \
    -subj "/C=US/ST=State/L=City/O=WhisperS2T/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" >/dev/null 2>&1
chown -R whisper:whisper /opt/whisper-appliance/ssl

print_status "Creating systemd service..."
cat > /etc/systemd/system/whisper-appliance.service << 'SERVICE_EOF'
[Unit]
Description=WhisperS2T Speech-to-Text Service
After=network.target

[Service]
Type=simple
User=whisper
Group=whisper
WorkingDirectory=/opt/whisper-appliance
Environment="PATH=/home/whisper/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /opt/whisper-appliance/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

print_status "Enabling and starting service..."
systemctl daemon-reload
systemctl enable whisper-appliance.service
systemctl start whisper-appliance.service

print_status "Waiting for service to start..."
sleep 10

if systemctl is-active --quiet whisper-appliance.service; then
    print_status "✅ WhisperS2T installed successfully!"
    echo ""
    echo "Service Status:"
    systemctl status whisper-appliance.service --no-pager | head -10
    echo ""
    
    # Get container IP
    IP=$(hostname -I | awk '{print $1}')
    echo "Access WhisperS2T at:"
    echo "  🌐 Main Interface: https://$IP:5001"
    echo "  ⚙️ Admin Panel: https://$IP:5001/admin"
    echo "  📚 API Docs: https://$IP:5001/docs"
    echo ""
    echo "Note: Accept the self-signed certificate warning in your browser"
else
    print_error "Service failed to start. Check logs with: journalctl -u whisper-appliance -n 50"
    exit 1
fi
INSTALL_EOF

# Execute installation script in container
pct push $CTID /tmp/install-whisper.sh /tmp/install-whisper.sh
pct exec $CTID -- chmod +x /tmp/install-whisper.sh
pct exec $CTID -- /tmp/install-whisper.sh

# Get container IP
CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')

msg_ok "WhisperS2T installation complete!"
echo ""
msg_info "Container Details:"
msg_info "  ID: $CTID"
msg_info "  IP: $CONTAINER_IP"
msg_info "  Main Interface: https://$CONTAINER_IP:5001"
msg_info "  Admin Panel: https://$CONTAINER_IP:5001/admin"
msg_info "  API Docs: https://$CONTAINER_IP:5001/docs"
echo ""
msg_info "To update WhisperS2T in the future:"
msg_info "  1. Enter container: pct enter $CTID"
msg_info "  2. Run: cd /opt/whisper-appliance && git pull && systemctl restart whisper-appliance"
echo ""
msg_ok "Enjoy WhisperS2T!"
