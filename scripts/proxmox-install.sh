#!/usr/bin/env bash

# WhisperS2T Proxmox Container Installation Script
# Called by proxmox-helper.sh to install WhisperS2T in LXC container

set -e

# Colors
BL='\033[36m'
RD='\033[0;31m'
GN='\033[1;92m'
CL='\033[m'

function msg_info() { echo -e "${BL}[INFO]${CL} $1"; }
function msg_ok() { echo -e "${GN}[OK]${CL} $1"; }
function msg_error() { echo -e "${RD}[ERROR]${CL} $1"; }

# Create LXC Container
msg_info "Creating LXC Container"

# Download template if not exists
TEMPLATE="ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
TEMPLATE_PATH="/var/lib/vz/template/cache/$TEMPLATE"

if [[ ! -f "$TEMPLATE_PATH" ]]; then
    msg_info "Downloading Ubuntu 22.04 LXC template"
    pveam download local $TEMPLATE
fi

# Create container
pct create $CTID $TEMPLATE_PATH \
    --hostname $PCT_HOSTNAME \
    --cores $PCT_CORES \
    --memory $PCT_MEMORY \
    --rootfs local-lvm:$PCT_DISK_SIZE \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --features nesting=1,keyctl=1 \
    --unprivileged 1 \
    --onboot 1 \
    --start 1

msg_ok "LXC Container created with ID: $CTID"

# Wait for container to be ready
msg_info "Waiting for container to start"
sleep 10

# Install WhisperS2T in container
msg_info "Installing WhisperS2T in container"
pct exec $CTID -- bash -c "
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl git

# Clone WhisperS2T repository
cd /root
git clone https://github.com/GaboCapo/whisper-appliance.git
cd whisper-appliance

# Run container installation
chmod +x install-container.sh
./install-container.sh
"

msg_ok "WhisperS2T installation completed"

# Get container IP
CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
msg_ok "Container IP: $CONTAINER_IP"
msg_ok "WhisperS2T Web Interface: http://$CONTAINER_IP:5000"