#!/bin/bash
# Fix WhisperS2T service for local development setup

set -e

echo "🔧 Fixing WhisperS2T service for local development..."

# Check if running as commander user
if [ "$USER" != "commander" ]; then
    echo "❌ Please run as commander user"
    exit 1
fi

# Current working directory
CURRENT_DIR="$(pwd)"
if [[ ! "$CURRENT_DIR" == *"whisper-appliance"* ]]; then
    cd /home/commander/Code/whisper-appliance
    CURRENT_DIR="$(pwd)"
fi

echo "📁 Working in: $CURRENT_DIR"

# Stop and remove old service if exists
if systemctl is-active --quiet whisper-appliance 2>/dev/null; then
    sudo systemctl stop whisper-appliance
    echo "🛑 Stopped old service"
fi

if systemctl is-enabled --quiet whisper-appliance 2>/dev/null; then
    sudo systemctl disable whisper-appliance
    echo "🔄 Disabled old service"
fi

if [ -f "/etc/systemd/system/whisper-appliance.service" ]; then
    sudo rm /etc/systemd/system/whisper-appliance.service
    echo "🗑️ Removed old service file"
fi

# Create new systemd service for local development
echo "🏗️ Creating local development service..."
sudo tee /etc/systemd/system/whisper-appliance.service > /dev/null << EOF
[Unit]
Description=WhisperS2T Appliance (Local Development)
After=network.target

[Service]
Type=simple
User=commander
Group=commander
WorkingDirectory=$CURRENT_DIR/src
Environment=PATH=/home/commander/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/src/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Check if SSL certificates exist, create if not
SSL_DIR="$CURRENT_DIR/ssl"
if [ ! -f "$SSL_DIR/whisper-appliance.crt" ] || [ ! -f "$SSL_DIR/whisper-appliance.key" ]; then
    echo "🔒 Creating SSL certificates..."
    mkdir -p "$SSL_DIR"
    cd "$SSL_DIR"
    
    # Auto-detect IP addresses for SAN
    LOCAL_IPS=$(hostname -I | tr ' ' '\n' | grep -v '^127\.' | grep -v '^::1' | head -5)
    PRIMARY_IP=$(echo "$LOCAL_IPS" | head -1)
    
    # Build SAN list
    SAN_LIST="DNS:localhost,DNS:$(hostname)"
    for ip in $LOCAL_IPS; do
        if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            SAN_LIST="${SAN_LIST},IP:${ip}"
            echo "📍 Adding IP to SSL certificate: $ip"
        fi
    done
    
    CN_VALUE="${PRIMARY_IP:-localhost}"
    echo "🎯 Certificate CN: $CN_VALUE"
    
    # Generate private key
    openssl genrsa -out whisper-appliance.key 2048
    
    # Generate certificate with SAN
    if openssl req -help 2>&1 | grep -q "addext"; then
        openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt \
            -subj "/C=DE/ST=NRW/L=Development/O=WhisperS2T/OU=Local/CN=${CN_VALUE}/emailAddress=dev@whisper-appliance.local" \
            -addext "subjectAltName=${SAN_LIST}"
    else
        cat > ssl.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = DE
ST = NRW
L = Development
O = WhisperS2T
OU = Local
CN = ${CN_VALUE}
emailAddress = dev@whisper-appliance.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = ${SAN_LIST}
EOF
        openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt -config ssl.conf
        rm ssl.conf
    fi
    
    chmod 600 whisper-appliance.key
    chmod 644 whisper-appliance.crt
    chown commander:commander whisper-appliance.*
    
    echo "✅ SSL certificates created"
    cd "$CURRENT_DIR"
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
if ! python3 -c "import whisper, flask, flask_socketio" 2>/dev/null; then
    echo "⚠️  Installing missing Python dependencies..."
    pip3 install --user openai-whisper flask flask-cors flask-socketio flask-swagger-ui
fi

# Configure firewall for HTTPS access
echo "🔥 Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    sudo ufw --force enable
    sudo ufw allow 5001/tcp comment "WhisperS2T HTTPS Local"
    echo "✅ Firewall configured"
fi

# Reload systemd and enable service
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl enable whisper-appliance

# Start service with retry
echo "🚀 Starting WhisperS2T service..."
for i in {1..3}; do
    echo "Starting attempt $i/3..."
    if sudo systemctl start whisper-appliance; then
        sleep 5
        if systemctl is-active --quiet whisper-appliance; then
            echo "✅ WhisperS2T service started successfully"
            break
        else
            echo "⚠️  Service started but not active, checking logs..."
            sudo journalctl -u whisper-appliance --no-pager -l | tail -10
        fi
    else
        echo "❌ Failed to start service on attempt $i"
        if [[ $i -eq 3 ]]; then
            echo "💥 Service failed after 3 attempts. Check logs:"
            echo "   sudo journalctl -u whisper-appliance -f"
        else
            sleep 3
        fi
    fi
done

# Final status check
echo ""
echo "📊 Service Status:"
sudo systemctl status whisper-appliance --no-pager -l

echo ""
echo "🎉 Local WhisperS2T Setup Complete!"
echo ""
echo "🌐 Access URLs:"
echo "   Main Interface: https://localhost:5001"
echo "   Admin Panel: https://localhost:5001/admin"
echo "   API Docs: https://localhost:5001/docs"
echo "   Health Check: https://localhost:5001/health"
echo ""
echo "🔧 Debug Commands:"
echo "   sudo systemctl status whisper-appliance"
echo "   sudo journalctl -u whisper-appliance -f"
echo "   curl -k https://localhost:5001/health"
