// # frontend/src/services/api.ts
/**
 * DocuReview Pro - Complete API Service
 * HTTP client configuration and service methods
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8555/api';

// Create axios instance with default configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication and logging
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log requests in development
    if (import.meta.env.DEV) {
      console.log(`🔄 ${config.method?.toUpperCase()} ${config.url}`, config.data || config.params);
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    console.error('API Error:', error);

    if (error.response) {
      const { status, data } = error.response;
      
      // Handle specific error status codes
      switch (status) {
        case 400:
          toast.error(data.detail || 'Bad request. Please check your input.');
          break;
        
        case 401:
          toast.error('Authentication required. Please log in.');
          // Redirect to login if needed
          break;
        
        case 403:
          toast.error('Access forbidden. You don\'t have permission for this action.');
          break;
        
        case 404:
          toast.error('Resource not found.');
          break;
        
        case 422:
          // Validation errors
          if (data.detail && Array.isArray(data.detail)) {
            const validationErrors = data.detail.map((err: any) => err.msg).join(', ');
            toast.error(`Validation error: ${validationErrors}`);
          } else {
            toast.error(data.detail || 'Validation error');
          }
          break;
        
        case 429:
          toast.error('Too many requests. Please slow down.');
          break;
        
        case 500:
          toast.error('Internal server error. Please try again.');
          break;
        
        case 503:
          toast.error('Service unavailable. Please try again later.');
          break;
        
        default:
          if (data.detail) {
            toast.error(data.detail);
          } else {
            toast.error(`Request failed with status ${status}`);
          }
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.');
    } else {
      // Other error
      toast.error('An unexpected error occurred.');
    }

    return Promise.reject(error);
  }
);

// Type definitions for API responses
interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

interface PaginatedResponse<T> {
  documents: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface Document {
  id: number;
  title: string;
  slug: string;
  version: number;
  created_at: string;
  updated_at: string;
  author?: string;
  domain?: string;
  tags?: string;
  status: string;
  bytes: number;
  checksum?: string;
}

interface SQLExecuteRequest {
  query: string;
  parameters?: any[];
  limit_results?: boolean;
  explain_plan?: boolean;
}

interface SQLExecuteResponse {
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

// API service methods
export const apiService = {
  // Document endpoints
  documents: {
    list: (params?: URLSearchParams): Promise<AxiosResponse<PaginatedResponse<Document>>> => 
      apiClient.get('/documents', { params }),
    
    get: (id: number): Promise<AxiosResponse<ApiResponse<Document>>> => 
      apiClient.get(`/documents/${id}`),
    
    upload: (formData: FormData): Promise<AxiosResponse<ApiResponse<Document>>> => 
      apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    
    delete: (id: number, deleteAllVersions = false): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.delete(`/documents/${id}?delete_all_versions=${deleteAllVersions}`),
    
    analyze: (id: number, forceReanalysis = false): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.post(`/documents/${id}/analyze`, { force_reanalysis: forceReanalysis }),
    
    getAnalysis: (id: number): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get(`/documents/${id}/analysis`),
    
    getStats: (id: number): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get(`/documents/${id}/stats`),
    
    getVersions: (slug: string): Promise<AxiosResponse<ApiResponse<Document[]>>> => 
      apiClient.get(`/documents/slug/${slug}/versions`),
  },

  // Comparison endpoints
  comparison: {
    compare: (data: {
      doc_a_id: number;
      doc_b_id: number;
      granularity?: string;
      algorithm?: string;
    }): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.post('/comparison/compare', data),
    
    compareBySlug: (data: {
      slug: string;
      version_a: number;
      version_b: number;
      granularity?: string;
      algorithm?: string;
    }): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.post('/comparison/compare-by-slug', data),
    
    getHistory: (documentSlug: string, params?: URLSearchParams): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get(`/comparison/history/${documentSlug}`, { params }),
    
    getConfig: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/comparison/config'),
    
    updateConfig: (config: any): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.put('/comparison/config', config),
  },

  // Search endpoints
  search: {
    documents: (params: {
      query: string;
      search_type?: 'semantic' | 'keyword';
      domain?: string;
      author?: string;
      dateRange?: string;
      limit?: number;
    }): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.post('/search/documents', params),
    
    similar: (documentId: number, limit = 10): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get(`/search/similar/${documentId}?limit=${limit}`),
    
    stats: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/search/stats'),
    
    suggestions: (query: string): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get(`/search/suggestions?q=${encodeURIComponent(query)}`),
  },

  // Admin endpoints
  admin: {
    executeSql: (data: SQLExecuteRequest): Promise<AxiosResponse<SQLExecuteResponse>> => 
      apiClient.post('/admin/sql/execute', data),
    
    getDatabaseSchema: (tableName?: string): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/admin/sql/schema', { params: { table_name: tableName } }),
    
    getSystemStats: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/admin/stats/system'),
    
    getAuditLogs: (params?: URLSearchParams): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/admin/logs', { params }),
    
    performMaintenance: (operation: string, params?: any): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.post('/admin/maintenance', { operation, parameters: params }),
    
    getHealth: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/admin/health'),
    
    exportData: (format: 'csv' | 'json', table?: string): Promise<AxiosResponse<Blob>> => 
      apiClient.get(`/admin/export?format=${format}&table=${table || ''}`, {
        responseType: 'blob'
      }),
  },

  // Health check
  health: (): Promise<AxiosResponse<ApiResponse>> => 
    apiClient.get('/health', { baseURL: API_BASE_URL.replace('/api', '') }),

  // Analytics endpoints
  analytics: {
    getOverview: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/analytics/overview'),
    
    getDocumentTrends: (period: 'week' | 'month' | 'year'): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get(`/analytics/documents/trends?period=${period}`),
    
    getComparisonMetrics: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/analytics/comparisons'),
    
    getSearchAnalytics: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/analytics/search'),
  },

  // User preferences (for future use)
  preferences: {
    get: (): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.get('/preferences'),
    
    update: (preferences: any): Promise<AxiosResponse<ApiResponse>> => 
      apiClient.put('/preferences', preferences),
  },
};

// Utility functions for API calls
export const apiUtils = {
  // Build query string from object
  buildQueryString: (params: Record<string, any>): string => {
    const urlParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        urlParams.append(key, String(value));
      }
    });
    return urlParams.toString();
  },

  // Handle file download
  downloadFile: (blob: Blob, filename: string): void => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  // Format file size
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // Format date
  formatDate: (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  // Validate file type
  isValidFileType: (file: File, allowedTypes: string[]): boolean => {
    const fileType = file.type;
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    return allowedTypes.some(type => 
      fileType === type || 
      (fileExtension && type.includes(fileExtension))
    );
  },

  // Check if file size is valid
  isValidFileSize: (file: File, maxSizeInMB: number): boolean => {
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
    return file.size <= maxSizeInBytes;
  },
};

// Export default client for direct use
export default apiClient;