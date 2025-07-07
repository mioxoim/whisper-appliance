/**
 * WhisperAppliance Admin Chat History
 * Handles transcription history display and export
 */

const ChatHistory = {
    currentPage: 1,
    itemsPerPage: 20,
    totalItems: 0,
    historyData: []
};

// Initialize chat history
ChatHistory.init = function() {
    console.log('Initializing Chat History Manager');
    this.loadHistory();
    this.bindEventListeners();
};

// Load chat history
ChatHistory.loadHistory = async function(page = 1) {
    try {
        const response = await fetch(`/api/v1/chat/history?page=${page}&limit=${this.itemsPerPage}`);
        const data = await response.json();
        
        this.historyData = data.items || [];
        this.totalItems = data.total || 0;
        this.currentPage = page;
        
        this.updateHistoryDisplay();
        this.updatePagination();
        
    } catch (error) {
        console.error('Failed to load chat history:', error);
        AdminCore.showAlert('Failed to load chat history', 'danger');
    }
};

// Update history display
ChatHistory.updateHistoryDisplay = function() {
    const container = document.getElementById('chat-history-container');
    if (!container) return;
    
    if (this.historyData.length === 0) {
        container.innerHTML = '<p class="text-muted">No transcription history available.</p>';
        return;
    }
    
    const html = `
        <div class="table-container">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Source</th>
                        <th>Language</th>
                        <th>Text Preview</th>
                        <th>Duration</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.historyData.map(entry => `
                        <tr>
                            <td>${this.formatTimestamp(entry.timestamp)}</td>
                            <td>
                                <span class="badge badge-${this.getSourceClass(entry.source)}">
                                    ${entry.source}
                                </span>
                            </td>
                            <td>${entry.language || 'auto'}</td>
                            <td class="text-preview">
                                ${this.truncateText(entry.text, 100)}
                            </td>
                            <td>${this.formatDuration(entry.duration)}</td>
                            <td>
                                <button class="btn btn-sm btn-secondary" 
                                        onclick="ChatHistory.viewDetails('${entry.id}')">
                                    View
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
};

// Update pagination
ChatHistory.updatePagination = function() {
    const container = document.getElementById('chat-history-pagination');
    if (!container) return;
    
    const totalPages = Math.ceil(this.totalItems / this.itemsPerPage);
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination">';
    
    // Previous button
    if (this.currentPage > 1) {
        html += `<button class="btn btn-sm" onclick="ChatHistory.loadHistory(${this.currentPage - 1})">Previous</button>`;
    }
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === this.currentPage) {
            html += `<span class="page-current">${i}</span>`;
        } else {
            html += `<button class="btn btn-sm" onclick="ChatHistory.loadHistory(${i})">${i}</button>`;
        }
    }
    
    // Next button
    if (this.currentPage < totalPages) {
        html += `<button class="btn btn-sm" onclick="ChatHistory.loadHistory(${this.currentPage + 1})">Next</button>`;
    }
    
    html += '</div>';
    container.innerHTML = html;
};

// View entry details
ChatHistory.viewDetails = function(entryId) {
    const entry = this.historyData.find(e => e.id === entryId);
    if (!entry) return;
    
    const content = `
        <div class="entry-details">
            <div class="detail-row">
                <strong>Timestamp:</strong> ${this.formatTimestamp(entry.timestamp)}
            </div>
            <div class="detail-row">
                <strong>Source:</strong> ${entry.source}
            </div>
            <div class="detail-row">
                <strong>Language:</strong> ${entry.language || 'auto-detected'}
            </div>
            <div class="detail-row">
                <strong>Duration:</strong> ${this.formatDuration(entry.duration)}
            </div>
            <div class="detail-row">
                <strong>Full Text:</strong>
                <div class="text-content">${entry.text}</div>
            </div>
        </div>
    `;
    
    AdminCore.showModal(
        'Transcription Details',
        content,
        [
            {
                text: 'Copy Text',
                type: 'secondary',
                onclick: `ChatHistory.copyText('${entry.id}')`
            },
            {
                text: 'Close',
                type: 'primary',
                onclick: 'document.querySelector(".modal-overlay").remove()'
            }
        ]
    );
};

// Copy text to clipboard
ChatHistory.copyText = function(entryId) {
    const entry = this.historyData.find(e => e.id === entryId);
    if (!entry) return;
    
    navigator.clipboard.writeText(entry.text).then(() => {
        AdminCore.showAlert('Text copied to clipboard', 'success');
    }).catch(err => {
        AdminCore.showAlert('Failed to copy text', 'danger');
    });
};

// Export history
ChatHistory.exportHistory = async function(format = 'json') {
    AdminCore.showAlert(`Exporting history as ${format.toUpperCase()}...`, 'info');
    
    try {
        const response = await fetch(`/api/v1/chat/export?format=${format}`);
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `whisper-history-${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        AdminCore.showAlert('Export completed successfully', 'success');
        
    } catch (error) {
        console.error('Failed to export history:', error);
        AdminCore.showAlert('Failed to export history', 'danger');
    }
};

// Search history
ChatHistory.searchHistory = async function(query) {
    if (!query) {
        this.loadHistory();
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/chat/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        this.historyData = data.items || [];
        this.totalItems = data.total || 0;
        this.currentPage = 1;
        
        this.updateHistoryDisplay();
        this.updatePagination();
        
    } catch (error) {
        console.error('Failed to search history:', error);
        AdminCore.showAlert('Failed to search history', 'danger');
    }
};

// Utility functions
ChatHistory.formatTimestamp = function(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
};

ChatHistory.formatDuration = function(seconds) {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

ChatHistory.truncateText = function(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
};

ChatHistory.getSourceClass = function(source) {
    const classes = {
        'live': 'primary',
        'upload': 'success',
        'api': 'secondary'
    };
    return classes[source] || 'secondary';
};

// Bind event listeners
ChatHistory.bindEventListeners = function() {
    // Search input
    const searchInput = document.getElementById('history-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchHistory(e.target.value);
            }, 500);
        });
    }
    
    // Export buttons
    const exportJsonBtn = document.getElementById('export-json');
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', () => this.exportHistory('json'));
    }
    
    const exportCsvBtn = document.getElementById('export-csv');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => this.exportHistory('csv'));
    }
};

// Initialize on page load
if (document.getElementById('chat-history-container')) {
    document.addEventListener('DOMContentLoaded', () => {
        ChatHistory.init();
    });
}

// Export for global use
window.ChatHistory = ChatHistory;

// Add CSS for chat history
const style = document.createElement('style');
style.textContent = `
.text-preview {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    font-weight: 500;
}

.badge-primary {
    background: var(--primary-color);
    color: white;
}

.badge-success {
    background: var(--success-color);
    color: white;
}

.badge-secondary {
    background: var(--bg-tertiary);
    color: var(--text-primary);
}

.pagination {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1rem;
}

.page-current {
    padding: 4px 12px;
    background: var(--primary-color);
    color: white;
    border-radius: var(--radius-sm);
}

.entry-details .detail-row {
    margin-bottom: 1rem;
}

.entry-details .text-content {
    margin-top: 0.5rem;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
}
`;
document.head.appendChild(style);
