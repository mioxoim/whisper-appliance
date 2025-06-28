# 🔑 SSH Deploy Key Setup for WhisperS2T Appliance

## 📋 Generated Deploy Key Information

**Generated:** 2025-06-28  
**Key Type:** ED25519 (most secure)  
**Purpose:** GitHub Deploy Key for automated deployments

### 🔐 Public Key (for GitHub)

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINF1fn8l/ZsQuWEmlx4qfSVL9ykCovOcpdCbxnvKYrsP deploy-key-whisper-appliance-20250628
```

## 🚀 GitHub Deploy Key Setup

### Step 1: Add Deploy Key to GitHub Repository

1. **Go to your GitHub repository** 
2. **Navigate to:** Settings → Deploy keys
3. **Click:** "Add deploy key"
4. **Configure:**
   - **Title:** `WhisperS2T Appliance Deploy Key - 2025-06-28`
   - **Key:** Copy the public key above
   - **Allow write access:** ✅ Check if you need push access
   - **Click:** "Add key"

### Step 2: Configure SSH for Deployment

```bash
# Clone repository using SSH (instead of HTTPS)
git clone git@github.com:yourusername/whisper-appliance.git

# Or change existing remote to SSH
git remote set-url origin git@github.com:yourusername/whisper-appliance.git
```

### Step 3: Test SSH Connection

```bash
# Test SSH connection to GitHub
ssh -T git@github.com -i /home/commander/Code/whisper-appliance/deploy_key_whisper_appliance

# Expected response:
# Hi yourusername/whisper-appliance! You've successfully authenticated, but GitHub does not provide shell access.
```

## 🔧 Automated Deployment Usage

### Container Deployment Script Enhancement

Add SSH key usage to automated deployment:

```bash
# Example: Enhanced container deployment with SSH key
#!/bin/bash

# Set SSH key for git operations
export GIT_SSH_COMMAND="ssh -i /path/to/deploy_key_whisper_appliance -o IdentitiesOnly=yes"

# Clone repository in container
git clone git@github.com:yourusername/whisper-appliance.git
cd whisper-appliance
./install-container.sh
```

### CI/CD Integration

For GitHub Actions or other CI/CD systems:

```yaml
# Example GitHub Actions usage (add private key as secret)
- name: Setup SSH for deployment
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.DEPLOY_PRIVATE_KEY }}" > ~/.ssh/deploy_key
    chmod 600 ~/.ssh/deploy_key
    ssh-keyscan github.com >> ~/.ssh/known_hosts
    
- name: Clone and deploy
  run: |
    export GIT_SSH_COMMAND="ssh -i ~/.ssh/deploy_key -o IdentitiesOnly=yes"
    git clone git@github.com:yourusername/whisper-appliance.git
```

## 🛡️ Security Best Practices

### Deploy Key Security
- ✅ **Read-only access** recommended (unless push needed)
- ✅ **Repository-specific** - this key only works for whisper-appliance
- ✅ **No passphrase** for automated deployments (but store securely)
- ✅ **Regular rotation** - generate new key every 6-12 months

### Private Key Protection
- 🔒 **Never commit private key** to repository (already in .gitignore)
- 🔒 **Secure storage** on deployment servers only
- 🔒 **Limited access** - only deployment users/services
- 🔒 **Proper permissions** (600 for private key)

### Key Management
```bash
# Secure private key permissions
chmod 600 /home/commander/Code/whisper-appliance/deploy_key_whisper_appliance

# Verify key fingerprint
ssh-keygen -lf /home/commander/Code/whisper-appliance/deploy_key_whisper_appliance.pub
# Should show: 256 SHA256:aFI8HIBnK5H7g79OwpDMHG467AYFO7YF6AIy+ip9nzo
```

## 📦 Proxmox Container Deployment Integration

### Enhanced Container Installation

Update container deployment to use SSH key:

```bash
# In container: Clone via SSH
export GIT_SSH_COMMAND="ssh -i /opt/deploy_key -o IdentitiesOnly=yes"
git clone git@github.com:yourusername/whisper-appliance.git /opt/whisper-appliance
cd /opt/whisper-appliance
./install-container.sh
```

### Automated Updates

```bash
# Update script for containers
#!/bin/bash
cd /opt/whisper-appliance
export GIT_SSH_COMMAND="ssh -i /opt/deploy_key -o IdentitiesOnly=yes"
git pull origin main
systemctl restart whisper-appliance
```

## 🔄 Key Rotation Process

### When to Rotate
- Every 6-12 months
- When team members leave
- If key is potentially compromised
- Before major releases

### Rotation Steps
1. Generate new SSH key pair
2. Add new public key to GitHub
3. Update deployment systems with new private key
4. Test deployments with new key
5. Remove old key from GitHub
6. Delete old private key files

## 📝 Usage Examples

### Manual Deployment with Key
```bash
# Clone repository for deployment
GIT_SSH_COMMAND="ssh -i ./deploy_key_whisper_appliance" \
git clone git@github.com:yourusername/whisper-appliance.git

# Deploy to container
cd whisper-appliance
./install-container.sh
```

### Batch Container Setup
```bash
# Deploy to multiple containers
for container_ip in 192.168.1.100 192.168.1.101 192.168.1.102; do
  ssh root@$container_ip "
    export GIT_SSH_COMMAND='ssh -i /opt/deploy_key -o IdentitiesOnly=yes'
    git clone git@github.com:yourusername/whisper-appliance.git
    cd whisper-appliance
    ./install-container.sh
  "
done
```

---

## ⚠️ Important Notes

1. **Private Key Security:** The private key file (`deploy_key_whisper_appliance`) is already added to .gitignore
2. **GitHub Setup:** Remember to add the public key to your GitHub repository's Deploy Keys
3. **Write Access:** Only enable if you need to push from deployment systems
4. **Key Verification:** Always verify the key fingerprint matches when setting up

**🔑 Your public key is ready to add to GitHub Deploy Keys!**