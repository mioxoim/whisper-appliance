#!/usr/bin/env bash

# WhisperS2T Proxmox Standalone Installer
# Self-contained installation without GitHub dependency
# Usage: Copy this script to Proxmox and run as root

set -e

# Colors
BL='\033[36m'
RD='\033[0;31m'
GN='\033[1;92m'
YW='\033[33m'
CL='\033[m'

function msg_info() { echo -e "${BL}[INFO]${CL} $1"; }
function msg_ok() { echo -e "${GN}[OK]${CL} $1"; }
function msg_error() { echo -e "${RD}[ERROR]${CL} $1"; }
function msg_warn() { echo -e "${YW}[WARN]${CL} $1"; }

clear
cat <<"EOF"
 __        ___     _                  ____ ____  _____ 
 \ \      / / |__ (_)___ _ __   ___ _ / ___|___ \|_   _|
  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '_\___ \ __) | | |  
   \ V  V / | | | | \__ \ |_) |  __/ |  ___) / __/  | |  
    \_/\_/  |_| |_|_|___/ .__/ \___|_| |____/_____| |_|  
                        |_|                              

WhisperS2T Proxmox LXC Container Creator (Standalone)
===================================================
EOF

# Check if running on Proxmox
if ! command -v pct >/dev/null 2>&1; then
    msg_error "This script must be run on Proxmox VE"
    exit 1
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    msg_error "This script must be run as root"
    exit 1
fi

# Get next available container ID
CTID=$(pvesh get /cluster/nextid)
msg_info "Using Container ID: $CTID"

# Configuration
HOSTNAME="whisper-appliance"
CORES="2"
MEMORY="4096"
DISK_SIZE="20"
TEMPLATE="ubuntu-22.04-standard_22.04-1_amd64.tar.zst"

msg_info "Creating WhisperS2T LXC Container"
msg_info "  ID: $CTID"
msg_info "  Hostname: $HOSTNAME"
msg_info "  CPU: $CORES cores"
msg_info "  RAM: $MEMORY MB"
msg_info "  Disk: $DISK_SIZE GB"

# Download template if needed
TEMPLATE_PATH="/var/lib/vz/template/cache/$TEMPLATE"
if [[ ! -f "$TEMPLATE_PATH" ]]; then
    msg_info "Downloading Ubuntu 22.04 template (this may take a while)..."
    pveam download local $TEMPLATE
    msg_ok "Template downloaded"
fi

# Create container
msg_info "Creating LXC container..."
pct create $CTID $TEMPLATE_PATH \
    --hostname $HOSTNAME \
    --cores $CORES \
    --memory $MEMORY \
    --rootfs local-lvm:$DISK_SIZE \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --features nesting=1,keyctl=1 \
    --unprivileged 1 \
    --onboot 1 \
    --tags "ai,speech,transcription,whisper"

msg_ok "Container created"

# Start container
msg_info "Starting container..."
pct start $CTID
sleep 10
msg_ok "Container started"

# Install WhisperS2T
msg_info "Installing WhisperS2T (this will take 10-15 minutes)..."

# Create installation script inside container
pct exec $CTID -- bash -c 'cat > /root/install-whisper.sh << "INSTALL_EOF"
#!/bin/bash
set -e

# Colors for output
RED='\''\\033[0;31m'\''
GREEN='\''\\033[0;32m'\''
YELLOW='\''\\033[1;33m'\''
BLUE='\''\\033[0;34m'\''
NC='\''\\033[0m'\''

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

export DEBIAN_FRONTEND=noninteractive

print_status "Updating system packages..."
apt-get update >/dev/null 2>&1
apt-get upgrade -y >/dev/null 2>&1

print_status "Installing system dependencies..."
apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release >/dev/null 2>&1

print_status "Installing Python development environment..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel >/dev/null 2>&1

print_status "Installing multimedia libraries..."
apt-get install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libasound2-dev \
    libpulse-dev \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev >/dev/null 2>&1

print_status "Installing web server..."
apt-get install -y nginx >/dev/null 2>&1

print_status "Creating application user..."
if ! id "whisper" &>/dev/null; then
    useradd -m -s /bin/bash whisper
    usermod -aG audio whisper
fi

print_status "Setting up application directories..."
mkdir -p /opt/whisper-appliance/{src,templates,static,models,uploads,logs,config}
chown -R whisper:whisper /opt/whisper-appliance

print_status "Installing Python dependencies..."
sudo -u whisper python3 -m pip install --user --upgrade pip >/dev/null 2>&1
sudo -u whisper python3 -m pip install --user \
    torch torchaudio --index-url https://download.pytorch.org/whl/cpu >/dev/null 2>&1
sudo -u whisper python3 -m pip install --user \
    transformers \
    openai-whisper \
    flask \
    flask-cors \
    gunicorn \
    librosa \
    soundfile \
    pydub \
    requests \
    python-multipart \
    werkzeug \
    psutil >/dev/null 2>&1

print_status "Creating WhisperS2T application..."
cat > /opt/whisper-appliance/src/app.py << "PYTHON_EOF"
#!/usr/bin/env python3
import os
import tempfile
import logging
import subprocess
from flask import Flask, request, render_template_string, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import whisper
    model = whisper.load_model("base")
    WHISPER_AVAILABLE = True
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.warning(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False
    model = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WhisperS2T Appliance</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .upload-area { border: 2px dashed #007bff; padding: 40px; text-align: center; margin: 20px 0; border-radius: 10px; background: #f8f9fa; }
        .upload-area:hover { background: #e9ecef; }
        .result { margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 5px; border-left: 4px solid #28a745; }
        .error { background: #f8d7da; border-left-color: #dc3545; }
        button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        .status { text-align: center; margin: 20px 0; }
        .status.running { color: #28a745; }
        .status.error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 WhisperS2T Appliance</h1>
        
        <div class="status {{ 'running' if whisper_available else 'error' }}">
            Status: {{ 'Whisper Model Ready' if whisper_available else 'Whisper Model Loading...' }}
        </div>
        
        {% if whisper_available %}
        <p>Upload an audio file to transcribe it using OpenAI Whisper</p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <input type="file" name="audio" accept="audio/*" required>
                <p>Select an audio file (MP3, WAV, M4A, etc.)</p>
                <p><small>Maximum file size: 100MB</small></p>
            </div>
            <button type="submit">🎵 Transcribe Audio</button>
        </form>
        
        <div id="result" class="result" style="display:none;">
            <h3>Transcription Result:</h3>
            <div id="transcription"></div>
        </div>
        {% else %}
        <div class="result error">
            <h3>⚠️ Service Starting</h3>
            <p>The Whisper model is currently loading. Please refresh the page in a few moments.</p>
            <button onclick="location.reload()">🔄 Refresh Page</button>
        </div>
        {% endif %}
    </div>

    <script>
        {% if whisper_available %}
        document.getElementById("uploadForm").onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            document.getElementById("result").style.display = "block";
            document.getElementById("transcription").innerHTML = "🔄 Processing audio file, please wait...";
            
            fetch("/transcribe", {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById("result").className = "result error";
                    document.getElementById("transcription").innerHTML = "❌ Error: " + data.error;
                } else {
                    document.getElementById("result").className = "result";
                    document.getElementById("transcription").innerHTML = "📝 " + data.text;
                }
            })
            .catch(error => {
                document.getElementById("result").className = "result error";
                document.getElementById("transcription").innerHTML = "❌ Network error: " + error;
            });
        };
        {% endif %}
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, whisper_available=WHISPER_AVAILABLE)

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "whisper_available": WHISPER_AVAILABLE,
        "version": "0.6.0"
    })

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not WHISPER_AVAILABLE:
        return jsonify({"error": "Whisper model not available"})
    
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"})
        
        audio_file = request.files["audio"]
        if audio_file.filename == "":
            return jsonify({"error": "No audio file selected"})
        
        filename = secure_filename(audio_file.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_file.save(tmp_file.name)
            
            logger.info(f"Transcribing file: {filename}")
            result = model.transcribe(tmp_file.name)
            
            os.unlink(tmp_file.name)
            
            logger.info("Transcription completed successfully")
            return jsonify({"text": result["text"]})
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    logger.info("🎤 WhisperS2T Appliance starting...")
    app.run(host="0.0.0.0", port=5001, debug=False)
PYTHON_EOF

chown whisper:whisper /opt/whisper-appliance/src/app.py

print_status "Creating systemd service..."
cat > /etc/systemd/system/whisper-appliance.service << "SERVICE_EOF"
[Unit]
Description=WhisperS2T Appliance
After=network.target

[Service]
Type=simple
User=whisper
Group=whisper
WorkingDirectory=/opt/whisper-appliance
Environment=PATH=/home/whisper/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/whisper-appliance
ExecStart=/home/whisper/.local/bin/gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 300 src.app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF

print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/whisper-appliance << "NGINX_EOF"
server {
    listen 5000;
    server_name _;

    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/whisper-appliance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t

print_status "Starting services..."
systemctl daemon-reload
systemctl enable whisper-appliance
systemctl enable nginx

systemctl restart nginx
systemctl start whisper-appliance

if command -v ufw >/dev/null 2>&1; then
    ufw --force enable
    ufw allow 5000/tcp
    ufw allow ssh
fi

print_success "WhisperS2T installation completed!"
INSTALL_EOF

chmod +x /root/install-whisper.sh'

# Run installation
msg_info "Executing installation inside container..."
pct exec $CTID -- /root/install-whisper.sh

# Get container IP
msg_info "Getting container IP address..."
sleep 5
CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')

# Success message
clear
cat <<"EOF"
 __        ___     _                  ____ ____  _____ 
 \ \      / / |__ (_)___ _ __   ___ _ / ___|___ \|_   _|
  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '_\___ \ __) | | |  
   \ V  V / | | | | \__ \ |_) |  __/ |  ___) / __/  | |  
    \_/\_/  |_| |_|_|___/ .__/ \___|_| |____/_____| |_|  
                        |_|                              

🎉 INSTALLATION SUCCESSFUL! 🎉
EOF

echo
msg_ok "WhisperS2T LXC Container created successfully!"
msg_ok "Container ID: $CTID"
msg_ok "IP Address: $CONTAINER_IP"
echo
msg_ok "🌐 Web Interface: http://$CONTAINER_IP:5000"
msg_ok "🔧 SSH Access: ssh root@$CONTAINER_IP"
echo
msg_info "Features available:"
msg_info "  • Upload and transcribe audio files"
msg_info "  • Health monitoring endpoint"
msg_info "  • Automatic service management"
echo
msg_warn "Note: First transcription may take longer as Whisper downloads models"
echo
msg_info "Container management commands:"
msg_info "  pct start $CTID    # Start container"
msg_info "  pct stop $CTID     # Stop container"
msg_info "  pct enter $CTID    # Enter container console"
echo