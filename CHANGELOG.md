# Enhanced WhisperS2T Appliance - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-06-30

### Added - INTELLIGENT NETWORK SSL & PROXMOX READY 🌐
- **🧠 Intelligent SSL Generation**: Auto-detects all network IPs and creates certificates with SAN (Subject Alternative Names)
- **🔗 Network IP Support**: SSL certificates now work for ALL network IPs (192.168.x.x, container IPs, etc.)
- **🎯 Dynamic Certificate Creation**: Automatically includes `DNS:localhost`, `DNS:hostname`, and `IP:x.x.x.x` entries
- **🔧 OpenSSL Version Detection**: Supports both modern (`-addext`) and legacy (config file) OpenSSL methods
- **🌍 External IP Detection**: Optionally includes public IP in certificate SAN if detected
- **🚀 Proxmox Integration**: Enhanced `proxmox-standalone.sh` script with automatic network SSL setup
- **🔥 Direct HTTPS Mode**: Flask app runs directly on HTTPS:5001 without Nginx proxy (more efficient)

### Changed - NETWORK-FIRST ARCHITECTURE ⚡
- **🔒 Network HTTPS by Default**: All installation scripts now generate network-ready SSL certificates
- **🎙️ Microphone Access Everywhere**: Works on ANY network IP, not just localhost
- **📍 Smart IP Detection**: Automatically discovers and configures all available network interfaces
- **⚡ Simplified Architecture**: Removed redundant Nginx proxy, Flask handles HTTPS directly
- **🎯 Certificate Validation**: Automatic verification of SAN configuration after generation
- **🔧 Enhanced Container Setup**: Proxmox containers now get full network SSL support out-of-the-box

### Fixed - CRITICAL NETWORK ACCESS ISSUES 🐛
- **🌐 ERR_SSL_PROTOCOL_ERROR**: Fixed SSL certificate issues for network IPs (192.168.x.x)
- **🎙️ Cross-Network Microphone Access**: Microphone now works from any device on the network
- **🔗 Multi-IP Certificate Support**: One certificate validates ALL network interfaces
- **📱 Browser Security Compliance**: Proper SSL handling for getUserMedia() across network connections
- **🚨 Container IP Changes**: SSL certificates adapt to dynamic container IP assignment

## [0.8.0] - 2025-06-30

### Added - ENTERPRISE HTTPS & MICROPHONE ACCESS 🔒
- **🔐 Self-Signed SSL Certificate**: Created `create-ssl-cert.sh` script for instant HTTPS setup
- **🌐 HTTPS Support**: Application automatically detects SSL certificates and runs with HTTPS
- **🎙️ Microphone Permission Handling**: Enhanced device enumeration with proper permission requests
- **📁 Upload File Status**: Real-time display of selected file info (name, size, type)
- **🎨 Pre-Commit Hook**: Automatic code formatting (isort + Black + ShellCheck) before commits
- **📱 Drag & Drop File Info**: Shows dropped file details immediately

### Changed - PRODUCTION READY IMPROVEMENTS ⚡
- **🔒 HTTPS by Default**: Auto-detects SSL certificates in `/ssl/` directory
- **🎙️ Enhanced Device Selection**: Better microphone enumeration with permission requests
- **📊 Improved Error Messages**: HTTPS requirement clearly communicated to users
- **🚀 Enterprise Code Quality**: Pre-commit hooks prevent unformatted code commits
- **📝 Better Upload UX**: File selection immediately shows file information

### Fixed - CRITICAL MICROPHONE ACCESS 🐛
- **🎙️ Microphone Device List**: Fixed empty device dropdown by requesting permissions first
- **🔐 HTTPS Requirement**: Clear error messages when HTTPS is required for microphone access
- **📱 Device Label Display**: Proper microphone names instead of "Microphone undefined"
- **🌐 Browser Compatibility**: Enhanced getUserMedia error handling across browsers

### Security Enhancements 🔐
- **🔒 SSL/TLS Support**: Self-signed certificates for local HTTPS development
- **🎙️ Secure Microphone Access**: Modern browser security requirements fulfilled
- **🛡️ Browser Security Warnings**: Clear instructions for accepting self-signed certificates

### Developer Experience 🛠️
- **🎨 Automated Code Formatting**: Pre-commit hooks ensure consistent code style
- **📋 GitHub Actions Ready**: Prevents CI/CD failures through local formatting
- **🔍 Shell Script Quality**: ShellCheck integration for robust bash scripts
- **⚡ Enterprise Standards**: Consistent versioning across all modules

### 🚀 **PROXMOX ONE-LINER SSL AUTOMATION** 
- **🔐 Automatic SSL Certificate Generation**: One-Liner now generates self-signed certificates automatically
- **🎙️ HTTPS Microphone Access Ready**: No manual steps required - microphone works immediately
- **⚡ Zero-Configuration HTTPS**: Installation script handles complete SSL setup
- **🛠️ Enterprise One-Liner**: True one-command deployment with all features enabled

### 📋 **UPDATED PROXMOX ONE-LINER:**
```bash
curl -fsSL https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/install-container.sh | sudo bash
```
**Result:** Complete HTTPS-enabled WhisperS2T with working microphone access!
**❓ High Priority Testing Needed:**
- [ ] **WebSocket Stability**: Test long-duration live speech sessions (>10 minutes)
- [ ] **SSL Certificate Acceptance**: Browser workflow for self-signed certificate acceptance
- [ ] **Device Switching**: Hot-swapping microphones during active sessions
- [ ] **File Upload Limits**: Test behavior with files near 100MB limit
- [ ] **Concurrent Users**: Multiple WebSocket connections simultaneously

**❓ Performance Questions:**
- [ ] **Memory Usage**: Monitor memory consumption during extended live sessions
- [ ] **Audio Quality**: Test different microphone bitrates and sample rates
- [ ] **Network Latency**: WebSocket performance over slow connections
- [ ] **Browser Support**: Test across Chrome/Firefox/Safari/Edge

**❓ Production Deployment:**
- [ ] **Let's Encrypt Integration**: Upgrade from self-signed to real certificates
- [ ] **Reverse Proxy**: Nginx/Apache configuration for production
- [ ] **Container Deployment**: HTTPS support in Docker/Proxmox containers
- [ ] **Backup/Recovery**: SSL certificate management and renewal

### Architecture Notes 🏗️
- **SSL Path**: `/ssl/whisper-appliance.{crt,key}` (auto-detected)
- **HTTPS Port**: 5001 (same as HTTP, auto-switches based on certificates)
- **Fallback**: Graceful degradation to HTTP when SSL certificates not found
- **Security**: Self-signed certificates valid for 365 days

---

## [0.7.2] - 2025-06-30

### Fixed
- **🐛 Critical Deployment Fix**: Fixed hardcoded template path causing systemd service failures
- **🔧 Working Directory**: Corrected systemd service working directory to /opt/whisper-appliance/src
- **📦 Dependencies**: Added flask-swagger-ui to Proxmox installer pip packages
- **🎙️ HTTPS Microphone Access**: Enhanced getUserMedia error handling with HTTPS requirement detection
- **🖥️ Device Selection**: Restored complete audio device enumeration and selection functionality

### Added
- **📱 Enhanced Error Messages**: Better microphone access error messages with HTTPS guidance
- **🔄 Robust Template Loading**: Dynamic path resolution using script directory
- **⚙️ Complete Audio Interface**: Full microphone device selection and initialization

### Changed
- **🏗️ Code Architecture**: Cleaned up main.py by moving JavaScript directly to template
- **📝 Template Integration**: Self-contained HTML template with embedded functionality
- **🌐 Production Ready**: Fixed all deployment issues for Proxmox containers

### Technical Details
- **Template Path**: Now uses `os.path.join(script_dir, "templates", "main_interface.html")`
- **SystemD Service**: WorkingDirectory set to `/opt/whisper-appliance/src`
- **Dependencies**: flask-swagger-ui added to installation script
- **Microphone Access**: Enhanced with HTTPS requirement detection and better error handling

## [0.7.1] - 2025-06-29

### Added
- **📚 Professional SwaggerUI**: Replaced custom API documentation with industry-standard SwaggerUI
- **🎙️ Live Speech Demo**: Complete microphone recording demo in /demo interface
- **🔄 Dynamic Base URL**: API documentation automatically detects current server URL
- **📱 Interactive API Testing**: "Try it out" functionality directly in SwaggerUI

### Changed
- **🎯 API Documentation**: Migrated from custom HTML to OpenAPI 3.0 specification
- **🌐 Demo Interface**: Enhanced with real-time speech recording and testing
- **📊 Professional Standards**: Industry-standard API documentation interface

### Fixed
- **🔗 Hardcoded URLs**: Removed "your-server:5001" with dynamic URL detection
- **📝 Documentation Quality**: Professional appearance matching industry standards

### Technical Details
- **SwaggerUI Integration**: OpenAPI 3.0 with complete endpoint documentation
- **Live Speech Demo**: Start/stop recording, language selection, visual feedback
- **WebSocket Integration**: Real-time audio processing in demo interface
- **Dynamic Configuration**: Server URL automatically detected from request headers

## [0.7.0] - 2025-06-29

### Added
- **🏗️ Modular Architecture**: Complete restructure into modular components (live_speech, upload_handler, admin_panel, api_docs)
- **🎙️ Real Live Speech**: Implemented genuine WebSocket audio processing (replaced simulated connection)
- **⚙️ Admin Panel with Navigation**: Comprehensive admin dashboard with inter-interface navigation
- **📚 Enhanced API Documentation**: Swagger-like interface with interactive "Try it out" functionality
- **🎯 Enhanced Demo Interface**: Interactive testing interface with WebSocket testing
- **🔄 Real-time Audio Processing**: MediaRecorder API integration with base64 audio streaming
- **📱 Responsive Navigation**: Unified navigation header across all interfaces

### Changed
- **🏗️ Architecture**: Converted from monolithic (1513 lines) to modular structure (max 471 lines per file)
- **🔌 WebSocket Implementation**: Replaced "Connected (Simulated)" with real audio chunk processing
- **🎨 UI Enhancement**: Preserved Purple Gradient UI while adding cross-interface navigation
- **📊 System Monitoring**: Enhanced admin panel with real-time statistics and quick actions
- **🌐 Endpoint Organization**: Structured API endpoints with comprehensive documentation

### Fixed
- **🔧 File Structure**: Resolved corrupted enhanced_app.py with clean modular implementation
- **📝 Feature Preservation**: Maintained all original functionality while enhancing architecture
- **⚡ Performance**: Optimized file sizes according to MainPrompt.md guidelines (≤400 lines)
- **🔗 Navigation**: Added seamless navigation between main interface, admin, docs, and demo

### Technical Details
- **Framework**: Flask + SocketIO with modular handlers
- **Modules**: live_speech.py, upload_handler.py, admin_panel.py, api_docs.py
- **Templates**: Separated HTML templates in dedicated templates/ directory
- **Features**: Purple Gradient UI + Real WebSocket + Upload + Full Navigation
- **Endpoints**: /, /admin, /docs, /demo, /health, /transcribe, /api/transcribe-live, /api/status

## [0.6.3] - 2025-06-29

### Fixed
- **Critical Service Fix**: Resolved persistent gunicorn exit-code 3 by converting FastAPI to Flask
- **Framework Compatibility**: Fixed incompatibility between FastAPI app and gunicorn WSGI server
- **Service Startup**: Service now starts successfully without exit-code errors
- **Purple Gradient Interface**: Restored original enhanced UI with dual-tab interface

### Changed
- **Framework Migration**: Converted enhanced_app.py from FastAPI to Flask for gunicorn compatibility
- **Interface Design**: Maintained purple gradient background with live speech + upload tabs
- **Dependencies**: Optimized package requirements (removed FastAPI/uvicorn, kept Flask/gunicorn)
- **Service Configuration**: Standard gunicorn WSGI deployment (no worker-class needed)

### Added
- **Dual Interface**: Live Speech tab (simulated) + Upload Audio tab (functional)
- **Enhanced UI Elements**: Drag & drop upload, status displays, connection simulation
- **API Endpoints**: /health, /transcribe, /api/status for monitoring and functionality
- **Error Handling**: Comprehensive error handling for uploads and transcription

### Technical Details
- **Root Cause**: FastAPI app was incompatible with gunicorn WSGI server
- **Solution**: Migrated to Flask while preserving all UI features and functionality
- **Result**: Service starts correctly, interface loads, transcription works
- **Performance**: Maintained original enhanced UI with improved stability

## [0.6.2] - 2025-06-29

### Fixed
- **Critical Deployment Fix**: Resolved gunicorn service exit-code 3 error in Proxmox deployment
- **File Naming Consistency**: Fixed enhanced_app.py vs app.py naming conflict in deployment scripts
- **Service Configuration**: Updated all scripts to use consistent `src.enhanced_app:app` module path
- **Audio Dependencies**: Added missing sounddevice and numpy packages for live speech functionality

### Changed
- **Script Consistency**: Updated proxmox-standalone.sh to save enhanced_app.py with correct filename
- **Install Scripts**: Fixed install-container.sh to create enhanced_app.py instead of app.py
- **Service Files**: All systemd services now correctly reference src.enhanced_app:app

### Technical Details
- Resolved module import error where service tried to load src.enhanced_app:app but file was saved as app.py
- Enhanced deployment reliability by fixing download/save filename consistency
- Improved audio input support with proper dependency installation

## [0.6.1] - 2025-06-29

### Fixed
- **GitHub Actions CI/CD**: Resolved isort import sorting failures
- **Proxmox Deployment**: Fixed gunicorn service configuration (src.app → src.enhanced_app)
- **Script Consolidation**: Removed redundant Proxmox scripts, kept only robust `proxmox-standalone.sh`
- **Documentation**: Updated README.md and PROXMOX-HELPER-SCRIPTS.md to reference correct scripts

### Restored
- **Original Enhanced Interface**: Purple gradient background with glassmorphism effects
- **Live Speech Functionality**: WebSocket-based real-time speech recognition (/ws/audio)
- **Device Selection**: Whisper model and microphone selection dropdowns
- **Language Recognition**: Multi-language support with auto-detection
- **Test Mode**: Simulated audio input for testing scenarios

### Removed
- **Redundant Scripts**: Deleted proxmox-helper.sh, proxmox-install.sh, proxmox-oneliner.sh
- **Script Chaos**: Consolidated to single robust deployment solution

### Changed
- **Version**: Enhanced App updated to v0.6.1
- **Script Architecture**: Simplified to single `proxmox-standalone.sh` with fallback mechanisms
- **Documentation**: Clarified one-liner installation process

## [Unreleased]

### Added
- 🎙️ **Live Speech Recognition**: Real-time microphone-based transcription
- **Dual Interface**: Live Speech + File Upload tabs in single application
- **Audio Input Manager**: Hardware microphone detection with simulated fallback
- **Audio Visualization**: Real-time audio level indicators during recording
- **Background Transcription**: Non-blocking continuous speech processing
- **Enhanced UI**: Modern tabbed interface with improved user experience
- Enterprise-level development status warning in README
- Professional changelog structure following industry standards

### Changed
- **Enhanced App**: Integrated live speech capabilities into main application
- **Dependencies**: Added sounddevice and numpy for audio input processing
- **System Dependencies**: Improved audio library support in installation scripts

### Fixed
- Audio input management and microphone detection
- Real-time transcription worker threading
- User interface responsiveness during live recording

## [0.6.0] - 2025-06-29

### 🔄 **MAJOR STRATEGY CHANGE**

#### **NEW APPROACH: Proxmox Container First**
- **Priority Shift**: Focus on Proxmox LXC Container deployment instead of ISO builds
- **Reason**: Fedora livemedia-creator proved unreliable with 15+ hour build times and library conflicts
- **Target**: Debian-based ISO builds planned for future (more stable than Fedora Rawhide)

### Added
- ✅ **Proxmox One-Liner Deployment** - Complete installation with single command
- ✅ **Container-First Architecture** - LXC container deployment strategy
- ✅ **Automated Setup Scripts** - `install-container.sh` and `proxmox-standalone.sh`
- ✅ **Web-based Update Management** - Update system with safety features and rollback
- ✅ **Health Check Endpoints** - `/health` API for monitoring
- ✅ **Enterprise CI/CD Pipeline** - GitHub Actions with quality checks
- ✅ **Comprehensive Documentation** - Architecture, deployment, and troubleshooting guides
- ✅ **Security Configuration** - Firewall setup and user isolation

### Changed
- **Deployment Strategy**: Container-first approach instead of ISO builds
- **Target OS**: Ubuntu 22.04 LTS instead of Fedora Rawhide
- **Installation Time**: Reduced from 15+ hours to 10-15 minutes

### Fixed
- ShellCheck SC1078 error in proxmox-standalone.sh (unclosed quote in Jinja2 template)
- Permission issues in LXC container script execution
- GitHub Actions CI/CD pipeline failures

### Security
- Added security policy and vulnerability reporting process
- Implemented secure deployment practices
- Added code audit recommendations for production use

---

## [0.5.0] - 2025-06-27

### Attempted
- **Fedora ISO Build System**: Extensive work on livemedia-creator
- **Mock Build Environment**: Complex dependency management

### Issues Found
- Library conflicts between packages
- 15+ hour build times with frequent hangs
- Mock environment instability
- `auth` vs `authselect` kickstart syntax changes

### Deprecated
- Fedora-based ISO build approach (moved to container-first strategy)

## [0.4.0] - 2025-06-26

### Added
- Initial WhisperS2T integration
- Docker development environment
- Basic web interface implementation
- File upload functionality

## [0.3.0] - 2025-06-25

### Added
- Project structure establishment
- Multi-platform build system design
- Development tooling (`dev.sh`)
- Initial documentation structure

---

## Technical Notes

### **Fedora ISO Build Issues Encountered**
- `auth` vs `authselect` kickstart syntax changes
- Missing `dracut-live` packages
- `livmedia-creator` "results_dir should not exist" errors  
- PulseAudio vs PipeWire conflicts
- Missing libblockdev libraries in Mock environment
- 15+ hour build times with frequent hangs

### **Container Advantages**
- Standard Linux distribution base (Debian/Ubuntu)
- Package manager reliability
- Faster iteration cycles
- Standard deployment workflows
- Better debugging capabilities

---

## Future Planning

### **Container Deployment (v0.6.x)**
- [x] ✅ Proxmox LXC template creation
- [x] ✅ Automated dependency installation  
- [x] ✅ Git-based deployment workflow
- [x] ✅ SSH deployment scripting
- [x] ✅ Container optimization
- [ ] Multi-model support (base, small, medium, large)
- [ ] GPU acceleration support
- [ ] Container template packaging

### **Debian ISO Build (v0.7.x)**  
- [ ] Switch to Debian stable base
- [ ] Standard live-build toolchain
- [ ] Reliable ISO generation
- [ ] Hardware compatibility testing

### **Production Deployment (v0.8.x)**
- [ ] Hardware appliance testing
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation completion
