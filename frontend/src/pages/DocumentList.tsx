// # frontend/src/pages/DocumentList.tsx
/**
 * DocuReview Pro - Document List Page
 * Browse and manage all documents
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  FileText,
  Search,
  Filter,
  Upload,
  Eye,
  GitCompare,
  MoreVertical,
  Calendar,
  User,
  Tag,
  ChevronDown,
  ChevronUp,
  RefreshCw
} from 'lucide-react';
import { apiService } from '@/services/api';

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
}

const DocumentList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'title'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['documents', { page, limit, search: searchTerm, domain: selectedDomain, sortBy, sortOrder }],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (selectedDomain) params.append('domain', selectedDomain);
      
      const response = await apiService.documents.list(params);
      return response.data;
    }
  });

  const documents: Document[] = data?.documents || [];
  const totalCount = data?.total || 0;
  const totalPages = Math.ceil(totalCount / limit);

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSortIcon = (field: typeof sortBy) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? 
      <ChevronUp className="h-4 w-4" /> : 
      <ChevronDown className="h-4 w-4" />;
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Documents</h3>
        <p className="text-gray-600 mb-4">Failed to load documents. Please try again.</p>
        <button onClick={() => refetch()} className="btn-primary">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="mt-2 text-gray-600">
            Manage your document library and version history
          </p>
        </div>
        <Link to="/documents/upload" className="btn-primary">
          <Upload className="h-4 w-4 mr-2" />
          Upload Document
        </Link>
      </div>

      {/* Filters and Search */}
      <div className="card-enterprise">
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search documents..."
                  className="form-input pl-10"
                />
              </div>
            </div>

            {/* Domain Filter */}
            <div>
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="form-input"
              >
                <option value="">All Domains</option>
                <option value="Technical">Technical</option>
                <option value="Legal">Legal</option>
                <option value="Marketing">Marketing</option>
                <option value="Business">Business</option>
              </select>
            </div>

            {/* Sort */}
            <div>
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field as typeof sortBy);
                  setSortOrder(order as typeof sortOrder);
                }}
                className="form-input"
              >
                <option value="updated_at-desc">Recently Updated</option>
                <option value="created_at-desc">Recently Created</option>
                <option value="title-asc">Title A-Z</option>
                <option value="title-desc">Title Z-A</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <div>
          Showing {documents.length} of {totalCount} documents
        </div>
        <div className="flex items-center space-x-4">
          <span>Page {page} of {totalPages}</span>
          <div className="flex space-x-1">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary text-sm py-1 px-2 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary text-sm py-1 px-2 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Document Table */}
      <div className="card-enterprise">
        <div className="overflow-x-auto">
          <table className="table-enterprise">
            <thead className="table-header">
              <tr>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('title')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Title</span>
                    {getSortIcon('title')}
                  </div>
                </th>
                <th>Version</th>
                <th>Domain</th>
                <th>Author</th>
                <th>Size</th>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('updated_at')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Last Updated</span>
                    {getSortIcon('updated_at')}
                  </div>
                </th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody className="table-body">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="text-center py-12">
                    <div className="flex items-center justify-center">
                      <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                      Loading documents...
                    </div>
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Documents Found</h3>
                    <p className="text-gray-600 mb-4">
                      {searchTerm || selectedDomain ? 'No documents match your filters.' : 'Get started by uploading your first document.'}
                    </p>
                    <Link to="/documents/upload" className="btn-primary">
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Document
                    </Link>
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td>
                      <div className="flex items-center space-x-3">
                        <FileText className="h-5 w-5 text-gray-400" />
                        <div>
                          <Link
                            to={`/documents/${doc.id}`}
                            className="font-medium text-blue-600 hover:text-blue-800"
                          >
                            {doc.title}
                          </Link>
                          {doc.tags && (
                            <div className="flex items-center mt-1 space-x-1">
                              <Tag className="h-3 w-3 text-gray-400" />
                              <span className="text-xs text-gray-500">{doc.tags}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge-info">v{doc.version}</span>
                    </td>
                    <td>
                      {doc.domain ? (
                        <span className="badge-gray">{doc.domain}</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td>
                      {doc.author ? (
                        <div className="flex items-center space-x-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="text-sm">{doc.author}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="text-sm text-gray-600">
                      {formatFileSize(doc.bytes)}
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          {formatDate(doc.updated_at)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${
                        doc.status === 'analyzed' ? 'badge-success' :
                        doc.status === 'analyzing' ? 'badge-warning' :
                        doc.status === 'error' ? 'badge-error' : 'badge-gray'
                      }`}>
                        {doc.status}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="text-blue-600 hover:text-blue-800"
                          title="View Document"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                        <Link
                          to={`/compare?doc=${doc.id}`}
                          className="text-green-600 hover:text-green-800"
                          title="Compare Versions"
                        >
                          <GitCompare className="h-4 w-4" />
                        </Link>
                        <button
                          className="text-gray-400 hover:text-gray-600"
                          title="More Actions"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {(page - 1) * limit + 1} to {Math.min(page * limit, totalCount)} of {totalCount} results
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(1)}
              disabled={page === 1}
              className="btn-secondary text-sm py-1 px-3 disabled:opacity-50"
            >
              First
            </button>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary text-sm py-1 px-3 disabled:opacity-50"
            >
              Previous
            </button>
            
            {/* Page Numbers */}
            <div className="flex space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`px-3 py-1 text-sm rounded ${
                      page === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary text-sm py-1 px-3 disabled:opacity-50"
            >
              Next
            </button>
            <button
              onClick={() => setPage(totalPages)}
              disabled={page === totalPages}
              className="btn-secondary text-sm py-1 px-3 disabled:opacity-50"
            >
              Last
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentList;