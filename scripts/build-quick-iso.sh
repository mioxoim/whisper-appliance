#!/bin/bash

# Enhanced WhisperS2T Appliance v0.5.0 - Quick ISO Build
# Creates a bootable ISO for rapid deployment testing

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[BUILD]${NC} $1"
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

# Configuration
APPLIANCE_NAME="WhisperS2T-Appliance"
VERSION="0.5.0"
SCRIPT_DIR="$(dirname "$0")"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$ROOT_DIR/build"
ISO_DIR="$BUILD_DIR/iso-build"
OUTPUT_DIR="$BUILD_DIR/output"

print_step "Enhanced WhisperS2T Appliance Quick ISO Builder v$VERSION"
print_step "============================================================="

# Check for required tools
MISSING_TOOLS=""
for tool in mkisofs genisoimage xorriso; do
    if command -v $tool &> /dev/null; then
        ISO_TOOL=$tool
        break
    else
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

if [ -z "$ISO_TOOL" ]; then
    print_error "No ISO creation tool found!"
    print_warning "Please install one of: mkisofs, genisoimage, or xorriso"
    echo "  Fedora: sudo dnf install genisoimage xorriso"
    echo "  Ubuntu: sudo apt install genisoimage xorriso"
    exit 1
fi

print_success "Using $ISO_TOOL for ISO creation"

# Create build directories
rm -rf "$ISO_DIR"
mkdir -p "$ISO_DIR"
mkdir -p "$OUTPUT_DIR"

print_step "Creating ISO filesystem structure..."

# Create basic directory structure
mkdir -p "$ISO_DIR"/{boot,whisper-appliance,isolinux}

# Copy application files
print_step "Copying application files..."
cp -r "$ROOT_DIR/src" "$ISO_DIR/whisper-appliance/"
cp "$ROOT_DIR/requirements.txt" "$ISO_DIR/whisper-appliance/"
cp "$ROOT_DIR/README.md" "$ISO_DIR/whisper-appliance/"
cp "$ROOT_DIR/ARCHITECTURE.md" "$ISO_DIR/whisper-appliance/"

# Create container-ready requirements (lightweight)
cat > "$ISO_DIR/whisper-appliance/requirements-lite.txt" << 'LITE_REQS'
# Enhanced WhisperS2T Appliance v0.5.0 - Lite Requirements
# Minimal setup for quick testing and development

# Core Web Framework Dependencies
fastapi==0.115.13
uvicorn==0.34.3
websockets==15.0.1

# Audio Processing Dependencies (basic)
pydub==0.25.1

# Basic Speech Recognition (CPU-only, smaller models)
openai-whisper==20240930

# Scientific Computing Dependencies (minimal)
numpy>=1.21.0

# Web Framework Extensions
starlette>=0.40.0
python-multipart>=0.0.5

# System Monitoring Dependencies
psutil>=5.8.0

# Utility Dependencies
python-dateutil>=2.8.0
typing-extensions>=4.8.0

# Note: This is a lightweight setup for quick deployment testing
# For production use, install the full requirements.txt
LITE_REQS

# Create installation script
cat > "$ISO_DIR/whisper-appliance/install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash

# Enhanced WhisperS2T Appliance v0.5.0 - Quick Install
echo "🎤 Installing Enhanced WhisperS2T Appliance v0.5.0"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements-lite.txt" ]; then
    echo "❌ Installation files not found"
    echo "Please run this script from the whisper-appliance directory"
    exit 1
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "⬇️  Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-lite.txt

# Create startup script
cat > start-appliance.sh << 'STARTUP'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
cd src/webgui/backend
echo "🎤 Starting Enhanced WhisperS2T Appliance v0.5.0"
echo "🌐 Web Interface: http://localhost:5000"
echo "🔧 Admin Panel: http://localhost:5000/admin"
echo "🎙️ Demo Interface: http://localhost:5000/demo"
echo ""
echo "Press Ctrl+C to stop the appliance"
python start_appliance.py
STARTUP

chmod +x start-appliance.sh

echo ""
echo "✅ Enhanced WhisperS2T Appliance installed successfully!"
echo ""
echo "🚀 Quick Start:"
echo "   ./start-appliance.sh"
echo ""
echo "🌐 Web Interfaces:"
echo "   Main:  http://localhost:5000"
echo "   Admin: http://localhost:5000/admin"
echo "   Demo:  http://localhost:5000/demo"
echo ""
echo "📚 Documentation:"
echo "   README.md - User guide"
echo "   ARCHITECTURE.md - Technical details"
echo ""
echo "⚠️  Note: This is a lite installation for quick testing"
echo "   For full features, install requirements.txt instead"
INSTALL_SCRIPT

chmod +x "$ISO_DIR/whisper-appliance/install.sh"

# Create autorun script for ISO
cat > "$ISO_DIR/autorun.sh" << 'AUTORUN'
#!/bin/bash

echo "🎤 Enhanced WhisperS2T Appliance v0.5.0 - Quick Deploy ISO"
echo "============================================================="
echo ""
echo "This ISO contains the Enhanced WhisperS2T Appliance for quick deployment."
echo ""
echo "Installation Options:"
echo ""
echo "1. Copy to local system:"
echo "   cp -r /media/cdrom/whisper-appliance ~/whisper-appliance"
echo "   cd ~/whisper-appliance"
echo "   ./install.sh"
echo ""
echo "2. Run directly from ISO (if filesystem is writable):"
echo "   cd /media/cdrom/whisper-appliance"
echo "   ./install.sh"
echo ""
echo "3. Container deployment:"
echo "   podman load -i /media/cdrom/whisper-appliance-container.tar"
echo "   podman run -p 5000:5000 whisper-appliance:0.5.0"
echo ""
echo "🌐 After installation, access via:"
echo "   http://localhost:5000"
echo ""
AUTORUN

chmod +x "$ISO_DIR/autorun.sh"

# Create ISO label file
cat > "$ISO_DIR/README.txt" << 'README'
Enhanced WhisperS2T Appliance v0.5.0 - Quick Deploy ISO
=======================================================

This ISO contains:
- Complete Enhanced WhisperS2T Appliance source code
- Lite installation script for quick testing
- Documentation and setup guides
- Container image (if built)

Quick Start:
1. Copy whisper-appliance folder to your system
2. Run ./install.sh in the copied folder
3. Start with ./start-appliance.sh
4. Access http://localhost:5000

For more information, see README.md

Build Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
README

# Copy container if it exists
if [ -f "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar" ]; then
    print_step "Including container image in ISO..."
    cp "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar" "$ISO_DIR/"
    
    # Add container instructions
    cat >> "$ISO_DIR/README.txt" << 'CONTAINER_INFO'

Container Deployment:
- Container file: whisper-appliance-v0.5.0-container.tar
- Load: podman load -i whisper-appliance-v0.5.0-container.tar
- Run: podman run -p 5000:5000 whisper-appliance:0.5.0
CONTAINER_INFO
fi

# Create ISO image
print_step "Creating ISO image..."

ISO_FILE="$OUTPUT_DIR/whisper-appliance-v${VERSION}-deploy.iso"

$ISO_TOOL \
    -o "$ISO_FILE" \
    -b isolinux/isolinux.bin \
    -c isolinux/boot.cat \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    -J -R -V "WhisperS2T_v${VERSION}" \
    "$ISO_DIR" 2>/dev/null || {
    
    # Fallback: Create simple ISO without bootloader
    print_warning "Bootable ISO creation failed, creating data ISO instead..."
    
    if command -v genisoimage &> /dev/null; then
        genisoimage -o "$ISO_FILE" -J -R -V "WhisperS2T_v${VERSION}" "$ISO_DIR"
    elif command -v mkisofs &> /dev/null; then
        mkisofs -o "$ISO_FILE" -J -R -V "WhisperS2T_v${VERSION}" "$ISO_DIR"
    elif command -v xorriso &> /dev/null; then
        xorriso -as mkisofs -o "$ISO_FILE" -J -R -V "WhisperS2T_v${VERSION}" "$ISO_DIR"
    else
        print_error "No working ISO tool found!"
        exit 1
    fi
}

if [ $? -eq 0 ]; then
    print_success "ISO created successfully!"
else
    print_error "ISO creation failed"
    exit 1
fi

# Generate checksums
cd "$OUTPUT_DIR"
sha256sum "$(basename "$ISO_FILE")" > "$(basename "$ISO_FILE").sha256"

# Create deployment info
cat > "$OUTPUT_DIR/deployment-info.txt" << INFO
Enhanced WhisperS2T Appliance v$VERSION - Quick Deploy ISO
==========================================================

Deployment Information:
- Build Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- ISO File: $(basename "$ISO_FILE")
- Size: $(du -h "$ISO_FILE" | cut -f1)
- Type: Data ISO (bootable on compatible systems)

Checksum:
- SHA256: $(cat "$(basename "$ISO_FILE").sha256" | cut -d' ' -f1)

Quick Deployment:
1. Mount or copy ISO contents
2. Copy whisper-appliance/ to target system
3. Run ./install.sh in the directory
4. Start with ./start-appliance.sh
5. Access http://localhost:5000

Contents:
✅ Complete source code
✅ Lite installation script
✅ Documentation and guides
✅ Container image (if available)
$([ -f "$ISO_DIR/whisper-appliance-v${VERSION}-container.tar" ] && echo "✅ Container deployment ready" || echo "⚠️  Container not included")

Features:
✅ Quick installation (lite dependencies)
✅ Web-based interface
✅ Real-time speech recognition
✅ Admin dashboard
✅ Demo interface
✅ GDPR-compliant local processing

System Requirements:
- Python 3.8+
- 2GB+ RAM (4GB recommended)
- 2GB+ disk space
- Internet connection for dependency installation

For production deployment with full features,
use the complete requirements.txt instead of requirements-lite.txt
INFO

print_success "Quick Deploy ISO completed successfully!"
echo ""
print_step "Deployment Summary:"
echo "ISO File: $ISO_FILE"
echo "Size: $(du -h "$ISO_FILE" | cut -f1)"
echo "SHA256: $(cat "$(basename "$ISO_FILE").sha256" | cut -d' ' -f1)"
echo ""
print_step "Quick Test:"
echo "Mount: sudo mount -o loop '$ISO_FILE' /mnt"
echo "Copy: cp -r /mnt/whisper-appliance ~/"
echo "Install: cd ~/whisper-appliance && ./install.sh"
echo "Start: ./start-appliance.sh"
echo ""
print_success "🎉 Enhanced WhisperS2T Appliance Quick Deploy ISO ready!"
