#!/bin/bash
# Manual update script for Proxmox container

echo "🔄 Manual Update Script for WhisperS2T"
echo "======================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Navigate to application directory
cd /opt/whisper-appliance || exit

echo "📍 Current directory: $(pwd)"
echo "📊 Current version:"
git log --oneline -1

echo ""
echo "🔄 Fetching latest updates..."
git fetch origin main

echo ""
echo "📊 Available updates:"
git log HEAD..origin/main --oneline

echo ""
read -p "📥 Pull latest updates? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⬇️ Pulling updates..."
    git pull origin main
    
    echo ""
    echo "📦 Installing dependencies if needed..."
    pip3 install -r requirements.txt
    
    echo ""
    echo "🔄 Restarting service..."
    systemctl restart whisper-appliance
    
    echo ""
    echo "✅ Update complete!"
    echo "📊 New version:"
    git log --oneline -1
else
    echo "❌ Update cancelled"
fi
