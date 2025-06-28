#!/bin/bash
# WhisperS2T Appliance Auto-Updater
# Standalone update script for production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[UPDATE]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Configuration
APP_DIR="/opt/whisper-appliance"
BACKUP_DIR="$APP_DIR/.backups"
SERVICE_NAME="whisper-appliance"
UPDATE_MODE="${1:-check}"

# Check if running as root (required for service management)
if [ "$EUID" -ne 0 ] && [ "$UPDATE_MODE" != "check" ]; then
    print_error "This script must be run as root for system updates"
    print_status "Use 'sudo $0 $UPDATE_MODE' or run './dev.sh update $UPDATE_MODE' instead"
    exit 1
fi

print_section "🔄 WhisperS2T Auto-Updater v0.6.0"

# Change to application directory
if [ ! -d "$APP_DIR" ]; then
    print_error "Application directory not found: $APP_DIR"
    print_status "This script is designed for container installations"
    exit 1
fi

cd "$APP_DIR"

# Check if git repository
if [ ! -d ".git" ]; then
    print_error "Not a git repository. Cannot perform updates."
    print_status "This updater only works with git-cloned installations"
    exit 1
fi

# Configure SSH if deploy key exists
if [ -f "./deploy_key_whisper_appliance" ]; then
    export GIT_SSH_COMMAND="ssh -i ./deploy_key_whisper_appliance -o IdentitiesOnly=yes"
    print_status "Using deploy key for GitHub access"
fi

update_check() {
    print_section "🔍 Checking for Updates"
    
    print_status "Fetching latest changes from GitHub..."
    if ! git fetch origin main 2>/dev/null; then
        print_error "Failed to fetch updates from GitHub"
        return 1
    fi
    
    # Get current and remote commits
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo $LOCAL_COMMIT | cut -c1-8)
    
    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        print_success "✅ System is up to date!"
        print_status "Current version: $CURRENT_VERSION"
        return 0
    fi
    
    print_warning "🔄 Updates available!"
    print_status "Current version: $CURRENT_VERSION"
    print_status "Current commit:  $LOCAL_COMMIT"
    print_status "Latest commit:   $REMOTE_COMMIT"
    
    # Show what will be updated
    COMMITS_BEHIND=$(git rev-list --count "$LOCAL_COMMIT..origin/main")
    print_status "Commits behind: $COMMITS_BEHIND"
    
    echo ""
    echo "Recent changes:"
    git log --oneline --decorate --color=always -5 "$LOCAL_COMMIT..origin/main"
    echo ""
    
    return 2  # Updates available
}

create_backup() {
    print_section "💾 Creating Backup"
    
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)-$(git rev-parse --short HEAD)"
    CURRENT_COMMIT=$(git rev-parse HEAD)
    
    # Save current commit info
    echo "$CURRENT_COMMIT" > "$BACKUP_DIR/$BACKUP_NAME.commit"
    echo "$(date)" > "$BACKUP_DIR/$BACKUP_NAME.timestamp"
    
    print_success "Backup created: $BACKUP_NAME"
    print_status "Backup location: $BACKUP_DIR/$BACKUP_NAME.commit"
    
    # Keep only last 5 backups
    cd "$BACKUP_DIR"
    ls -t *.commit 2>/dev/null | tail -n +6 | while read backup; do
        backup_name=$(basename "$backup" .commit)
        rm -f "$backup" "$backup_name.timestamp" 2>/dev/null || true
        print_status "Removed old backup: $backup_name"
    done
    cd "$APP_DIR"
}

stop_services() {
    print_section "🛑 Stopping Services"
    
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_status "Stopping $SERVICE_NAME service..."
        if systemctl stop "$SERVICE_NAME"; then
            print_success "Service stopped successfully"
            SERVICE_WAS_RUNNING=true
        else
            print_warning "Failed to stop service gracefully"
        fi
    else
        print_status "Service is not running"
        SERVICE_WAS_RUNNING=false
    fi
}

apply_updates() {
    print_section "⬇️ Applying Updates"
    
    print_status "Pulling latest changes from GitHub..."
    
    if git pull origin main; then
        print_success "✅ Updates applied successfully!"
        
        # Update file permissions
        print_status "Updating file permissions..."
        chmod +x *.sh 2>/dev/null || true
        
        # Get new version
        NEW_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
        print_success "Updated to version: $NEW_VERSION"
        
        # Check if requirements changed
        if git diff --name-only HEAD~1 HEAD | grep -q "requirements"; then
            print_warning "⚠️ Requirements files changed!"
            print_status "You may need to update Python dependencies:"
            print_status "  pip install -r requirements-container.txt"
        fi
        
        return 0
    else
        print_error "❌ Update failed!"
        print_warning "You may need to resolve conflicts manually"
        return 1
    fi
}

start_services() {
    print_section "🚀 Starting Services"
    
    if [ "$SERVICE_WAS_RUNNING" = true ]; then
        print_status "Restarting $SERVICE_NAME service..."
        if systemctl start "$SERVICE_NAME"; then
            print_success "Service started successfully"
            
            # Wait a moment and check if it's running
            sleep 3
            if systemctl is-active --quiet "$SERVICE_NAME"; then
                print_success "✅ Service is running properly"
            else
                print_warning "⚠️ Service may have failed to start"
                print_status "Check logs: journalctl -u $SERVICE_NAME -n 20"
            fi
        else
            print_error "❌ Failed to start service"
            return 1
        fi
    else
        print_status "Service was not running before update - not starting"
    fi
}

test_installation() {
    print_section "🧪 Testing Installation"
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    sleep 2
    
    if curl -s "http://localhost:5000/health" >/dev/null 2>&1; then
        print_success "✅ Health endpoint responsive"
        
        # Check if response is valid JSON
        HEALTH_RESPONSE=$(curl -s "http://localhost:5000/health")
        if echo "$HEALTH_RESPONSE" | grep -q '"status"'; then
            print_success "✅ Health check returns valid response"
        else
            print_warning "⚠️ Health endpoint returns unexpected response"
        fi
    else
        print_warning "⚠️ Health endpoint not accessible"
        print_status "Service may still be starting up"
    fi
    
    # Run container test if available
    if [ -f "./test-container.sh" ]; then
        print_status "Running installation test..."
        if timeout 30 ./test-container.sh >/dev/null 2>&1; then
            print_success "✅ Installation test passed"
        else
            print_warning "⚠️ Installation test failed or timed out"
        fi
    fi
}

update_apply() {
    print_section "🔄 Applying WhisperS2T Updates"
    
    # Check for updates first
    if ! update_check; then
        print_error "Update check failed"
        exit 1
    fi
    
    # If no updates available, exit
    if [ $? -eq 0 ]; then
        print_success "System is already up to date"
        exit 0
    fi
    
    # Confirm update
    if [ -t 0 ]; then  # If running interactively
        echo ""
        read -p "Continue with update? [y/N]: " CONFIRM
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            print_status "Update cancelled"
            exit 0
        fi
    fi
    
    # Create backup
    create_backup
    
    # Stop services
    stop_services
    
    # Apply updates
    if apply_updates; then
        # Start services
        start_services
        
        # Test installation
        test_installation
        
        print_section "✅ Update Complete!"
        print_success "WhisperS2T has been updated successfully!"
        
        NEW_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
        print_success "Version: $NEW_VERSION"
        
        CONTAINER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
        print_success "Web Interface: http://$CONTAINER_IP:5000"
        
    else
        print_error "Update failed!"
        print_warning "Attempting to restore from backup..."
        
        # Try to restore from backup
        if rollback_update; then
            print_success "System restored from backup"
        else
            print_error "Backup restoration failed!"
            print_status "Manual intervention may be required"
        fi
        exit 1
    fi
}

rollback_update() {
    print_section "⏪ Rolling Back Update"
    
    # Find latest backup
    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "No backup directory found"
        return 1
    fi
    
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.commit 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "No backup found"
        return 1
    fi
    
    BACKUP_COMMIT=$(cat "$LATEST_BACKUP")
    BACKUP_NAME=$(basename "$LATEST_BACKUP" .commit)
    
    print_status "Rolling back to: $BACKUP_NAME"
    print_status "Backup commit: $BACKUP_COMMIT"
    
    # Stop services
    stop_services
    
    # Rollback to backup commit
    if git reset --hard "$BACKUP_COMMIT"; then
        print_success "✅ Rollback successful!"
        
        # Update file permissions
        chmod +x *.sh 2>/dev/null || true
        
        # Start services
        start_services
        
        # Remove used backup
        rm -f "$LATEST_BACKUP" "$BACKUP_DIR/$BACKUP_NAME.timestamp"
        print_status "Backup $BACKUP_NAME removed"
        
        CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
        print_success "Rolled back to version: $CURRENT_VERSION"
        
        return 0
    else
        print_error "❌ Rollback failed!"
        return 1
    fi
}

show_status() {
    print_section "📊 Update Status"
    
    CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
    CURRENT_COMMIT=$(git rev-parse HEAD)
    CURRENT_BRANCH=$(git branch --show-current)
    
    print_status "Current version: $CURRENT_VERSION"
    print_status "Current commit:  $CURRENT_COMMIT"
    print_status "Current branch:  $CURRENT_BRANCH"
    echo ""
    
    # Check for updates
    print_status "Checking for updates..."
    if git fetch origin main 2>/dev/null; then
        REMOTE_COMMIT=$(git rev-parse origin/main)
        
        if [ "$CURRENT_COMMIT" = "$REMOTE_COMMIT" ]; then
            print_success "✅ System is up to date"
        else
            print_warning "🔄 Updates available"
            COMMITS_BEHIND=$(git rev-list --count "$CURRENT_COMMIT..origin/main")
            print_status "Commits behind: $COMMITS_BEHIND"
        fi
    else
        print_warning "⚠️ Cannot check for updates (network/auth issue)"
    fi
    
    # Service status
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_success "✅ Service is running"
    else
        print_warning "⚠️ Service is not running"
    fi
    
    # Show available backups
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        echo ""
        print_status "Available backups:"
        for backup in "$BACKUP_DIR"/*.commit; do
            if [ -f "$backup" ]; then
                backup_name=$(basename "$backup" .commit)
                if [ -f "$BACKUP_DIR/$backup_name.timestamp" ]; then
                    timestamp=$(cat "$BACKUP_DIR/$backup_name.timestamp")
                    print_status "  - $backup_name ($timestamp)"
                else
                    print_status "  - $backup_name"
                fi
            fi
        done
    fi
}

show_help() {
    echo "WhisperS2T Auto-Updater v0.6.0"
    echo ""
    echo "USAGE:"
    echo "  $0 [command]"
    echo ""
    echo "COMMANDS:"
    echo "  check     - Check for available updates (default)"
    echo "  apply     - Apply available updates with backup"
    echo "  rollback  - Rollback to previous version"
    echo "  status    - Show current version and update status"
    echo "  help      - Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 check              # Check for updates"
    echo "  sudo $0 apply         # Apply updates (requires root)"
    echo "  sudo $0 rollback      # Rollback to previous version"
    echo "  $0 status             # Show status"
    echo ""
    echo "NOTE: Apply and rollback require root privileges for service management"
}

# Main execution
case "$UPDATE_MODE" in
    "check")
        update_check
        exit $?
        ;;
    "apply")
        update_apply
        ;;
    "rollback")
        rollback_update
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $UPDATE_MODE"
        show_help
        exit 1
        ;;
esac