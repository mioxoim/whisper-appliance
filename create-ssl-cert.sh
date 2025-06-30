#!/bin/bash
# Intelligent SSL Certificate Generator for WhisperS2T Appliance v0.8.0
# Auto-detects IPs and creates certificates with SAN for network access
# Enables HTTPS for microphone access in browsers across the network

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

echo "🔐 Creating Intelligent SSL Certificate for WhisperS2T Appliance v0.9.0..."

# Auto-detect container/host IP addresses
print_status "🔍 Auto-detecting IP addresses for SAN certificate..."

# Get all IP addresses (excluding loopback)
LOCAL_IPS=$(hostname -I | tr ' ' '\n' | grep -v '^127\.' | grep -v '^::1' | head -5)
EXTERNAL_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "")

# Build SAN list dynamically
SAN_LIST="DNS:localhost,DNS:$(hostname)"

# Add local IPs to SAN
IP_COUNT=1
for ip in $LOCAL_IPS; do
    if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        SAN_LIST="${SAN_LIST},IP:${ip}"
        print_status "📍 Added local IP to SAN: $ip"
        ((IP_COUNT++))
    fi
done

# Add external IP if available and different from local IPs
if [ -n "$EXTERNAL_IP" ] && [[ $EXTERNAL_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    if ! echo "$LOCAL_IPS" | grep -q "$EXTERNAL_IP"; then
        SAN_LIST="${SAN_LIST},IP:${EXTERNAL_IP}"
        print_status "🌐 Added external IP to SAN: $EXTERNAL_IP"
        ((IP_COUNT++))
    fi
fi

print_status "🎯 SAN Configuration: $SAN_LIST"

# Create SSL directory if it doesn't exist
mkdir -p ssl || exit 1
cd ssl || exit 1

# Use primary local IP for CN (Common Name)
PRIMARY_IP=$(echo "$LOCAL_IPS" | head -1)
if [ -z "$PRIMARY_IP" ]; then
    PRIMARY_IP="localhost"
    print_warning "⚠️  No local IP detected, using localhost as CN"
else
    print_status "🎯 Using primary IP as CN: $PRIMARY_IP"
fi

# Generate private key
print_status "📝 Generating 2048-bit RSA private key..."
openssl genrsa -out whisper-appliance.key 2048

# Generate self-signed certificate with SAN (OpenSSL 1.1.1+ method)
print_status "🔒 Generating self-signed certificate with SAN support..."

# Check OpenSSL version and use appropriate method
OPENSSL_VERSION=$(openssl version | cut -d' ' -f2)
print_status "🔧 OpenSSL Version: $OPENSSL_VERSION"

# Use modern OpenSSL addext flag if available (1.1.1+)
if openssl req -help 2>&1 | grep -q "addext"; then
    print_status "✅ Using modern OpenSSL -addext method"
    openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt \
        -subj "/C=DE/ST=NRW/L=Container/O=WhisperS2T/OU=Production/CN=${PRIMARY_IP}/emailAddress=admin@whisper-appliance.local" \
        -addext "subjectAltName=${SAN_LIST}"
else
    # Fallback for older OpenSSL versions using config file
    print_status "🔄 Using legacy OpenSSL config file method"
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
CN = ${PRIMARY_IP}
emailAddress = admin@whisper-appliance.local

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = ${SAN_LIST}
EOF

    openssl req -x509 -new -key whisper-appliance.key -sha256 -days 365 -out whisper-appliance.crt \
        -config ssl.conf
    
    # Clean up config file
    rm ssl.conf
fi

# Set appropriate permissions
chmod 600 whisper-appliance.key
chmod 644 whisper-appliance.crt

# Verify certificate SAN
print_status "🔍 Verifying certificate SAN configuration..."
openssl x509 -in whisper-appliance.crt -text -noout | grep -A5 "Subject Alternative Name" || true

print_success "✅ Intelligent SSL Certificate created successfully!"
print_success ""
print_success "📁 Files created:"
print_success "   - ssl/whisper-appliance.key (Private Key)"
print_success "   - ssl/whisper-appliance.crt (Certificate with SAN)"
print_success ""
print_success "🌐 HTTPS will be available at:"
print_success "   📍 https://localhost:5001"
for ip in $LOCAL_IPS; do
    if [[ $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_success "   🔗 https://${ip}:5001"
    fi
done

if [ -n "$EXTERNAL_IP" ] && [[ $EXTERNAL_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_success "   🌍 https://${EXTERNAL_IP}:5001"
fi

print_success ""
print_success "🎙️ Microphone Access: ✅ Enabled for ALL configured IPs"
print_success "⚠️  Browser Security Warning: Click 'Advanced' → 'Continue to site'"
print_success "🔒 Certificate valid for 365 days"
print_success ""
print_warning "📝 Note: Add certificate to your browser's trusted roots for production use"
