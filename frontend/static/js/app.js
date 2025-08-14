// app/frontend/static/js/app.js

class DocuReviewApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.documents = [];
        this.currentDocuments = [];
        this.pagination = { limit: 20, offset: 0, total: 0 };
        this.filters = { search: '', domain: '', status: '' };
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.setupModals();
        await this.loadDashboard();
        
        // Auto-refresh dashboard every 30 seconds
        setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboard();
            }
        }, 30000);
    }

    setupEventListeners() {
        // Upload button
        document.getElementById('upload-btn').addEventListener('click', () => {
            this.showUploadModal();
        });

        // Upload form
        document.getElementById('upload-form').addEventListener('submit', (e) => {
            this.handleDocumentUpload(e);
        });

        // Document search
        const searchInput = document.getElementById('document-search');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(() => {
                this.filters.search = searchInput.value;
                this.loadDocuments();
            }, 500));
        }

        // Filters
        document.getElementById('domain-filter')?.addEventListener('change', (e) => {
            this.filters.domain = e.target.value;
            this.loadDocuments();
        });

        document.getElementById('status-filter')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.loadDocuments();
        });

        // Comparison setup
        this.setupComparisonEventListeners();
        
        // Search functionality
        this.setupSearchEventListeners();
    }

    setupNavigation() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = btn.dataset.page;
                this.navigateToPage(page);
            });
        });
    }

    setupModals() {
        // Close modal buttons
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.hideModal(modal);
            });
        });

        // Click outside to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal);
                }
            });
        });
    }

    async navigateToPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });

        // Hide all pages
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });

        // Show current page
        document.getElementById(`${page}-page`).classList.add('active');
        this.currentPage = page;

        // Load page data
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'documents':
                await this.loadDocuments();
                break;
            case 'comparison':
                await this.loadComparisonPage();
                break;
            case 'search':
                await this.loadSearchPage();
                break;
            case 'admin':
                await this.loadAdminPage();
                break;
        }
    }

    // Dashboard functionality
    async loadDashboard() {
        try {
            // Load system stats
            const searchStats = await api.getSearchStats();
            this.updateDashboardMetrics(searchStats);

            // Load recent documents
            const recentDocs = await api.getDocuments({ limit: 6, offset: 0 });
            this.renderRecentDocuments(recentDocs.documents || []);

        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    updateDashboardMetrics(stats) {
        const indexingStats = stats.indexing_stats || {};
        document.getElementById('total-documents').textContent = indexingStats.total_documents || 0;
        document.getElementById('analyzed-documents').textContent = indexingStats.analyzed_chunks || 0;
        document.getElementById('total-comparisons').textContent = '0'; // Will be updated when comparison history is available
        document.getElementById('search-readiness').textContent = `${indexingStats.search_readiness || 0}%`;
    }

    renderRecentDocuments(documents) {
        const container = document.getElementById('recent-documents');
        
        if (documents.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No documents uploaded yet</p>';
            return;
        }

        container.innerHTML = documents.map(doc => this.createDocumentCard(doc)).join('');
    }

    // Document management
    async loadDocuments() {
        try {
            const params = {
                limit: this.pagination.limit,
                offset: this.pagination.offset,
                ...this.filters
            };

            const response = await api.getDocuments(params);
            this.currentDocuments = response.documents || [];
            this.pagination.total = response.total || 0;

            this.renderDocuments();
            this.renderPagination();

        } catch (error) {
            console.error('Failed to load documents:', error);
        }
    }

    renderDocuments() {
        const container = document.getElementById('documents-container');
        
        if (this.currentDocuments.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No documents found</p>';
            return;
        }

        container.innerHTML = this.currentDocuments.map(doc => this.createDocumentCard(doc)).join('');
    }

    createDocumentCard(doc) {
        const tags = doc.tags.slice(0, 3); // Show max 3 tags
        const statusClass = `status-${doc.status}`;
        
        return `
            <div class="document-card fade-in" onclick="app.showDocumentDetail(${doc.id})">
                <div class="document-header">
                    <div>
                        <div class="document-title">${escapeHtml(doc.title)}</div>
                        <div class="document-meta">
                            v${doc.version} â€¢ ${formatDate(doc.updated_at)}
                            ${doc.author ? ` â€¢ ${escapeHtml(doc.author)}` : ''}
                        </div>
                    </div>
                    <div class="document-version">v${doc.version}</div>
                </div>
                
                <div class="document-tags">
                    ${tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                    ${doc.tags.length > 3 ? `<span class="tag">+${doc.tags.length - 3} more</span>` : ''}
                </div>
                
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="status-badge ${statusClass}">${doc.status}</span>
                        ${doc.has_analysis ? '<i class="fas fa-brain" title="AI Analyzed"></i>' : ''}
                    </div>
                    <div class="text-right">
                        <div class="font-weight-500">${formatFileSize(doc.bytes)}</div>
                        <div class="text-muted">${doc.chunk_count} chunks</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination() {
        const container = document.getElementById('pagination');
        const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
        const currentPage = Math.floor(this.pagination.offset / this.pagination.limit) + 1;

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let pagination = `
            <button ${currentPage === 1 ? 'disabled' : ''} onclick="app.goToPage(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
                pagination += `
                    <button class="${i === currentPage ? 'active' : ''}" onclick="app.goToPage(${i})">
                        ${i}
                    </button>
                `;
            } else if (i === currentPage - 3 || i === currentPage + 3) {
                pagination += '<span>...</span>';
            }
        }

        pagination += `
            <button ${currentPage === totalPages ? 'disabled' : ''} onclick="app.goToPage(${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        container.innerHTML = pagination;
    }

    goToPage(page) {
        this.pagination.offset = (page - 1) * this.pagination.limit;
        this.loadDocuments();
    }

    // Upload functionality
    showUploadModal() {
        const modal = document.getElementById('upload-modal');
        modal.classList.add('show');
        document.getElementById('doc-title').focus();
    }

    hideModal(modal) {
        modal.classList.remove('show');
        // Reset form if it's the upload modal
        if (modal.id === 'upload-modal') {
            document.getElementById('upload-form').reset();
        }
    }

    async handleDocumentUpload(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            showNotification('error', 'Please select a file to upload');
            return;
        }

        // Append form data
        formData.append('file', file);
        formData.append('title', document.getElementById('doc-title').value);
        formData.append('author', document.getElementById('doc-author').value);
        formData.append('domain', document.getElementById('doc-domain').value);
        formData.append('tags', document.getElementById('doc-tags').value);
        formData.append('notes', document.getElementById('doc-notes').value);
        formData.append('auto_analyze', document.getElementById('auto-analyze').checked);

        try {
            const response = await api.uploadDocument(formData);
            
            if (response.success) {
                showNotification('success', `Document "${response.document.title}" uploaded successfully`);
                this.hideModal(document.getElementById('upload-modal'));
                
                // Refresh current view
                if (this.currentPage === 'documents') {
                    this.loadDocuments();
                } else if (this.currentPage === 'dashboard') {
                    this.loadDashboard();
                }
            }
        } catch (error) {
            showNotification('error', `Upload failed: ${error.message}`);
        }
    }

    // Document detail
    async showDocumentDetail(docId) {
        try {
            const doc = await api.getDocument(docId, { 
                include_content: false, 
                include_analysis: true 
            });
            
            const modal = document.getElementById('document-modal');
            const titleEl = document.getElementById('doc-modal-title');
            const contentEl = document.getElementById('doc-modal-content');
            
            titleEl.textContent = `${doc.title} v${doc.version}`;
            contentEl.innerHTML = this.renderDocumentDetail(doc);
            
            modal.classList.add('show');
            
        } catch (error) {
            showNotification('error', `Failed to load document: ${error.message}`);
        }
    }

    renderDocumentDetail(doc) {
        const analysis = doc.analysis_summary;
        
        return `
            <div class="document-detail">
                <div class="detail-section">
                    <h4>Document Information</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>Title:</label>
                            <span>${escapeHtml(doc.title)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Version:</label>
                            <span>v${doc.version}</span>
                        </div>
                        <div class="detail-item">
                            <label>Status:</label>
                            <span class="status-badge status-${doc.status}">${doc.status}</span>
                        </div>
                        <div class="detail-item">
                            <label>Author:</label>
                            <span>${escapeHtml(doc.author || 'Unknown')}</span>
                        </div>
                        <div class="detail-item">
                            <label>Domain:</label>
                            <span>${escapeHtml(doc.domain || 'None')}</span>
                        </div>
                        <div class="detail-item">
                            <label>Size:</label>
                            <span>${formatFileSize(doc.bytes)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Created:</label>
                            <span>${formatDate(doc.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <label>Updated:</label>
                            <span>${formatDate(doc.updated_at)}</span>
                        </div>
                    </div>
                </div>

                ${doc.tags.length > 0 ? `
                    <div class="detail-section">
                        <h4>Tags</h4>
                        <div class="document-tags">
                            ${doc.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}

                ${analysis ? `
                    <div class="detail-section">
                        <h4>Analysis Summary</h4>
                        <div class="analysis-stats">
                            <div class="stat-item">
                                <label>Total Chunks:</label>
                                <span>${analysis.analysis_stats?.analyzed_chunks || 0}</span>
                            </div>
                            <div class="stat-item">
                                <label>Intent Distribution:</label>
                                <div class="intent-chips">
                                    ${Object.entries(analysis.analysis_stats?.intent_distribution || {})
                                        .map(([intent, count]) => 
                                            `<span class="intent-chip">${intent}: ${count}</span>`
                                        ).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                ` : ''}

                <div class="detail-actions">
                    <button class="btn btn-primary" onclick="app.navigateToPage('comparison')">
                        <i class="fas fa-code-compare"></i>
                        Compare Versions
                    </button>
                    <button class="btn btn-secondary" onclick="app.analyzeDocument(${doc.id})">
                        <i class="fas fa-brain"></i>
                        Reanalyze
                    </button>
                    <button class="btn btn-warning" onclick="app.deleteDocument(${doc.id})">
                        <i class="fas fa-trash"></i>
                        Delete
                    </button>
                </div>
            </div>
        `;
    }

    async analyzeDocument(docId) {
        try {
            await api.analyzeDocument(docId, true);
            showNotification('info', 'Document analysis started. This may take a few moments.');
            
            // Close modal and refresh
            this.hideModal(document.getElementById('document-modal'));
            if (this.currentPage === 'documents') {
                this.loadDocuments();
            }
        } catch (error) {
            showNotification('error', `Analysis failed: ${error.message}`);
        }
    }

    async deleteDocument(docId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }

        try {
            await api.deleteDocument(docId);
            showNotification('success', 'Document deleted successfully');
            
            this.hideModal(document.getElementById('document-modal'));
            if (this.currentPage === 'documents') {
                this.loadDocuments();
            }
        } catch (error) {
            showNotification('error', `Delete failed: ${error.message}`);
        }
    }

    // Comparison functionality
    setupComparisonEventListeners() {
        // Document selection change
        document.getElementById('doc-a-select')?.addEventListener('change', (e) => {
            this.loadVersionsForDocument('a', e.target.value);
        });

        document.getElementById('doc-b-select')?.addEventListener('change', (e) => {
            this.loadVersionsForDocument('b', e.target.value);
        });

        // Similarity threshold slider
        const thresholdSlider = document.getElementById('similarity-threshold');
        const thresholdValue = document.getElementById('threshold-value');
        if (thresholdSlider && thresholdValue) {
            thresholdSlider.addEventListener('input', (e) => {
                thresholdValue.textContent = e.target.value;
            });
        }

        // Compare button
        document.getElementById('compare-btn')?.addEventListener('click', () => {
            this.performComparison();
        });
    }

    async loadComparisonPage() {
        try {
            // Load documents for selection
            const docs = await api.getDocuments({ limit: 100 });
            this.populateDocumentSelectors(docs.documents || []);
            
            // Hide previous results
            document.getElementById('comparison-results').style.display = 'none';
        } catch (error) {
            console.error('Failed to load comparison page:', error);
        }
    }

    populateDocumentSelectors(documents) {
        const docASelect = document.getElementById('doc-a-select');
        const docBSelect = document.getElementById('doc-b-select');

        if (!docASelect || !docBSelect) return;

        const options = documents.map(doc => 
            `<option value="${doc.slug}">${escapeHtml(doc.title)} (v${doc.version})</option>`
        ).join('');

        docASelect.innerHTML = '<option value="">Select document...</option>' + options;
        docBSelect.innerHTML = '<option value="">Select document...</option>' + options;
    }

    async loadVersionsForDocument(side, slug) {
        if (!slug) return;

        try {
            const versions = await api.getDocumentVersions(slug);
            const selectEl = document.getElementById(`version-${side}-select`);
            
            const options = versions.versions.map(v => 
                `<option value="${v.version}">v${v.version} - ${formatDate(v.created_at)}</option>`
            ).join('');

            selectEl.innerHTML = '<option value="">Select version...</option>' + options;
        } catch (error) {
            console.error('Failed to load versions:', error);
        }
    }

    async performComparison() {
        const docASlug = document.getElementById('doc-a-select').value;
        const docBSlug = document.getElementById('doc-b-select').value;
        const versionA = document.getElementById('version-a-select').value;
        const versionB = document.getElementById('version-b-select').value;

        if (!docASlug || !docBSlug || !versionA || !versionB) {
            showNotification('error', 'Please select both documents and versions');
            return;
        }

        const comparisonData = {
            document_slug: docASlug,
            version_a: parseInt(versionA),
            version_b: parseInt(versionB),
            granularity: document.getElementById('granularity-select').value,
            algorithm: document.getElementById('algorithm-select').value,
            similarity_threshold: parseFloat(document.getElementById('similarity-threshold').value)
        };

        try {
            const result = await api.compareBySlug(comparisonData);
            this.displayComparisonResults(result);
        } catch (error) {
            showNotification('error', `Comparison failed: ${error.message}`);
        }
    }

    displayComparisonResults(result) {
        const container = document.getElementById('comparison-results');
        const metrics = result.metrics || {};
        
        container.innerHTML = `
            <div class="comparison-summary">
                <h3>Comparison Results</h3>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <label>Overall Similarity:</label>
                        <span class="metric-value">${(metrics.overall_similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric-item">
                        <label>Text Similarity:</label>
                        <span class="metric-value">${(metrics.text_similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric-item">
                        <label>Structural Similarity:</label>
                        <span class="metric-value">${(metrics.structural_similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric-item">
                        <label>Change Significance:</label>
                        <span class="metric-value">${metrics.change_significance || 'N/A'}</span>
                    </div>
                </div>
            </div>

            ${result.ai_summary ? `
                <div class="ai-summary">
                    <h4>AI Analysis Summary</h4>
                    <p>${escapeHtml(result.ai_summary.executive_summary || 'No summary available')}</p>
                    
                    ${result.ai_summary.major_additions?.length > 0 ? `
                        <div class="change-section">
                            <h5>Major Additions:</h5>
                            <ul>
                                ${result.ai_summary.major_additions.map(item => 
                                    `<li>${escapeHtml(item)}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    ${result.ai_summary.major_removals?.length > 0 ? `
                        <div class="change-section">
                            <h5>Major Removals:</h5>
                            <ul>
                                ${result.ai_summary.major_removals.map(item => 
                                    `<li>${escapeHtml(item)}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : ''}

            ${this.renderTextDiff(result.text_diff)}
        `;

        container.style.display = 'block';
    }

    renderTextDiff(textDiff) {
        if (!textDiff || !textDiff.operations) {
            return '<p>No text differences to display</p>';
        }

        const operations = textDiff.operations;
        let diffHtml = '<div class="diff-viewer">';
        
        // Simplified diff rendering
        diffHtml += '<div class="diff-panel">';
        diffHtml += '<div class="diff-header">Changes Summary</div>';
        diffHtml += '<div class="diff-content">';
        
        operations.forEach(op => {
            if (op.operation === 'insert') {
                diffHtml += `<span class="diff-addition">+ ${escapeHtml(op.b_content.join(' '))}</span><br>`;
            } else if (op.operation === 'delete') {
                diffHtml += `<span class="diff-deletion">- ${escapeHtml(op.a_content.join(' '))}</span><br>`;
            } else if (op.operation === 'replace') {
                diffHtml += `<span class="diff-deletion">- ${escapeHtml(op.a_content.join(' '))}</span><br>`;
                diffHtml += `<span class="diff-addition">+ ${escapeHtml(op.b_content.join(' '))}</span><br>`;
            }
        });
        
        diffHtml += '</div></div></div>';
        return diffHtml;
    }

    // Search functionality
    setupSearchEventListeners() {
        const searchBtn = document.getElementById('semantic-search-btn');
        const searchInput = document.getElementById('semantic-search-input');

        if (searchBtn && searchInput) {
            searchBtn.addEventListener('click', () => this.performSearch());
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }

    async loadSearchPage() {
        // Load search statistics
        try {
            const stats = await api.getSearchStats();
            // Display search readiness info
        } catch (error) {
            console.error('Failed to load search stats:', error);
        }
    }

    async performSearch() {
        const query = document.getElementById('semantic-search-input').value.trim();
        
        if (!query) {
            showNotification('error', 'Please enter a search query');
            return;
        }

        const searchData = {
            query: query,
            search_scope: document.getElementById('search-scope').value,
            filters: {
                intent: document.getElementById('intent-filter').value
            },
            top_k: parseInt(document.getElementById('search-limit').value) || 20
        };

        try {
            const results = await api.globalSearch(searchData);
            this.displaySearchResults(results);
        } catch (error) {
            showNotification('error', `Search failed: ${error.message}`);
        }
    }

    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        
        if (!results.results || results.results.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No results found</p>';
            return;
        }

        container.innerHTML = `
            <div class="search-summary">
                <p>Found ${results.total_results} results in ${results.processing_time_ms}ms</p>
            </div>
            <div class="results-list">
                ${results.results.map(result => this.createSearchResult(result)).join('')}
            </div>
        `;
    }

createSearchResult(result) {
        return `
            <div class="search-result fade-in">
                <div class="result-header">
                    <h4 class="result-title">${escapeHtml(result.document_title)}</h4>
                    <span class="result-score">${(result.similarity_score * 100).toFixed(1)}%</span>
                </div>
                <div class="result-preview">
                    ${escapeHtml(result.text_preview)}
                </div>
                <div class="result-meta">
                    <span>v${result.document_version}</span>
                    <span>Chunk ${result.chunk_index}</span>
                    ${result.intent_label ? `<span class="intent-chip">${result.intent_label}</span>` : ''}
                    ${result.heading ? `<span>Section: ${escapeHtml(result.heading)}</span>` : ''}
                </div>
            </div>
        `;
    }

    // Admin functionality
    async loadAdminPage() {
        // Load default tab
        this.loadAdminTab('sql-executor');
    }

    async loadAdminTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Show current tab
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load tab-specific data
        switch (tabName) {
            case 'system-stats':
                await this.loadSystemStats();
                break;
            case 'audit-logs':
                await this.loadAuditLogs();
                break;
        }
    }

    async loadSystemStats() {
        try {
            const stats = await api.getSystemStats();
            document.getElementById('system-stats-content').innerHTML = this.renderSystemStats(stats);
        } catch (error) {
            console.error('Failed to load system stats:', error);
        }
    }

    renderSystemStats(stats) {
        return `
            <div class="stats-grid">
                <div class="stats-card">
                    <h4>Application</h4>
                    <div class="stat-item">
                        <span class="stat-label">Name:</span>
                        <span class="stat-value">${stats.application?.name || 'DocuReview Pro'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Version:</span>
                        <span class="stat-value">${stats.application?.version || '1.0.0'}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Debug Mode:</span>
                        <span class="stat-value">${stats.application?.debug_mode ? 'Yes' : 'No'}</span>
                    </div>
                </div>

                <div class="stats-card">
                    <h4>Database</h4>
                    <div class="stat-item">
                        <span class="stat-label">Total Documents:</span>
                        <span class="stat-value">${stats.database?.documents?.total || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Total Chunks:</span>
                        <span class="stat-value">${stats.database?.total_chunks || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Vector Indexes:</span>
                        <span class="stat-value">${stats.database?.vector_indexes || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Database Size:</span>
                        <span class="stat-value">${stats.database?.database_size_mb || 0} MB</span>
                    </div>
                </div>

                <div class="stats-card">
                    <h4>System Resources</h4>
                    <div class="stat-item">
                        <span class="stat-label">CPU Usage:</span>
                        <span class="stat-value">${stats.system?.cpu_percent || 0}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Memory Used:</span>
                        <span class="stat-value">${stats.system?.memory_used_gb || 0} GB</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${stats.system?.memory_percent || 0}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Disk Used:</span>
                        <span class="stat-value">${stats.system?.disk_used_gb || 0} GB</span>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${stats.system?.disk_percent || 0}%"></div>
                        </div>
                    </div>
                </div>

                <div class="stats-card">
                    <h4>Storage</h4>
                    <div class="stat-item">
                        <span class="stat-label">Total Files:</span>
                        <span class="stat-value">${stats.storage?.total_files || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Storage Used:</span>
                        <span class="stat-value">${stats.storage?.total_size_mb || 0} MB</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Avg File Size:</span>
                        <span class="stat-value">${stats.storage?.avg_file_size_kb || 0} KB</span>
                    </div>
                </div>
            </div>
        `;
    }

    async loadAuditLogs() {
        try {
            const logs = await api.getAuditLogs({ limit: 50 });
            document.getElementById('audit-logs-content').innerHTML = this.renderAuditLogs(logs.logs || []);
        } catch (error) {
            console.error('Failed to load audit logs:', error);
        }
    }

    renderAuditLogs(logs) {
        if (logs.length === 0) {
            return '<p class="text-center text-muted">No audit logs found</p>';
        }

        return `
            <div class="audit-logs-container">
                ${logs.map(log => `
                    <div class="audit-log">
                        <div class="log-header">
                            <span class="log-operation">${log.operation}</span>
                            <span class="log-timestamp">${formatDate(log.timestamp)}</span>
                        </div>
                        <div class="log-details">
                            <span class="log-entity">${log.entity_type}</span>
                            ${log.details || 'No additional details'}
                            ${log.execution_time_ms ? `<span class="text-muted">(${log.execution_time_ms}ms)</span>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

// Global maintenance functions
async function performMaintenance(operation) {
    const daysInput = document.getElementById('cleanup-days');
    const days = daysInput ? parseInt(daysInput.value) : 30;

    const maintenanceData = {
        operation: operation,
        parameters: { days_old: days },
        dry_run: false
    };

    if (!confirm(`Are you sure you want to perform ${operation}?`)) {
        return;
    }

    try {
        const result = await api.performMaintenance(maintenanceData);
        if (result.success) {
            showNotification('success', result.message || 'Maintenance operation completed');
        } else {
            showNotification('error', result.error || 'Maintenance operation failed');
        }
    } catch (error) {
        showNotification('error', `Maintenance failed: ${error.message}`);
    }
}

async function createBackup() {
    if (!confirm('Create a database backup? This may take a few moments.')) {
        return;
    }

    try {
        const result = await api.createBackup();
        if (result.success) {
            showNotification('success', `Backup created: ${result.backup_file}`);
        } else {
            showNotification('error', 'Backup creation failed');
        }
    } catch (error) {
        showNotification('error', `Backup failed: ${error.message}`);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DocuReviewApp();
});