#!/bin/bash
# Build WhisperS2T Live ISO using official Fedora methods
# Based on: https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD

set -e

VERSION="0.6.0"
ISO_NAME="whisper-appliance-v${VERSION}-live.iso"
WORK_DIR="/home/commander/Code/whisper-appliance"
KS_FILE="$WORK_DIR/build/fedora-iso/fedora-live-whisper.ks"
OUTPUT_DIR="$WORK_DIR/build/output"
CACHED_ISO="$WORK_DIR/cache/Fedora-Server-netinst-x86_64-Rawhide.iso"

echo "🎤 WhisperS2T Appliance Live ISO Builder v${VERSION}"
echo "Using official Fedora live templates and methods"

# Check cached ISO
if [ ! -f "$CACHED_ISO" ]; then
    echo "❌ Cached Fedora ISO not found: $CACHED_ISO"
    echo "Please download it first:"
    echo "cd $WORK_DIR/cache"
    echo "wget -O Fedora-Server-netinst-x86_64-Rawhide.iso \\"
    echo "  'https://download.fedoraproject.org/pub/fedora/linux/development/rawhide/Server/x86_64/iso/Fedora-Server-netinst-x86_64-Rawhide-\$(date +%Y%m%d).n.0.iso'"
    exit 1
fi

echo "✅ Using cached ISO: $CACHED_ISO"

# Validate kickstart
echo "🔍 Validating kickstart file..."
if command -v ksvalidator >/dev/null 2>&1; then
    ksvalidator "$KS_FILE" || {
        echo "❌ Kickstart validation failed!"
        exit 1
    }
    echo "✅ Kickstart validation passed"
else
    echo "⚠️  ksvalidator not found, skipping validation"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
rm -rf "$OUTPUT_DIR"/*

echo "🚀 Starting ISO build with livemedia-creator..."
echo "This will take 30-60 minutes..."

# Build the ISO using the new approach
mock -r fedora-rawhide-x86_64 --clean
mock -r fedora-rawhide-x86_64 --init

# Install livemedia-creator in mock environment
echo "📦 Installing livemedia-creator in mock..."
mock -r fedora-rawhide-x86_64 --install lorax anaconda-tui lorax-lmc-novirt

# Copy files into mock
echo "📋 Copying files to mock environment..."
mock -r fedora-rawhide-x86_64 --copyin "$KS_FILE" /builddir/whisper.ks
mock -r fedora-rawhide-x86_64 --copyin "$CACHED_ISO" /builddir/fedora.iso

# Run livemedia-creator in mock
echo "⚙️  Running livemedia-creator..."
mock -r fedora-rawhide-x86_64 --enable-network --chroot -- livemedia-creator \
    --ks /builddir/whisper.ks \
    --no-virt \
    --resultdir /builddir/results \
    --project "WhisperS2T-Appliance" \
    --make-iso \
    --volid "WhisperS2T-v${VERSION}" \
    --iso-only \
    --iso-name "$ISO_NAME" \
    --releasever 42 \
    --macboot \
    --iso /builddir/fedora.iso

# Copy results out
echo "📤 Copying results..."
mock -r fedora-rawhide-x86_64 --copyout /builddir/results/ "$OUTPUT_DIR/results/"

# Find and copy the ISO
if [ -f "$OUTPUT_DIR/results/images/$ISO_NAME" ]; then
    cp "$OUTPUT_DIR/results/images/$ISO_NAME" "$OUTPUT_DIR/"
    
    ISO_SIZE=$(du -h "$OUTPUT_DIR/$ISO_NAME" | cut -f1)
    echo "🎉 SUCCESS! Live ISO created:"
    echo "   File: $OUTPUT_DIR/$ISO_NAME"
    echo "   Size: $ISO_SIZE"
    echo ""
    echo "🚀 You can now boot this ISO on any system to run WhisperS2T!"
else
    echo "❌ Error: ISO file not found in build results"
    echo "Available files:"
    find "$OUTPUT_DIR/results" -name "*.iso" -o -name "*.img" 2>/dev/null || echo "No ISO/IMG files found"
    exit 1
fi
