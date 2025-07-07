/**
 * WhisperAppliance Admin Core JavaScript
 * Core functionality for admin interface
 */

// Global state management
const AdminCore = {
    config: {
        apiBase: '/api/v1',
        refreshInterval: 30000, // 30 seconds
        wsEndpoint: null
    },
    state: {
        isConnected: false,
        currentModel: null,
        systemStats: {}
    },
    timers: {}
};

// Initialize admin interface
document.addEventListener('DOMContentLoaded', () => {
    AdminCore.init();
});

AdminCore.init = function() {
    console.log('Initializing WhisperAppliance Admin Interface');
    
    // Set active navigation
    this.setActiveNavigation();
    
    // Initialize auto-refresh
    this.initAutoRefresh();
    
    // Initialize tooltips
    this.initTooltips();
    
    // Load initial data
    this.loadSystemStatus();
};

// Navigation handling
AdminCore.setActiveNavigation = function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
};

// Auto-refresh functionality
AdminCore.initAutoRefresh = function() {
    const refreshableElements = document.querySelectorAll('[data-refresh]');
    
    refreshableElements.forEach(element => {
        const refreshInterval = parseInt(element.dataset.refresh) || this.config.refreshInterval;
        const refreshFunction = element.dataset.refreshFunction;
        
        if (refreshFunction && this[refreshFunction]) {
            // Initial load
            this[refreshFunction]();
            
            // Set interval
            const timerId = setInterval(() => {
                this[refreshFunction]();
            }, refreshInterval);
            
            this.timers[refreshFunction] = timerId;
        }
    });
};

// System status loading
AdminCore.loadSystemStatus = async function() {
    try {
        const response = await fetch(`${this.config.apiBase}/system/status`);
        const data = await response.json();
        
        this.state.systemStats = data;
        this.updateSystemStatusUI(data);
    } catch (error) {
        console.error('Failed to load system status:', error);
        this.showAlert('Failed to load system status', 'danger');
    }
};

// Update system status UI
AdminCore.updateSystemStatusUI = function(data) {
    // Update uptime
    const uptimeElement = document.getElementById('system-uptime');
    if (uptimeElement) {
        uptimeElement.textContent = this.formatUptime(data.uptime);
    }
    
    // Update model status
    const modelElement = document.getElementById('current-model');
    if (modelElement) {
        modelElement.textContent = data.currentModel || 'None';
    }
    
    // Update connection status
    const connectionElement = document.getElementById('connection-status');
    if (connectionElement) {
        connectionElement.innerHTML = data.isConnected 
            ? '<span class="status status-online"><span class="status-dot"></span> Online</span>'
            : '<span class="status status-offline"><span class="status-dot"></span> Offline</span>';
    }
};

// Utility functions
AdminCore.formatUptime = function(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    parts.push(`${secs}s`);
    
    return parts.join(' ');
};

AdminCore.formatBytes = function(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

// Alert system
AdminCore.showAlert = function(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || this.createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button class="btn btn-sm" onclick="this.parentElement.remove()">×</button>
    `;
    
    alertContainer.appendChild(alert);
    
    if (duration > 0) {
        setTimeout(() => {
            alert.remove();
        }, duration);
    }
};

AdminCore.createAlertContainer = function() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1000; max-width: 400px;';
    document.body.appendChild(container);
    return container;
};

// Modal system
AdminCore.showModal = function(title, content, buttons = []) {
    const modalHtml = `
        <div class="modal-overlay" onclick="AdminCore.closeModal(event)">
            <div class="modal" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>${title}</h3>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${buttons.map(btn => `
                        <button class="btn btn-${btn.type || 'secondary'}" onclick="${btn.onclick}">
                            ${btn.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
};

AdminCore.closeModal = function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        event.target.remove();
    }
};

// Tooltip system
AdminCore.initTooltips = function() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', this.showTooltip);
        element.addEventListener('mouseleave', this.hideTooltip);
    });
};

AdminCore.showTooltip = function(event) {
    const text = event.target.dataset.tooltip;
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 14px;
        z-index: 1000;
        pointer-events: none;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    
    event.target._tooltip = tooltip;
};

AdminCore.hideTooltip = function(event) {
    if (event.target._tooltip) {
        event.target._tooltip.remove();
        delete event.target._tooltip;
    }
};

// Export for use in other modules
window.AdminCore = AdminCore;
