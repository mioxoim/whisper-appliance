#!/bin/bash
# Enhanced WhisperS2T Appliance - Full ISO Build (Simplified)
# v0.5.0 - Installation ISO for existing Linux systems

build_full_iso_simple() {
    print_section "🌍 Building Installation ISO"
    
    ISO_BUILD_DIR="$ROOT_DIR/build/iso-full"
    OUTPUT_FILE="$ROOT_DIR/build/output/whisper-appliance-v${VERSION}-full.iso"
    
    # Clean and create build directory
    rm -rf "$ISO_BUILD_DIR"
    mkdir -p "$ISO_BUILD_DIR/install"
    
    print_step "Creating installation package..."
    
    # Copy our application
    cp -r "$ROOT_DIR/src" "$ISO_BUILD_DIR/install/"
    cp "$ROOT_DIR/requirements.txt" "$ISO_BUILD_DIR/install/"
    cp "$ROOT_DIR/requirements-dev.txt" "$ISO_BUILD_DIR/install/"
    
    # Create installer script
    cat > "$ISO_BUILD_DIR/install.sh" << 'EOF'
#!/bin/bash
# Enhanced WhisperS2T Appliance - System Installer
set -e

clear
echo "==============================================="
echo "🎤 Enhanced WhisperS2T Appliance v0.5.0"
echo "==============================================="
echo "System Installation"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This installer must be run as root"
    echo "Please run: sudo ./install.sh"
    exit 1
fi

echo "This installer will:"
echo "• Install to /opt/whisper-appliance"
echo "• Create systemd service"
echo "• Setup automatic startup"
echo "• Configure web interface on port 5000"
echo ""

read -p "Continue? [y/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

INSTALL_DIR="/opt/whisper-appliance"

echo ""
echo "📦 Installing to: $INSTALL_DIR"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cp -r install/* "$INSTALL_DIR/"

# Install system dependencies
echo "📦 Installing system dependencies..."
if command -v dnf &> /dev/null; then
    dnf update -y
    dnf install -y python3 python3-pip python3-venv git ffmpeg
elif command -v apt &> /dev/null; then
    apt update
    apt install -y python3 python3-pip python3-venv git ffmpeg portaudio19-dev python3-dev
else
    echo "⚠️ Unknown package manager. Please install Python 3.8+ manually."
fi

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt

# Create systemd service
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/whisper-appliance.service << 'SERVICE_EOF'
[Unit]
Description=Enhanced WhisperS2T Appliance
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/whisper-appliance/src/webgui/backend
ExecStart=/opt/whisper-appliance/venv/bin/python dev_server.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/whisper-appliance/src

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable and start service
systemctl daemon-reload
systemctl enable whisper-appliance
systemctl start whisper-appliance

# Wait for service to start
sleep 5

# Get IP address
IP=$(hostname -I | awk '{print $1}' || echo "localhost")

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "==============================================="
echo "🎤 Enhanced WhisperS2T Appliance v0.5.0"
echo "==============================================="
echo ""
echo "✅ System ready!"
echo "🌐 Web Interface: http://$IP:5000"
echo "🔧 Admin Panel: http://$IP:5000/admin"
echo ""
echo "📋 System Status:"
echo "• Installation: $INSTALL_DIR"
echo "• Service: $(systemctl is-active whisper-appliance)"
echo "• Hostname: $(hostname)"
echo "• IP Address: $IP"
echo ""
echo "💡 Service Management:"
echo "  sudo systemctl status whisper-appliance"
echo "  sudo systemctl restart whisper-appliance"
echo "  sudo journalctl -u whisper-appliance -f"
echo "==============================================="
EOF

    chmod +x "$ISO_BUILD_DIR/install.sh"
    
    # Create README
    cat > "$ISO_BUILD_DIR/README.md" << EOF
# Enhanced WhisperS2T Appliance v${VERSION}

## Installation ISO for Linux Systems

This ISO contains a complete installation package for the Enhanced WhisperS2T Appliance.

### Requirements
- Existing Linux system (Ubuntu, Fedora, Debian, CentOS, etc.)
- Root/sudo access
- Internet connection
- 4GB RAM minimum (8GB recommended)
- 20GB free disk space

### Installation Methods

#### Method 1: Direct Installation
1. Mount this ISO on your Linux system
2. Run: \`sudo ./install.sh\`
3. Follow the prompts
4. Access web interface at displayed IP

#### Method 2: USB Installation
1. Copy ISO contents to USB stick
2. Boot target computer with any Linux Live USB
3. Mount USB and run installer
4. Reboot into installed system

#### Method 3: Network Installation
1. Copy installer to target system
2. Run installation remotely via SSH
3. Access web interface over network

### After Installation
- **Web Interface:** http://[IP]:5000
- **Admin Panel:** http://[IP]:5000/admin

### Service Management
\`\`\`bash
# Check status
sudo systemctl status whisper-appliance

# Restart service
sudo systemctl restart whisper-appliance

# View logs
sudo journalctl -u whisper-appliance -f
\`\`\`

### Features
- Complete ML stack for speech recognition
- Web-based interface
- Real-time audio processing (in container mode)
- Multi-language support
- RESTful API
- System monitoring and administration

Created: $(date)
Version: v${VERSION}
Type: Linux Installation Package
EOF

    # Create installation guide
    cat > "$ISO_BUILD_DIR/INSTALLATION-GUIDE.txt" << EOF
ENHANCED WHISPERS2T APPLIANCE - INSTALLATION GUIDE
==================================================

QUICK START (5 minutes):
1. Mount this ISO: sudo mount whisper-appliance-v${VERSION}-full.iso /mnt
2. Run installer: sudo /mnt/install.sh
3. Access web interface: http://[displayed-IP]:5000

DETAILED INSTALLATION:

Prerequisites:
- Linux system (any distribution)
- Root/sudo access
- Internet connection for dependencies
- 4GB+ RAM, 20GB+ disk space

Step-by-Step:
1. Mount ISO:
   sudo mkdir -p /mnt/whisper
   sudo mount whisper-appliance-v${VERSION}-full.iso /mnt/whisper

2. Run installer:
   cd /mnt/whisper
   sudo ./install.sh

3. Follow prompts:
   - Confirms installation location (/opt/whisper-appliance)
   - Downloads and installs dependencies
   - Sets up Python virtual environment
   - Creates systemd service
   - Starts the appliance

4. Access web interface:
   - IP address shown after installation
   - Default port: 5000
   - Automatic startup on reboot

USB INSTALLATION (for dedicated hardware):
1. Boot target computer with Ubuntu/Fedora Live USB
2. Copy this ISO to USB or network location
3. Mount and run installer as above
4. Remove Live USB and reboot
5. System boots directly into appliance

TROUBLESHOOTING:
- Installation fails: Check internet connection
- Service won't start: Check logs with journalctl -u whisper-appliance
- Web interface not accessible: Check firewall settings
- Port conflicts: Edit /etc/systemd/system/whisper-appliance.service

UNINSTALLING:
sudo systemctl stop whisper-appliance
sudo systemctl disable whisper-appliance
sudo rm -rf /opt/whisper-appliance
sudo rm /etc/systemd/system/whisper-appliance.service
sudo systemctl daemon-reload
EOF

    # Build the ISO
    print_step "Building installation ISO..."
    
    if command -v genisoimage &> /dev/null; then
        genisoimage -r -J -V "WhisperS2T-v${VERSION}" -o "$OUTPUT_FILE" "$ISO_BUILD_DIR"
    elif command -v mkisofs &> /dev/null; then
        mkisofs -r -J -V "WhisperS2T-v${VERSION}" -o "$OUTPUT_FILE" "$ISO_BUILD_DIR"
    else
        print_error "No ISO creation tool found"
        print_info "Install with: sudo dnf install genisoimage"
        return 1
    fi
    
    if [ $? -eq 0 ]; then
        ISO_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        print_success "Installation ISO created successfully!"
        print_info "File: $OUTPUT_FILE"
        print_info "Size: $ISO_SIZE"
        print_info "Type: Linux Installation Package"
        
        # Create usage guide
        cat > "$ROOT_DIR/build/output/FULL-ISO-USAGE.md" << EOF
# Enhanced WhisperS2T Appliance - Full ISO Usage Guide

## What is this ISO?
This is an **Installation ISO** containing the complete Enhanced WhisperS2T Appliance that can be installed on any existing Linux system.

## Important Note
**This is NOT a bootable live system** - it requires an existing Linux environment to run the installer.

## Installation Methods

### Method 1: Install on Running Linux System
\`\`\`bash
# Mount the ISO
sudo mkdir -p /mnt/whisper
sudo mount whisper-appliance-v${VERSION}-full.iso /mnt/whisper

# Run the installer
cd /mnt/whisper
sudo ./install.sh

# Follow the prompts
# System will install and start automatically
\`\`\`

### Method 2: Use with Live USB (Recommended for bare metal)
1. **Create Linux Live USB** (Ubuntu, Fedora, etc.)
2. **Boot target computer** from Live USB
3. **Copy this ISO** to the Live environment
4. **Mount and install** as in Method 1
5. **Reboot** into installed system

### Method 3: USB Installation Kit
\`\`\`bash
# Extract ISO contents to USB stick
mkdir -p /mnt/usb
sudo mount /dev/sdX1 /mnt/usb
sudo mount -o loop whisper-appliance-v${VERSION}-full.iso /tmp/iso
sudo cp -r /tmp/iso/* /mnt/usb/
sudo umount /tmp/iso /mnt/usb

# Boot target system with any Live USB
# Mount USB and run: sudo /path/to/usb/install.sh
\`\`\`

## After Installation
- **Automatic startup** on boot
- **Web interface** on port 5000
- **IP address displayed** on console
- **Full appliance functionality**

## Use Cases
- **Development servers** - Install on existing Linux
- **Production deployment** - Use with Live USB method  
- **Edge computing** - Install on minimal Linux systems
- **Container hosts** - Install alongside other services

## Next Steps
After successful installation:
1. Access web interface at displayed IP
2. Configure speech recognition settings
3. Upload audio files for testing
4. Integrate with your applications via API

This installation method provides maximum compatibility while maintaining full appliance functionality.
EOF

        print_info "Usage guide: $ROOT_DIR/build/output/FULL-ISO-USAGE.md"
    else
        print_error "Failed to create installation ISO"
        return 1
    fi
    
    # Cleanup
    rm -rf "$ISO_BUILD_DIR"
    
    print_success "Full ISO build completed!"
    print_warning "Note: This ISO requires an existing Linux system to run the installer"
    print_info "For bare metal installation, use with a Linux Live USB"
}
