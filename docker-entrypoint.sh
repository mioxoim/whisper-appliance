#!/bin/bash
# Docker entrypoint for OpenAI Whisper Web Interface
# Handles SSL certificate generation and application startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
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

# Welcome message
echo "🎤 OpenAI Whisper Web Interface v1.0.0-rc1"
echo "=============================================="

# Check SSL certificates
SSL_CERT_PATH="${SSL_CERT_PATH:-/app/ssl/whisper-appliance.crt}"
SSL_KEY_PATH="${SSL_KEY_PATH:-/app/ssl/whisper-appliance.key}"

if [ ! -f "$SSL_CERT_PATH" ] || [ ! -f "$SSL_KEY_PATH" ]; then
    print_info "SSL certificates not found, generating new ones..."
    
    # Create SSL directory
    mkdir -p /app/ssl
    cd /app/ssl
    
    # Auto-detect container IP and create SAN certificate
    CONTAINER_IP=$(hostname -I | awk '{print $1}')
    print_info "Container IP: $CONTAINER_IP"
    
    # Build SAN list for Docker container
    SAN_LIST="DNS:localhost,DNS:$(hostname),IP:127.0.0.1"
    if [ ! -z "$CONTAINER_IP" ]; then
        SAN_LIST="${SAN_LIST},IP:${CONTAINER_IP}"
    fi
    
    # Add Docker network IPs if available
    for ip in $(hostname -I | tr ' ' '\n'); do
        if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && [ "$ip" != "127.0.0.1" ]; then
            SAN_LIST="${SAN_LIST},IP:${ip}"
        fi
    done
    
    print_info "SAN Configuration: $SAN_LIST"
    
    # Generate private key
    openssl genrsa -out whisper-appliance.key 2048
    
    # Generate certificate with SAN
    CN_VALUE="${CONTAINER_IP:-localhost}"
    if openssl req -help 2>&1 | grep -q "addext"; then
        # Modern OpenSSL
        openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt \
            -subj "/C=US/ST=Docker/L=Container/O=WhisperApp/OU=Docker/CN=${CN_VALUE}/emailAddress=admin@whisper-app.local" \
            -addext "subjectAltName=${SAN_LIST}"
    else
        # Legacy OpenSSL
        cat > ssl.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = Docker
L = Container
O = WhisperApp
OU = Docker
CN = ${CN_VALUE}
emailAddress = admin@whisper-app.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = ${SAN_LIST}
EOF
        openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt -config ssl.conf
        rm ssl.conf
    fi
    
    # Set permissions
    chmod 600 whisper-appliance.key
    chmod 644 whisper-appliance.crt
    
    print_success "SSL certificates generated successfully"
else
    print_info "Using existing SSL certificates"
fi

# Create data directories
mkdir -p /app/data /app/logs

# Set up Whisper model cache directory
export WHISPER_CACHE_DIR="/app/models"
mkdir -p "$WHISPER_CACHE_DIR"

# Pre-download default model if requested
if [ "${PRELOAD_MODEL:-false}" = "true" ]; then
    print_info "Pre-loading Whisper model: ${WHISPER_MODEL}"
    python3 -c "
import whisper
import os
os.environ['WHISPER_CACHE_DIR'] = '/app/models'
try:
    model = whisper.load_model('${WHISPER_MODEL}')
    print('✅ Model ${WHISPER_MODEL} loaded successfully')
except Exception as e:
    print(f'⚠️  Model loading failed: {e}')
    print('Model will be downloaded on first use')
"
fi

# Display startup information
print_success "Container initialization complete"
print_info "Configuration:"
print_info "  - Whisper Model: ${WHISPER_MODEL}"
print_info "  - HTTPS Port: ${HTTPS_PORT:-5001}"
print_info "  - Max Upload: ${MAX_UPLOAD_SIZE:-100MB}"
print_info "  - SSL Cert: $SSL_CERT_PATH"
print_info "  - Model Cache: $WHISPER_CACHE_DIR"

echo ""
print_info "🌐 Access URLs:"
print_info "  - Main Interface: https://localhost:${HTTPS_PORT:-5001}"
print_info "  - Admin Panel: https://localhost:${HTTPS_PORT:-5001}/admin"
print_info "  - API Docs: https://localhost:${HTTPS_PORT:-5001}/docs"
print_info "  - Health Check: https://localhost:${HTTPS_PORT:-5001}/health"

echo ""
print_warning "🔒 Note: Browser will show SSL warnings (self-signed certificate)"
print_info "         Click 'Advanced' → 'Continue to localhost' to proceed"

echo ""
print_info "🚀 Starting Flask application..."

# Execute the main command
exec "$@"
