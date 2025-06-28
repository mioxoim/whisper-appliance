#!/bin/bash
# Container Installation Script for WhisperS2T Appliance
# Optimized for Ubuntu 22.04/Debian 12 LXC containers

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (or with sudo)"
    exit 1
fi

print_section "🎤 WhisperS2T Appliance Container Installation"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
else
    print_error "Cannot detect OS version"
    exit 1
fi

print_status "Detected OS: $OS $VERSION"

# Update system
print_section "📦 Updating System Packages"
apt update && apt upgrade -y

# Install system dependencies
print_section "🔧 Installing System Dependencies"
apt install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Python and development tools
print_section "🐍 Installing Python Development Environment"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel

# Install multimedia libraries
print_section "🎵 Installing Multimedia Libraries"
apt install -y \
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
    libssl-dev

# Install web server
print_section "🌐 Installing Web Server"
apt install -y nginx

# Create application user
print_section "👤 Creating Application User"
if ! id "whisper" &>/dev/null; then
    useradd -m -s /bin/bash whisper
    usermod -aG audio whisper
    print_success "Created user 'whisper'"
else
    print_status "User 'whisper' already exists"
fi

# Create application directories
print_section "📁 Setting up Application Directories"
mkdir -p /opt/whisper-appliance/{src,templates,static,models,uploads,logs,config}
chown -R whisper:whisper /opt/whisper-appliance

# Install Python dependencies
print_section "📚 Installing Python Dependencies"
sudo -u whisper python3 -m pip install --user --upgrade pip
sudo -u whisper python3 -m pip install --user \
    torch torchaudio --index-url https://download.pytorch.org/whl/cpu
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
    python-multipart

# Copy application files if in repository
if [ -d "./src" ]; then
    print_section "📋 Copying Application Files"
    cp -r ./src/* /opt/whisper-appliance/src/
    cp -r ./templates/* /opt/whisper-appliance/templates/ 2>/dev/null || true
    cp -r ./static/* /opt/whisper-appliance/static/ 2>/dev/null || true
    cp -r ./config/* /opt/whisper-appliance/config/ 2>/dev/null || true
    chown -R whisper:whisper /opt/whisper-appliance
fi

# Create systemd service
print_section "⚙️ Creating System Service"
cat > /etc/systemd/system/whisper-appliance.service << 'EOF'
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
EOF

# Create nginx configuration
print_section "🔧 Configuring Nginx"
cat > /etc/nginx/sites-available/whisper-appliance << 'EOF'
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
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/whisper-appliance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Create basic health check endpoint
print_section "🏥 Creating Health Check"
mkdir -p /opt/whisper-appliance/src
cat > /opt/whisper-appliance/src/app.py << 'EOF'
#!/usr/bin/env python3
import os
import tempfile
import logging
from flask import Flask, request, render_template_string, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load whisper, fallback gracefully
try:
    import whisper
    model = whisper.load_model("base")
    WHISPER_AVAILABLE = True
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.warning(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False
    model = None

HTML_TEMPLATE = '''
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
        document.getElementById('uploadForm').onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('transcription').innerHTML = '🔄 Processing audio file, please wait...';
            
            fetch('/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('result').className = 'result error';
                    document.getElementById('transcription').innerHTML = '❌ Error: ' + data.error;
                } else {
                    document.getElementById('result').className = 'result';
                    document.getElementById('transcription').innerHTML = '📝 ' + data.text;
                }
            })
            .catch(error => {
                document.getElementById('result').className = 'result error';
                document.getElementById('transcription').innerHTML = '❌ Network error: ' + error;
            });
        };
        {% endif %}
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, whisper_available=WHISPER_AVAILABLE)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'whisper_available': WHISPER_AVAILABLE,
        'version': '0.6.0'
    })

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if not WHISPER_AVAILABLE:
        return jsonify({'error': 'Whisper model not available'})
    
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'})
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'})
        
        # Secure filename
        filename = secure_filename(audio_file.filename)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            # Transcribe audio
            logger.info(f"Transcribing file: {filename}")
            result = model.transcribe(tmp_file.name)
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
            logger.info("Transcription completed successfully")
            return jsonify({'text': result['text']})
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    logger.info("🎤 WhisperS2T Appliance starting...")
    app.run(host='0.0.0.0', port=5001, debug=False)
EOF

chown whisper:whisper /opt/whisper-appliance/src/app.py

# Enable and start services
print_section "🚀 Starting Services"
systemctl daemon-reload
systemctl enable whisper-appliance
systemctl enable nginx

# Start nginx first
systemctl restart nginx
systemctl start whisper-appliance

# Configure firewall if ufw is available
if command -v ufw >/dev/null 2>&1; then
    print_section "🔥 Configuring Firewall"
    ufw --force enable
    ufw allow 5000/tcp
    ufw allow ssh
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

print_section "✅ Installation Complete!"
print_success "WhisperS2T Appliance installed successfully!"
print_success ""
print_success "🌐 Access URLs:"
print_success "   Web Interface: http://$CONTAINER_IP:5000"
print_success "   Health Check:  http://$CONTAINER_IP:5000/health"
print_success ""
print_success "🔧 Service Management:"
print_success "   Status:  systemctl status whisper-appliance"
print_success "   Logs:    journalctl -u whisper-appliance -f"
print_success "   Restart: systemctl restart whisper-appliance"
print_success ""
print_success "📁 Application Directory: /opt/whisper-appliance"
print_success "👤 Application User: whisper"

print_warning ""
print_warning "⏳ Note: Whisper model download may take a few minutes on first access"
print_warning "    The service will show 'Whisper Model Loading...' until ready"

print_success ""
print_success "🎤 Ready to transcribe audio files!"
