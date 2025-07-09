(progress)
                        : '<span class="status status-pending"><span class="status-dot"></span> Not Downloaded</span>'
                }
            </td>
            <td>${modelInfo.size}</td>
            <td>${modelInfo.description}</td>
            <td>
                ${this.getActionButtons(modelId, isDownloaded, isCurrent, progress)}
            </td>
        `;
        
        tableBody.appendChild(row);
    });
};

// Helper function to format bytes
ModelManager.formatBytes = function(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

// Get progress HTML
ModelManager.getProgressHtml = function(progressData) {
    if (!progressData || typeof progressData.progress === 'undefined') {
        return '<small>Checking status...</small>';
    }

    const percent = progressData.progress || 0;
    let progressText = `${percent}% downloaded`;

    if (typeof progressData.downloaded_size !== 'undefined' && typeof progressData.total_size !== 'undefined' && progressData.total_size > 0) {
        const downloadedFormatted = this.formatBytes(progressData.downloaded_size);
        const totalFormatted = this.formatBytes(progressData.total_size);
        let remainingFormatted = '';
        if (typeof progressData.remaining_size !== 'undefined' && progressData.remaining_size >= 0) {
            remainingFormatted = ` - ${this.formatBytes(progressData.remaining_size)} remaining`;
        }
        progressText = `${downloadedFormatted} / ${totalFormatted} (${percent}%)${remainingFormatted}`;
    } else if (percent === 100 && progressData.status === 'completed') {
        progressText = `Completed`;
         if (typeof progressData.total_size !== 'undefined' && progressData.total_size > 0) {
            progressText += ` (${this.formatBytes(progressData.total_size)})`;
        }
    } else if (progressData.status === 'downloading') {
         progressText = `Downloading... ${percent}%`;
    } else if (progressData.status === 'pending') {
        progressText = `Pending...`;
    } else if (progressData.status === 'failed') {
        progressText = `Failed. ${progressData.error_message || ''}`;
    } else if (progressData.status === 'cancelled') {
        progressText = `Cancelled.`;
    }


    return `
        <div class="progress" style="width: 100%; margin-bottom: 0.25rem;">
            <div class="progress-bar" style="width: ${percent}%"></div>
        </div>
        <small>${progressText}</small>
    `;
};

// Get action buttons for model
ModelManager.getActionButtons = function(modelId, isDownloaded, isCurrent, progressData) {
    const buttons = [];
    // Check if progressData exists and indicates an active download state
    const isActiveDownload = progressData && (progressData.status === 'downloading' || progressData.status === 'pending');

    if (isActiveDownload) {
        buttons.push(`
            <button class="btn btn-sm btn-danger" onclick="ModelManager.cancelDownload('${modelId}')">
                Cancel
            </button>
        `);
    } else if (isDownloaded) {
        if (!isCurrent) {
            buttons.push(`
                <button class="btn btn-sm btn-primary" onclick="ModelManager.switchModel('${modelId}')">
                    Use Model
                </button>
            `);
        }
        buttons.push(`
            <button class="btn btn-sm btn-danger" onclick="ModelManager.deleteModel('${modelId}')">
                Delete
            </button>
        `);
    } else {
        buttons.push(`
            <button class="btn btn-sm btn-success" onclick="ModelManager.downloadModel('${modelId}')">
                Download
            </button>
        `);
    }
    
    return buttons.join(' ');
};

// Download model
ModelManager.downloadModel = async function(modelId) {
    try {
        AdminCore.showAlert(`Starting download of ${this.availableModels[modelId].name}`, 'info');
        
        const response = await fetch(`/api/v1/models/download/${modelId}`, {
            method: 'POST'
        });
        
        const result = await response.json();

        if (!response.ok || result.status === 'error') {
            throw new Error(result.message || 'Download failed to start');
        }
        
        AdminCore.showAlert(result.message || `Download started for ${this.availableModels[modelId].name}`, 'info');
        // Start progress monitoring only if not already completed or in progress from the initial response
        if (result.message && !result.message.includes("already downloaded") && !result.message.includes("already in progress")) {
            this.monitorDownloadProgress(modelId);
        } else {
            // If already downloaded or in progress, refresh table to show current state
            this.loadModelStatus();
        }
        
    } catch (error) {
        console.error('Failed to start download:', error.message);
        AdminCore.showAlert('Failed to start model download', 'danger');
    }
};

// Monitor download progress
ModelManager.monitorDownloadProgress = function(modelId) {
    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/models/download/${modelId}/progress`);
            const result = await response.json();

            if (!response.ok || result.status === 'error') {
                console.error('Error fetching progress:', result.message);
                // Potentially stop monitoring if server indicates an issue with progress endpoint itself
                // For now, we'll let it continue trying or rely on timeout/manual cancellation
                // clearInterval(progressInterval);
                // AdminCore.showAlert(`Error fetching progress for ${modelId}: ${result.message}`, 'warning');
                // this.updateModelTable(); // Refresh to show potential error state if any
                return; // Skip this update if fetching progress fails
            }
            
            const progressData = result.data; // The actual progress data is nested

            if (!progressData) {
                console.warn(`No progress data received for model ${modelId} in API response.`);
                // this.updateModelTable(); // Update table to reflect current state (might remove progress bar)
                return;
            }

            this.downloadProgress[modelId] = progressData; // Store the whole progress object

            if (progressData.status === 'completed') {
                clearInterval(progressInterval);
                // Remove from active progress tracking, but keep the final 'completed' state
                // delete this.downloadProgress[modelId]; // Let's keep it for the table to show 'Completed'
                if (!this.downloadedModels.includes(modelId)) {
                    this.downloadedModels.push(modelId);
                }
                 AdminCore.showAlert(`${this.availableModels[modelId].name} downloaded successfully`, 'success');
            } else if (progressData.status === 'failed') {
                clearInterval(progressInterval);
                // Keep the 'failed' state in downloadProgress for display
                AdminCore.showAlert(`Failed to download ${this.availableModels[modelId].name}: ${progressData.error_message || 'Unknown error'}`, 'danger');
            } else if (progressData.status === 'cancelled') {
                clearInterval(progressInterval);
                 AdminCore.showAlert(`Download of ${this.availableModels[modelId].name} cancelled.`, 'info');
            }
            // For 'downloading' or 'pending', just update the table
            this.updateModelTable();

        } catch (error) {
            console.error('Failed to get download progress:', error);
            // clearInterval(progressInterval); // Decide if we should stop on any client-side error
            // AdminCore.showAlert('Network error while fetching download progress.', 'warning');
        }
    }, 2000); // Check every 2 seconds
};

// Switch model
ModelManager.switchModel = async function(modelId) {
    try {
        const response = await fetch('/api/v1/models/switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: modelId })
        });
        
        if (!response.ok) {
            throw new Error('Failed to switch model');
        }
        
        this.currentModel = modelId;
        this.updateModelTable();
        AdminCore.showAlert(`Switched to ${this.availableModels[modelId].name}`, 'success');
        
    } catch (error) {
        console.error('Failed to switch model:', error);
        AdminCore.showAlert('Failed to switch model', 'danger');
    }
};

// Delete model
ModelManager.deleteModel = async function(modelId) {
    const modelName = this.availableModels[modelId].name;
    
    AdminCore.showModal(
        'Confirm Delete',
        `<p>Are you sure you want to delete the model "${modelName}"?</p>
         <p>This action cannot be undone.</p>`,
        [
            {
                text: 'Cancel',
                type: 'secondary',
                onclick: 'document.querySelector(".modal-overlay").remove()'
            },
            {
                text: 'Delete',
                type: 'danger',
                onclick: `ModelManager.confirmDelete('${modelId}')`
            }
        ]
    );
};

// Confirm delete
ModelManager.confirmDelete = async function(modelId) {
    document.querySelector('.modal-overlay').remove();
    
    try {
        const response = await fetch(`/api/v1/models/${modelId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete model');
        }
        
        this.downloadedModels = this.downloadedModels.filter(id => id !== modelId);
        if (this.currentModel === modelId) {
            this.currentModel = null;
        }
        this.updateModelTable();
        AdminCore.showAlert(`Model deleted successfully`, 'success');
        
    } catch (error) {
        console.error('Failed to delete model:', error);
        AdminCore.showAlert('Failed to delete model', 'danger');
    }
};

// Cancel download
ModelManager.cancelDownload = async function(modelId) {
    try {
        const response = await fetch(`/api/v1/models/download/${modelId}/cancel`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to cancel download');
        }
        
        delete this.downloadProgress[modelId];
        this.updateModelTable();
        AdminCore.showAlert('Download cancelled', 'info');
        
    } catch (error) {
        console.error('Failed to cancel download:', error);
        AdminCore.showAlert('Failed to cancel download', 'danger');
    }
};

// Bind event listeners
ModelManager.bindEventListeners = function() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-models');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => this.loadModelStatus());
    }
};

// Initialize on page load
if (document.getElementById('model-table-body')) {
    document.addEventListener('DOMContentLoaded', () => {
        ModelManager.init();
    });
}

// Export for global use
window.ModelManager = ModelManager;
