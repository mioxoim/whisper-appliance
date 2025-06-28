#!/bin/bash
# Quick minimal test build

set -e

echo "🧪 Quick Minimal Test Build"

KS_FILE="/home/commander/Code/whisper-appliance/build/fedora-iso/fedora-live-minimal-test.ks"
CACHED_ISO="/home/commander/Code/whisper-appliance/cache/Fedora-Server-netinst-x86_64-Rawhide.iso"

# Clean and start fresh
mock -r fedora-rawhide-x86_64 --clean
mock -r fedora-rawhide-x86_64 --init

# Install tools
mock -r fedora-rawhide-x86_64 --install lorax anaconda-tui

# Copy files
mock -r fedora-rawhide-x86_64 --copyin "$KS_FILE" /builddir/test.ks
mock -r fedora-rawhide-x86_64 --copyin "$CACHED_ISO" /builddir/fedora.iso

echo "🚀 Starting MINIMAL test build (should take 15-30 minutes)..."

# Run with timeout
timeout 45m mock -r fedora-rawhide-x86_64 --enable-network --chroot -- livemedia-creator \
    --ks /builddir/test.ks \
    --no-virt \
    --resultdir /builddir/results \
    --project "Test" \
    --make-iso \
    --volid "Test" \
    --iso-only \
    --iso-name "test.iso" \
    --releasever 42 \
    --iso /builddir/fedora.iso

echo "✅ Test completed!"
