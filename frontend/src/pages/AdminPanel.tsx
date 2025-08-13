// # frontend/src/pages/AdminPanel.tsx
/**
 * DocuReview Pro - Admin Panel Component
 * Comprehensive administrative interface with SQL executor
 */
import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  Database,
  Play,
  Download,
  Copy,
  History,
  Activity,
  BarChart3,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  Trash2,
  RefreshCw,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  Code,
  Terminal
} from 'lucide-react';

import { apiService } from '@/services/api';

// Types
interface SQLResult {
  success: boolean;
  query_type: string;
  execution_time_ms: number;
  rows_affected?: number;
  columns?: string[];
  data?: Record<string, any>[];
  row_count?: number;
  error?: string;
  warnings?: string[];
  explain_plan?: string;
}

interface QueryHistory {
  id: string;
  query: string;
  timestamp: Date;
  execution_time: number;
  success: boolean;
  error?: string;
}

const AdminPanel: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // State
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'sql');
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM documents LIMIT 10;');
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [showQueryHistory, setShowQueryHistory] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [resultsPage, setResultsPage] = useState(1);
  const [resultsPerPage] = useState(50);
  
  // Refs
  const sqlEditorRef = useRef<HTMLTextAreaElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Update URL when tab changes
  useEffect(() => {
    setSearchParams({ tab: activeTab });
  }, [activeTab, setSearchParams]);

  // SQL Execution Mutation
  const sqlMutation = useMutation({
    mutationFn: async (query: string) => {
      const response = await apiService.admin.executeSql({
        query,
        limit_results: true,
        explain_plan: false
      });
      return response.data;
    },
    onSuccess: (data: SQLResult) => {
      if (data.success) {
        toast.success(`Query executed successfully in ${data.execution_time_ms.toFixed(2)}ms`);
        
        // Add to history
        const historyEntry: QueryHistory = {
          id: Date.now().toString(),
          query: sqlQuery,
          timestamp: new Date(),
          execution_time: data.execution_time_ms,
          success: true
        };
        setQueryHistory(prev => [historyEntry, ...prev.slice(0, 49)]); // Keep last 50
        
        // Show warnings if any
        if (data.warnings && data.warnings.length > 0) {
          data.warnings.forEach(warning => toast.warning(warning));
        }
      } else {
        toast.error(`Query failed: ${data.error}`);
        
        // Add failed query to history
        const historyEntry: QueryHistory = {
          id: Date.now().toString(),
          query: sqlQuery,
          timestamp: new Date(),
          execution_time: 0,
          success: false,
          error: data.error
        };
        setQueryHistory(prev => [historyEntry, ...prev.slice(0, 49)]);
      }
    },
    onError: (error: any) => {
      toast.error(`Error executing query: ${error.message}`);
    }
  });

  // System Stats Query
  const { data: systemStats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: async () => {
      const response = await apiService.admin.getSystemStats();
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: activeTab === 'stats'
  });

  // Database Schema Query
  const { data: dbSchema, isLoading: schemaLoading } = useQuery({
    queryKey: ['admin', 'schema'],
    queryFn: async () => {
      const response = await apiService.admin.getDatabaseSchema();
      return response.data;
    },
    enabled: activeTab === 'sql'
  });

  // Execute SQL Query
  const handleExecuteQuery = () => {
    if (!sqlQuery.trim()) {
      toast.error('Please enter a SQL query');
      return;
    }
    sqlMutation.mutate(sqlQuery);
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleExecuteQuery();
    }
    
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
      e.preventDefault();
      setSqlQuery('');
    }
  };

  // Export results to CSV
  const exportToCSV = (result: SQLResult) => {
    if (!result.data || !result.columns) return;
    
    const csv = [
      result.columns.join(','),
      ...result.data.map(row => 
        result.columns!.map(col => 
          JSON.stringify(row[col] || '')
        ).join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_results_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Copy query to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  // Load query from history
  const loadFromHistory = (query: string) => {
    setSqlQuery(query);
    setShowQueryHistory(false);
    if (sqlEditorRef.current) {
      sqlEditorRef.current.focus();
    }
  };

  // Render SQL Results Table
  const renderSQLResults = (result: SQLResult) => {
    if (!result.success) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <XCircle className="h-5 w-5 text-red-500 mr-2" />
            <h3 className="text-lg font-medium text-red-900">Query Error</h3>
          </div>
          <pre className="text-sm text-red-700 bg-red-100 p-3 rounded font-mono overflow-x-auto">
            {result.error}
          </pre>
        </div>
      );
    }

    if (!result.data || result.data.length === 0) {
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <CheckCircle className="h-12 w-12 text-blue-500 mx-auto mb-2" />
          <h3 className="text-lg font-medium text-blue-900 mb-1">Query Executed Successfully</h3>
          <p className="text-blue-700">
            {result.query_type} executed in {result.execution_time_ms.toFixed(2)}ms
            {result.rows_affected !== undefined && ` (${result.rows_affected} rows affected)`}
          </p>
        </div>
      );
    }

    // Paginate results
    const startIndex = (resultsPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const paginatedData = result.data.slice(startIndex, endIndex);
    const totalPages = Math.ceil(result.data.length / resultsPerPage);

    return (
      <div className="space-y-4">
        {/* Results Header */}
        <div className="flex items-center justify-between bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-green-600">
              <CheckCircle className="h-5 w-5 mr-2" />
              <span className="font-medium">Success</span>
            </div>
            <div className="flex items-center text-gray-600">
              <Clock className="h-4 w-4 mr-1" />
              <span>{result.execution_time_ms.toFixed(2)}ms</span>
            </div>
            <div className="flex items-center text-gray-600">
              <FileText className="h-4 w-4 mr-1" />
              <span>{result.row_count} rows</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => exportToCSV(result)}
              className="btn-secondary text-sm py-1 px-3"
            >
              <Download className="h-4 w-4 mr-1" />
              Export CSV
            </button>
            <button
              onClick={() => copyToClipboard(JSON.stringify(result.data, null, 2))}
              className="btn-secondary text-sm py-1 px-3"
            >
              <Copy className="h-4 w-4 mr-1" />
              Copy JSON
            </button>
          </div>
        </div>

        {/* Results Table */}
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="table-enterprise">
            <thead className="table-header">
              <tr>
                {result.columns?.map((column, index) => (
                  <th key={index} className="px-4 py-3 text-left">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="table-body">
              {paginatedData.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {result.columns?.map((column, colIndex) => (
                    <td key={colIndex} className="px-4 py-3 text-sm">
                      <div className="max-w-xs truncate" title={String(row[column] || '')}>
                        {row[column] !== null && row[column] !== undefined 
                          ? String(row[column]) 
                          : <span className="text-gray-400 italic">NULL</span>
                        }
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between bg-gray-50 px-4 py-3 rounded-lg">
            <div className="text-sm text-gray-700">
              Showing {startIndex + 1} to {Math.min(endIndex, result.data.length)} of {result.data.length} results
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setResultsPage(page => Math.max(1, page - 1))}
                disabled={resultsPage === 1}
                className="btn-secondary text-sm py-1 px-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {resultsPage} of {totalPages}
              </span>
              <button
                onClick={() => setResultsPage(page => Math.min(totalPages, page + 1))}
                disabled={resultsPage === totalPages}
                className="btn-secondary text-sm py-1 px-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      <div className="page-container py-6">
        {/* Header */}
        <div className="page-header flex items-center justify-between">
          <div>
            <h1 className="page-title flex items-center">
              <Settings className="h-7 w-7 mr-2 text-blue-600" />
              Admin Panel
            </h1>
            <p className="page-subtitle">
              System administration and database management
            </p>
          </div>
          
          {activeTab === 'sql' && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowQueryHistory(!showQueryHistory)}
                className="btn-secondary"
              >
                <History className="h-4 w-4 mr-2" />
                Query History
              </button>
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="btn-secondary"
              >
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'sql', name: 'SQL Executor', icon: Database },
              { id: 'stats', name: 'System Stats', icon: BarChart3 },
              { id: 'logs', name: 'Activity Logs', icon: Activity },
              { id: 'maintenance', name: 'Maintenance', icon: Settings }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* SQL Executor Tab */}
        {activeTab === 'sql' && (
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Query Editor */}
            <div className="xl:col-span-3 space-y-4">
              <div className="card-enterprise">
                <div className="card-header flex items-center justify-between">
                  <h2 className="text-lg font-medium flex items-center">
                    <Terminal className="h-5 w-5 mr-2" />
                    SQL Query Editor
                  </h2>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      Ctrl+Enter to execute
                    </span>
                    <button
                      onClick={() => setSqlQuery('')}
                      className="btn-secondary text-sm py-1 px-2"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="card-body">
                  <textarea
                    ref={sqlEditorRef}
                    value={sqlQuery}
                    onChange={(e) => setSqlQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter your SQL query here..."
                    className="w-full h-32 p-3 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    spellCheck={false}
                  />
                  <div className="mt-3 flex items-center justify-between">
                    <div className="text-sm text-gray-500">
                      {sqlQuery.length} characters
                    </div>
                    <button
                      onClick={handleExecuteQuery}
                      disabled={sqlMutation.isPending || !sqlQuery.trim()}
                      className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {sqlMutation.isPending ? (
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4 mr-2" />
                      )}
                      Execute Query
                    </button>
                  </div>
                </div>
              </div>

              {/* Query Results */}
              {sqlMutation.data && (
                <div className="card-enterprise">
                  <div className="card-header">
                    <h3 className="text-lg font-medium">Query Results</h3>
                  </div>
                  <div className="card-body" ref={resultsRef}>
                    {renderSQLResults(sqlMutation.data)}
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
              {/* Database Schema */}
              <div className="card-enterprise">
                <div className="card-header">
                  <h3 className="text-lg font-medium">Database Schema</h3>
                </div>
                <div className="card-body">
                  {schemaLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <RefreshCw className="h-5 w-5 animate-spin mr-2" />
                      Loading schema...
                    </div>
                  ) : dbSchema ? (
                    <div className="space-y-2">
                      {dbSchema.tables?.map((table: any) => (
                        <div key={table.name} className="text-sm">
                          <button
                            onClick={() => setSqlQuery(`SELECT * FROM ${table.name} LIMIT 10;`)}
                            className="w-full text-left p-2 hover:bg-gray-50 rounded flex items-center justify-between"
                          >
                            <span className="font-medium text-blue-600">{table.name}</span>
                            <span className="text-gray-500">{table.row_count} rows</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">Schema not available</p>
                  )}
                </div>
              </div>

              {/* Quick Queries */}
              <div className="card-enterprise">
                <div className="card-header">
                  <h3 className="text-lg font-medium">Quick Queries</h3>
                </div>
                <div className="card-body">
                  <div className="space-y-2">
                    {[
                      { name: 'All Documents', query: 'SELECT id, title, version, created_at FROM documents ORDER BY created_at DESC LIMIT 20;' },
                      { name: 'Document Stats', query: 'SELECT COUNT(*) as total_docs, COUNT(DISTINCT slug) as unique_docs FROM documents;' },
                      { name: 'Recent Uploads', query: 'SELECT title, version, created_at FROM documents WHERE created_at > datetime("now", "-7 days") ORDER BY created_at DESC;' },
                      { name: 'Large Documents', query: 'SELECT title, bytes, created_at FROM documents WHERE bytes > 50000 ORDER BY bytes DESC;' },
                      { name: 'Version History', query: 'SELECT slug, COUNT(*) as versions FROM documents GROUP BY slug HAVING versions > 1 ORDER BY versions DESC;' }
                    ].map((query, index) => (
                      <button
                        key={index}
                        onClick={() => setSqlQuery(query.query)}
                        className="w-full text-left p-2 text-sm hover:bg-gray-50 rounded"
                      >
                        {query.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Query History Sidebar */}
            {showQueryHistory && queryHistory.length > 0 && (
              <div className="fixed right-4 top-20 bottom-4 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-40 overflow-hidden">
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="font-medium">Query History</h3>
                  <button
                    onClick={() => setShowQueryHistory(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XCircle className="h-5 w-5" />
                  </button>
                </div>
                <div className="overflow-y-auto h-full p-4 space-y-2">
                  {queryHistory.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 border border-gray-200 rounded cursor-pointer hover:bg-gray-50"
                      onClick={() => loadFromHistory(item.query)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs ${item.success ? 'text-green-600' : 'text-red-600'}`}>
                          {item.success ? 'Success' : 'Error'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {item.execution_time.toFixed(0)}ms
                        </span>
                      </div>
                      <div className="text-xs font-mono text-gray-700 truncate">
                        {item.query}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {item.timestamp.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* System Stats Tab */}
        {activeTab === 'stats' && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {statsLoading ? (
              <div className="col-span-full flex items-center justify-center py-12">
                <RefreshCw className="h-8 w-8 animate-spin mr-3" />
                Loading system statistics...
              </div>
            ) : systemStats ? (
              <>
                {/* Application Stats */}
                <div className="card-enterprise">
                  <div className="card-header">
                    <h3 className="text-lg font-medium">Application</h3>
                  </div>
                  <div className="card-body space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Version</span>
                      <span className="font-medium">{systemStats.application?.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Uptime</span>
                      <span className="font-medium">{systemStats.application?.uptime}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Environment</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        systemStats.application?.environment === 'production' 
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {systemStats.application?.environment}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Database Stats */}
                <div className="card-enterprise">
                  <div className="card-header">
                    <h3 className="text-lg font-medium">Database</h3>
                  </div>
                  <div className="card-body space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Documents</span>
                      <span className="font-medium">{systemStats.database?.total_documents}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Chunks</span>
                      <span className="font-medium">{systemStats.database?.total_chunks}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Database Size</span>
                      <span className="font-medium">{systemStats.database?.size_mb} MB</span>
                    </div>
                  </div>
                </div>

                {/* System Resources */}
                <div className="card-enterprise">
                  <div className="card-header">
                    <h3 className="text-lg font-medium">System Resources</h3>
                  </div>
                  <div className="card-body space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">CPU Usage</span>
                      <span className="font-medium">{systemStats.system?.cpu_percent}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Memory Usage</span>
                      <span className="font-medium">{systemStats.system?.memory_percent}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Disk Usage</span>
                      <span className="font-medium">{systemStats.system?.disk_percent}%</span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="col-span-full text-center py-12">
                <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                <p className="text-gray-600">Unable to load system statistics</p>
              </div>
            )}
          </div>
        )}

        {/* Other tabs can be implemented similarly */}
        {activeTab === 'logs' && (
          <div className="card-enterprise">
            <div className="card-body text-center py-12">
              <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Activity Logs</h3>
              <p className="text-gray-600">Activity logging functionality coming soon...</p>
            </div>
          </div>
        )}

        {activeTab === 'maintenance' && (
          <div className="card-enterprise">
            <div className="card-body text-center py-12">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Maintenance Tools</h3>
              <p className="text-gray-600">Maintenance functionality coming soon...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;