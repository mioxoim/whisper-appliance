# Aufgaben - JavaScript Extraction

## 🎯 **Aktuelle Priorität (Phase 2)**

### **Phase 2A: JavaScript-Code-Analyse** ⏳
- [ ] `admin_panel.py` Zeilen 325-1200+ komplett analysieren
- [ ] JavaScript-Funktionen identifizieren und kategorisieren:
  - [ ] `switchAdminModel()` - Admin UI switching
  - [ ] `performUpdate()` - Update execution
  - [ ] `checkUpdates()` - Update checking
  - [ ] `restartService()` - Service management
  - [ ] `uploadFile()` - File upload handling
  - [ ] WebSocket functions - Real-time communication
- [ ] Abhängigkeiten zwischen JavaScript-Funktionen ermitteln
- [ ] Python → JavaScript Datenübergabe-Punkte identifizieren

### **Phase 2B: JavaScript-Dateien erstellen** ⏳
- [ ] `static/js/admin-core.js` erstellen
  - [ ] `switchAdminModel()` Function migrieren
  - [ ] Admin-Navigation Logic extrahieren
  - [ ] UI-State-Management implementieren
- [ ] `static/js/update-manager.js` erstellen  
  - [ ] `performUpdate()` Function migrieren
  - [ ] `checkUpdates()` Function migrieren
  - [ ] `restartService()` Function migrieren
  - [ ] Progress-Tracking Logic extrahieren
- [ ] `static/js/ui-helpers.js` erstellen
  - [ ] `uploadFile()` Function migrieren
  - [ ] WebSocket helper functions extrahieren
  - [ ] Utility functions sammeln

### **Phase 2C: Template Integration** ⏳ 
- [ ] HTML-Templates identifizieren die JavaScript verwenden
- [ ] `<script src="/static/js/...">` Tags hinzufügen
- [ ] Python → JavaScript Datenübergabe via JSON implementieren
- [ ] Template-Variablen in JavaScript-accessible Format konvertieren

### **Phase 2D: Python-Code Cleanup** ⏳
- [ ] JavaScript-Blöcke aus `admin_panel.py` entfernen
- [ ] Python-Code refactoring für clean separation
- [ ] Route-Handler auf reine Backend-Logik reduzieren
- [ ] API-Endpoints für JavaScript-Frontend definieren

## 🔧 **Technische Validierungen**
- [ ] Alle JavaScript-Funktionen arbeiten korrekt in separaten Dateien
- [ ] Python-Backend sendet korrekte JSON-Responses
- [ ] Frontend kann Backend-APIs erfolgreich aufrufen
- [ ] WebSocket-Verbindungen funktionieren weiterhin
- [ ] File-Upload-Mechanismus bleibt funktional
- [ ] Admin-Panel UI-Navigation unverändert

## 🚨 **Critical Success Factors**
- [ ] **Zero Functionality Loss** - Alle Features bleiben erhalten
- [ ] **Clean Separation** - Kein JavaScript mehr in Python-Code
- [ ] **Maintainability** - JavaScript-Änderungen unabhängig von Python
- [ ] **Performance** - Keine Performance-Degradation

## 📋 **Testing Checklist**
- [ ] Admin Panel lädt vollständig
- [ ] Update-Funktionen arbeiten korrekt
- [ ] File-Upload funktioniert
- [ ] WebSocket-Verbindungen stabil
- [ ] Service-Restart funktional
- [ ] Browser-Console zeigt keine JavaScript-Fehler

## ➡️ **Übergang zu Phase 3**
Nach erfolgreichem JavaScript Extraction:
- **Template Method Pattern** Implementation
- **Clean Architecture Validation**
- **GitHub Actions Integration**
