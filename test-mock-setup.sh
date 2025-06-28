#!/bin/bash
# Quick test for Fedora 42 Mock setup

echo "🔧 Testing Fedora 42 Mock Environment..."

# Test mock group membership
if groups | grep -q mock; then
    echo "✅ User is in mock group"
else
    echo "❌ User NOT in mock group - logout/login required"
    exit 1
fi

# Test mock command
if command -v mock &> /dev/null; then
    echo "✅ Mock command available"
else
    echo "❌ Mock command not found"
    exit 1
fi

# Test mock configuration
echo "🔍 Available mock configurations:"
mock --list-chroots | grep fedora | head -5

# Test if fedora-rawhide config exists
if mock -r fedora-rawhide-x86_64 --print-root-path &> /dev/null; then
    echo "✅ Fedora Rawhide mock config available"
else
    echo "❌ Fedora Rawhide mock config not found"
    echo "Available configs:"
    mock --list-chroots | grep fedora
fi

# Test basic mock functionality
echo "🧪 Testing mock initialization..."
if mock -r fedora-rawhide-x86_64 --init --quiet; then
    echo "✅ Mock initialization successful"
    mock -r fedora-rawhide-x86_64 --clean
else
    echo "❌ Mock initialization failed"
    echo "Try: mock -r fedora-rawhide-x86_64 --init"
fi

echo ""
echo "🎯 If all checks pass, you can run:"
echo "   ./dev.sh build fedora"
echo ""
