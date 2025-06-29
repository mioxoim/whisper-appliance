# Enhanced WhisperS2T Appliance - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
