// # frontend/src/components/RecentDocuments.tsx
/**
 * DocuReview Pro - Recent Documents Component
 * Display recently uploaded/updated documents
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Clock, Eye, GitCompare, ArrowRight } from 'lucide-react';

interface Document {
  id: number;
  title: string;
  version: number;
  updated_at: string;
  status: string;
  author?: string;
}

interface RecentDocumentsProps {
  documents: Document[];
  loading?: boolean;
}

const RecentDocuments: React.FC<RecentDocumentsProps> = ({ documents, loading = false }) => {
  if (loading) {
    return (
      <div className="card-enterprise">
        <div className="card-header">
          <h3 className="text-lg font-medium">Recent Documents</h3>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex items-center space-x-4">
                <div className="w-8 h-8 bg-gray-200 rounded"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-enterprise">
      <div className="card-header flex items-center justify-between">
        <h3 className="text-lg font-medium">Recent Documents</h3>
        <Link to="/documents" className="text-sm text-blue-600 hover:text-blue-800 flex items-center">
          View all <ArrowRight className="h-4 w-4 ml-1" />
        </Link>
      </div>
      <div className="card-body">
        {documents.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Documents Yet</h4>
            <p className="text-gray-600 mb-4">Upload your first document to get started</p>
            <Link to="/documents/upload" className="btn-primary">
              Upload Document
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div>
                    <Link to={`/documents/${doc.id}`} className="font-medium text-gray-900 hover:text-blue-600">
                      {doc.title}
                    </Link>
                    <div className="flex items-center space-x-3 text-sm text-gray-500">
                      <span>v{doc.version}</span>
                      <div className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {new Date(doc.updated_at).toLocaleDateString()}
                      </div>
                      {doc.author && <span>by {doc.author}</span>}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`badge ${
                    doc.status === 'analyzed' ? 'badge-success' :
                    doc.status === 'analyzing' ? 'badge-warning' : 'badge-gray'
                  }`}>
                    {doc.status}
                  </span>
                  <div className="flex space-x-1">
                    <Link to={`/documents/${doc.id}`} className="text-gray-400 hover:text-blue-600">
                      <Eye className="h-4 w-4" />
                    </Link>
                    <Link to={`/compare?doc=${doc.id}`} className="text-gray-400 hover:text-green-600">
                      <GitCompare className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentDocuments;

