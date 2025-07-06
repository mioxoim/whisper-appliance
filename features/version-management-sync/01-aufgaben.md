# Aufgaben - Version Management Synchronization

## 🏷️ **PROAKTIV ERKANNT: Versionierungs-Inkonsistenz**

### **Problem identifiziert:**
- ✅ VERSION file erstellt (0.8.1)
- ❌ Verschiedene Versionen in verschiedenen Dateien
- ❌ Keine automatische Sync zwischen Version-Quellen
- ❌ Update-System findet möglicherweise falsche Versionen

### **Phase 1: Version-Source-Audit** ⏳
- [ ] **Alle Version-Definitionen finden:**
  ```bash
  # Suche nach allen Versionsreferenzen
  grep -r "version.*=" src/
  grep -r "__version__" src/
  grep -r "0\." . --include="*.py" --include="*.md" --include="*.json"
  ```

- [ ] **Inkonsistenzen dokumentieren:**
  - [ ] README.md Header-Version
  - [ ] main.py FastAPI app version
  - [ ] setup.py/pyproject.toml wenn vorhanden
  - [ ] package.json wenn vorhanden
  - [ ] CHANGELOG.md aktuelle Version

### **Phase 2: Zentrale Version-Source** ⏳
- [ ] **VERSION file als Single Source of Truth:**
  - [x] `/VERSION` file erstellt (0.8.1)
  - [ ] Version-Reader-Utility erstellen
  - [ ] Alle anderen Dateien lesen aus VERSION
  - [ ] Update-System nutzt VERSION file primär

- [ ] **Version-Manager-Utility:**
  ```python
  # Zentrale Versionsverwaltung
  class VersionManager:
      @staticmethod
      def get_current_version() -> str
      @staticmethod  
      def update_all_version_files(new_version: str)
      @staticmethod
      def validate_version_consistency() -> bool
  ```

### **Phase 3: Automatische Synchronisation** ⏳
- [ ] **Update-Hook für Versionierung:**
  - [ ] Pre-commit hook für Version-Validation
  - [ ] Automated version bump bei Updates
  - [ ] Git tag creation bei Version-Änderungen
  - [ ] CHANGELOG.md automatische Updates

- [ ] **Version-Validation in Update-System:**
  - [ ] Semantic version comparison
  - [ ] Version format validation
  - [ ] Update-Berechtigung basierend auf Version-Hierarchie

### **Phase 4: Documentation & Tools** ⏳
- [ ] **Developer Tools:**
  - [ ] `bump-version.py` script für manuelle Version-Updates
  - [ ] Version-Consistency-Check in CI/CD
  - [ ] Version-Release-Notes-Generator
  - [ ] Automated README.md version sync

## 🔧 **Technische Implementation**

### **Version-Reader Implementation:**
```python
# src/utils/version.py
import os
from pathlib import Path

def get_version() -> str:
    """Get current version from VERSION file"""
    version_file = Path(__file__).parent.parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"

def update_version_references(new_version: str):
    """Update all version references across the project"""
    # README.md, main.py, CHANGELOG.md, etc.
```

### **Integration in Update-System:**
```python
# Erweitere UpdateManager.get_update_status()
from ..utils.version import get_version

current_version = get_version()  # Statt komplexer Regex-Suche
```

## 📋 **Entdeckte Dateien für Version-Sync**

### **Primäre Version-Quellen:**
- [x] `/VERSION` (0.8.1) - Single Source of Truth
- [ ] `README.md` Header (aktuell: Enhanced WhisperS2T Appliance v0.8.0)
- [ ] `src/main.py` FastAPI app version
- [ ] `CHANGELOG.md` neueste Version

### **Sekundäre Version-Quellen:**
- [ ] Git tags (für Release-Tracking)
- [ ] Docker container labels
- [ ] API version responses
- [ ] Documentation version references

## ✅ **Success Criteria**
- [ ] **Single VERSION file als einzige Quelle**
- [ ] **Alle anderen Dateien lesen aus VERSION**
- [ ] **Update-System nutzt VERSION file primär**
- [ ] **Automatische Sync bei Version-Changes**
- [ ] **Version-Validation in CI/CD**

## 🔗 **Dependencies & Integration**

### **Integriert mit:**
- **Update System Testing**: Bessere Version-Detection für Tests
- **Proxmox Deployment**: Konsistente Versionierung in Container
- **Clean Refactor 7+1**: Modular version utilities

### **Blockiert:**
- [ ] Update-System Testing (braucht korrekte Version-Detection)
- [ ] Production deployment (braucht consistent versioning)

## 💡 **Proaktive Erkenntnisse**

### **Automatisierung-Potentiale:**
- [ ] **Release-Pipeline**: Automated version bump → git tag → GitHub release
- [ ] **Documentation-Sync**: Version in docs automatisch aktualisiert
- [ ] **Container-Tagging**: Docker images mit korrekter Version getaggt
- [ ] **API-Versioning**: Endpoint-Versioning basierend auf Application-Version
