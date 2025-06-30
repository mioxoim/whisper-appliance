#!/bin/bash
# Container Installation Script for WhisperS2T Appliance v0.9.0
# Optimized for Ubuntu 22.04/Debian 12 LXC containers with Intelligent Network SSL Support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (or with sudo)"
    exit 1
fi

print_section "🎤 WhisperS2T Appliance Container Installation v0.9.0"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
else
    print_error "Cannot detect OS version"
    exit 1
fi

print_status "Detected OS: $OS $VERSION"

# Update system
print_section "📦 Updating System Packages"
apt update && apt upgrade -y

# Install system dependencies including SSL support
print_section "🔧 Installing System Dependencies"
apt install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    openssl

# Install Python and development tools
print_section "🐍 Installing Python Development Environment"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel

# Install multimedia libraries
print_section "🎵 Installing Multimedia Libraries"
apt install -y \
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
    libssl-dev

# Create application user
print_section "👤 Creating Application User"
if ! id "whisper" &>/dev/null; then
    useradd -m -s /bin/bash whisper
    print_success "Created user: whisper"
fi

# Create application directory
print_section "📁 Setting up Application Directory"
mkdir -p /opt/whisper-appliance/src
chown -R whisper:whisper /opt/whisper-appliance

# Install Python packages
print_section "📦 Installing Python Dependencies"
pip3 install --upgrade pip
pip3 install \
    torch \
    whisper-openai \
    flask \
    flask-cors \
    flask-socketio \
    flask-swagger-ui \
    gunicorn \
    requests

# Copy application files if they exist locally
if [ -f "./src/main.py" ]; then
    print_section "📁 Installing Enhanced Application Files"
    print_status "Copying enhanced application to container..."
    cp -r ./src/* /opt/whisper-appliance/src/
    print_success "✅ Enhanced WhisperS2T application installed"
else
    print_warning "⚠️  Enhanced app not found, downloading from GitHub..."
    # Download enhanced application from GitHub
    cd /opt/whisper-appliance || exit 1
    wget -O src/main.py "https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/src/main.py" || {
        print_error "Failed to download enhanced application"
        exit 1
    }
    print_success "✅ Downloaded WhisperS2T application from GitHub"
fi

# Auto-generate SSL certificates with intelligent SAN for network access
print_section "🔐 Setting up Intelligent SSL Certificates for Network HTTPS"
print_status "Generating SSL certificate with auto-detected IPs for network access..."

# Copy our intelligent SSL script if available
if [ -f "./create-ssl-cert.sh" ]; then
    print_status "📋 Using enhanced SSL generation script..."
    cp ./create-ssl-cert.sh /opt/whisper-appliance/
    cd /opt/whisper-appliance || exit 1
    chmod +x create-ssl-cert.sh
    ./create-ssl-cert.sh
else
    print_status "🔄 Using integrated intelligent SSL generation..."
    
    # Create SSL directory
    mkdir -p /opt/whisper-appliance/ssl
    cd /opt/whisper-appliance/ssl || exit 1
    
    # Auto-detect IP addresses for SAN
    LOCAL_IPS=$(hostname -I | tr ' ' '\n' | grep -v '^127\.' | grep -v '^::1' | head -5)
    PRIMARY_IP=$(echo "$LOCAL_IPS" | head -1)
    
    # Build SAN list
    SAN_LIST="DNS:localhost,DNS:$(hostname)"
    for ip in $LOCAL_IPS; do
        if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            SAN_LIST="${SAN_LIST},IP:${ip}"
            print_status "📍 Adding IP to certificate: $ip"
        fi
    done
    
    # Use primary IP as CN if available
    CN_VALUE="${PRIMARY_IP:-localhost}"
    print_status "🎯 Certificate CN: $CN_VALUE"
    print_status "🌐 SAN Configuration: $SAN_LIST"
    
    # Generate private key
    openssl genrsa -out whisper-appliance.key 2048
    
    # Generate certificate with SAN (try modern method first)
    if openssl req -help 2>&1 | grep -q "addext"; then
        print_status "✅ Using modern OpenSSL with SAN support"
        openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt \
            -subj "/C=DE/ST=NRW/L=Container/O=WhisperS2T/OU=Production/CN=${CN_VALUE}/emailAddress=admin@whisper-appliance.local" \
            -addext "subjectAltName=${SAN_LIST}"
    else
        # Fallback for older OpenSSL
        print_status "🔄 Using legacy OpenSSL config method"
        cat > ssl.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = DE
ST = NRW
L = Container
O = WhisperS2T
OU = Production
CN = ${CN_VALUE}
emailAddress = admin@whisper-appliance.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = ${SAN_LIST}
EOF
        openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt -config ssl.conf
        rm ssl.conf
    fi
    
    cd /opt/whisper-appliance || exit 1
fi

# Set appropriate permissions
chmod 600 /opt/whisper-appliance/ssl/whisper-appliance.key
chmod 644 /opt/whisper-appliance/ssl/whisper-appliance.crt
chown -R whisper:whisper /opt/whisper-appliance/ssl

print_success "✅ Intelligent SSL certificates generated for network HTTPS access"
print_status "🎙️ Microphone access enabled for ALL detected network IPs"

# Setup Git repository for updates (if we're in a git repo)
if [ -d "./.git" ]; then
    print_section "🔧 Setting up Update Management"
    
    # Copy git repository to application directory
    print_status "Copying git repository for update management..."
    cp -r ./.git /opt/whisper-appliance/
    
    # Copy deploy key if it exists
    if [ -f "./deploy_key_whisper_appliance" ]; then
        print_status "Copying deploy key for GitHub access..."
        cp ./deploy_key_whisper_appliance /opt/whisper-appliance/
        chmod 600 /opt/whisper-appliance/deploy_key_whisper_appliance
        chown whisper:whisper /opt/whisper-appliance/deploy_key_whisper_appliance
    fi
    
    # Set git ownership
    chown -R whisper:whisper /opt/whisper-appliance/.git
fi

# Create systemd service
print_section "⚙️ Creating System Service"
cat > /etc/systemd/system/whisper-appliance.service << 'EOF'
[Unit]
Description=WhisperS2T Appliance v0.9.0 with Intelligent Network SSL Support
After=network.target

[Service]
Type=simple
User=whisper
Group=whisper
WorkingDirectory=/opt/whisper-appliance/src
Environment=PATH=/home/whisper/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/whisper-appliance/src
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Set proper ownership for all files
chown -R whisper:whisper /opt/whisper-appliance

# Enable and start services
print_section "🚀 Starting Services"
systemctl daemon-reload
systemctl enable whisper-appliance
systemctl start whisper-appliance

# Configure firewall if ufw is available
if command -v ufw >/dev/null 2>&1; then
    print_section "🔥 Configuring Firewall"
    ufw --force enable
    ufw allow 5001/tcp comment "WhisperS2T HTTPS"
    ufw allow ssh
fi

# Wait a moment for service to start
sleep 3

# Get container IP and show all possible URLs
CONTAINER_IP=$(hostname -I | awk '{print $1}')
ALL_IPS=$(hostname -I | tr ' ' '\n' | grep -v '^127\.' | grep -v '^::1')

print_section "✅ Installation Complete!"
print_success "WhisperS2T Appliance v0.9.0 installed successfully!"
print_success ""
print_success "🌐 Access URLs (All IPs configured with SSL):"
print_success "   📍 Primary:              https://$CONTAINER_IP:5001"
for ip in $ALL_IPS; do
    if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && [ "$ip" != "$CONTAINER_IP" ]; then
        print_success "   🔗 Additional Network:   https://$ip:5001"
    fi
done
print_success ""
print_success "📚 Essential Endpoints:"
print_success "   🏥 Health Check:         https://$CONTAINER_IP:5001/health"
print_success "   ⚙️ Admin Panel:          https://$CONTAINER_IP:5001/admin"
print_success "   📖 API Documentation:   https://$CONTAINER_IP:5001/docs"
print_success "   🎮 Demo Interface:       https://$CONTAINER_IP:5001/demo"
print_success ""
print_success "🔒 SSL/HTTPS Configuration:"
print_success "   ✅ Intelligent SSL certificate with SAN generated"
print_success "   🎙️ Microphone access enabled via HTTPS on ALL network IPs"
print_success "   🌐 Certificate valid for ALL detected IP addresses"
print_success "   ⚠️  Browser will show security warning (click 'Advanced' → 'Continue')"
print_success ""
print_success "🔧 Service Management:"
print_success "   Status:  systemctl status whisper-appliance"
print_success "   Logs:    journalctl -u whisper-appliance -f"
print_success "   Restart: systemctl restart whisper-appliance"
print_success ""
print_success "📁 Application Directory: /opt/whisper-appliance"
print_success "👤 Application User: whisper"
print_success "🔐 SSL Certificates: /opt/whisper-appliance/ssl/"

print_warning ""
print_warning "⏳ Note: Whisper model download may take a few minutes on first access"
print_warning "    The service will show 'Whisper Model Loading...' until ready"

print_success ""
print_success "🎤 Ready for live speech recognition and audio file transcription!"
print_success "🔒 HTTPS enabled - Microphone access will work in all modern browsers!"

# Final service status check
print_section "🔍 Final Status Check"
if systemctl is-active --quiet whisper-appliance; then
    print_success "✅ WhisperS2T service is running"
else
    print_warning "⚠️  WhisperS2T service may need a moment to start"
    print_status "Check logs with: journalctl -u whisper-appliance -f"
fi
