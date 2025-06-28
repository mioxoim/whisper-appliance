#!/bin/bash
# Alternative: Use livecd-creator instead of livemedia-creator
# This might be simpler for our use case

echo "🔄 ALTERNATIVE APPROACH: Using stable tools"

# Check if we're on Fedora 41 stable instead of Rawhide
echo "Current Fedora version:"
cat /etc/fedora-release

echo ""
echo "📋 RECOMMENDED NEXT STEPS:"
echo ""
echo "Option 1: Switch to Fedora 41 stable repos"
echo "  - More stable than Rawhide"
echo "  - Better library compatibility"
echo ""
echo "Option 2: Use livecd-creator (simpler tool)"
echo "  - Fewer dependencies"
echo "  - More reliable for basic Live ISOs"
echo ""
echo "Option 3: Use existing Fedora Spin as base"
echo "  - Customize existing Live ISO"
echo "  - Add WhisperS2T afterwards"
echo ""

echo "🚨 The livblockdev error suggests Mock environment issues"
echo "   that might require system-level fixes"
