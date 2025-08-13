// # frontend/src/types/index.ts
/**
 * DocuReview Pro - Type Definitions
 * Centralized type definitions for the application
 */

// Document Types
export interface Document {
  id: number;
  title: string;
  slug: string;
  version: number;
  created_at: string;
  updated_at: string;
  author?: string;
  domain?: string;
  tags?: string;
  status: 'pending' | 'analyzing' | 'analyzed' | 'error';
  bytes: number;
  checksum?: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  documents: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// User Types
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

// Search Types
export interface SearchResult {
  id: number;
  title: string;
  excerpt: string;
  relevance_score: number;
  created_at: string;
  author?: string;
  domain?: string;
}

// Comparison Types
export interface ComparisonResult {
  id: number;
  document_a_id: number;
  document_b_id: number;
  granularity: string;
  algorithm: string;
  similarity_score: number;
  changes: ComparisonChange[];
  created_at: string;
}

export interface ComparisonChange {
  type: 'addition' | 'deletion' | 'modification' | 'semantic';
  content: string;
  position: number;
  confidence: number;
}

// Admin Types
export interface SystemStats {
  application: {
    version: string;
    uptime_hours: number;
    environment: string;
  };
  database: {
    total_documents: number;
    total_chunks: number;
    size_mb: number;
  };
  system: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
  };
  storage: {
    total_size_mb: number;
    uploads_folder_size_mb: number;
  };
}

export interface SQLExecuteRequest {
  query: string;
  parameters?: any[];
  limit_results?: boolean;
  explain_plan?: boolean;
}

export interface SQLExecuteResponse {
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

// Analysis Types
export interface AnalysisResult {
  document_id: number;
  total_chunks: number;
  analyzed_chunks: number;
  unique_intents: number;
  entities_count: number;
  summary: string;
  analysis_time: number;
  created_at: string;
}

// Form Types
export interface UploadMetadata {
  title?: string;
  author?: string;
  domain?: string;
  tags?: string;
  notes?: string;
}

// Navigation Types
export interface NavigationItem {
  name: string;
  href: string;
  icon: string;
  current: boolean;
  children?: { name: string; href: string }[];
}

// Component Props Types
export interface StatCardProps {
  title: string;
  value: number | string;
  change?: number;
  changeLabel?: string;
  icon: React.ComponentType<any>;
  loading?: boolean;
  trend?: 'up' | 'down' | 'neutral';
}

export interface RecentDocumentsProps {
  documents: Document[];
  loading?: boolean;
}

// Utility Types
export type SortOrder = 'asc' | 'desc';
export type SortField = 'created_at' | 'updated_at' | 'title' | 'size';
export type FileStatus = 'pending' | 'uploading' | 'success' | 'error';
export type SearchType = 'semantic' | 'keyword';
export type DiffGranularity = 'character' | 'word' | 'sentence' | 'paragraph';
export type DiffAlgorithm = 'syntactic' | 'semantic' | 'hybrid';