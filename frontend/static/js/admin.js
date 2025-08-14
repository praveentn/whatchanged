// app/frontend/static/js/admin.js

class AdminPanel {
    constructor() {
        this.queryHistory = [];
        this.currentResults = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                app.loadAdminTab(btn.dataset.tab);
            });
        });

        // SQL Executor
        document.getElementById('execute-sql')?.addEventListener('click', () => {
            this.executeSQL();
        });

        document.getElementById('clear-sql')?.addEventListener('click', () => {
            document.getElementById('sql-query').value = '';
        });

        document.getElementById('export-results')?.addEventListener('click', () => {
            this.exportResults();
        });

        // SQL query textarea - handle Ctrl+Enter
        document.getElementById('sql-query')?.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.executeSQL();
            }
        });

        // Audit log filters
        document.getElementById('filter-logs')?.addEventListener('click', () => {
            this.filterAuditLogs();
        });
    }

    async executeSQL() {
        const query = document.getElementById('sql-query').value.trim();
        
        if (!query) {
            showNotification('error', 'Please enter a SQL query');
            return;
        }

        const sqlData = {
            query: query,
            limit_results: true
        };

        try {
            const result = await api.executeSQL(sqlData);
            this.displaySQLResults(result);
            this.addToQueryHistory(query, result);
        } catch (error) {
            showNotification('error', `SQL execution failed: ${error.message}`);
        }
    }

    displaySQLResults(result) {
        const resultsContainer = document.getElementById('sql-results');
        const executionTimeEl = document.getElementById('execution-time');
        const rowCountEl = document.getElementById('row-count');
        const resultsTableEl = document.getElementById('results-table');

        if (!result.success) {
            resultsTableEl.innerHTML = `
                <div class="error-message">
                    <h4>Query Error</h4>
                    <p>${escapeHtml(result.error || 'Unknown error occurred')}</p>
                </div>
            `;
            return;
        }

        // Update execution info
        executionTimeEl.textContent = `${result.execution_time_ms}ms`;
        
        if (result.query_type === 'SELECT') {
            rowCountEl.textContent = `${result.row_count || 0} rows`;
            this.renderQueryResults(result.data || [], result.columns || []);
        } else {
            rowCountEl.textContent = `${result.rows_affected || 0} rows affected`;
            resultsTableEl.innerHTML = `
                <div class="success-message">
                    <h4>Query Executed Successfully</h4>
                    <p>Operation: ${result.query_type}</p>
                    <p>Rows affected: ${result.rows_affected || 0}</p>
                </div>
            `;
        }

        this.currentResults = result;
    }

    renderQueryResults(data, columns) {
        const resultsTableEl = document.getElementById('results-table');
        
        if (!data || data.length === 0) {
            resultsTableEl.innerHTML = '<p class="no-results">No data returned</p>';
            return;
        }

        let tableHtml = '<table><thead><tr>';
        columns.forEach(col => {
            tableHtml += `<th>${escapeHtml(col)}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';

        data.forEach(row => {
            tableHtml += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                let displayValue = '';
                
                if (value === null || value === undefined) {
                    displayValue = '<em>NULL</em>';
                } else if (typeof value === 'string' && value.length > 100) {
                    displayValue = escapeHtml(value.substring(0, 100)) + '...';
                } else {
                    displayValue = escapeHtml(String(value));
                }
                
                tableHtml += `<td>${displayValue}</td>`;
            });
            tableHtml += '</tr>';
        });

        tableHtml += '</tbody></table>';
        resultsTableEl.innerHTML = tableHtml;
    }

    addToQueryHistory(query, result) {
        this.queryHistory.unshift({
            query: query,
            timestamp: new Date(),
            success: result.success,
            executionTime: result.execution_time_ms,
            rowCount: result.row_count || result.rows_affected || 0
        });

        // Keep only last 50 queries
        if (this.queryHistory.length > 50) {
            this.queryHistory = this.queryHistory.slice(0, 50);
        }
    }

    exportResults() {
        if (!this.currentResults || !this.currentResults.data) {
            showNotification('error', 'No results to export');
            return;
        }

        try {
            const data = this.currentResults.data;
            const columns = this.currentResults.columns;
            
            // Convert to CSV
            let csv = columns.join(',') + '\n';
            data.forEach(row => {
                const values = columns.map(col => {
                    const value = row[col];
                    if (value === null || value === undefined) {
                        return '';
                    }
                    // Escape CSV values
                    const stringValue = String(value);
                    if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                        return '"' + stringValue.replace(/"/g, '""') + '"';
                    }
                    return stringValue;
                });
                csv += values.join(',') + '\n';
            });

            // Download file
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `query_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showNotification('success', 'Results exported successfully');
        } catch (error) {
            showNotification('error', `Export failed: ${error.message}`);
        }
    }

    async filterAuditLogs() {
        const operation = document.getElementById('operation-filter').value;
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;

        const params = {
            limit: 50,
            offset: 0
        };

        if (operation) params.operation = operation;
        if (startDate) params.start_date = startDate + 'T00:00:00Z';
        if (endDate) params.end_date = endDate + 'T23:59:59Z';

        try {
            const logs = await api.getAuditLogs(params);
            document.getElementById('audit-logs-content').innerHTML = app.renderAuditLogs(logs.logs || []);
        } catch (error) {
            showNotification('error', `Failed to filter logs: ${error.message}`);
        }
    }

    // SQL Query templates
    getQueryTemplates() {
        return {
            'Documents Overview': 'SELECT id, title, version, status, created_at, bytes FROM documents ORDER BY created_at DESC LIMIT 10;',
            'Chunk Analysis': 'SELECT d.title, c.intent_label, COUNT(*) as count FROM chunks c JOIN documents d ON c.document_id = d.id WHERE c.intent_label IS NOT NULL GROUP BY d.title, c.intent_label ORDER BY count DESC;',
            'Document Status Summary': 'SELECT status, COUNT(*) as count FROM documents GROUP BY status;',
            'Recent Comparisons': 'SELECT doc_slug, version_a, version_b, similarity_score, created_at FROM comparisons ORDER BY created_at DESC LIMIT 10;',
            'Storage Analysis': 'SELECT domain, COUNT(*) as doc_count, SUM(bytes) as total_bytes FROM documents WHERE domain IS NOT NULL GROUP BY domain;',
            'Analysis Progress': 'SELECT d.status, COUNT(DISTINCT d.id) as documents, COUNT(c.id) as chunks FROM documents d LEFT JOIN chunks c ON d.id = c.document_id GROUP BY d.status;'
        };
    }

    insertQueryTemplate(templateName) {
        const templates = this.getQueryTemplates();
        const query = templates[templateName];
        if (query) {
            document.getElementById('sql-query').value = query;
        }
    }
}

// Initialize admin panel
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('admin-page')) {
        window.adminPanel = new AdminPanel();
    }
});