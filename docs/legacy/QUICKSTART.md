# 🚀 Schnellstart-Anleitung - Whisper Appliance v0.4.0

## ⚡ 5-Minuten Setup

### **1. Repository Setup**
```bash
git clone <your-repository-url>
cd whisper-appliance
```

### **2. Python Environment**
```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Aktivieren (Windows)
venv\Scripts\activate
```

### **3. Dependencies installieren**
```bash
# Alle Requirements installieren
pip install -r requirements.txt

# Zusätzliche Audio-Libraries
pip install pydub ffmpeg-python
```

### **4. Server starten**
```bash
# In das Backend-Verzeichnis wechseln
cd src/webgui/backend

# Enhanced Server starten
python enhanced_final_working.py
```

### **5. Demo testen**
```bash
# Browser öffnen:
# Hauptseite:
http://localhost:5000
```

---

## 🎤 Erste Schritte

### **Echtes Mikrofon verwenden:**

1. **Haupt-Interface öffnen** → http://localhost:5000
2. **Mikrofon-Berechtigung geben** (Browser fragt)
3. **"🔌 Connect WebSocket"** klicken (falls separate Verbindung nötig)
4. **Test Mode auf "Disabled"** setzen (falls vorhanden)
5. **Sprache wählen** (z.B. "German")
6. **"🎙️ START RECORDING"** → **Sprechen!**

### **Whisper-Modell wechseln:**

1. **Modell auswählen** (tiny = schnell, large = genau)
2. **"📥 Load Model"** klicken
3. **Warten** (Download beim ersten Mal)
4. **Verwenden** (automatisch für neue Aufnahmen)

---

## 📁 Wichtige Dateien

```
whisper-appliance/
├── src/webgui/backend/
│   └── enhanced_final_working.py  ← Hauptserver
├── requirements.txt               ← Dependencies
├── README.md                      ← Vollständige Dokumentation
└── QUICKSTART.md                  ← Diese Datei
```

---

## 🔧 Konfiguration

### **Modell-Downloads (automatisch)**
- **Faster-Whisper:** `~/.cache/huggingface/`
- **OpenAI-Whisper:** `~/.cache/whisper/`

### **Port ändern (optional)**
```python
# In enhanced_final_working.py (letzte Zeile):
uvicorn.run(app, host="0.0.0.0", port=8080)  # Statt 5000
```

---

## ⚠️ Troubleshooting

### **Mikrofon funktioniert nicht**
- Browser-Berechtigung geben
- "🔄 Refresh Mics" klicken
- Bei Firefox: `about:config` → `media.navigator.permission.disabled` = false

### **Modell lädt nicht**
- Internet-Verbindung prüfen
- Speicherplatz frei (bis 1.5GB für große Modelle)
- Cache löschen: `rm -rf ~/.cache/whisper ~/.cache/huggingface`

### **Server startet nicht**
```bash
# Dependencies prüfen
pip install fastapi uvicorn websockets faster-whisper

# Port prüfen
lsof -i :5000

# Verbose starten
python enhanced_final_working.py --log-level debug
```

---

## 🎯 Nächste Schritte

1. **README.md lesen** → Vollständige Dokumentation
2. **Verschiedene Modelle testen** → tiny vs. large
3. **Verschiedene Sprachen testen** → Deutsch, Englisch, etc.
4. **API erkunden** → http://localhost:5000/api/status

---

**🎤 Happy Voice Recognition! 🎉**
