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

// Get progress HTML
ModelManager.getProgressHtml = function(progress) {
    return `
        <div class="progress" style="width: 150px;">
            <div class="progress-bar" style="width: ${progress}%"></div>
        </div>
        <small>${progress}% downloaded</small>
    `;
};

// Get action buttons for model
ModelManager.getActionButtons = function(modelId, isDownloaded, isCurrent, progress) {
    const buttons = [];
    
    if (progress) {
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
        
        if (!response.ok) {
            throw new Error('Download failed');
        }
        
        // Start progress monitoring
        this.monitorDownloadProgress(modelId);
        
    } catch (error) {
        console.error('Failed to start download:', error);
        AdminCore.showAlert('Failed to start model download', 'danger');
    }
};

// Monitor download progress
ModelManager.monitorDownloadProgress = function(modelId) {
    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/models/download/${modelId}/progress`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(progressInterval);
                delete this.downloadProgress[modelId];
                this.downloadedModels.push(modelId);
                this.updateModelTable();
                AdminCore.showAlert(`${this.availableModels[modelId].name} downloaded successfully`, 'success');
            } else if (data.status === 'failed') {
                clearInterval(progressInterval);
                delete this.downloadProgress[modelId];
                this.updateModelTable();
                AdminCore.showAlert(`Failed to download ${this.availableModels[modelId].name}`, 'danger');
            } else {
                this.downloadProgress[modelId] = data.progress || 0;
                this.updateModelTable();
            }
        } catch (error) {
            console.error('Failed to get download progress:', error);
            clearInterval(progressInterval);
        }
    }, 1000);
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
