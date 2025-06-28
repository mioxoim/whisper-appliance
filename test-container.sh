#!/bin/bash
# Test Container Installation for WhisperS2T Appliance
# Tests all core functionality after container deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${BLUE}=== WhisperS2T Container Installation Test ===${NC}"
echo -e "Container IP: ${YELLOW}$CONTAINER_IP${NC}"
echo ""

# Test 1: Service Status
print_test "Checking whisper-appliance service status"
if systemctl is-active --quiet whisper-appliance; then
    print_pass "Service is running"
else
    print_fail "Service is not running"
    print_info "Checking service logs..."
    journalctl -u whisper-appliance -n 10 --no-pager
    exit 1
fi

# Test 2: Nginx Status  
print_test "Checking nginx service status"
if systemctl is-active --quiet nginx; then
    print_pass "Nginx is running"
else
    print_fail "Nginx is not running"
    exit 1
fi

# Test 3: Port Listening
print_test "Checking if port 5000 is listening"
if netstat -tlnp | grep -q ":5000 "; then
    print_pass "Port 5000 is listening"
else
    print_fail "Port 5000 is not listening"
    print_info "Current listening ports:"
    netstat -tlnp | grep LISTEN
    exit 1
fi

# Test 4: Health Endpoint
print_test "Testing health endpoint"
if curl -s "http://127.0.0.1:5000/health" > /dev/null; then
    print_pass "Health endpoint accessible"
    
    # Check health response
    health_response=$(curl -s "http://127.0.0.1:5000/health")
    if echo "$health_response" | grep -q '"status": "healthy"'; then
        print_pass "Health check returns healthy status"
    else
        print_fail "Health check shows unhealthy status"
        print_info "Health response: $health_response"
    fi
else
    print_fail "Health endpoint not accessible"
    exit 1
fi

# Test 5: Web Interface
print_test "Testing web interface"  
if curl -s "http://127.0.0.1:5000/" | grep -q "WhisperS2T Appliance"; then
    print_pass "Web interface accessible"
else
    print_fail "Web interface not accessible"
    exit 1
fi

# Test 6: Python Dependencies
print_test "Checking Python dependencies"
if sudo -u whisper python3 -c "import whisper, flask, torch" 2>/dev/null; then
    print_pass "Core Python dependencies available"
else
    print_fail "Missing Python dependencies"
    print_info "Testing individual imports..."
    
    # Test individual packages
    for pkg in whisper flask torch; do
        if sudo -u whisper python3 -c "import $pkg" 2>/dev/null; then
            echo "  ✓ $pkg"
        else  
            echo "  ✗ $pkg"
        fi
    done
    exit 1
fi

# Test 7: Whisper Model Loading
print_test "Testing Whisper model loading (this may take a few minutes on first run)"
if timeout 300 sudo -u whisper python3 -c "import whisper; model = whisper.load_model('base'); print('Model loaded successfully')" 2>/dev/null; then
    print_pass "Whisper model loads successfully"
else
    print_fail "Whisper model failed to load"
    print_info "This might be normal on first run - model download can take time"
fi

# Test 8: File Permissions
print_test "Checking file permissions"
if [ -w "/opt/whisper-appliance" ] && [ -w "/opt/whisper-appliance/uploads" ]; then
    print_pass "File permissions correct"
else
    print_fail "File permission issues detected"
    ls -la /opt/whisper-appliance/
fi

# Test 9: System Resources
print_test "Checking system resources"
mem_total=$(free -m | awk 'NR==2{printf "%.0f", $2}')
mem_available=$(free -m | awk 'NR==2{printf "%.0f", $7}')
disk_free=$(df -h /opt | awk 'NR==2{print $4}' | sed 's/G//')

echo "  Memory: ${mem_available}MB available of ${mem_total}MB total"
echo "  Disk: ${disk_free}GB free"

if [ "$mem_available" -gt 2000 ]; then
    print_pass "Sufficient memory available"
else
    print_fail "Low memory warning - less than 2GB available"
fi

# Test 10: Firewall Configuration
print_test "Checking firewall configuration"
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "5000.*ALLOW"; then
        print_pass "Firewall allows port 5000"
    else
        print_fail "Port 5000 not allowed in firewall"
        print_info "Current firewall status:"
        ufw status
    fi
else
    print_info "UFW not installed - assuming firewall is open"
fi

# Summary
echo ""
echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "${GREEN}✅ WhisperS2T Container Installation Test Complete${NC}"
echo ""
echo -e "${YELLOW}🌐 Access URLs:${NC}"
echo -e "   Web Interface: http://$CONTAINER_IP:5000"
echo -e "   Health Check:  http://$CONTAINER_IP:5000/health"
echo ""
echo -e "${YELLOW}🔧 Service Commands:${NC}"
echo -e "   Status:  systemctl status whisper-appliance"
echo -e "   Logs:    journalctl -u whisper-appliance -f"
echo -e "   Restart: systemctl restart whisper-appliance"
echo ""
echo -e "${GREEN}🎤 Ready to transcribe audio files!${NC}"

# Optional: Simple transcription test if test audio exists
if [ -f "test.wav" ] || [ -f "sample.mp3" ]; then
    echo ""
    print_test "Running optional transcription test"
    
    test_file=""
    if [ -f "test.wav" ]; then
        test_file="test.wav"
    elif [ -f "sample.mp3" ]; then
        test_file="sample.mp3"
    fi
    
    if [ -n "$test_file" ]; then
        print_info "Testing with $test_file"
        response=$(curl -s -X POST -F "audio=@$test_file" "http://127.0.0.1:5000/transcribe")
        
        if echo "$response" | grep -q '"text"'; then
            print_pass "Transcription test successful"
            echo "Response: $response"
        else
            print_fail "Transcription test failed"
            echo "Response: $response"
        fi
    fi
fi