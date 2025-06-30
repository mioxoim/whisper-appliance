#!/bin/bash
# Quick Fix Script for WhisperS2T v0.9.0 Container Issues
# Run this directly on the container to fix startup problems

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

print_status "🔧 WhisperS2T v0.9.0 Quick Fix Script"
print_status "Fixing container startup issues..."

# Stop any running services
print_status "Stopping existing services..."
systemctl stop whisper-appliance 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true

# Remove old Nginx configuration (v0.9.0 uses direct HTTPS)
print_status "Removing old Nginx proxy configuration..."
rm -f /etc/nginx/sites-enabled/whisper-appliance
rm -f /etc/nginx/sites-available/whisper-appliance

# Update to latest code
print_status "Updating to latest WhisperS2T v0.9.0..."
cd /opt/whisper-appliance || exit 1

# Download latest main.py and modules
print_status "Downloading latest application code..."
wget -q -O src/main.py "https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/src/main.py" || {
    print_error "Failed to download latest main.py"
    exit 1
}

# Create modules directory if it doesn't exist
mkdir -p src/modules

# Download all required modules
for module in "__init__.py" "model_manager.py" "chat_history.py" "upload_handler.py" "live_speech.py" "admin_panel.py" "api_docs.py"; do
    print_status "Downloading module: $module"
    wget -q -O "src/modules/$module" "https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/src/modules/$module" || {
        print_warning "Failed to download $module, but continuing..."
    }
done

# Download template
mkdir -p src/templates
wget -q -O src/templates/main_interface.html "https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/src/templates/main_interface.html" || {
    print_warning "Failed to download template, but continuing..."
}

# Install correct Whisper package
print_status "Installing/updating Python dependencies..."
pip3 install --upgrade openai-whisper flask flask-cors flask-socketio flask-swagger-ui

# Fix permissions
print_status "Fixing file permissions..."
chown -R whisper:whisper /opt/whisper-appliance
chmod -R u+rw /opt/whisper-appliance

# Create data directory for chat history
mkdir -p /opt/whisper-appliance/data
chown -R whisper:whisper /opt/whisper-appliance/data

# Update systemd service configuration
print_status "Updating systemd service configuration..."
cat > /etc/systemd/system/whisper-appliance.service << 'EOF'
[Unit]
Description=WhisperS2T Appliance v0.9.0 with Direct HTTPS
After=network.target

[Service]
Type=simple
User=whisper
Group=whisper
WorkingDirectory=/opt/whisper-appliance/src
Environment=PATH=/home/whisper/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/whisper-appliance/src
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Test the application before starting
print_status "Testing application startup..."
cd /opt/whisper-appliance/src

if sudo -u whisper python3 -c "
import sys
sys.path.insert(0, '/opt/whisper-appliance/src')
try:
    print('Testing imports...')
    from modules import ModelManager, ChatHistoryManager
    print('✅ Core modules imported successfully')
    
    # Test initialization
    model_manager = ModelManager()
    chat_history = ChatHistoryManager()
    print('✅ Components initialize successfully')
    
    print('✅ Application test passed - ready to start')
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"; then
    print_success "✅ Application test passed"
else
    print_error "❌ Application test failed"
    print_status "Showing recent logs for debugging:"
    journalctl -u whisper-appliance -n 10 --no-pager || true
    exit 1
fi

# Configure firewall for direct HTTPS
print_status "Configuring firewall for direct HTTPS (port 5001)..."
if command -v ufw >/dev/null 2>&1; then
    ufw --force enable
    ufw allow 5001/tcp comment "WhisperS2T HTTPS Direct"
    ufw allow ssh
fi

# Start the service
print_status "Starting WhisperS2T service..."
systemctl daemon-reload
systemctl enable whisper-appliance
systemctl start whisper-appliance

# Wait and check status
print_status "Waiting for service to start..."
sleep 8

if systemctl is-active --quiet whisper-appliance; then
    print_success "✅ WhisperS2T service is running successfully!"
    
    # Get container IP
    CONTAINER_IP=$(hostname -I | awk '{print $1}')
    
    print_success ""
    print_success "🎉 WhisperS2T v0.9.0 is now ready!"
    print_success ""
    print_success "🌐 Access URLs:"
    print_success "   📍 Primary HTTPS: https://$CONTAINER_IP:5001"
    print_success "   🏥 Health Check:  https://$CONTAINER_IP:5001/health"
    print_success "   ⚙️ Admin Panel:   https://$CONTAINER_IP:5001/admin"
    print_success "   📚 API Docs:      https://$CONTAINER_IP:5001/docs"
    print_success ""
    print_success "🔒 Note: Browser will show security warning for self-signed cert"
    print_success "    Click 'Advanced' → 'Continue to site'"
    print_success ""
    print_success "🎙️ Microphone access now works across the network!"
    
else
    print_error "❌ Service failed to start. Showing logs:"
    journalctl -u whisper-appliance -n 20 --no-pager
    
    print_status ""
    print_status "🔧 Troubleshooting steps:"
    print_status "1. Check logs: journalctl -u whisper-appliance -f"
    print_status "2. Manual test: sudo -u whisper python3 /opt/whisper-appliance/src/main.py"
    print_status "3. Check permissions: ls -la /opt/whisper-appliance/"
    print_status "4. Test imports: python3 -c 'from modules import ModelManager'"
fi
