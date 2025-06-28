# Enhanced WhisperS2T Appliance v0.6.0 - Setup Instructions (Fedora 42)

## 🎯 NACH DEM RE-LOGIN

### **SCHRITT 1: Mock-Setup testen**

```bash
cd /home/commander/Code/whisper-appliance
./test-mock-setup.sh
```

Falls alles ✅ ist, weiter zu Schritt 2.

### **SCHRITT 2: Fedora ISO Build starten**

```bash
./dev.sh build fedora
```

**ODER direkt:**

```bash
./build/fedora-iso/build-fedora-iso.sh
```

---

## 📋 ANPASSUNGEN FÜR FEDORA 42 (RAWHIDE)

### ✅ **Automatisch angepasst:**

- **Repository URL** → Fedora Rawhide Development
- **Mock Config** → fedora-rawhide-x86_64
- **Release Version** → 42
- **ISO Download** → Fedora Rawhide Server netinst

### **Build-Details:**
- **Target:** Fedora 42 (Rawhide/Development)
- **Base:** Fedora Server (minimal)
- **Mock Environment:** fedora-rawhide-x86_64
- **Expected Size:** ~800MB-1.5GB

---

## 📋 WAS WURDE VORBEREITET

### ✅ **Dateien erstellt:**

1. **Kickstart-Datei:** `/build/fedora-iso/whisper-appliance.ks`
   - Fedora Server als Basis
   - WhisperS2T Appliance vorinstalliert
   - Systemd Services konfiguriert
   - Automatische Netzwerk-Konfiguration

2. **Build-Script:** `/build/fedora-iso/build-fedora-iso.sh`
   - Kompletter livemedia-creator Workflow
   - Mock-Environment Setup
   - ISO-Erstellung mit Lorax
   - Automatische Dokumentation

3. **dev.sh erweitert:**
   - Neuer Command: `./dev.sh build fedora`
   - Version auf 0.6.0 erhöht
   - Integration in bestehendes Build-System

---

## 🎤 WHISPERS2T APPLIANCE v0.6.0 FEATURES

### **Nach Installation:**
- **Fedora Server** - Minimal, sicher, production-ready
- **Web Interface** - http://[IP]:5000
- **Automatischer Start** - Systemd Service
- **Model Downloads** - On-demand, keine großen ISO-Dateien
- **Console Display** - IP-Adresse wird angezeigt
- **Remote Access** - SSH, HTTP, Web-Management

### **Erwartete ISO-Größe:** ~800MB-1.5GB
(Ohne ML-Models, diese werden nachgeladen)

---

## 🚀 BUILD-PROCESS

### **Was passiert beim Build:**

1. **Mock Environment** - Saubere Fedora 41 Build-Umgebung
2. **Fedora Download** - Fedora 41 Server netinst ISO
3. **Kickstart Installation** - Automatische System-Installation
4. **WhisperS2T Setup** - Appliance-Software installation
5. **ISO Creation** - Bootbares ISO mit Lorax
6. **Dokumentation** - Automatische Anleitungen

### **Build-Zeit:** 30-60 Minuten
(Je nach Internet-Geschwindigkeit und CPU)

---

## 🎯 ERGEBNIS

Nach erfolgreichem Build:

```
/home/commander/Code/whisper-appliance/build/output/
├── whisper-appliance-v0.6.0-bootable.iso     (~800MB-1.5GB)
├── whisper-appliance-v0.6.0-bootable.iso.sha256
├── BOOTABLE-ISO-GUIDE.md
└── fedora-build-results/                     (Build-Logs)
```

### **USB-Stick erstellen:**
```bash
sudo dd if=whisper-appliance-v0.6.0-bootable.iso of=/dev/sdX bs=4M status=progress
```

### **Installation:**
1. USB-Stick in Mini-PC
2. Von USB booten
3. Automatische Installation
4. Reboot → Appliance läuft!

---

## 🔧 TROUBLESHOOTING

### **Falls Mock-Probleme:**
```bash
# Mock-Status prüfen
groups

# Mock-Konfiguration prüfen
mock -r fedora-41-x86_64 --print-root-path

# Cache leeren
mock -r fedora-41-x86_64 --clean
```

### **Falls Build fehlschlägt:**
- Logs in `/build/output/fedora-build-results/`
- Network-Connectivity prüfen
- Diskspace prüfen (mindestens 20GB frei)

---

## 🎉 BEREIT ZUM STARTEN!

**Du kannst jetzt mit dem Build beginnen, sobald du die Dependencies installiert hast!**

```bash
# 1. Dependencies installieren
sudo dnf install -y lorax anaconda-tui mock lorax-lmc-novirt spin-kickstarts

# 2. Mock-Gruppe hinzufügen
sudo usermod -a -G mock $USER

# 3. Logout/Login für Gruppe

# 4. ISO Build starten
./dev.sh build fedora
```

**Das wird dein erstes echtes, bootbares WhisperS2T Appliance ISO! 🎤✨**
