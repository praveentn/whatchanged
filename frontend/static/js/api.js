// app/frontend/static/js/api.js

class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            showLoading();
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            showNotification('error', `API Error: ${error.message}`);
            throw error;
        } finally {
            hideLoading();
        }
    }

    // Document API methods
    async uploadDocument(formData) {
        return this.request('/documents/upload', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
    }

    async getDocuments(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/documents/?${queryString}`);
    }

    async getDocument(id, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/documents/${id}?${queryString}`);
    }

    async getDocumentVersions(slug) {
        return this.request(`/documents/slug/${slug}/versions`);
    }

    async analyzeDocument(id, force = false) {
        return this.request(`/documents/${id}/analyze`, {
            method: 'POST',
            body: JSON.stringify({ force_reanalysis: force })
        });
    }

    async getDocumentAnalysis(id) {
        return this.request(`/documents/${id}/analysis`);
    }

    async getDocumentStats(id) {
        return this.request(`/documents/${id}/stats`);
    }

    async deleteDocument(id, deleteAllVersions = false) {
        return this.request(`/documents/${id}?delete_all_versions=${deleteAllVersions}`, {
            method: 'DELETE'
        });
    }

    // Comparison API methods
    async compareDocuments(comparisonData) {
        return this.request('/comparison/compare', {
            method: 'POST',
            body: JSON.stringify(comparisonData)
        });
    }

    async compareBySlug(comparisonData) {
        return this.request('/comparison/compare-by-slug', {
            method: 'POST',
            body: JSON.stringify(comparisonData)
        });
    }

    async getComparisonAlgorithms() {
        return this.request('/comparison/algorithms');
    }

    async getComparisonHistory(slug, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/comparison/history/${slug}?${queryString}`);
    }

    async getDiffConfigurations() {
        return this.request('/comparison/configurations');
    }

    async createDiffConfiguration(config) {
        return this.request('/comparison/configurations', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    // Search API methods
    async semanticSearch(searchData) {
        return this.request('/search/semantic', {
            method: 'POST',
            body: JSON.stringify(searchData)
        });
    }

    async globalSearch(searchData) {
        return this.request('/search/global', {
            method: 'POST',
            body: JSON.stringify(searchData)
        });
    }

    async getSearchSuggestions(query, limit = 5) {
        return this.request(`/search/suggestions?query=${encodeURIComponent(query)}&limit=${limit}`);
    }

    async getSearchStats() {
        return this.request('/search/stats');
    }

    // Admin API methods
    async executeSQL(sqlData) {
        return this.request('/admin/sql/execute', {
            method: 'POST',
            body: JSON.stringify(sqlData)
        });
    }

    async getDatabaseSchema(tableName = null) {
        const endpoint = tableName ? `/admin/sql/schema?table_name=${tableName}` : '/admin/sql/schema';
        return this.request(endpoint);
    }

    async getSystemStats() {
        return this.request('/admin/stats/system');
    }

    async getAuditLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/admin/audit/logs?${queryString}`);
    }

    async performMaintenance(maintenanceData) {
        return this.request('/admin/maintenance', {
            method: 'POST',
            body: JSON.stringify(maintenanceData)
        });
    }

    async createBackup() {
        return this.request('/admin/backup/create');
    }

    async getHealthCheck() {
        return this.request('/health', { baseURL: '' });
    }
}

// Global API client instance
const api = new APIClient();

// Loading and notification utilities
function showLoading() {
    document.getElementById('loading-overlay').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('show');
}

function showNotification(type, message, duration = 5000) {
    const container = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <p>${message}</p>
        </div>
    `;

    container.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, duration);

    // Allow manual close
    notification.addEventListener('click', () => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    });
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for use in other modules
window.api = api;
window.showNotification = showNotification;
window.formatDate = formatDate;
window.formatFileSize = formatFileSize;
window.truncateText = truncateText;
window.escapeHtml = escapeHtml;
window.debounce = debounce;