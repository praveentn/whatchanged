// # frontend/src/pages/SearchPage.tsx
/**
 * DocuReview Pro - Search Page
 * Advanced document search with semantic capabilities
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  FileText,
  Clock,
  User,
  Tag,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { apiService } from '@/services/api';

const SearchPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState<'semantic' | 'keyword'>('semantic');
  const [filters, setFilters] = useState({
    domain: '',
    author: '',
    dateRange: ''
  });

  const { data: searchResults, isLoading, error } = useQuery({
    queryKey: ['search', searchTerm, searchType, filters],
    queryFn: async () => {
      if (!searchTerm.trim()) return null;
      
      const response = await apiService.search.documents({
        query: searchTerm,
        search_type: searchType,
        ...filters
      });
      return response.data;
    },
    enabled: !!searchTerm.trim()
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Search is triggered automatically by React Query
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Search className="h-8 w-8 mr-3 text-blue-600" />
          Search Documents
        </h1>
        <p className="mt-2 text-gray-600">
          Find documents using AI-powered semantic search or traditional keyword search
        </p>
      </div>

      {/* Search Form */}
      <div className="card-enterprise">
        <div className="card-body">
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Main Search */}
            <div className="flex space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search for documents, content, or concepts..."
                    className="form-input pl-10 text-lg"
                  />
                </div>
              </div>
              <button type="submit" className="btn-primary px-8">
                Search
              </button>
            </div>

            {/* Search Options */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="form-label">Search Type</label>
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value as 'semantic' | 'keyword')}
                  className="form-input"
                >
                  <option value="semantic">Semantic Search</option>
                  <option value="keyword">Keyword Search</option>
                </select>
              </div>
              <div>
                <label className="form-label">Domain</label>
                <select
                  value={filters.domain}
                  onChange={(e) => setFilters(prev => ({ ...prev, domain: e.target.value }))}
                  className="form-input"
                >
                  <option value="">All Domains</option>
                  <option value="Technical">Technical</option>
                  <option value="Legal">Legal</option>
                  <option value="Marketing">Marketing</option>
                </select>
              </div>
              <div>
                <label className="form-label">Author</label>
                <input
                  type="text"
                  value={filters.author}
                  onChange={(e) => setFilters(prev => ({ ...prev, author: e.target.value }))}
                  placeholder="Author name..."
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Date Range</label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                  className="form-input"
                >
                  <option value="">Any Time</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                  <option value="90d">Last 90 Days</option>
                </select>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Search Results */}
      <div className="card-enterprise">
        <div className="card-body">
          {!searchTerm ? (
            <div className="text-center py-12">
              <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start Your Search</h3>
              <p className="text-gray-600">
                Enter a search term to find relevant documents and content
              </p>
            </div>
          ) : isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Searching documents...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Search Error</h3>
              <p className="text-gray-600">Failed to search documents. Please try again.</p>
            </div>
          ) : !searchResults || searchResults.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
              <p className="text-gray-600">
                No documents match your search criteria. Try different keywords or filters.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                Found {searchResults.length} results for "{searchTerm}"
              </div>
              
              {searchResults.map((result: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-blue-600 hover:text-blue-800">
                        {result.title}
                      </h3>
                      <p className="text-gray-600 mt-1 line-clamp-2">
                        {result.excerpt || 'No excerpt available'}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-1" />
                          {result.author || 'Unknown'}
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {new Date(result.created_at).toLocaleDateString()}
                        </div>
                        {result.domain && (
                          <div className="flex items-center">
                            <Tag className="h-4 w-4 mr-1" />
                            {result.domain}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      {result.relevance_score && (
                        <div className="text-sm text-gray-500">
                          {Math.round(result.relevance_score * 100)}% match
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;