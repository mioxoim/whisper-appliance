#!/bin/bash

# Enhanced WhisperS2T Appliance v0.5.0 - Developer Helper
# Zentrale Steuerung für alle Entwicklungs- und Build-Aufgaben

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="Enhanced WhisperS2T Appliance"
VERSION="0.6.0"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo -e "${BOLD}${CYAN}🎤 $PROJECT_NAME v$VERSION - Developer Helper${NC}"
    echo -e "${BOLD}${BLUE}================================================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BOLD}${YELLOW}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..60})${NC}"
}

print_step() {
    echo -e "${BLUE}[DEV]${NC} $1"
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

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Helper functions
check_requirements() {
    print_step "Checking development environment..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        return 1
    fi
    
    # Check virtual environment
    if [ ! -d "$ROOT_DIR/venv" ]; then
        print_warning "Virtual environment not found, creating..."
        python3 -m venv "$ROOT_DIR/venv"
    fi
    
    print_success "Development environment ready"
}

# Development server functions
dev_start() {
    print_section "🚀 Starting Development Server"
    
    check_requirements
    
    print_step "Activating virtual environment..."
    source "$ROOT_DIR/venv/bin/activate"
    
    print_step "Installing dependencies..."
    pip install -q --upgrade pip setuptools wheel
    
    # Try dev requirements first for development
    if [ -f "$ROOT_DIR/requirements-dev.txt" ]; then
        print_step "Installing development dependencies..."
        pip install -q -r "$ROOT_DIR/requirements-dev.txt" || {
            print_warning "Dev requirements failed, trying manual installation..."
            
            # Install core dependencies manually
            print_step "Installing core web framework..."
            pip install -q fastapi==0.115.13 uvicorn==0.34.3 websockets==15.0.1
            
            print_step "Installing audio processing..."
            pip install -q pydub==0.25.1 numpy
            
            print_step "Installing system monitoring..."
            pip install -q psutil python-dateutil typing-extensions
            
            print_step "Installing web extensions..."
            pip install -q starlette python-multipart
            
            print_warning "Skipping problematic ML dependencies for dev server"
            print_info "For full ML features, use the container deployment"
        }
    else
        print_step "Installing full requirements..."
        pip install -q -r "$ROOT_DIR/requirements.txt" || {
            print_error "Full requirements installation failed"
            print_info "This may be due to Python 3.13 compatibility issues"
            print_info "Consider using the container deployment instead"
            return 1
        }
    fi
    
    print_step "Starting development server..."
    cd "$ROOT_DIR/src/webgui/backend"
    
    # Use the dedicated development server
    if [ -f "dev_server.py" ]; then
        MAIN_SCRIPT="dev_server.py"
    elif [ -f "appliance_server.py" ]; then
        MAIN_SCRIPT="appliance_server.py"
    elif [ -f "main.py" ]; then
        MAIN_SCRIPT="main.py"
    else
        print_error "No main script found in backend directory"
        return 1
    fi
    
    print_success "Development server starting..."
    print_info "Using script: $MAIN_SCRIPT"
    print_info "Web Interface: http://localhost:5000"
    print_info "Admin Panel: http://localhost:5000/admin"
    print_info "Demo Interface: http://localhost:5000/demo"
    print_info "API Docs: http://localhost:5000/docs"
    echo ""
    print_warning "Note: Running in lite mode - some ML features may be limited"
    print_info "For full features, use: ./dev.sh container start"
    print_info "Press Ctrl+C to stop the server"
    echo ""
    
    python "$MAIN_SCRIPT"
}

dev_stop() {
    print_section "🛑 Stopping Development Server"
    
    print_step "Searching for running processes..."
    
    # Find Python processes on port 5000 or with our script names
    PIDS=$(pgrep -f "dev_server.py\|start_appliance.py\|appliance_server.py" || true)
    PORT_PIDS=$(lsof -ti:5000 2>/dev/null || true)
    
    # Combine PIDs and remove duplicates
    ALL_PIDS=$(echo "$PIDS $PORT_PIDS" | tr ' ' '\n' | sort -u | tr '\n' ' ')
    
    if [ -n "$ALL_PIDS" ]; then
        print_step "Stopping processes: $ALL_PIDS"
        for pid in $ALL_PIDS; do
            if kill -0 "$pid" 2>/dev/null; then
                print_step "Stopping PID $pid..."
                kill "$pid" 2>/dev/null || true
            fi
        done
        
        sleep 2
        
        # Force kill if still running
        for pid in $ALL_PIDS; do
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Force stopping PID $pid..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        done
        
        print_success "Development server stopped"
    else
        print_info "No running development server found"
    fi
}

dev_status() {
    print_section "📊 Development Status"
    
    # Check if server is running
    PIDS=$(pgrep -f "start_appliance.py" || true)
    if [ -n "$PIDS" ]; then
        print_success "Development server is running (PID: $PIDS)"
        print_info "Web Interface: http://localhost:5000"
    else
        print_info "Development server is not running"
    fi
    
    # Check virtual environment
    if [ -d "$ROOT_DIR/venv" ]; then
        print_success "Virtual environment exists"
    else
        print_warning "Virtual environment not found"
    fi
    
    # Check dependencies
    if [ -f "$ROOT_DIR/requirements.txt" ]; then
        print_success "Requirements file found"
    else
        print_warning "Requirements file missing"
    fi
}

# Build functions
build_quick_iso() {
    print_section "📀 Building Quick Deploy ISO"
    
    BUILD_SCRIPT="$ROOT_DIR/scripts/build-quick-iso.sh"
    
    if [ ! -f "$BUILD_SCRIPT" ]; then
        print_error "Build script not found: $BUILD_SCRIPT"
        return 1
    fi
    
    print_step "Starting ISO build..."
    chmod +x "$BUILD_SCRIPT"
    cd "$ROOT_DIR"
    "$BUILD_SCRIPT"
    
    if [ $? -eq 0 ]; then
        print_success "Quick Deploy ISO built successfully!"
        print_info "Location: $ROOT_DIR/build/output/"
    else
        print_error "ISO build failed"
        return 1
    fi
}

build_container() {
    print_section "🐳 Building Container Image"
    
    BUILD_SCRIPT="$ROOT_DIR/scripts/build-container.sh"
    
    if [ ! -f "$BUILD_SCRIPT" ]; then
        print_error "Build script not found: $BUILD_SCRIPT"
        return 1
    fi
    
    print_step "Starting container build..."
    print_warning "This may take 15-20 minutes for full ML stack"
    chmod +x "$BUILD_SCRIPT"
    cd "$ROOT_DIR"
    "$BUILD_SCRIPT"
    
    if [ $? -eq 0 ]; then
        print_success "Container image built successfully!"
        print_info "Location: $ROOT_DIR/build/output/"
    else
        print_error "Container build failed"
        return 1
    fi
}

build_all() {
    print_section "🏗️ Building All Deployment Options"
    
    print_info "This will build all available deployment options:"
    print_info "1. Quick Deploy ISO (minimal, ~1MB)"
    print_info "2. Container Image (full ML stack, ~10GB)"
    print_info "3. Full Bootable ISO (complete system, ~2-4GB)"
    print_info ""
    print_warning "Total estimated time: 20-35 minutes"
    print_info ""
    
    read -p "Continue with all builds? [y/N]: " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        print_info "Build cancelled"
        return 0
    fi
    
    # Build Quick Deploy ISO
    print_step "Building Quick Deploy ISO..."
    build_quick_iso
    
    if [ $? -ne 0 ]; then
        print_error "Quick Deploy ISO build failed"
        return 1
    fi
    
    echo ""
    print_step "Building Container Image..."
    build_container
    
    if [ $? -ne 0 ]; then
        print_warning "Container build failed, continuing with Full ISO..."
    fi
    
    echo ""
    print_step "Building Full Bootable ISO..."
    build_full_iso
    
    if [ $? -ne 0 ]; then
        print_warning "Full ISO build failed"
    fi
    
    print_success "All builds completed!"
    build_status
}

build_status() {
    print_section "📦 Build Status"
    
    OUTPUT_DIR="$ROOT_DIR/build/output"
    
    if [ ! -d "$OUTPUT_DIR" ]; then
        print_info "No builds found (output directory missing)"
        return
    fi
    
    echo "Build artifacts in $OUTPUT_DIR:"
    echo ""
    
    # Check Quick Deploy ISO
    if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-deploy.iso" ]; then
        SIZE=$(du -h "$OUTPUT_DIR/whisper-appliance-v${VERSION}-deploy.iso" | cut -f1)
        print_success "Quick Deploy ISO: $SIZE (✅ Ready for deployment)"
    else
        print_info "Quick Deploy ISO: Not built"
    fi
    
    # Check Full Bootable ISO
    if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-full.iso" ]; then
        SIZE=$(du -h "$OUTPUT_DIR/whisper-appliance-v${VERSION}-full.iso" | cut -f1)
        print_success "Full Bootable ISO: $SIZE (✅ Ready for USB creation)"
    else
        print_info "Full Bootable ISO: Not built"
    fi
    
    # Check Container
    if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar" ]; then
        SIZE=$(du -h "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar" | cut -f1)
        print_success "Container Image: $SIZE (✅ Ready for deployment)"
    else
        print_info "Container Image: Not built"
    fi
    
    # Show deployment options
    echo ""
    print_info "📋 Deployment Options:"
    
    if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-deploy.iso" ]; then
        print_info "• Quick Deploy: Mount ISO and run install.sh"
    fi
    
    if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-full.iso" ]; then
        print_info "• USB Stick: Write Full ISO to USB and boot from it"
        print_info "  Command: sudo dd if=whisper-appliance-v${VERSION}-full.iso of=/dev/sdX"
    fi
    
    if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar" ]; then
        print_info "• Container: podman load -i whisper-appliance-v${VERSION}-container.tar"
    fi
    
    # List all files with details
    if [ "$(ls -A $OUTPUT_DIR 2>/dev/null)" ]; then
        echo ""
        print_info "📁 All build artifacts:"
        ls -lah "$OUTPUT_DIR" | grep -v "^total" | grep -v "^d" | awk '{print "  " $9 " (" $5 ")"}'
        
        # Show guides
        echo ""
        print_info "📚 Available guides:"
        if [ -f "$OUTPUT_DIR/USB-CREATION-GUIDE.md" ]; then
            print_info "  • USB-CREATION-GUIDE.md"
        fi
        if [ -f "$OUTPUT_DIR/INSTALLATION.md" ]; then
            print_info "  • INSTALLATION.md"
        fi
        if [ -f "$OUTPUT_DIR/deployment-guide.md" ]; then
            print_info "  • deployment-guide.md"
        fi
    fi
}

# Container functions
container_start() {
    print_section "🐳 Starting Container"
    
    CONTAINER_FILE="$ROOT_DIR/build/output/whisper-appliance-v${VERSION}-container.tar"
    
    if [ ! -f "$CONTAINER_FILE" ]; then
        print_error "Container image not found: $CONTAINER_FILE"
        print_info "Build it first with: $0 build container"
        return 1
    fi
    
    # Check if container runtime is available
    if command -v podman &> /dev/null; then
        RUNTIME="podman"
    elif command -v docker &> /dev/null; then
        RUNTIME="docker"
    else
        print_error "No container runtime found (podman or docker required)"
        return 1
    fi
    
    print_step "Using $RUNTIME as container runtime"
    
    # Check if image is already loaded
    if ! $RUNTIME images | grep -q "whisper-appliance.*$VERSION"; then
        print_step "Loading container image..."
        $RUNTIME load -i "$CONTAINER_FILE"
    fi
    
    # Stop existing container if running
    if $RUNTIME ps | grep -q whisper-appliance; then
        print_step "Stopping existing container..."
        $RUNTIME stop whisper-appliance 2>/dev/null || true
    fi
    
    # Remove existing container
    $RUNTIME rm whisper-appliance 2>/dev/null || true
    
    print_step "Starting new container..."
    $RUNTIME run -d \
        --name whisper-appliance \
        -p 5000:5000 \
        -v whisper-models:/home/whisper/.cache \
        whisper-appliance:$VERSION
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully!"
        print_info "Web Interface: http://localhost:5000"
        print_info "Admin Panel: http://localhost:5000/admin"
        print_info "Demo Interface: http://localhost:5000/demo"
        print_info "Container Name: whisper-appliance"
    else
        print_error "Failed to start container"
        return 1
    fi
}

container_stop() {
    print_section "🛑 Stopping Container"
    
    # Check if container runtime is available
    if command -v podman &> /dev/null; then
        RUNTIME="podman"
    elif command -v docker &> /dev/null; then
        RUNTIME="docker"
    else
        print_error "No container runtime found"
        return 1
    fi
    
    if $RUNTIME ps | grep -q whisper-appliance; then
        print_step "Stopping container..."
        $RUNTIME stop whisper-appliance
        print_success "Container stopped"
    else
        print_info "Container is not running"
    fi
}

container_status() {
    print_section "📊 Container Status"
    
    # Check if container runtime is available
    if command -v podman &> /dev/null; then
        RUNTIME="podman"
    elif command -v docker &> /dev/null; then
        RUNTIME="docker"
    else
        print_info "No container runtime found"
        return 1
    fi
    
    print_step "Checking container status..."
    
    if $RUNTIME ps | grep -q whisper-appliance; then
        print_success "Container is running"
        print_info "Status:"
        $RUNTIME ps | grep whisper-appliance
        print_info "Web Interface: http://localhost:5000"
    elif $RUNTIME ps -a | grep -q whisper-appliance; then
        print_warning "Container exists but is not running"
        print_info "Start it with: $0 container start"
    else
        print_info "Container not found"
        print_info "Start it with: $0 container start"
    fi
}

container_logs() {
    print_section "📋 Container Logs"
    
    # Check if container runtime is available
    if command -v podman &> /dev/null; then
        RUNTIME="podman"
    elif command -v docker &> /dev/null; then
        RUNTIME="docker"
    else
        print_error "No container runtime found"
        return 1
    fi
    
    if $RUNTIME ps | grep -q whisper-appliance; then
        print_step "Showing container logs (press Ctrl+C to exit)..."
        $RUNTIME logs -f whisper-appliance
    else
        print_error "Container is not running"
        print_info "Start it with: $0 container start"
    fi
}

# Full ISO Build functions
# Full ISO Build functions - Simplified Installation ISO
build_full_iso() {
    print_section "🌍 Building Installation ISO"
    
    print_step "Creating installation package..."
    
    ISO_BUILD_DIR="$ROOT_DIR/build/iso-full"
    OUTPUT_FILE="$ROOT_DIR/build/output/whisper-appliance-v${VERSION}-full.iso"
    
    # Clean and create build directory
    rm -rf "$ISO_BUILD_DIR"
    mkdir -p "$ISO_BUILD_DIR/install"
    
    # Copy our application
    print_step "Packaging application files..."
    cp -r "$ROOT_DIR/src" "$ISO_BUILD_DIR/install/"
    cp "$ROOT_DIR/requirements.txt" "$ISO_BUILD_DIR/install/"
    cp "$ROOT_DIR/requirements-dev.txt" "$ISO_BUILD_DIR/install/"
    
    # Create installer script
    print_step "Creating installer script..."
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
echo "🎤 Demo Interface: http://$IP:5000/demo"
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
    
    # Create documentation
    print_step "Creating documentation..."
    cat > "$ISO_BUILD_DIR/README.md" << EOF
# Enhanced WhisperS2T Appliance v${VERSION}

## Installation ISO for Linux Systems

### Quick Installation
1. Mount this ISO: \`sudo mount whisper-appliance-v${VERSION}-full.iso /mnt\`
2. Run installer: \`sudo /mnt/install.sh\`
3. Access web interface at displayed IP address

### Requirements
- Linux system (any distribution)
- Root/sudo access
- Internet connection
- 4GB+ RAM, 20GB+ disk space

### After Installation
- Web Interface: http://[IP]:5000
- Admin Panel: http://[IP]:5000/admin
- Demo Interface: http://[IP]:5000/demo

### Service Management
\`\`\`bash
sudo systemctl status whisper-appliance
sudo systemctl restart whisper-appliance
sudo journalctl -u whisper-appliance -f
\`\`\`

Created: $(date)
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
# Enhanced WhisperS2T Appliance - Installation ISO Usage

## What This ISO Does
This ISO contains a complete installer for the Enhanced WhisperS2T Appliance that can be installed on any Linux system.

## Installation Methods

### Method 1: Direct Installation (Existing Linux)
\`\`\`bash
sudo mount whisper-appliance-v${VERSION}-full.iso /mnt
cd /mnt
sudo ./install.sh
\`\`\`

### Method 2: USB Installation (Bare Metal)
1. Boot target computer with any Linux Live USB
2. Mount this ISO or copy to USB
3. Run installer as in Method 1
4. Reboot into installed system

### Method 3: Remote Installation
1. Copy ISO to target system via SCP
2. SSH into target system
3. Mount and install as in Method 1

## After Installation
- Automatic startup on boot
- Web interface on port 5000
- IP address displayed on console
- Full appliance functionality

Perfect for dedicated mini-PC deployments!
EOF

        print_info "Usage guide: $ROOT_DIR/build/output/FULL-ISO-USAGE.md"
    else
        print_error "Failed to create installation ISO"
        return 1
    fi
    
    # Cleanup
    rm -rf "$ISO_BUILD_DIR"
    
    print_success "Installation ISO completed!"
    print_info "Mount this ISO on any Linux system and run: sudo ./install.sh"
}

# Fedora Live ISO Build functions
build_fedora_bootable_iso() {
    print_section "🎤 Building Fedora Live ISO (New Method)"
    
    print_step "Using official Fedora live templates..."
    
    FEDORA_BUILDER="$ROOT_DIR/build-live-iso.sh"
    
    if [ ! -f "$FEDORA_BUILDER" ]; then
        print_error "Fedora Live ISO builder not found: $FEDORA_BUILDER"
        print_error "Expected: $FEDORA_BUILDER"
        return 1
    fi
    
    if [ ! -x "$FEDORA_BUILDER" ]; then
        chmod +x "$FEDORA_BUILDER"
    fi
    
    print_info "Starting Fedora Live ISO build with official templates..."
    print_warning "This requires: mock group membership, cached Fedora ISO, and 30-60 minutes"
    
    "$FEDORA_BUILDER"
    
    if [ $? -eq 0 ]; then
        print_success "Fedora Live ISO build completed!"
        print_info "Check: $ROOT_DIR/build/output/ for whisper-appliance-v${VERSION}-bootable.iso"
    else
        print_error "Fedora ISO build failed"
        return 1
    fi
}


test_run() {
    print_section "🧪 Running Tests"
    
    check_requirements
    source "$ROOT_DIR/venv/bin/activate"
    
    if [ -d "$ROOT_DIR/tests" ]; then
        print_step "Running pytest..."
        cd "$ROOT_DIR"
        pytest tests/ -v
    else
        print_warning "No tests directory found"
        print_info "Create tests in $ROOT_DIR/tests/"
    fi
}

test_api() {
    print_section "🔌 Testing API Endpoints"
    
    # Check if server is running
    if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
        print_error "Development server is not running"
        print_info "Start it with: $0 dev start"
        return 1
    fi
    
    print_step "Testing health endpoint..."
    curl -s http://localhost:5000/health | python3 -m json.tool || print_error "Health check failed"
    
    print_step "Testing admin endpoint..."
    curl -s http://localhost:5000/admin/system/info | python3 -m json.tool || print_warning "Admin endpoint may require authentication"
    
    print_success "API tests completed"
}

# Utility functions
clean_build() {
    print_section "🧹 Cleaning Build Artifacts"
    
    BUILD_DIR="$ROOT_DIR/build"
    
    if [ -d "$BUILD_DIR" ]; then
        print_step "Removing build directory..."
        rm -rf "$BUILD_DIR"
        print_success "Build artifacts cleaned"
    else
        print_info "No build artifacts to clean"
    fi
}

clean_cache() {
    print_section "🗑️ Cleaning Cache and Temporary Files"
    
    print_step "Cleaning Python cache..."
    find "$ROOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    print_step "Cleaning log files..."
    find "$ROOT_DIR" -type f -name "*.log" -delete 2>/dev/null || true
    
    print_success "Cache and temporary files cleaned"
}

setup_dev() {
    print_section "⚙️ Setting Up Development Environment"
    
    check_requirements
    
    print_step "Installing development dependencies..."
    source "$ROOT_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$ROOT_DIR/requirements.txt"
    
    # Install additional dev tools
    print_step "Installing development tools..."
    pip install black flake8 pytest pytest-asyncio
    
    print_success "Development environment setup completed"
    print_info "You can now use: $0 dev start"
}

# Documentation functions
docs_serve() {
    print_section "📚 Serving Documentation"
    
    DOCS_DIR="$ROOT_DIR/docs"
    
    if [ ! -d "$DOCS_DIR" ]; then
        print_error "Documentation directory not found"
        return 1
    fi
    
    print_step "Starting documentation server..."
    print_info "Documentation will be available at: http://localhost:8000"
    print_info "Press Ctrl+C to stop"
    
    cd "$DOCS_DIR"
    python3 -m http.server 8000
}

# Update functions
update_check() {
    print_section "🔍 Checking for Updates"
    
    if [ ! -d ".git" ]; then
        print_error "Not a git repository. Cannot check for updates."
        print_info "This command only works for git-cloned installations."
        return 1
    fi
    
    print_step "Fetching latest changes from GitHub..."
    
    # Configure SSH if deploy key exists
    if [ -f "./deploy_key_whisper_appliance" ]; then
        export GIT_SSH_COMMAND="ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes"
        print_info "Using deploy key for GitHub access"
    fi
    
    # Fetch latest changes
    if ! git fetch origin main; then
        print_error "Failed to fetch updates from GitHub"
        return 1
    fi
    
    # Check if updates are available
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        print_success "✅ System is up to date!"
        print_info "Current version: $(git describe --tags --always)"
        return 0
    fi
    
    print_warning "🔄 Updates available!"
    print_info "Current commit:  $LOCAL_COMMIT"
    print_info "Latest commit:   $REMOTE_COMMIT"
    print_info ""
    
    # Show what will be updated
    echo "Changes that will be applied:"
    git log --oneline --decorate --color=always "$LOCAL_COMMIT..$REMOTE_COMMIT"
    echo ""
    
    print_info "Run './dev.sh update apply' to install updates"
    return 2  # Updates available
}

update_apply() {
    print_section "⬇️ Applying Updates"
    
    if [ ! -d ".git" ]; then
        print_error "Not a git repository. Cannot apply updates."
        return 1
    fi
    
    # Check if updates are available first
    print_step "Checking for updates..."
    update_check_result=$(update_check >/dev/null 2>&1; echo $?)
    
    if [ "$update_check_result" -eq 0 ]; then
        print_success "System is already up to date!"
        return 0
    elif [ "$update_check_result" -eq 1 ]; then
        print_error "Update check failed"
        return 1
    fi
    
    # Create backup before updating
    print_step "Creating backup of current version..."
    BACKUP_DIR="$ROOT_DIR/.backups"
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)-$(git rev-parse --short HEAD)"
    
    mkdir -p "$BACKUP_DIR"
    
    # Save current commit info
    echo "$(git rev-parse HEAD)" > "$BACKUP_DIR/$BACKUP_NAME.commit"
    echo "$(date)" > "$BACKUP_DIR/$BACKUP_NAME.timestamp"
    
    print_success "Backup created: $BACKUP_NAME"
    
    # Stop services before updating
    print_step "Stopping services..."
    if systemctl is-active --quiet whisper-appliance 2>/dev/null; then
        systemctl stop whisper-appliance
        RESTART_SERVICE=true
        print_info "Stopped whisper-appliance service"
    fi
    
    # Configure SSH if deploy key exists
    if [ -f "./deploy_key_whisper_appliance" ]; then
        export GIT_SSH_COMMAND="ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes"
    fi
    
    # Apply updates
    print_step "Applying updates from GitHub..."
    if git pull origin main; then
        print_success "✅ Updates applied successfully!"
        
        # Update file permissions
        print_step "Updating file permissions..."
        chmod +x *.sh 2>/dev/null || true
        
        # Check if requirements changed
        if git diff --name-only HEAD~1 HEAD | grep -q "requirements"; then
            print_warning "Requirements files changed. You may need to update dependencies:"
            print_info "  - For container: re-run install-container.sh"
            print_info "  - For development: pip install -r requirements.txt"
        fi
        
        # Restart services if they were running
        if [ "$RESTART_SERVICE" = true ]; then
            print_step "Restarting whisper-appliance service..."
            systemctl start whisper-appliance
            print_success "Service restarted"
        fi
        
        # Show what was updated
        NEW_VERSION=$(git describe --tags --always)
        print_success "Updated to version: $NEW_VERSION"
        
        # Test installation
        print_step "Testing installation..."
        if [ -f "./test-container.sh" ]; then
            if ./test-container.sh >/dev/null 2>&1; then
                print_success "✅ Installation test passed"
            else
                print_warning "⚠️ Installation test failed - check logs"
            fi
        fi
        
    else
        print_error "❌ Update failed!"
        print_warning "You may need to resolve conflicts manually"
        print_info "Run './dev.sh update rollback' to restore previous version"
        return 1
    fi
}

update_rollback() {
    print_section "⏪ Rolling Back to Previous Version"
    
    if [ ! -d ".git" ]; then
        print_error "Not a git repository. Cannot rollback."
        return 1
    fi
    
    BACKUP_DIR="$ROOT_DIR/.backups"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "No backups found. Cannot rollback."
        return 1
    fi
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.commit 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "No backup commits found. Cannot rollback."
        return 1
    fi
    
    BACKUP_COMMIT=$(cat "$LATEST_BACKUP")
    BACKUP_NAME=$(basename "$LATEST_BACKUP" .commit)
    
    print_warning "This will rollback to backup: $BACKUP_NAME"
    print_info "Backup commit: $BACKUP_COMMIT"
    
    if [ -f "$BACKUP_DIR/$BACKUP_NAME.timestamp" ]; then
        print_info "Backup created: $(cat "$BACKUP_DIR/$BACKUP_NAME.timestamp")"
    fi
    
    echo ""
    read -p "Continue with rollback? [y/N]: " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        print_info "Rollback cancelled"
        return 0
    fi
    
    # Stop services
    print_step "Stopping services..."
    if systemctl is-active --quiet whisper-appliance 2>/dev/null; then
        systemctl stop whisper-appliance
        RESTART_SERVICE=true
    fi
    
    # Rollback to backup commit
    print_step "Rolling back to previous version..."
    if git reset --hard "$BACKUP_COMMIT"; then
        print_success "✅ Rollback successful!"
        
        # Restart services if they were running
        if [ "$RESTART_SERVICE" = true ]; then
            print_step "Restarting whisper-appliance service..."
            systemctl start whisper-appliance
            print_success "Service restarted"
        fi
        
        # Remove used backup
        rm -f "$LATEST_BACKUP" "$BACKUP_DIR/$BACKUP_NAME.timestamp"
        print_info "Backup $BACKUP_NAME removed"
        
        CURRENT_VERSION=$(git describe --tags --always)
        print_success "Rolled back to version: $CURRENT_VERSION"
        
    else
        print_error "❌ Rollback failed!"
        return 1
    fi
}

update_status() {
    print_section "📊 Update Status"
    
    if [ ! -d ".git" ]; then
        print_error "Not a git repository."
        print_info "This appears to be a manual installation."
        return 1
    fi
    
    # Current version
    CURRENT_VERSION=$(git describe --tags --always)
    CURRENT_COMMIT=$(git rev-parse HEAD)
    CURRENT_BRANCH=$(git branch --show-current)
    
    print_info "Current version: $CURRENT_VERSION"
    print_info "Current commit:  $CURRENT_COMMIT"
    print_info "Current branch:  $CURRENT_BRANCH"
    print_info ""
    
    # Check for updates
    print_step "Checking for updates..."
    
    # Configure SSH if deploy key exists
    if [ -f "./deploy_key_whisper_appliance" ]; then
        export GIT_SSH_COMMAND="ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes"
    fi
    
    if git fetch origin main 2>/dev/null; then
        REMOTE_COMMIT=$(git rev-parse origin/main)
        
        if [ "$CURRENT_COMMIT" = "$REMOTE_COMMIT" ]; then
            print_success "✅ System is up to date"
        else
            print_warning "🔄 Updates available"
            print_info "Latest commit: $REMOTE_COMMIT"
            
            # Count commits behind
            COMMITS_BEHIND=$(git rev-list --count "$CURRENT_COMMIT..origin/main")
            print_info "Commits behind: $COMMITS_BEHIND"
        fi
    else
        print_warning "⚠️ Cannot check for updates (network/auth issue)"
    fi
    
    # Show available backups
    BACKUP_DIR="$ROOT_DIR/.backups"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR")" ]; then
        print_info ""
        print_info "Available backups:"
        for backup in "$BACKUP_DIR"/*.commit; do
            if [ -f "$backup" ]; then
                backup_name=$(basename "$backup" .commit)
                if [ -f "$BACKUP_DIR/$backup_name.timestamp" ]; then
                    timestamp=$(cat "$BACKUP_DIR/$backup_name.timestamp")
                    print_info "  - $backup_name ($timestamp)"
                else
                    print_info "  - $backup_name"
                fi
            fi
        done
    fi
    
    # Installation type
    print_info ""
    if [ -f "/etc/systemd/system/whisper-appliance.service" ]; then
        print_success "✅ Production installation (systemd service)"
        if systemctl is-active --quiet whisper-appliance; then
            print_success "✅ Service is running"
        else
            print_warning "⚠️ Service is not running"
        fi
    else
        print_info "📦 Development installation"
    fi
}

# Help function
show_help() {
    print_header
    
    echo -e "${BOLD}USAGE:${NC}"
    echo "  $0 <command> [options]"
    echo ""
    
    echo -e "${BOLD}DEVELOPMENT COMMANDS:${NC}"
    echo "  dev start          Start development server (lite mode)"
    echo "  dev stop           Stop development server"  
    echo "  dev status         Show development status"
    echo "  dev setup          Setup development environment"
    echo ""
    
    echo -e "${BOLD}CONTAINER COMMANDS:${NC}"
    echo "  container start    Start container (full ML features)"
    echo "  container stop     Stop container"
    echo "  container status   Show container status"
    echo "  container logs     Show container logs"
    echo ""
    
    echo -e "${BOLD}BUILD COMMANDS:${NC}"
    echo "  build quick        Build Quick Deploy ISO (minimal)"
    echo "  build container    Build Container Image (full ML stack)"
    echo "  build full         Build Full ISO Image (installation package)"
    echo "  build fedora       Build Fedora Live ISO (official templates, bootable)"
    echo "  build all          Build all deployment options"
    echo "  build status       Show build status"
    echo ""
    
    echo -e "${BOLD}TEST COMMANDS:${NC}"
    echo "  test run           Run unit tests"
    echo "  test api           Test API endpoints"
    echo ""
    
    echo -e "${BOLD}UTILITY COMMANDS:${NC}"
    echo "  clean build        Clean build artifacts"
    echo "  clean cache        Clean cache and temp files"
    echo "  docs serve         Serve documentation locally"
    echo ""
    
    echo -e "${BOLD}UPDATE COMMANDS:${NC}"
    echo "  update check       Check for available updates from GitHub"
    echo "  update apply       Apply available updates (with backup)"
    echo "  update rollback    Rollback to previous version"
    echo "  update status      Show current version and update status"
    echo ""
    
    echo -e "${BOLD}EXAMPLES:${NC}"
    echo "  $0 dev start       # Start development server"
    echo "  $0 build quick     # Build minimal ISO for testing"
    echo "  $0 build all       # Build both ISO and container"
    echo "  $0 test api        # Test if API is working"
    echo ""
}

# Main command handler
case "${1:-}" in
    "dev")
        case "${2:-}" in
            "start") dev_start ;;
            "stop") dev_stop ;;
            "status") dev_status ;;
            "setup") setup_dev ;;
            *) print_error "Unknown dev command: ${2:-}"; show_help ;;
        esac
        ;;
    "container")
        case "${2:-}" in
            "start") container_start ;;
            "stop") container_stop ;;
            "status") container_status ;;
            "logs") container_logs ;;
            *) print_error "Unknown container command: ${2:-}"; show_help ;;
        esac
        ;;
    "build")
        case "${2:-}" in
            "quick") build_quick_iso ;;
            "container") build_container ;;
            "full") build_full_iso ;;
            "fedora") build_fedora_bootable_iso ;;
            "all") build_all ;;
            "status") build_status ;;
            *) print_error "Unknown build command: ${2:-}"; show_help ;;
        esac
        ;;
    "test")
        case "${2:-}" in
            "run") test_run ;;
            "api") test_api ;;
            *) print_error "Unknown test command: ${2:-}"; show_help ;;
        esac
        ;;
    "clean")
        case "${2:-}" in
            "build") clean_build ;;
            "cache") clean_cache ;;
            *) print_error "Unknown clean command: ${2:-}"; show_help ;;
        esac
        ;;
    "docs")
        case "${2:-}" in
            "serve") docs_serve ;;
            *) print_error "Unknown docs command: ${2:-}"; show_help ;;
        esac
        ;;
    "update")
        case "${2:-}" in
            "check") update_check ;;
            "apply") update_apply ;;
            "rollback") update_rollback ;;
            "status") update_status ;;
            *) print_error "Unknown update command: ${2:-}"; show_help ;;
        esac
        ;;
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
