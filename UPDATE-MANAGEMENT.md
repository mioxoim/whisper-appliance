# 🔄 WhisperS2T Update Management

## 📋 Overview

WhisperS2T v0.6.0 includes comprehensive update management that allows you to automatically receive bug fixes, new features, and security updates directly from GitHub.

## 🎯 Update Methods

### 1. Web Interface (Recommended)
- Access your WhisperS2T web interface
- Click on the **"Updates"** tab
- Click **"Check for Updates"** 
- If updates are available, click **"Install Updates"**
- System will automatically backup, update, and restart

### 2. Command Line (dev.sh)
```bash
# Check for updates
./dev.sh update check

# Apply updates
./dev.sh update apply

# Rollback to previous version
./dev.sh update rollback

# Show update status
./dev.sh update status
```

### 3. Auto-Updater Script
```bash
# Check for updates
./auto-update.sh check

# Apply updates (requires root)
sudo ./auto-update.sh apply

# Rollback to previous version (requires root)
sudo ./auto-update.sh rollback

# Show status
./auto-update.sh status
```

## 🛡️ Safety Features

### Automatic Backup
- **Before every update**, the system creates a backup
- Backup includes current commit hash and timestamp
- **Rollback capability** - can restore previous version instantly
- **Backup retention** - keeps last 5 backups automatically

### Safe Update Process
1. ✅ **Check for updates** from GitHub
2. ✅ **Create backup** of current version
3. ✅ **Stop services** gracefully
4. ✅ **Download updates** via git pull
5. ✅ **Update file permissions**
6. ✅ **Restart services**
7. ✅ **Test installation** with health checks
8. ✅ **Rollback automatically** if update fails

## 📦 What Gets Updated

### Code Updates
- ✅ Web interface improvements
- ✅ Bug fixes and security patches
- ✅ New features and functionality
- ✅ Performance optimizations
- ✅ Documentation updates

### Configuration Preservation
- ✅ **User data preserved** - no transcription data lost
- ✅ **Configuration maintained** - service settings kept
- ✅ **Models preserved** - downloaded Whisper models kept
- ✅ **Log retention** - system logs maintained

## 🔧 Container Installation Updates

### For Proxmox LXC Containers

If you installed via the container method:

```bash
# SSH into your container
ssh root@your-container-ip

# Navigate to application directory
cd /opt/whisper-appliance

# Check for updates
./auto-update.sh check

# Apply updates if available
sudo ./auto-update.sh apply

# Or use the web interface at http://container-ip:5000
```

### Update via Web Interface
1. **Access:** `http://your-container-ip:5000`
2. **Navigate:** Click "Updates" tab
3. **Check:** Click "Check for Updates"
4. **Apply:** Click "Install Updates" if available
5. **Wait:** System will update and restart automatically

## 🚨 Troubleshooting Updates

### Update Check Fails
```bash
# Check internet connectivity
ping github.com

# Verify GitHub access with SSH key
ssh -T git@github.com -i /opt/whisper-appliance/deploy_key_whisper_appliance

# Check git repository status
cd /opt/whisper-appliance
git status
```

### Update Apply Fails
```bash
# Check for conflicts
cd /opt/whisper-appliance
git status

# Rollback to previous version
sudo ./auto-update.sh rollback

# Or via web interface "System" tab → "Restart Service"
```

### Service Won't Start After Update
```bash
# Check service logs
journalctl -u whisper-appliance -n 50

# Rollback to previous working version
sudo ./auto-update.sh rollback

# Check health endpoint
curl http://localhost:5000/health
```

## ⚙️ Manual Update Process

If automatic updates fail, you can update manually:

```bash
# Stop service
sudo systemctl stop whisper-appliance

# Navigate to app directory
cd /opt/whisper-appliance

# Create manual backup
git rev-parse HEAD > .manual-backup-$(date +%Y%m%d-%H%M%S)

# Pull latest changes
git pull origin main

# Update permissions
chmod +x *.sh

# Restart service
sudo systemctl start whisper-appliance

# Test installation
./test-container.sh
```

## 🔄 Update Frequency

### Automatic Checking
- **Web interface** checks for updates when "Updates" tab is accessed
- **No automatic installation** - user must approve updates
- **Safe by default** - updates only when explicitly requested

### Recommended Update Schedule
- **Security updates:** Apply immediately when available
- **Feature updates:** Apply during maintenance windows
- **Major updates:** Test in development environment first

## 📊 Update Status Information

### Version Information
- **Current Version:** Shows git tag or commit hash
- **Current Commit:** Full commit hash for precise tracking
- **Commits Behind:** Number of updates available
- **Last Update Check:** Timestamp of last update check

### Available from Web Interface
- Navigate to **"Updates"** tab for full update status
- Navigate to **"System"** tab for service information
- **Health Check** button tests all system components

## 🎯 Best Practices

### Before Updating
1. ✅ **Test current system** - ensure everything works
2. ✅ **Note current version** - record for rollback reference
3. ✅ **Check update notes** - review what's changing
4. ✅ **Plan maintenance window** - especially for production

### During Updates
1. ✅ **Monitor progress** - watch web interface or logs
2. ✅ **Don't interrupt** - let update complete fully
3. ✅ **Wait for restart** - services need time to reload
4. ✅ **Test functionality** - verify transcription works

### After Updates
1. ✅ **Test core functionality** - upload test audio file
2. ✅ **Check all features** - verify web interface
3. ✅ **Monitor performance** - ensure no degradation
4. ✅ **Review logs** - check for any errors

## 🔮 Future Update Features

### Planned Enhancements (v0.7+)
- [ ] **Scheduled updates** - automatic update scheduling
- [ ] **Update notifications** - email/webhook notifications
- [ ] **Staged rollouts** - gradual deployment of updates
- [ ] **Update channels** - stable vs. beta update tracks
- [ ] **Dependency management** - automatic Python package updates

---

**💡 Pro Tip:** Use the web interface for easiest update management - it provides visual feedback and handles all the complexity automatically!

**🛡️ Safety Note:** Updates are designed to be safe and reversible. If anything goes wrong, you can always rollback to the previous working version.