// # frontend/src/pages/AnalysisResults.tsx
/**
 * DocuReview Pro - Analysis Results Page
 * View detailed analysis results for a document
 */
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  FileText,
  TrendingUp,
  Users,
  Target,
  Clock,
  ArrowLeft,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { apiService } from '@/services/api';

const AnalysisResults: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => apiService.documents.getAnalysis(Number(id)),
    enabled: !!id
  });

  if (isLoading) {
    return (
      <div className="min-h-96 flex items-center justify-center">
        <div className="flex items-center">
          <RefreshCw className="h-6 w-6 animate-spin mr-3" />
          Loading analysis results...
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Analysis Not Available</h3>
        <p className="text-gray-600 mb-4">
          Analysis results could not be loaded for this document.
        </p>
        <Link to={`/documents/${id}`} className="btn-primary">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Document
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to={`/documents/${id}`} className="btn-secondary">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <BarChart3 className="h-7 w-7 mr-2 text-blue-600" />
              Analysis Results
            </h1>
            <p className="text-gray-600">
              Detailed AI analysis for document {analysis.data?.document_title || id}
            </p>
          </div>
        </div>
      </div>

      {/* Analysis Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card-enterprise">
          <div className="card-body text-center">
            <FileText className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              {analysis.data?.total_chunks || 0}
            </div>
            <div className="text-gray-600">Content Chunks</div>
          </div>
        </div>
        
        <div className="card-enterprise">
          <div className="card-body text-center">
            <Target className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              {analysis.data?.unique_intents || 0}
            </div>
            <div className="text-gray-600">Intent Types</div>
          </div>
        </div>
        
        <div className="card-enterprise">
          <div className="card-body text-center">
            <Users className="h-8 w-8 text-purple-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              {analysis.data?.entities_count || 0}
            </div>
            <div className="text-gray-600">Entities Found</div>
          </div>
        </div>
        
        <div className="card-enterprise">
          <div className="card-body text-center">
            <Clock className="h-8 w-8 text-orange-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              {analysis.data?.analysis_time || '0'}s
            </div>
            <div className="text-gray-600">Analysis Time</div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intent Distribution */}
        <div className="card-enterprise">
          <div className="card-header">
            <h3 className="text-lg font-medium">Intent Distribution</h3>
          </div>
          <div className="card-body">
            <div className="text-center py-8 text-gray-500">
              Intent analysis visualization will be displayed here
            </div>
          </div>
        </div>

        {/* Key Entities */}
        <div className="card-enterprise">
          <div className="card-header">
            <h3 className="text-lg font-medium">Key Entities</h3>
          </div>
          <div className="card-body">
            <div className="text-center py-8 text-gray-500">
              Entity extraction results will be displayed here
            </div>
          </div>
        </div>
      </div>

      {/* Document Summary */}
      <div className="card-enterprise">
        <div className="card-header">
          <h3 className="text-lg font-medium">AI-Generated Summary</h3>
        </div>
        <div className="card-body">
          <div className="prose max-w-none">
            <p className="text-gray-600">
              {analysis.data?.summary || 'Document summary will be generated here using AI analysis.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults;