# WhisperS2T 7+1 Project Structure

## Overview
This project follows the **7+1 Design Pattern** for maintainable and scalable architecture.

## Directory Structure

```
src/
├── components/       # 🎨 UI Components & Templates
│   ├── templates/    # HTML Jinja2 Templates
│   ├── admin/        # Admin Panel Components
│   └── interfaces/   # User Interface Components
├── modules/          # 🧠 Business Logic Modules
│   ├── core/         # Core Whisper Functionality
│   ├── update/       # Update System (clean naming)
│   ├── maintenance/  # Maintenance Mode
│   ├── api/          # API Endpoints
│   └── [legacy]/     # Existing modules (during migration)
├── static/           # 🎨 Static Assets
│   ├── js/           # JavaScript Files
│   ├── css/          # Stylesheets
│   └── assets/       # Images, Icons
├── config/           # ⚙️ Configuration Management
│   ├── settings/     # App Settings
│   ├── deployment/   # Deployment Configs
│   └── defaults/     # Default Configurations
├── utils/            # 🔧 Helper Functions
│   ├── file_ops/     # File Operations
│   ├── networking/   # Network Utilities
│   └── validation/   # Input Validation
├── services/         # 🌐 External Integrations
│   ├── whisper/      # Whisper Service Integration
│   ├── websocket/    # WebSocket Handling
│   └── external/     # External API Integrations
├── tests/            # 🧪 Testing Suite
│   ├── unit/         # Unit Tests
│   ├── integration/  # Integration Tests
│   └── fixtures/     # Test Data
├── vendor/           # 📦 External Dependencies (+1)
│   └── third_party/  # Third-party modules (if any)
└── main.py           # 🚀 Application Entry Point
```

## Migration Status

### ✅ Phase 1A Completed: Directory Structure Creation
- All 7+1 directories created
- Python packages initialized with __init__.py
- Import compatibility verified

### 🔄 Next: Phase 1B - File Migration
- Move files to appropriate directories (preserving originals)
- Update import statements
- Clean naming (remove Shopware/Enterprise branding)

## Principles

1. **Separation of Concerns**: Each directory has a specific purpose
2. **Maintainability**: Clear organization for future development
3. **Scalability**: Structure supports growth and complexity
4. **Professional Standards**: Clean, enterprise-ready architecture
