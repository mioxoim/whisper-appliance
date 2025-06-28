#!/bin/bash

# Enhanced WhisperS2T Appliance v0.5.0 - Fedora-compatible Container Build
# Alternative approach using Podman/Docker for cross-platform building

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
OUTPUT_DIR="$BUILD_DIR/output"

print_step "Enhanced WhisperS2T Appliance Container Builder v$VERSION"
print_step "========================================================="

# Check if we have Podman or Docker
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    print_success "Using Podman for container building"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    print_success "Using Docker for container building"
else
    print_error "Neither Podman nor Docker found!"
    echo "Please install one of them:"
    echo "  Fedora: sudo dnf install podman"
    echo "  Ubuntu: sudo apt install docker.io"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

print_step "Creating containerized WhisperS2T Appliance..."

# Create Dockerfile for the appliance
cat > "$BUILD_DIR/Dockerfile" << 'DOCKERFILE'
FROM debian:12-slim

# Metadata
LABEL name="Enhanced WhisperS2T Appliance"
LABEL version="0.5.0"
LABEL description="Production-ready Speech-to-Text Network Appliance"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV WHISPER_APPLIANCE_VERSION=0.5.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    alsa-utils \
    pulseaudio \
    curl \
    wget \
    htop \
    vim \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create whisper user
RUN useradd -m -s /bin/bash whisper && \
    echo "whisper:whisper" | chpasswd

# Create application directory
RUN mkdir -p /opt/whisper-appliance
WORKDIR /opt/whisper-appliance

# Copy application files
COPY src/ ./src/
COPY requirements-container.txt ./requirements.txt
COPY README.md ./
COPY ARCHITECTURE.md ./

# Set ownership
RUN chown -R whisper:whisper /opt/whisper-appliance

# Switch to whisper user
USER whisper

# Create Python virtual environment
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Create startup script
RUN echo '#!/bin/bash' > /opt/whisper-appliance/start.sh && \
    echo 'cd /opt/whisper-appliance' >> /opt/whisper-appliance/start.sh && \
    echo 'source venv/bin/activate' >> /opt/whisper-appliance/start.sh && \
    echo 'cd src/webgui/backend' >> /opt/whisper-appliance/start.sh && \
    echo 'python start_appliance.py' >> /opt/whisper-appliance/start.sh && \
    chmod +x /opt/whisper-appliance/start.sh

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Set working directory
WORKDIR /opt/whisper-appliance/src/webgui/backend

# Default command
CMD ["/opt/whisper-appliance/start.sh"]
DOCKERFILE

print_success "Dockerfile created"

# Build the container image
print_step "Building container image..."

cd "$ROOT_DIR"
$CONTAINER_CMD build -t whisper-appliance:$VERSION -f "$BUILD_DIR/Dockerfile" .

if [ $? -eq 0 ]; then
    print_success "Container image built successfully"
else
    print_error "Container build failed"
    exit 1
fi

# Export container as tar archive
print_step "Exporting container image..."

CONTAINER_FILE="$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar"
$CONTAINER_CMD save whisper-appliance:$VERSION -o "$CONTAINER_FILE"

print_success "Container exported to: $CONTAINER_FILE"

# Create VM disk image using the container
print_step "Creating VM-ready disk image..."

# Create a simple run script for the container
cat > "$OUTPUT_DIR/run-whisper-appliance.sh" << 'RUNSCRIPT'
#!/bin/bash

# Enhanced WhisperS2T Appliance Container Runner
echo "🎤 Starting Enhanced WhisperS2T Appliance v0.5.0"

# Check if container runtime is available
if command -v podman &> /dev/null; then
    RUNTIME="podman"
elif command -v docker &> /dev/null; then
    RUNTIME="docker"
else
    echo "❌ No container runtime found (podman or docker required)"
    exit 1
fi

# Load container if not already loaded
if ! $RUNTIME images | grep -q whisper-appliance:0.5.0; then
    echo "📦 Loading WhisperS2T Appliance container..."
    $RUNTIME load -i whisper-appliance-v0.5.0-container.tar
fi

# Run the appliance
echo "🚀 Starting WhisperS2T Appliance container..."
echo "🌐 Web Interface will be available at: http://localhost:5000"
echo "🔧 Admin Interface: http://localhost:5000/admin"
echo "🎙️ Demo Interface: http://localhost:5000/demo"
echo ""
echo "Press Ctrl+C to stop the appliance"

$RUNTIME run --rm -it \
    --name whisper-appliance \
    -p 5000:5000 \
    -v whisper-models:/home/whisper/.cache \
    --device /dev/snd \
    whisper-appliance:0.5.0
RUNSCRIPT

chmod +x "$OUTPUT_DIR/run-whisper-appliance.sh"

# Create Docker Compose file for easy deployment
cat > "$OUTPUT_DIR/docker-compose.yml" << 'COMPOSE'
version: '3.8'

services:
  whisper-appliance:
    image: whisper-appliance:0.5.0
    container_name: whisper-appliance
    ports:
      - "5000:5000"
    volumes:
      - whisper-models:/home/whisper/.cache
      - whisper-logs:/var/log
    devices:
      - "/dev/snd:/dev/snd"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  whisper-models:
    driver: local
  whisper-logs:
    driver: local
COMPOSE

# Create installation guide
cat > "$OUTPUT_DIR/INSTALLATION.md" << 'INSTALL'
# 🎤 Enhanced WhisperS2T Appliance v0.5.0 - Container Installation

## Quick Start

### Option 1: Direct Container Run
```bash
# Load and run the appliance
./run-whisper-appliance.sh
```

### Option 2: Docker Compose (Recommended)
```bash
# Load the container image first
podman load -i whisper-appliance-v0.5.0-container.tar
# or
docker load -i whisper-appliance-v0.5.0-container.tar

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 3: Manual Container Run
```bash
# Load image
podman load -i whisper-appliance-v0.5.0-container.tar

# Run container
podman run -d \
  --name whisper-appliance \
  -p 5000:5000 \
  -v whisper-models:/home/whisper/.cache \
  whisper-appliance:0.5.0
```

## Access Points

- **Web Interface:** http://localhost:5000
- **Admin Dashboard:** http://localhost:5000/admin  
- **Demo Interface:** http://localhost:5000/demo
- **API Documentation:** http://localhost:5000/docs
- **Health Check:** http://localhost:5000/health

## System Requirements

- **Minimum:** 2GB RAM, 2 CPU cores
- **Recommended:** 4GB RAM, 4 CPU cores
- **Container Runtime:** Podman or Docker
- **Disk Space:** 5GB free space

## Management

```bash
# View logs
podman logs whisper-appliance

# Stop appliance
podman stop whisper-appliance

# Start appliance
podman start whisper-appliance

# Update appliance
podman pull whisper-appliance:latest
```

## Production Deployment

For production use, consider:
- Using Docker Swarm or Kubernetes for orchestration
- Setting up reverse proxy (nginx/traefik) for SSL
- Implementing backup strategy for models and configuration
- Monitoring with Prometheus/Grafana
- Log aggregation with ELK stack

## Troubleshooting

### Audio Issues
```bash
# Check audio device access
ls -la /dev/snd/

# Run with additional audio privileges
podman run --privileged -p 5000:5000 whisper-appliance:0.5.0
```

### Performance Issues
```bash
# Check container resources
podman stats whisper-appliance

# Increase memory limit
podman run -m 4g -p 5000:5000 whisper-appliance:0.5.0
```

## Support

- Documentation: README.md
- Architecture: ARCHITECTURE.md
- Issues: GitHub Issues
- Community: GitHub Discussions
INSTALL

print_success "Container deployment created successfully!"

# Generate checksums
cd "$OUTPUT_DIR"
sha256sum "whisper-appliance-v${VERSION}-container.tar" > "whisper-appliance-v${VERSION}-container.tar.sha256"

# Create build information
cat > "$OUTPUT_DIR/build-info.txt" << BUILDINFO
Enhanced WhisperS2T Appliance v$VERSION - Container Build
=========================================================

Build Information:
- Build Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- Container File: whisper-appliance-v${VERSION}-container.tar
- Size: $(du -h "whisper-appliance-v${VERSION}-container.tar" | cut -f1)
- Base Image: Debian 12 (Bookworm)
- Runtime: Container (Podman/Docker)

Checksum:
- SHA256: $(cat "whisper-appliance-v${VERSION}-container.tar.sha256" | cut -d' ' -f1)

Quick Start:
1. Load container: podman load -i whisper-appliance-v${VERSION}-container.tar
2. Run appliance: ./run-whisper-appliance.sh
3. Access web interface: http://localhost:5000

Features:
✅ Real-time microphone integration
✅ Advanced system resource management  
✅ Multiple Whisper model support (tiny to large)
✅ Web-based administration interface
✅ Container-based deployment
✅ GDPR-compliant local processing
✅ Health monitoring and metrics
✅ Multi-language support (6+ languages)

Container Management:
- Start: podman start whisper-appliance
- Stop: podman stop whisper-appliance  
- Logs: podman logs whisper-appliance
- Stats: podman stats whisper-appliance

For production deployment, see INSTALLATION.md
BUILDINFO

print_success "Build completed successfully!"
echo ""
print_step "Build Summary:"
echo "Container File: $OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar"
echo "Size: $(du -h "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar" | cut -f1)"
echo "SHA256: $(cat "$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar.sha256" | cut -d' ' -f1)"
echo ""
print_step "Quick Test:"
echo "Load: $CONTAINER_CMD load -i '$OUTPUT_DIR/whisper-appliance-v${VERSION}-container.tar'"
echo "Run: cd '$OUTPUT_DIR' && ./run-whisper-appliance.sh"
echo ""
print_success "🎉 Enhanced WhisperS2T Appliance Container ready for deployment!"
