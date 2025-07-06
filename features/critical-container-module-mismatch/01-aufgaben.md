# Aufgaben - CRITICAL: Container Module Mismatch

## 🚨 **KRITISCHES PRODUKTIONSPROBLEM - Container-Development Mismatch**

### **Problem identifiziert aus Logs:**
```
⚠️ Enterprise Update System not available: No module named 'modules.update'
💡 Running with legacy update system
⚠️ Enterprise Update System not available - using fallback
```

**ROOT CAUSE:** Container läuft alte Version ohne modular update system

### **Phase 1: Container-Development Synchronisation** ⏳
- [ ] **Version-Mismatch-Analyse:**
  ```bash
  # Container Version ermitteln
  docker exec whisper-appliance find /opt/whisper-appliance -name "modules" -type d
  docker exec whisper-appliance ls -la /opt/whisper-appliance/src/modules/
  docker exec whisper-appliance cat /opt/whisper-appliance/VERSION
  
  # Development Version vergleichen
  ls -la /home/commander/Code/whisper-appliance/src/modules/
  cat /home/commander/Code/whisper-appliance/VERSION
  ```

- [ ] **Module-Structure-Audit:**
  - [ ] Container hat KEINE `src/modules/update/` Struktur
  - [ ] Container hat KEINE `src/modules/maintenance/` Struktur  
  - [ ] Container läuft mit legacy shopware_update_manager.py
  - [ ] Development hat vollständig refactored architecture

### **Phase 2: Immediate Container Update** ⚡
- [⏳] **Critical Path: Manual Container Update:**
  ```bash
  # USER COMMANDS TO EXECUTE:
  
  # 1. Backup current container state (Safety first)
  docker exec whisper-appliance cp -r /opt/whisper-appliance/src /opt/whisper-appliance/src_backup_$(date +%Y%m%d_%H%M%S)
  
  # 2. Copy current development version to container
  docker cp /home/commander/Code/whisper-appliance/src/modules/ whisper-appliance:/opt/whisper-appliance/src/
  docker cp /home/commander/Code/whisper-appliance/VERSION whisper-appliance:/opt/whisper-appliance/
  
  # 3. Restart container service
  docker exec whisper-appliance systemctl restart whisper-appliance
  
  # 4. Validate module imports
  docker exec whisper-appliance python3 -c "from modules.update import UpdateManager; print('✅ UPDATE MODULE OK')"
  docker exec whisper-appliance python3 -c "from modules.maintenance import MaintenanceManager; print('✅ MAINTENANCE MODULE OK')"
  
  # 5. Test Update APIs
  curl https://192.168.178.67:5001/api/enterprise/check-updates
  curl https://192.168.178.67:5001/api/enterprise/update-status
  ```

- [⏳] **Alternative: Redeploy Container (if manual sync fails):**
  ```bash
  # Fallback strategy
  docker stop whisper-appliance
  docker rm whisper-appliance
  
  # Neuer Deploy mit aktueller GitHub Version
  bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
  ```

### **Phase 3: Update-System Validation** ⏳
- [ ] **Module Import Testing:**
  ```bash
  # Test alle kritischen Imports im Container
  docker exec whisper-appliance python3 -c "
  from modules.update import UpdateManager
  from modules.maintenance import MaintenanceManager  
  from modules.update.enterprise import integrate_with_flask_app
  print('✅ ALL IMPORTS SUCCESSFUL')
  "
  ```

- [ ] **Update API Endpoints Testing:**
  ```bash
  # Test Update APIs nach Module-Fix
  curl https://CONTAINER-IP:5001/api/enterprise/check-updates
  curl https://CONTAINER-IP:5001/api/enterprise/update-status
  curl -X POST https://CONTAINER-IP:5001/api/enterprise/start-update
  ```

### **Phase 4: Root Cause Prevention** ⏳
- [ ] **Deployment Pipeline Fix:**
  - [ ] Proxmox script zieht möglicherweise alte GitHub Version
  - [ ] Container build process nicht synchron mit Development
  - [ ] Automated deployment testing needed
  - [ ] Version validation in deployment scripts

- [ ] **Container-Development Sync Process:**
  - [ ] Pre-deployment testing protocol
  - [ ] Automated module validation
  - [ ] Version consistency checks
  - [ ] Rollback procedures for failed updates

## 🔧 **Technische Lösung-Strategien**

### **Immediate Fix Strategy:**
1. **Manual Module Sync** (Fastest)
2. **Container Restart** (Test imports)
3. **API Validation** (Confirm functionality)
4. **Full Redeploy** (If manual fails)

### **Long-term Prevention:**
1. **Automated Testing Pipeline**
2. **Version Consistency Validation**
3. **Container Health Checks**
4. **Development-Container Sync Automation**

## ✅ **Success Criteria**
- [ ] **Container imports `modules.update` successfully**
- [ ] **Update APIs respond without errors**
- [ ] **No "Enterprise Update System not available" warnings**
- [ ] **Update Button functional in container**

## 🔗 **Verknüpfte kritische Probleme**
- **Transcription System Failure**: Separate critical issue
- **Update System Testing**: Blocked by this module issue
- **Container Deployment**: Needs immediate fix

## ⚠️ **IMPACT ANALYSIS**
- **Production System**: Currently NON-FUNCTIONAL for updates
- **Development Gap**: Major version mismatch
- **User Experience**: Update button fails, fallback modes only
- **Enterprise Features**: Completely disabled in container
