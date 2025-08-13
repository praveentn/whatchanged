// frontend/src/pages/DocumentComparison.tsx
/**
 * DocuReview Pro - Document Comparison Page
 * Compare document versions with advanced diff visualization
 */
import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  GitCompare,
  Settings,
  Download,
  Eye,
  EyeOff,
  RotateCcw,
  AlertTriangle
} from 'lucide-react';
import { apiService } from '@/services/api';

const DocumentComparison: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [diffConfig, setDiffConfig] = useState({
    granularity: 'word',
    algorithm: 'hybrid',
    showOnlyChanges: false
  });

  const docId = searchParams.get('doc');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <GitCompare className="h-8 w-8 mr-3 text-blue-600" />
            Document Comparison
          </h1>
          <p className="mt-2 text-gray-600">
            Compare document versions with AI-powered analysis
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button className="btn-secondary">
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </button>
          <button className="btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Document Selection */}
      <div className="card-enterprise">
        <div className="card-header">
          <h2 className="text-lg font-medium">Select Documents to Compare</h2>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="form-label">Document A</label>
              <select className="form-input">
                <option>Select document...</option>
              </select>
            </div>
            <div>
              <label className="form-label">Document B</label>
              <select className="form-input">
                <option>Select document...</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <button className="btn-primary">
              <GitCompare className="h-4 w-4 mr-2" />
              Compare Documents
            </button>
          </div>
        </div>
      </div>

      {/* Comparison Placeholder */}
      <div className="card-enterprise">
        <div className="card-body text-center py-12">
          <GitCompare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Document Comparison</h3>
          <p className="text-gray-600">Select two documents to see their differences</p>
        </div>
      </div>
    </div>
  );
};

export default DocumentComparison;