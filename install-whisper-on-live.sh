#!/bin/bash
# WhisperS2T Installation Script for Fedora Live ISO
# Run this after booting into Fedora Live

set -e

echo "🎤 WhisperS2T Appliance Installation"
echo "Installing on existing Fedora Live system..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please run as regular user, not root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo dnf update -y

# Install development tools
echo "🔧 Installing development tools..."
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3-pip python3-devel git cmake

# Enable RPM Fusion for ffmpeg
echo "📺 Enabling RPM Fusion repositories..."
sudo dnf install -y \
    "https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
    "https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

# Install multimedia packages
echo "🎵 Installing multimedia support..."
sudo dnf install -y ffmpeg ffmpeg-devel

# Install WhisperS2T dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip3 install --user transformers openai-whisper flask

# Create WhisperS2T directory
echo "📁 Setting up WhisperS2T..."
mkdir -p $HOME/whisper-appliance
cd $HOME/whisper-appliance

# Create simple WhisperS2T web interface
cat > app.py << 'EOF'
#!/usr/bin/env python3
import os
import tempfile
from flask import Flask, request, render_template_string, jsonify
import whisper

app = Flask(__name__)

# Load Whisper model
print("Loading Whisper model...")
model = whisper.load_model("base")

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>WhisperS2T Appliance</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .result { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 WhisperS2T Appliance</h1>
        <p>Upload an audio file to transcribe it using OpenAI Whisper</p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <input type="file" name="audio" accept="audio/*" required>
                <p>Select an audio file (MP3, WAV, M4A, etc.)</p>
            </div>
            <button type="submit">Transcribe Audio</button>
        </form>
        
        <div id="result" class="result" style="display:none;">
            <h3>Transcription Result:</h3>
            <div id="transcription"></div>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').onsubmit = function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('transcription').innerHTML = 'Processing...';
            
            fetch('/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('transcription').innerHTML = 
                    data.error ? 'Error: ' + data.error : data.text;
            });
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        audio_file = request.files['audio']
        if not audio_file:
            return jsonify({'error': 'No audio file provided'})
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            # Transcribe audio
            result = model.transcribe(tmp_file.name)
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
            return jsonify({'text': result['text']})
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🎤 WhisperS2T Appliance starting on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Make it executable
chmod +x app.py

# Create desktop shortcut
mkdir -p $HOME/Desktop
cat > $HOME/Desktop/WhisperS2T.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=WhisperS2T Appliance
Comment=Speech to Text with OpenAI Whisper
Exec=gnome-terminal -- python3 /home/liveuser/whisper-appliance/app.py
Icon=audio-input-microphone
Terminal=false
Categories=AudioVideo;Audio;
EOF

chmod +x $HOME/Desktop/WhisperS2T.desktop

echo ""
echo "🎉 WhisperS2T Appliance Installation Complete!"
echo ""
echo "📋 To start WhisperS2T:"
echo "  1. Double-click 'WhisperS2T' on the desktop, OR"
echo "  2. Open terminal and run: python3 $HOME/whisper-appliance/app.py"
echo ""
echo "🌐 Then open browser to: http://localhost:5000"
echo ""
echo "🎤 You can now upload audio files for transcription!"
EOF

chmod +x /home/commander/Code/whisper-appliance/app.py
