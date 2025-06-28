#!/usr/bin/env bash

# WhisperS2T Proxmox One-Liner Helper Script
# Usage: bash -c "$(wget -qLO - https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-oneliner.sh)"

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

WhisperS2T Proxmox LXC Container Creator
========================================
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
pct exec $CTID -- bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive

# Update system
apt-get update >/dev/null 2>&1
apt-get upgrade -y >/dev/null 2>&1

# Install git and curl
apt-get install -y git curl >/dev/null 2>&1

# Clone repository
cd /root
git clone https://github.com/GaboCapo/whisper-appliance.git >/dev/null 2>&1
cd whisper-appliance

# Run installation
chmod +x install-container.sh
./install-container.sh
'

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
msg_info "  • Web-based update management"
msg_info "  • Automatic GitHub updates"
msg_info "  • Health monitoring and system management"
echo
msg_warn "Note: First transcription may take longer as Whisper downloads models"
echo