// Model Manager for Admin Panel
const ModelManager = {
    availableModels: {},
    downloadedModels: [],
    currentModel: null,
    downloadProgress: {}, // Stores modelId: { progress, total_size, downloaded_size, status, error_message }

    // Initialize ModelManager
    init: async function() {
        console.log("ModelManager init");
        this.bindEventListeners();
        await this.loadModelStatus();
    },

    // Load model status from API
    loadModelStatus: async function() {
        try {
            const response = await fetch('/api/v1/models/status'); // Assuming this endpoint exists from admin_panel.py
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            this.availableModels = data.available || {};
            this.downloadedModels = data.downloaded || [];
            this.currentModel = data.current || null;

            // Also fetch detailed download status for progress of non-active downloads
            const detailedStatusResponse = await fetch('/api/models/download-status'); // main.py endpoint
            if (detailedStatusResponse.ok) {
                const detailedStatusData = await detailedStatusResponse.json();
                if (detailedStatusData.download_status) {
                    for (const modelId in detailedStatusData.download_status) {
                        const modelProg = detailedStatusData.download_status[modelId];
                        if (modelProg.downloaded && (!this.downloadProgress[modelId] || this.downloadProgress[modelId].status !== 'downloading')) {
                             // If model is downloaded and not actively downloading, ensure progress shows completed
                            this.downloadProgress[modelId] = {
                                status: 'completed',
                                progress: 100,
                                total_size: modelProg.info && modelProg.info.size_bytes ? modelProg.info.size_bytes : 0, // Placeholder for actual size
                                downloaded_size: modelProg.info && modelProg.info.size_bytes ? modelProg.info.size_bytes : 0,
                                error_message: ''
                            };
                        }
                    }
                }
            }

            this.updateModelTable();
        } catch (error) {
            console.error('Failed to load model status:', error);
            if (window.AdminCore && AdminCore.showAlert) {
                AdminCore.showAlert('Failed to load model information.', 'danger');
            }
        }
    },

    // Update model table in the DOM
    updateModelTable: function() {
        const tableBody = document.getElementById('model-table-body');
        if (!tableBody) return;
        tableBody.innerHTML = ''; // Clear existing rows

        for (const modelId in this.availableModels) {
            const modelInfo = this.availableModels[modelId];
            const isDownloaded = this.downloadedModels.includes(modelId);
            const isCurrent = this.currentModel === modelId;
            const progressData = this.downloadProgress[modelId]; // This will be an object or undefined

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <strong>${modelInfo.name}</strong>
                    ${isCurrent ? '<span class="status status-online">Current</span>' : ''}
                </td>
                <td>
                    ${progressData && (progressData.status === 'downloading' || progressData.status === 'pending' || progressData.status === 'failed' || progressData.status === 'cancelled' || progressData.status === 'not_downloaded')
                        ? this.getProgressHtml(progressData)
                        : isDownloaded
                            ? (this.downloadProgress[modelId] && this.downloadProgress[modelId].status === 'completed'
                                ? this.getProgressHtml(this.downloadProgress[modelId])
                                : '<span class="status status-online"><span class="status-dot"></span> Downloaded</span>')
                            : '<span class="status status-pending"><span class="status-dot"></span> Not Downloaded</span>'
                    }
                </td>
                <td>${modelInfo.size || 'N/A'}</td>
                <td>${modelInfo.parameters || 'N/A'}</td>
                <td>${modelInfo.speed || 'N/A'}</td>
                <td>${modelInfo.description || 'N/A'}</td>
                <td>
                    ${this.getActionButtons(modelId, isDownloaded, isCurrent, progressData)}
                </td>
            `;
            tableBody.appendChild(row);
        }
    },

    // Helper function to format bytes
    formatBytes: function(bytes, decimals = 2) {
        if (bytes === 0 || !bytes) return '0 Bytes'; // Added !bytes check
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        // Ensure bytes is a number for Math.log
        const numBytes = Number(bytes);
        if (isNaN(numBytes) || numBytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(numBytes) / Math.log(k));
        return parseFloat((numBytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },

    // Get progress HTML
    getProgressHtml: function(progressData) {
        if (!progressData || typeof progressData.progress === 'undefined') {
             // If status is completed but progress is undefined, make it 100
            if (progressData && progressData.status === 'completed') {
                progressData.progress = 100;
            } else {
                return '<small>Calculating...</small>';
            }
        }

        const percent = progressData.progress || 0;
        let progressText = `${percent}%`;

        if (progressData.status === 'downloading') {
            if (typeof progressData.downloaded_size !== 'undefined' && typeof progressData.total_size !== 'undefined' && progressData.total_size > 0) {
                const downloadedFormatted = this.formatBytes(progressData.downloaded_size);
                const totalFormatted = this.formatBytes(progressData.total_size);
                let remainingFormatted = '';
                if (typeof progressData.remaining_size !== 'undefined' && progressData.remaining_size >= 0) {
                    remainingFormatted = ` - ${this.formatBytes(progressData.remaining_size)} remaining`;
                }
                progressText = `${downloadedFormatted} / ${totalFormatted} (${percent}%)${remainingFormatted}`;
            } else {
                 progressText = `Downloading... ${percent}%`;
            }
        } else if (progressData.status === 'completed') {
            progressText = `Completed`;
            if (typeof progressData.total_size !== 'undefined' && progressData.total_size > 0) {
                progressText += ` (${this.formatBytes(progressData.total_size)})`;
            }
        } else if (progressData.status === 'pending') {
            progressText = `Pending...`;
        } else if (progressData.status === 'failed') {
            progressText = `Failed. ${progressData.error_message || ''}`;
        } else if (progressData.status === 'cancelled') {
            progressText = `Cancelled.`;
        } else if (progressData.status === 'not_downloaded') {
            // This status might come from the progress endpoint if no download has started
            // or if the model was deleted and progress reflects that state.
            return '<span class="status status-pending"><span class="status-dot"></span> Not Downloaded</span>';
        }
        
        const progressBarClass = (progressData.status === 'failed' || progressData.status === 'cancelled') ? 'progress-bar-danger' :
                                 (progressData.status === 'completed') ? 'progress-bar-success' : 'progress-bar';

        return `
            <div class="progress" style="width: 100%; margin-bottom: 0.25rem;">
                <div class="${progressBarClass}" style="width: ${percent}%"></div>
            </div>
            <small>${progressText}</small>
        `;
    },

    // Get action buttons for model
    getActionButtons: function(modelId, isDownloaded, isCurrent, progressData) {
        const buttons = [];
        const isActiveDownload = progressData && (progressData.status === 'downloading' || progressData.status === 'pending');

        if (isActiveDownload) {
            buttons.push(
                `<button class="btn btn-sm btn-danger" onclick="window.ModelManager.cancelDownload('${modelId}')">
                    Cancel
                </button>`
            );
        } else if (isDownloaded || (progressData && progressData.status === 'completed')) {
            if (!isCurrent) {
                buttons.push(
                    `<button class="btn btn-sm btn-primary" onclick="window.ModelManager.switchModel('${modelId}')">
                        Use Model
                    </button>`
                );
            }
            buttons.push(
                `<button class="btn btn-sm btn-danger" onclick="window.ModelManager.deleteModel('${modelId}')">
                    Delete
                </button>`
            );
        } else { // Not downloaded, and not actively downloading/pending (could be failed/cancelled)
            buttons.push(
                `<button class="btn btn-sm btn-success" onclick="window.ModelManager.downloadModel('${modelId}')">
                    Download
                </button>`
            );
        }
        
        return buttons.join(' ');
    },

    // Download model
    downloadModel: async function(modelId) {
        try {
            // Check if availableModels is populated
            if (!this.availableModels || !this.availableModels[modelId]) {
                AdminCore.showAlert('Model information not loaded yet. Please wait.', 'warning');
                await this.loadModelStatus(); // Try to load it
                if (!this.availableModels[modelId]) {
                     AdminCore.showAlert(`Cannot start download: Model ${modelId} info is missing.`, 'danger');
                     return;
                }
            }
            AdminCore.showAlert(`Starting download of ${this.availableModels[modelId].name}`, 'info');

            const response = await fetch(`/api/v1/models/download/${modelId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (!response.ok || result.status === 'error') {
                throw new Error(result.message || 'Download failed to start');
            }

            AdminCore.showAlert(result.message || `Download started for ${this.availableModels[modelId].name}`, 'info');

            if (result.message && !result.message.includes("already downloaded") && !result.message.includes("already in progress")) {
                this.monitorDownloadProgress(modelId);
            } else {
                this.loadModelStatus();
            }

        } catch (error) {
            console.error('Failed to start download:', error.message);
            AdminCore.showAlert(`Failed to start model download: ${error.message}`, 'danger');
        }
    },

    // Monitor download progress
    monitorDownloadProgress: function(modelId) {
        // Clear existing interval for this modelId if any
        if (this.downloadProgress[modelId] && this.downloadProgress[modelId].intervalId) {
            clearInterval(this.downloadProgress[modelId].intervalId);
        }

        const intervalId = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/models/download/${modelId}/progress`);
                const result = await response.json();

                if (!response.ok || result.status === 'error') {
                    console.error('Error fetching progress:', result.message);
                    // Do not clear interval here, let backend handle state
                    this.updateModelTable(); // Refresh to show potential error state from backend
                    return;
                }

                const progressData = result.data;

                if (!progressData) {
                    console.warn(`No progress data received for model ${modelId} in API response.`);
                    this.updateModelTable();
                    return;
                }

                progressData.intervalId = intervalId; // Store interval ID with progress
                this.downloadProgress[modelId] = progressData;

                if (progressData.status === 'completed' || progressData.status === 'failed' || progressData.status === 'cancelled') {
                    clearInterval(intervalId);
                    if (progressData.status === 'completed' && !this.downloadedModels.includes(modelId)) {
                        this.downloadedModels.push(modelId);
                    }
                    const alertType = progressData.status === 'completed' ? 'success' : (progressData.status === 'failed' ? 'danger' : 'info');
                    const message = progressData.status === 'completed' ? `${this.availableModels[modelId].name} downloaded successfully` :
                                    progressData.status === 'failed' ? `Failed to download ${this.availableModels[modelId].name}: ${progressData.error_message || 'Unknown error'}` :
                                    `Download of ${this.availableModels[modelId].name} cancelled.`;
                    AdminCore.showAlert(message, alertType);
                }
                this.updateModelTable();

            } catch (error) {
                console.error('Failed to get download progress:', error);
                // Potentially clear interval on persistent client-side error, though server should ideally manage state
                // clearInterval(intervalId);
                // AdminCore.showAlert('Network error while fetching download progress.', 'warning');
            }
        }, 2000);
         // Store the interval ID immediately so it can be cleared if another download starts for the same model
        if (this.downloadProgress[modelId]) {
            this.downloadProgress[modelId].intervalId = intervalId;
        } else { // Should not happen if downloadModel initializes it
            this.downloadProgress[modelId] = { intervalId: intervalId, status: 'pending' };
        }
    },

    // Switch model
    switchModel: async function(modelId) {
        try {
            const response = await fetch('/api/v1/models/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelId })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({message: 'Failed to switch model'}));
                throw new Error(errorData.message || 'Failed to switch model');
            }

            this.currentModel = modelId;
            this.updateModelTable(); // Refresh table to show new current model
            AdminCore.showAlert(`Switched to ${this.availableModels[modelId].name}`, 'success');

        } catch (error) {
            console.error('Failed to switch model:', error.message);
            AdminCore.showAlert(`Failed to switch model: ${error.message}`, 'danger');
        }
    },

    // Delete model
    deleteModel: async function(modelId) {
        const modelName = this.availableModels[modelId] ? this.availableModels[modelId].name : modelId;
        
        AdminCore.showModal(
            'Confirm Delete',
            `<p>Are you sure you want to delete the model "${modelName}"?</p>
             <p>This action cannot be undone.</p>`,
            [
                { text: 'Cancel', type: 'secondary', onclick: 'AdminCore.closeModal()' },
                { text: 'Delete', type: 'danger', onclick: `window.ModelManager.confirmDelete('${modelId}')` }
            ]
        );
    },

    // Confirm delete
    confirmDelete: async function(modelId) {
        AdminCore.closeModal();
        try {
            const response = await fetch(`/api/v1/models/${modelId}`, { // Assuming this is the correct API endpoint for delete
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({message: 'Failed to delete model'}));
                throw new Error(errorData.message || 'Failed to delete model');
            }

            this.downloadedModels = this.downloadedModels.filter(id => id !== modelId);
            if (this.currentModel === modelId) {
                this.currentModel = null;
            }
            delete this.downloadProgress[modelId]; // Remove any progress state for the deleted model
            this.updateModelTable();
            AdminCore.showAlert(`Model ${this.availableModels[modelId] ? this.availableModels[modelId].name : modelId} deleted successfully`, 'success');

        } catch (error) {
            console.error('Failed to delete model:', error.message);
            AdminCore.showAlert(`Failed to delete model: ${error.message}`, 'danger');
        }
    },

    // Cancel download
    cancelDownload: async function(modelId) {
        try {
            const response = await fetch(`/api/v1/models/download/${modelId}/cancel`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({message: 'Failed to cancel download'}));
                throw new Error(errorData.message || 'Failed to cancel download');
            }

            // The backend will set status to 'cancelled'. Frontend will pick this up via monitorDownloadProgress.
            // We can optimistically update UI here too.
            if (this.downloadProgress[modelId]) {
                 if(this.downloadProgress[modelId].intervalId) {
                    clearInterval(this.downloadProgress[modelId].intervalId);
                 }
                this.downloadProgress[modelId].status = 'cancelled';
            }
            this.updateModelTable(); // Refresh table immediately
            AdminCore.showAlert('Download cancellation requested.', 'info');

        } catch (error) {
            console.error('Failed to cancel download:', error.message);
            AdminCore.showAlert(`Failed to cancel download: ${error.message}`, 'danger');
        }
    },

    // Bind event listeners
    bindEventListeners: function() {
        const refreshBtn = document.getElementById('refresh-models');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadModelStatus());
        }
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
