/**
 * WhisperAppliance Admin Update System
 * Handles system updates and version management
 */

const UpdateManager = {
    currentVersion: null,
    latestVersion: null,
    updateInProgress: false,
    updateCheckInterval: null
};

// Initialize update manager
UpdateManager.init = function() {
    console.log('Initializing Update Manager');
    this.checkCurrentVersion();
    this.bindEventListeners();
    
    // Check for updates every hour
    this.updateCheckInterval = setInterval(() => {
        this.checkForUpdates(true); // Silent check
    }, 3600000);
};

// Get current version
UpdateManager.checkCurrentVersion = async function() {
    try {
        const response = await fetch('/api/v1/version');
        const data = await response.json();
        this.currentVersion = data.version;
        this.updateVersionDisplay();
    } catch (error) {
        console.error('Failed to get current version:', error);
    }
};

// Check for updates
UpdateManager.checkForUpdates = async function(silent = false) {
    if (!silent) {
        AdminCore.showAlert('Checking for updates...', 'info');
    }
    
    try {
        const response = await fetch('/api/v1/update/check');
        const data = await response.json();
        
        this.latestVersion = data.latest_version;
        
        if (data.update_available) {
            if (!silent) {
                this.showUpdateDialog(data);
            } else {
                // Show notification for silent checks
                AdminCore.showAlert(`Update available: ${data.latest_version}`, 'info', 10000);
            }
        } else if (!silent) {
            AdminCore.showAlert('System is up to date', 'success');
        }
        
        this.updateVersionDisplay();
        return data;
        
    } catch (error) {
        console.error('Failed to check for updates:', error);
        if (!silent) {
            AdminCore.showAlert('Failed to check for updates', 'danger');
        }
        return null;
    }
};

// Show update dialog
UpdateManager.showUpdateDialog = function(updateInfo) {
    const content = `
        <div class="update-info">
            <p><strong>New Version Available!</strong></p>
            <div class="version-compare">
                <div>
                    <span class="label">Current Version:</span>
                    <span class="version">${updateInfo.current_version}</span>
                </div>
                <div>
                    <span class="label">Latest Version:</span>
                    <span class="version new">${updateInfo.latest_version}</span>
                </div>
            </div>
            
            ${updateInfo.changelog ? `
            <div class="changelog">
                <h4>What's New:</h4>
                <div class="changelog-content">
                    ${updateInfo.changelog}
                </div>
            </div>
            ` : ''}
            
            <div class="update-warning">
                <p>⚠️ <strong>Important:</strong> The system will restart during the update process.</p>
                <p>Make sure to save any ongoing work before proceeding.</p>
            </div>
        </div>
    `;
    
    AdminCore.showModal(
        '🔄 System Update Available',
        content,
        [
            {
                text: 'Later',
                type: 'secondary',
                onclick: 'document.querySelector(".modal-overlay").remove()'
            },
            {
                text: 'Update Now',
                type: 'primary',
                onclick: 'UpdateManager.performUpdate()'
            }
        ]
    );
};

// Perform system update
UpdateManager.performUpdate = async function() {
    if (this.updateInProgress) {
        AdminCore.showAlert('Update already in progress', 'warning');
        return;
    }
    
    // Close modal
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
    
    this.updateInProgress = true;
    
    // Show progress modal
    AdminCore.showModal(
        '🔄 Updating System',
        `
        <div class="update-progress">
            <div class="spinner"></div>
            <p id="update-status">Starting update process...</p>
            <div class="progress mt-md">
                <div class="progress-bar" id="update-progress" style="width: 0%"></div>
            </div>
            <small id="update-details" class="text-muted"></small>
        </div>
        `,
        [] // No buttons during update
    );
    
    try {
        // Start update
        const response = await fetch('/api/v1/update/perform', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Update request failed');
        }
        
        // Monitor update progress
        this.monitorUpdateProgress();
        
    } catch (error) {
        console.error('Failed to start update:', error);
        this.updateInProgress = false;
        document.querySelector('.modal-overlay').remove();
        AdminCore.showAlert('Failed to start update process', 'danger');
    }
};

// Monitor update progress
UpdateManager.monitorUpdateProgress = function() {
    const statusElement = document.getElementById('update-status');
    const progressBar = document.getElementById('update-progress');
    const detailsElement = document.getElementById('update-details');
    
    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/v1/update/status');
            const data = await response.json();
            
            // Update UI
            if (statusElement) statusElement.textContent = data.status || 'Updating...';
            if (progressBar) progressBar.style.width = `${data.progress || 0}%`;
            if (detailsElement) detailsElement.textContent = data.details || '';
            
            // Check if complete
            if (data.status === 'completed') {
                clearInterval(progressInterval);
                this.updateInProgress = false;
                
                // Show success message
                document.querySelector('.modal-overlay').remove();
                AdminCore.showAlert('Update completed successfully! System will restart...', 'success');
                
                // Reload page after delay
                setTimeout(() => {
                    window.location.reload();
                }, 5000);
                
            } else if (data.status === 'failed') {
                clearInterval(progressInterval);
                this.updateInProgress = false;
                
                // Show error
                document.querySelector('.modal-overlay').remove();
                AdminCore.showAlert(`Update failed: ${data.error || 'Unknown error'}`, 'danger');
            }
            
        } catch (error) {
            console.error('Failed to get update status:', error);
            // Don't stop monitoring on temporary errors
        }
    }, 1000);
};

// Update version display
UpdateManager.updateVersionDisplay = function() {
    const versionElements = document.querySelectorAll('.version-display');
    versionElements.forEach(el => {
        if (this.currentVersion) {
            el.textContent = `v${this.currentVersion}`;
        }
    });
    
    // Show update badge if available
    if (this.latestVersion && this.currentVersion && this.latestVersion !== this.currentVersion) {
        const updateBadge = document.getElementById('update-badge');
        if (updateBadge) {
            updateBadge.style.display = 'inline-block';
        }
    }
};

// Bind event listeners
UpdateManager.bindEventListeners = function() {
    // Check updates button
    const checkButton = document.getElementById('check-updates');
    if (checkButton) {
        checkButton.addEventListener('click', () => this.checkForUpdates());
    }
};

// Initialize on page load
if (window.location.pathname.includes('/admin')) {
    document.addEventListener('DOMContentLoaded', () => {
        UpdateManager.init();
    });
}

// Export for global use
window.UpdateManager = UpdateManager;

// Add some CSS for update UI
const style = document.createElement('style');
style.textContent = `
.update-info .version-compare {
    display: flex;
    gap: 2rem;
    margin: 1rem 0;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
}

.update-info .version {
    font-size: 1.25rem;
    font-weight: bold;
}

.update-info .version.new {
    color: var(--success-color);
}

.update-info .changelog {
    margin: 1rem 0;
}

.update-info .changelog-content {
    max-height: 200px;
    overflow-y: auto;
    padding: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    font-size: 0.9rem;
}

.update-progress {
    text-align: center;
    padding: 2rem;
}

.update-warning {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(246, 173, 85, 0.1);
    border: 1px solid rgba(246, 173, 85, 0.3);
    border-radius: var(--radius-md);
    color: var(--warning-color);
}

#update-badge {
    display: none;
    background: var(--danger-color);
    color: white;
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    margin-left: 0.5rem;
}
`;
document.head.appendChild(style);
