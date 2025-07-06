# Aufgaben - Proxmox Deployment Test

## 🚨 **KRITISCHE VALIDIERUNG (vor Production)**

### **Phase 1: Pre-Test Vorbereitung** ✅
- [x] Phase 1 Clean Refactor 7+1 Architecture abgeschlossen
- [x] Code-Formatierung angewendet (isort + black)
- [x] Git push mit SSH-Key erfolgreich
- [x] Modular architecture vollständig implementiert

### **Phase 2: One-Line Deployment Test** ⏳
- [ ] **One-Liner Command validieren:**
  ```bash
  bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
  ```
- [ ] **LXC Container Deployment testen:**
  - [ ] Container wird korrekt erstellt
  - [ ] Ubuntu 22.04 LXC läuft stabil
  - [ ] Docker wird innerhalb Container installiert
  - [ ] WhisperS2T Service startet automatisch

### **Phase 3: Architecture Validation** ⏳
- [ ] **Modular Import System funktioniert:**
  - [ ] `from modules.update import UpdateManager` funktioniert
  - [ ] `from modules.maintenance import MaintenanceManager` funktioniert  
  - [ ] `from modules.update.enterprise import integrate_with_flask_app` funktioniert
- [ ] **Flask Enterprise Integration:**
  - [ ] `/api/enterprise/deployment-info` endpoint erreichbar
  - [ ] `/api/enterprise/check-updates` funktioniert
  - [ ] `/api/enterprise/update-status` antwortet korrekt

### **Phase 4: Feature Compatibility** ⏳
- [ ] **Core Features funktionieren:**
  - [ ] Live Speech Recognition Interface
  - [ ] Upload Transcription Interface
  - [ ] Admin Panel Navigation
  - [ ] WebSocket-Verbindungen stabil
  - [ ] API Documentation (/docs) erreichbar
- [ ] **Enterprise Features:**
  - [ ] Deployment detection korrekt (Proxmox LXC erkannt)
  - [ ] Update system funktional
  - [ ] Maintenance mode aktivierbar

## 🔧 **Technische Validierungen**

### **Container-Niveau Tests:**
- [ ] Service-Status: `systemctl status whisper-appliance`
- [ ] Port-Binding: `ss -tulnp | grep 5001`
- [ ] Container-Logs: `docker logs whisper-appliance`
- [ ] Application-Logs: `/opt/whisper-appliance/logs/`

### **Application-Niveau Tests:**
- [ ] Web-Interface erreichbar: `https://CONTAINER-IP:5001`
- [ ] SSL-Zertifikate funktional
- [ ] Mikrofon-Permissions (HTTPS erforderlich)
- [ ] File-Upload funktioniert
- [ ] API-Endpoints antworten korrekt

### **Architecture-Niveau Tests:**
- [ ] Import-Statements funktionieren ohne Fehler
- [ ] Modular components laden korrekt
- [ ] Backward compatibility erhalten
- [ ] Enterprise features voll funktional

## 🚨 **KRITISCHE PUNKTE**

**MÖGLICHE BREAKING CHANGES nach Phase 1:**
- [ ] Import-Paths könnten in Container anders sein
- [ ] Legacy-Dependencies könnten fehlen
- [ ] Modular architecture könnte Container-spezifische Anpassungen brauchen
- [ ] Enterprise features könnten neue Dependencies haben

**FALLBACK-PLAN:**
- [ ] Bei Problemen: Rollback zu letztem working commit vor Phase 1
- [ ] Container neu deployen mit stabilem Code
- [ ] Phase 1 Änderungen containertauglich machen
- [ ] Erneut testen

## ✅ **SUCCESS CRITERIA**
- [ ] **One-Liner funktioniert ohne Modifikation**
- [ ] **Container startet automatisch und stabil**
- [ ] **Alle Core-Features funktional**
- [ ] **Enterprise-Features arbeiten korrekt**
- [ ] **Performance nicht degradiert**
- [ ] **SSL/HTTPS funktioniert für Mikrofon-Zugriff**

## 📋 **Test Protocol**
```bash
# 1. Container deployment
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)

# 2. Service validation
systemctl status whisper-appliance
docker ps
docker logs whisper-appliance

# 3. Application validation  
curl https://CONTAINER-IP:5001/health
curl https://CONTAINER-IP:5001/api/enterprise/deployment-info

# 4. Feature validation
# - Test Live Speech via web interface
# - Test file upload
# - Test admin panel
# - Test update functionality
```

## 🎯 **NACH ERFOLGREICHEM TEST**
- [ ] Deployment als Production-ready markieren
- [ ] Phase 2 (JavaScript Extraction) kann beginnen
- [ ] Feature-Management-System ist validiert
- [ ] Architecture changes sind Container-kompatibel
