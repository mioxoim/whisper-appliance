#!/bin/bash
# Self-Signed SSL Certificate Generator for WhisperS2T Appliance
# Enables HTTPS for microphone access in browsers

set -e

echo "🔐 Creating Self-Signed SSL Certificate for WhisperS2T Appliance..."

# Create SSL directory if it doesn't exist
mkdir -p ssl || exit 1
cd ssl || exit 1

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out whisper-appliance.key 2048

# Generate certificate signing request
echo "📄 Creating certificate signing request..."
openssl req -new -key whisper-appliance.key -out whisper-appliance.csr -subj "/C=DE/ST=NRW/L=Cologne/O=WhisperS2T/OU=Development/CN=localhost/emailAddress=admin@whisper-appliance.local"

# Generate self-signed certificate (valid for 365 days)
echo "🔒 Generating self-signed certificate..."
openssl x509 -req -in whisper-appliance.csr -signkey whisper-appliance.key -out whisper-appliance.crt -days 365

# Set appropriate permissions
chmod 600 whisper-appliance.key
chmod 644 whisper-appliance.crt

echo "✅ SSL Certificate created successfully!"
echo "📁 Files created:"
echo "   - ssl/whisper-appliance.key (Private Key)"
echo "   - ssl/whisper-appliance.crt (Certificate)"
echo "   - ssl/whisper-appliance.csr (Certificate Request)"
echo ""
echo "🌐 HTTPS will be available at: https://localhost:5001"
echo "⚠️  Browser will show security warning for self-signed certificate - this is normal!"
echo "   Click 'Advanced' → 'Continue to localhost' to proceed"
