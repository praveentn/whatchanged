// # frontend/src/pages/DocumentDetail.tsx
/**
 * DocuReview Pro - Document Detail Page
 * View and manage individual document details
 */
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  FileText, 
  Clock, 
  User, 
  GitCompare, 
  Download, 
  Edit,
  ArrowLeft,
  BarChart3,
  AlertTriangle
} from 'lucide-react';
import { apiService } from '@/services/api';

const DocumentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', id],
    queryFn: () => apiService.documents.get(Number(id)),
    enabled: !!id
  });

  if (isLoading) {
    return (
      <div className="min-h-96 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Document Not Found</h3>
        <p className="text-gray-600 mb-4">The requested document could not be found.</p>
        <Link to="/documents" className="btn-primary">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Documents
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/documents" className="btn-secondary">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{document.data.title}</h1>
            <p className="text-gray-600">Version {document.data.version}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <Link to={`/documents/${id}/analysis`} className="btn-secondary">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analysis
          </Link>
          <button className="btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            Download
          </button>
          <button className="btn-primary">
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </button>
        </div>
      </div>

      {/* Document Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card-enterprise">
            <div className="card-header">
              <h2 className="text-lg font-medium">Document Content</h2>
            </div>
            <div className="card-body">
              <div className="prose max-w-none">
                <p className="text-gray-600">Document content will be displayed here...</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          {/* Metadata */}
          <div className="card-enterprise">
            <div className="card-header">
              <h3 className="text-lg font-medium">Metadata</h3>
            </div>
            <div className="card-body space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Created</span>
                <span className="font-medium">
                  {new Date(document.data.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Updated</span>
                <span className="font-medium">
                  {new Date(document.data.updated_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Size</span>
                <span className="font-medium">{document.data.bytes} bytes</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status</span>
                <span className="badge-success">{document.data.status}</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card-enterprise">
            <div className="card-header">
              <h3 className="text-lg font-medium">Quick Actions</h3>
            </div>
            <div className="card-body space-y-2">
              <Link to={`/compare?doc=${id}`} className="w-full btn-secondary text-left">
                <GitCompare className="h-4 w-4 mr-2" />
                Compare Versions
              </Link>
              <button className="w-full btn-secondary text-left">
                <FileText className="h-4 w-4 mr-2" />
                View Raw Content
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentDetail;