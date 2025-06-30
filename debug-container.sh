#!/bin/bash

# WhisperS2T Container Debug Script
# Run this inside the container to diagnose and fix service issues

echo "🔍 WhisperS2T Container Diagnostic Script"
echo "========================================"

# Check if we're running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root"
    exit 1
fi

echo "📊 System Information:"
echo "IP Address: $(hostname -I)"
echo "Container: $(hostname)"
echo "Date: $(date)"
echo ""

echo "🔍 Service Status Check:"
echo "------------------------"

# Check WhisperS2T service
echo "📋 WhisperS2T Service:"
if systemctl is-active --quiet whisper-appliance; then
    echo "✅ whisper-appliance: RUNNING"
else
    echo "❌ whisper-appliance: NOT RUNNING"
    echo "📝 Service logs (last 10 lines):"
    journalctl -u whisper-appliance -n 10 --no-pager
    echo ""
fi

# Check Nginx service  
echo "📋 Nginx Service:"
if systemctl is-active --quiet nginx; then
    echo "✅ nginx: RUNNING"
else
    echo "❌ nginx: NOT RUNNING"
    echo "📝 Nginx logs:"
    tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error log found"
    echo ""
fi

# Check Apache2 (should not be running)
echo "📋 Apache2 Check:"
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo "⚠️ apache2: RUNNING (CONFLICT!)"
    echo "🔧 Stopping Apache2..."
    systemctl stop apache2
    systemctl disable apache2
    echo "✅ Apache2 stopped and disabled"
else
    echo "✅ apache2: NOT RUNNING (good)"
fi

echo ""
echo "🔍 Port Status Check:"
echo "---------------------"

# Check what's listening on ports
echo "📋 Port 80 (HTTP):"
if command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep ":80 " || echo "Nothing listening on port 80"
else
    ss -tlnp | grep ":80 " || echo "Nothing listening on port 80"
fi

echo "📋 Port 5000 (Nginx):"
if command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep ":5000 " || echo "Nothing listening on port 5000"
else
    ss -tlnp | grep ":5000 " || echo "Nothing listening on port 5000"
fi

echo "📋 Port 5001 (Flask):"
if command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep ":5001 " || echo "Nothing listening on port 5001"
else
    ss -tlnp | grep ":5001 " || echo "Nothing listening on port 5001"
fi

echo ""
echo "🔍 Configuration Check:"
echo "-----------------------"

# Check Nginx configuration
echo "📋 Nginx Configuration:"
if [ -f "/etc/nginx/sites-enabled/whisper-appliance" ]; then
    echo "✅ whisper-appliance config exists"
else
    echo "❌ whisper-appliance config missing"
fi

if [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "⚠️ default nginx site still enabled (removing...)"
    rm -f /etc/nginx/sites-enabled/default
    echo "✅ default site removed"
else
    echo "✅ default nginx site not enabled"
fi

# Check WhisperS2T files
echo "📋 WhisperS2T Files:"
if [ -f "/opt/whisper-appliance/src/main.py" ]; then
    echo "✅ main.py exists"
else
    echo "❌ main.py missing"
fi

if [ -d "/opt/whisper-appliance/src/templates" ]; then
    echo "✅ templates directory exists"
else
    echo "❌ templates directory missing"
fi

echo ""
echo "🔧 Attempting Fixes:"
echo "--------------------"

# Fix 1: Restart services in correct order
echo "🔄 Restarting services..."
systemctl stop whisper-appliance
systemctl stop nginx
sleep 2
systemctl start nginx
sleep 2
systemctl start whisper-appliance
sleep 3

# Check if services are now running
if systemctl is-active --quiet nginx && systemctl is-active --quiet whisper-appliance; then
    echo "✅ Both services restarted successfully"
else
    echo "❌ Service restart failed"
    
    # Fix 2: Check for dependency issues
    echo "🔍 Checking for Python dependency issues..."
    cd /opt/whisper-appliance/src
    python3 -c "
try:
    from modules import APIDocs, AdminPanel, LiveSpeechHandler, UploadHandler
    print('✅ All modules import successfully')
except Exception as e:
    print(f'❌ Module import error: {e}')
" 2>/dev/null || echo "❌ Module import failed"
    
    # Fix 3: Check template loading
    echo "🔍 Checking template loading..."
    python3 -c "
import os
script_dir = '/opt/whisper-appliance/src'
template_path = os.path.join(script_dir, 'templates', 'main_interface.html')
if os.path.exists(template_path):
    print(f'✅ Template found: {template_path}')
else:
    print(f'❌ Template not found: {template_path}')
" 2>/dev/null || echo "❌ Template check failed"
fi

echo ""
echo "🌐 Final Status:"
echo "---------------"

# Final status check
if systemctl is-active --quiet nginx; then
    nginx_status="✅ RUNNING"
else
    nginx_status="❌ FAILED"
fi

if systemctl is-active --quiet whisper-appliance; then
    whisper_status="✅ RUNNING"
else
    whisper_status="❌ FAILED"
fi

echo "Nginx: $nginx_status"
echo "WhisperS2T: $whisper_status"

# Test connectivity
echo ""
echo "🔗 Connectivity Test:"
echo "---------------------"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:5000/ && echo " - Port 5000 (Nginx)" || echo "❌ Port 5000 unreachable"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:5001/ && echo " - Port 5001 (Flask)" || echo "❌ Port 5001 unreachable"

echo ""
if systemctl is-active --quiet nginx && systemctl is-active --quiet whisper-appliance; then
    echo "🎉 SUCCESS: Services should now be accessible!"
    echo "🌐 Try: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "❌ FAILED: Manual intervention required"
    echo "📝 Check logs with:"
    echo "   journalctl -u whisper-appliance -f"
    echo "   tail -f /var/log/nginx/error.log"
fi
