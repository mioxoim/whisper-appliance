#!/bin/bash

# 🚀 Enhanced WhisperS2T v0.4.0 - Setup Script
# Automatische Installation und Konfiguration

set -e

echo "🎤 Enhanced WhisperS2T v0.4.0 Setup"
echo "==================================="
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

# 1. System-Requirements prüfen
print_step "Prüfe System-Requirements..."

# Python Version prüfen
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 ist nicht installiert!"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION gefunden"

# FFmpeg prüfen
if ! command -v ffmpeg &> /dev/null; then
    print_warning "FFmpeg nicht gefunden - wird für Audio-Konvertierung benötigt"
    echo "Ubuntu/Debian: sudo apt install ffmpeg"
    echo "macOS: brew install ffmpeg"
    echo "Windows: Download von https://ffmpeg.org"
    echo ""
fi

# 2. Virtual Environment erstellen
print_step "Erstelle Virtual Environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual Environment erstellt"
else
    print_success "Virtual Environment existiert bereits"
fi

# 3. Virtual Environment aktivieren
print_step "Aktiviere Virtual Environment..."
source venv/bin/activate
print_success "Virtual Environment aktiviert"

# 4. Dependencies installieren
print_step "Installiere Dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    print_success "Alle Dependencies installiert"
else
    print_error "Fehler beim Installieren der Dependencies"
    exit 1
fi

# 5. Whisper-Modell vorladen (optional)
echo ""
read -p "Möchten Sie das Whisper 'tiny' Modell vorladen? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Lade Whisper 'tiny' Modell..."
    python3 -c "
import faster_whisper
try:
    model = faster_whisper.WhisperModel('tiny', device='cpu', compute_type='int8')
    print('✅ Faster-Whisper tiny model geladen')
except Exception as e:
    print(f'⚠️ Faster-Whisper fehlgeschlagen: {e}')
    try:
        import whisper
        model = whisper.load_model('tiny')
        print('✅ OpenAI-Whisper tiny model geladen')
    except Exception as e2:
        print(f'❌ Beide Whisper-Installationen fehlgeschlagen: {e2}')
"
fi

# 6. Berechtigungen setzen
print_step "Setze Ausführungsberechtigungen..."
chmod +x setup.sh
chmod +x src/webgui/backend/enhanced_final_working.py 2>/dev/null || true

# 7. Erstelle Start-Script
print_step "Erstelle Start-Script..."
cat > start_server.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
cd src/webgui/backend
python enhanced_final_working.py
EOF

chmod +x start_server.sh
print_success "Start-Script erstellt: ./start_server.sh"

# 8. Zusammenfassung
echo ""
echo "🎉 Installation erfolgreich abgeschlossen!"
echo "========================================"
echo ""
echo "🚀 Server starten:"
echo "   ./start_server.sh"
echo ""
echo "🌐 Haupt-Interface öffnen:"
echo "   http://localhost:5000"
echo ""
echo "📚 Dokumentation:"
echo "   README.md         - Vollständige Dokumentation"
echo "   QUICKSTART.md     - Schnellstart-Anleitung"
echo "   ARCHITECTURE.md   - Technische Details"
echo ""
echo "🎤 Erste Schritte:"
echo "   1. Server starten mit ./start_server.sh"
echo "   2. Browser öffnen: http://localhost:5000"
echo "   3. Mikrofon-Berechtigung geben"
echo "   4. WebSocket verbinden"
echo "   5. Recording starten und sprechen!"
echo ""
print_success "Enhanced WhisperS2T v0.4.0 ist bereit! 🎉"
