# Enhanced WhisperS2T Appliance - Changelog

## v0.6.0 - 2025-06-28

### 🔄 **MAJOR STRATEGY CHANGE**

#### **NEW APPROACH: Proxmox Container First**
- **Priority Shift**: Focus on Proxmox LXC Container deployment instead of ISO builds
- **Reason**: Fedora livemedia-creator proved unreliable with 15+ hour build times and library conflicts
- **Target**: Debian-based ISO builds planned for future (more stable than Fedora Rawhide)

#### **Container-First Benefits**
- ✅ **Faster Testing**: Minutes instead of hours
- ✅ **Easy Deployment**: Git clone and run
- ✅ **Resource Efficient**: LXC containers vs full VMs
- ✅ **Scalable**: Multiple instances possible
- ✅ **Reliable**: No complex ISO build dependencies

#### **Updated Deployment Strategy**
1. **Phase 1 (Current)**: Proxmox LXC Container - ✅ **READY**
2. **Phase 2 (Future)**: Debian-based Live ISO  
3. **Phase 3 (Future)**: Dedicated hardware appliance

#### **NEW: Proxmox One-Liner Deployment** 
- ✅ **Single command installation** - Complete deployment in one line
- ✅ **Automated container creation** - No manual Proxmox setup needed
- ✅ **Template management** - Downloads Ubuntu 22.04 automatically
- ✅ **Resource optimization** - Pre-configured for optimal performance
- ✅ **Community-scripts pattern** - Following established Proxmox standards
- ✅ **Batch deployment support** - Create multiple containers easily

#### **Container Deployment Ready**
- ✅ Complete install-container.sh script
- ✅ Systemd service configuration
- ✅ Nginx reverse proxy setup  
- ✅ Web interface with file upload
- ✅ Health check endpoints
- ✅ Resource optimization
- ✅ Security configuration

#### **NEW: Comprehensive Update Management** 
- ✅ **Web-based updates** - Update directly from browser interface
- ✅ **CLI update tools** - `./dev.sh update` and `./auto-update.sh` 
- ✅ **Automatic backups** - Safe rollback to previous versions
- ✅ **GitHub integration** - Pull updates directly from repository
- ✅ **Service management** - Automatic service restart after updates
- ✅ **Safety features** - Health checks and automatic rollback on failure

---

## Previous Versions

### v0.5.0 - 2025-06-27
- **Fedora ISO Build Attempts**: Extensive work on livemedia-creator
- **Issues Found**: Library conflicts, 15+ hour build times, Mock environment problems
- **Learning**: Custom ISO builds are complex and error-prone

### v0.4.0 - 2025-06-26  
- Initial WhisperS2T integration
- Docker and development environment setup
- Basic web interface implementation

### v0.3.0 - 2025-06-25
- Project structure establishment
- Multi-platform build system design
- Development tooling (`dev.sh`)

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
