// app/frontend/static/js/components.js

// Enhanced document components and utilities

class DocumentComponents {
    static createStatusBadge(status) {
        const statusMap = {
            'uploaded': { class: 'status-uploaded', icon: 'fas fa-upload', text: 'Uploaded' },
            'analyzing': { class: 'status-analyzing', icon: 'fas fa-brain', text: 'Analyzing' },
            'indexed': { class: 'status-indexed', icon: 'fas fa-check', text: 'Indexed' },
            'error': { class: 'status-error', icon: 'fas fa-exclamation', text: 'Error' }
        };

        const config = statusMap[status] || statusMap['uploaded'];
        return `
            <span class="status-badge ${config.class}">
                <i class="${config.icon}"></i>
                ${config.text}
            </span>
        `;
    }

    static createProgressBar(percentage, label = '') {
        return `
            <div class="progress-container">
                ${label ? `<label class="progress-label">${label}</label>` : ''}
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(100, Math.max(0, percentage))}%"></div>
                </div>
                <span class="progress-text">${percentage.toFixed(1)}%</span>
            </div>
        `;
    }

    static createMetricCard(title, value, icon, trend = null) {
        return `
            <div class="metric-card fade-in">
                <div class="metric-icon">
                    <i class="${icon}"></i>
                </div>
                <div class="metric-content">
                    <h3>${value}</h3>
                    <p>${title}</p>
                    ${trend ? `<span class="metric-trend ${trend.direction}">${trend.text}</span>` : ''}
                </div>
            </div>
        `;
    }

    static createIntentChip(intent, count = null) {
        const intentColors = {
            'overview': '#3b82f6',
            'requirements': '#10b981',
            'design': '#8b5cf6',
            'risks': '#ef4444',
            'procedure': '#f59e0b',
            'example': '#06b6d4',
            'conclusion': '#6b7280',
            'other': '#9ca3af'
        };

        const color = intentColors[intent] || intentColors['other'];
        const text = count ? `${intent} (${count})` : intent;

        return `
            <span class="intent-chip" style="background-color: ${color}20; color: ${color}; border: 1px solid ${color}40;">
                ${text}
            </span>
        `;
    }

    static createLoadingSpinner(size = 'medium') {
        const sizeClass = `spinner-${size}`;
        return `
            <div class="loading-container">
                <div class="spinner ${sizeClass}"></div>
                <p>Loading...</p>
            </div>
        `;
    }

    static createEmptyState(icon, title, description, actionButton = null) {
        return `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="${icon}"></i>
                </div>
                <h3>${title}</h3>
                <p>${description}</p>
                ${actionButton ? actionButton : ''}
            </div>
        `;
    }

    static createTooltip(content, text) {
        return `
            <span class="tooltip-container">
                ${text}
                <div class="tooltip">${content}</div>
            </span>
        `;
    }
}

// Search result highlighting
class SearchHighlighter {
    static highlight(text, query, maxLength = 200) {
        if (!query || !text) return truncateText(text, maxLength);

        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        let highlighted = text.replace(regex, '<mark>$1</mark>');
        
        // Find the best excerpt around the highlighted term
        const markIndex = highlighted.toLowerCase().indexOf('<mark>');
        if (markIndex !== -1) {
            const start = Math.max(0, markIndex - maxLength / 2);
            const end = Math.min(highlighted.length, start + maxLength);
            highlighted = highlighted.substring(start, end);
            
            if (start > 0) highlighted = '...' + highlighted;
            if (end < text.length) highlighted = highlighted + '...';
        } else {
            highlighted = truncateText(highlighted, maxLength);
        }

        return highlighted;
    }

    static escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Form validation utilities
class FormValidator {
    static validateRequired(value, fieldName) {
        if (!value || value.trim() === '') {
            return `${fieldName} is required`;
        }
        return null;
    }

    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return 'Please enter a valid email address';
        }
        return null;
    }

    static validateFileSize(file, maxSizeMB) {
        if (file.size > maxSizeMB * 1024 * 1024) {
            return `File size must be less than ${maxSizeMB}MB`;
        }
        return null;
    }

    static validateFileType(file, allowedTypes) {
        const fileType = file.type || '';
        const fileName = file.name || '';
        const extension = fileName.split('.').pop()?.toLowerCase();

        const isValidType = allowedTypes.some(type => {
            if (type.startsWith('.')) {
                return extension === type.substring(1);
            }
            return fileType.startsWith(type);
        });

        if (!isValidType) {
            return `File type not supported. Allowed types: ${allowedTypes.join(', ')}`;
        }
        return null;
    }

    static validateForm(formData, rules) {
        const errors = {};
        
        for (const [field, rule] of Object.entries(rules)) {
            const value = formData[field];
            let error = null;

            if (rule.required) {
                error = this.validateRequired(value, rule.label || field);
                if (error) {
                    errors[field] = error;
                    continue;
                }
            }

            if (rule.type === 'email' && value) {
                error = this.validateEmail(value);
            }

            if (rule.minLength && value && value.length < rule.minLength) {
                error = `${rule.label || field} must be at least ${rule.minLength} characters`;
            }

            if (rule.maxLength && value && value.length > rule.maxLength) {
                error = `${rule.label || field} must be no more than ${rule.maxLength} characters`;
            }

            if (error) {
                errors[field] = error;
            }
        }

        return Object.keys(errors).length === 0 ? null : errors;
    }
}

// Data table utilities
class DataTable {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            sortable: true,
            filterable: false,
            pageable: true,
            pageSize: 20,
            ...options
        };
        this.data = [];
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.currentPage = 1;
    }

    setData(data) {
        this.data = data;
        this.render();
    }

    render() {
        const { columns } = this.options;
        if (!columns || !this.data) return;

        let html = '<div class="data-table">';
        
        // Header
        html += '<table><thead><tr>';
        columns.forEach(col => {
            const sortable = this.options.sortable && col.sortable !== false;
            const sortClass = this.sortColumn === col.key ? `sort-${this.sortDirection}` : '';
            
            html += `
                <th class="${sortable ? 'sortable' : ''} ${sortClass}" 
                    ${sortable ? `onclick="dataTable.sort('${col.key}')"` : ''}>
                    ${col.title}
                    ${sortable ? '<i class="fas fa-sort"></i>' : ''}
                </th>
            `;
        });
        html += '</tr></thead>';

        // Body
        html += '<tbody>';
        const startIndex = (this.currentPage - 1) * this.options.pageSize;
        const endIndex = startIndex + this.options.pageSize;
        const pageData = this.data.slice(startIndex, endIndex);

        pageData.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                let value = row[col.key];
                if (col.render) {
                    value = col.render(value, row);
                } else if (value === null || value === undefined) {
                    value = '';
                } else {
                    value = escapeHtml(String(value));
                }
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';

        // Pagination
        if (this.options.pageable && this.data.length > this.options.pageSize) {
            html += this.renderPagination();
        }

        html += '</div>';
        this.container.innerHTML = html;
    }

    sort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        this.data.sort((a, b) => {
            const aVal = a[column];
            const bVal = b[column];
            const factor = this.sortDirection === 'asc' ? 1 : -1;

            if (aVal === bVal) return 0;
            if (aVal === null || aVal === undefined) return factor;
            if (bVal === null || bVal === undefined) return -factor;

            return (aVal < bVal ? -1 : 1) * factor;
        });

        this.render();
    }

    renderPagination() {
        const totalPages = Math.ceil(this.data.length / this.options.pageSize);
        if (totalPages <= 1) return '';

        let html = '<div class="table-pagination">';
        
        // Previous button
        html += `
            <button ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="dataTable.goToPage(${this.currentPage - 1})">
                Previous
            </button>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                html += `
                    <button class="${i === this.currentPage ? 'active' : ''}" 
                            onclick="dataTable.goToPage(${i})">
                        ${i}
                    </button>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                html += '<span>...</span>';
            }
        }

        // Next button
        html += `
            <button ${this.currentPage === totalPages ? 'disabled' : ''} 
                    onclick="dataTable.goToPage(${this.currentPage + 1})">
                Next
            </button>
        `;

        html += '</div>';
        return html;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.data.length / this.options.pageSize);
        this.currentPage = Math.max(1, Math.min(page, totalPages));
        this.render();
    }
}

// Export utilities
window.DocumentComponents = DocumentComponents;
window.SearchHighlighter = SearchHighlighter;
window.FormValidator = FormValidator;
window.DataTable = DataTable;