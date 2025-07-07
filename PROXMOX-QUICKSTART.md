# 🎤 Whisper Appliance Appliance - Proxmox Quick Start

## 🚀 5-Minuten-Deployment für Proxmox

### Schritt 1: Container erstellen

**In Proxmox Web-Interface:**
1. **Container Template:** Ubuntu 22.04 LTS herunterladen
2. **Container erstellen:**
   - **CT ID:** Beliebig (z.B. 200)
   - **Hostname:** whisper-appliance
   - **Template:** Ubuntu 22.04
   - **Root Password:** Sicher wählen
   - **CPU:** 2 Cores
   - **Memory:** 4096 MB
   - **Storage:** 20 GB
   - **Network:** vmbr0 (DHCP)
   - **Features:** Nesting aktivieren

### Schritt 2: Container starten und deployen

```bash
# SSH in Container (IP aus Proxmox Web-Interface ablesen)
ssh root@CONTAINER-IP

# Repository klonen und installieren
git clone https://github.com/yourusername/whisper-appliance.git
cd whisper-appliance
chmod +x install-container.sh
./install-container.sh
```

### Schritt 3: Zugriff

- **Web-Interface:** `http://CONTAINER-IP:5000`
- **Health Check:** `http://CONTAINER-IP:5000/health`

## ⚡ Was passiert bei der Installation?

1. **System-Updates** (2-3 Minuten)
2. **Python & Dependencies** (3-5 Minuten)  
3. **Whisper Installation** (2-3 Minuten)
4. **Service-Setup** (1 Minute)
5. **Web-Interface Start** (30 Sekunden)

**Gesamtzeit: ~10 Minuten**

## 🎯 Test der Installation

```bash
# Service-Status prüfen
systemctl status whisper-appliance

# Logs anzeigen  
journalctl -u whisper-appliance -f

# Health Check
curl http://CONTAINER-IP:5000/health
```

## 🔧 Service-Management

```bash
# Service neu starten
systemctl restart whisper-appliance

# Service stoppen
systemctl stop whisper-appliance

# Service aktivieren (Auto-Start)
systemctl enable whisper-appliance
```

## 📊 Resource-Monitoring

```bash
# Container-Resources in Proxmox
pct list
pct status CONTAINER-ID

# Im Container selbst
htop          # CPU/RAM usage
df -h         # Disk space
netstat -tlnp # Network ports
```

## 🎤 Audio-Test

**Test-Datei uploaden:** Über Web-Interface bei `http://CONTAINER-IP:5000`

**CLI-Test:**
```bash
curl -X POST -F "audio=@test.wav" http://CONTAINER-IP:5000/transcribe
```

## 🛠 Troubleshooting

### Service startet nicht
```bash
# Logs prüfen
journalctl -u whisper-appliance -n 50

# Whisper-Model manuell laden
sudo -u whisper python3 -c "import whisper; whisper.load_model('base')"
```

### Port-Probleme
```bash
# Firewall prüfen
ufw status
ufw allow 5000

# Port-Bindung prüfen
netstat -tlnp | grep 5000
```

### Speicher-Probleme
```bash
# Speicherverbrauch optimieren
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

## 🔄 Updates

```bash
cd /opt/whisper-appliance
git pull origin main
systemctl restart whisper-appliance
```

## 📱 Multi-Container Setup

Für mehrere Instanzen einfach weitere Container erstellen:
- **Container 201:** whisper-base (base model)
- **Container 202:** whisper-large (large model)  
- **Container 203:** whisper-gpu (mit GPU-Support)

---

**🎉 In 10 Minuten einsatzbereit!** Keine ISO-Builds, keine 15-Stunden-Wartezeiten!