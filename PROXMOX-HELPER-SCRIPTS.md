# 🚀 Proxmox Helper Scripts

## 📋 Overview

Whisper Appliance includes a **Proxmox VE Helper Script** inspired by the popular [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE) project. This script enables **one-command deployment** of Whisper Appliance in LXC containers.

## ⚡ One-Liner Installation

### **Instant Deployment**
```bash
# Download and run standalone script:
wget https://github.com/GaboCapo/whisper-appliance/raw/main/scripts/proxmox-standalone.sh
chmod +x proxmox-standalone.sh
./proxmox-standalone.sh
```

**Alternative (direct curl execution):**
```bash
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

**That's it!** This single command will:
- ✅ Create a new LXC container automatically
- ✅ Download Ubuntu 22.04 template if needed
- ✅ Install Whisper Appliance with all dependencies
- ✅ Configure web interface and services
- ✅ Setup update management system
- ✅ Provide you with the web interface URL

**⏱️ Total time: ~10-15 minutes**

## 🎯 What the Scripts Do

### **Automated Container Creation**
- **Container ID**: Automatically assigns next available ID
- **Template**: Downloads Ubuntu 22.04 LXC template
- **Resources**: 2 CPU cores, 4GB RAM, 20GB storage
- **Network**: DHCP configuration with bridge
- **Features**: Nesting and keyctl enabled for Docker support

### **Whisper Appliance Installation**
- **System Updates**: Updates container to latest packages
- **Dependencies**: Installs Python, FFmpeg, audio libraries
- **Application**: Clones and installs Whisper Appliance
- **Services**: Configures systemd and nginx
- **Updates**: Sets up GitHub-based update system

## 📊 Comparison with Manual Methods

| Method | Time | Steps | Complexity |
|--------|------|-------|------------|
| **One-Liner Script** | 10-15 min | 1 command | ⭐ Easy |
| **Manual Container + install-container.sh** | 20-30 min | 5-10 steps | ⭐⭐ Medium |
| **Full Manual Setup** | 45-60 min | 20+ steps | ⭐⭐⭐ Hard |

## 🔧 Script Architecture

### **proxmox-standalone.sh** (Complete Solution)
- **Purpose**: Complete automated deployment with fallback mechanisms
- **Features**: Robust downloads, template management, container creation, installation
- **Usage**: Perfect for all deployment scenarios
- **Output**: Ready-to-use Whisper Appliance container
- **Reliability**: Self-contained with robust error handling

**This is the only script you need!** All other scripts were consolidated into this robust solution.

## 🎛️ Configuration Options

### **Default Settings**
```bash
Container ID: Auto-assigned (next available)
Hostname: whisper-appliance
CPU Cores: 2
RAM: 4096 MB (4GB)
Storage: 20 GB
OS: Ubuntu 22.04 LTS
Network: DHCP on vmbr0
Features: nesting=1, keyctl=1
Unprivileged: Yes
```

### **Customization via Environment Variables**
```bash
# Custom resource allocation
export WHISPER_CPU="4"
export WHISPER_RAM="8192"
export WHISPER_DISK="50"

# Then run the script
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

## 🛠 Advanced Usage

### **Resource-Optimized Installation**
```bash
# High-performance deployment
export WHISPER_CPU="4"
export WHISPER_RAM="8192"
export WHISPER_DISK="50"
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

## 🔍 Troubleshooting

### **Common Issues**

**1. "Template not found"**
```bash
# Script will automatically download, but you can pre-download:
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

**2. "Container ID already in use"**
```bash
# Check available IDs:
pvesh get /cluster/nextid
```

**3. "Insufficient storage"**
```bash
# Check storage:
pvesh get /nodes/$(hostname)/storage
```

**4. "Network issues"**
```bash
# Check network bridge:
ip link show vmbr0
```

### **Manual Verification**
```bash
# Check container status
pct status <CTID>

# Get container IP
pct exec <CTID> -- hostname -I

# Check Whisper Appliance service
pct exec <CTID> -- systemctl status whisper-appliance

# Access container console
pct enter <CTID>
```

## 🎯 Post-Installation

### **Immediate Next Steps**
1. **Access Web Interface**: `http://<container-ip>:5000`
2. **Test Audio Upload**: Upload a test audio file
3. **Check Updates**: Go to Updates tab in web interface
4. **Configure as needed**: Adjust settings via web interface

### **Management Commands**
```bash
# Container management
pct start <CTID>     # Start container
pct stop <CTID>      # Stop container
pct restart <CTID>   # Restart container
pct destroy <CTID>   # Delete container

# Whisper Appliance management (inside container)
pct exec <CTID> -- systemctl restart whisper-appliance
pct exec <CTID> -- journalctl -u whisper-appliance -f
pct exec <CTID> -- /opt/whisper-appliance/auto-update.sh status
```

## 🔄 Updates and Maintenance

### **Update Whisper Appliance**
```bash
# Via web interface (recommended)
# Go to http://<container-ip>:5000 → Updates tab → Install Updates

# Via command line
pct exec <CTID> -- /opt/whisper-appliance/auto-update.sh apply
```

### **Container Backup**
```bash
# Create backup
vzdump <CTID> --storage local --compress gzip

# Restore from backup
pct restore <NEW_CTID> /var/lib/vz/dump/vzdump-lxc-<CTID>-*.tar.gz --storage local-lvm
```

## 🏗️ How It Works (Technical Details)

### **Script Execution Flow**
1. **Validation**: Check Proxmox environment and permissions
2. **Template Management**: Download Ubuntu 22.04 if not present
3. **Container Creation**: Create LXC with optimized settings
4. **Network Setup**: Configure DHCP networking
5. **Installation**: Clone repo and run install-container.sh
6. **Service Setup**: Configure systemd services and nginx
7. **Finalization**: Start services and report access URL

### **Behind the Scenes**
```bash
# What the one-liner actually does:
pct create <CTID> ubuntu-22.04-template \
    --hostname whisper-appliance \
    --cores 2 \
    --memory 4096 \
    --rootfs local-lvm:20 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --features nesting=1,keyctl=1 \
    --unprivileged 1 \
    --onboot 1

pct start <CTID>

pct exec <CTID> -- bash -c "
    apt-get update && apt-get upgrade -y
    apt-get install -y git curl
    git clone https://github.com/GaboCapo/whisper-appliance.git
    cd whisper-appliance
    ./install-container.sh
"
```

## 🌟 Why Use Helper Scripts?

### **Benefits over Manual Installation**
- **Speed**: 1 command vs 20+ manual steps
- **Reliability**: Tested and automated process
- **Consistency**: Same setup every time
- **Error Handling**: Automatic validation and error recovery
- **Best Practices**: Optimized container configuration

### **Inspired by Community Standards**
Our helper scripts follow the same patterns as the popular **community-scripts/ProxmoxVE** project:
- **One-liner deployment**: `bash -c "$(wget -qLO - <url>)"`
- **Interactive configuration**: Advanced settings when needed
- **Automatic template management**: Downloads dependencies
- **Error handling**: Robust validation and recovery
- **Community-friendly**: Easy to understand and modify

## 🎭 Multiple Deployment Scenarios

### **Single Instance (Most Common)**
```bash
# Quick single deployment
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

### **Development Setup**
```bash
# Multiple containers for testing - run multiple times with different hostnames
export WHISPER_HOSTNAME="whisper-dev"
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

### **Production Deployment**
```bash
# High-resource production container
export WHISPER_CPU="4"
export WHISPER_RAM="8192"
export WHISPER_DISK="50"
bash <(curl -s https://raw.githubusercontent.com/GaboCapo/whisper-appliance/main/scripts/proxmox-standalone.sh)
```

## 📈 Performance Considerations

### **Resource Requirements by Use Case**

| Use Case | CPU | RAM | Storage | Whisper Model |
|----------|-----|-----|---------|---------------|
| **Testing** | 1-2 cores | 2-4GB | 10-20GB | base |
| **Personal** | 2 cores | 4GB | 20GB | base/small |
| **Small Team** | 2-4 cores | 4-8GB | 30GB | small/medium |
| **Production** | 4+ cores | 8-16GB | 50GB+ | medium/large |

### **Optimization Tips**
- **CPU**: More cores = faster transcription
- **RAM**: Large models need more memory
- **Storage**: Models and uploads require space
- **Network**: Gigabit recommended for large files

## 🔐 Security Considerations

### **Container Security**
- **Unprivileged**: Containers run in unprivileged mode
- **Isolation**: Proper Linux namespaces and cgroups
- **Updates**: Automatic security updates available
- **Firewall**: Only port 5000 exposed by default

### **Access Control**
- **SSH**: Root access to container (secure with keys)
- **Web Interface**: No authentication by default (add nginx auth if needed)
- **Network**: Consider VPN for remote access

## 🎉 Success Stories

### **Typical User Experience**
1. **Copy one-liner** from documentation
2. **Paste in Proxmox shell** and press Enter
3. **Wait 10-15 minutes** while drinking coffee ☕
4. **Access web interface** and upload first audio file
5. **Get transcription** in seconds
6. **Share success** with friends! 🎉

---

## 💡 Pro Tips

- **Pre-download template**: `pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst`
- **Use SSD storage**: Faster container performance
- **Enable backups**: Regular vzdump scheduling
- **Monitor resources**: Check container resource usage
- **Update regularly**: Use web interface Updates tab

**🚀 Ready to deploy? Copy the one-liner and get Whisper Appliance running in minutes!**