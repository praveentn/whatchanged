// # frontend/src/pages/DocumentUpload.tsx
/**
 * DocuReview Pro - Document Upload Page
 * Upload and process new documents
 */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader,
  Plus
} from 'lucide-react';
import { apiService } from '@/services/api';

interface UploadedFile {
  file: File;
  preview?: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress?: number;
  error?: string;
  documentId?: number;
}

const DocumentUpload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [metadata, setMetadata] = useState({
    title: '',
    author: '',
    domain: '',
    tags: '',
    notes: ''
  });
  
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (uploadData: { file: File; metadata: any }) => {
      const formData = new FormData();
      formData.append('file', uploadData.file);
      
      // Add metadata
      Object.entries(uploadData.metadata).forEach(([key, value]) => {
        if (value) formData.append(key, value as string);
      });

      return apiService.documents.upload(formData);
    },
    onSuccess: (data, variables) => {
      const fileIndex = files.findIndex(f => f.file === variables.file);
      if (fileIndex >= 0) {
        setFiles(prev => prev.map((f, i) => 
          i === fileIndex 
            ? { ...f, status: 'success', documentId: data.data.id }
            : f
        ));
      }
      
      toast.success('Document uploaded successfully!');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error: any, variables) => {
      const fileIndex = files.findIndex(f => f.file === variables.file);
      if (fileIndex >= 0) {
        setFiles(prev => prev.map((f, i) => 
          i === fileIndex 
            ? { ...f, status: 'error', error: error.message }
            : f
        ));
      }
      
      toast.error(`Upload failed: ${error.message}`);
    }
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      file,
      status: 'pending',
      preview: file.type.startsWith('text/') ? URL.createObjectURL(file) : undefined
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 5 * 1024 * 1024, // 5MB
    multiple: true
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    for (const fileItem of pendingFiles) {
      const fileIndex = files.findIndex(f => f.file === fileItem.file);
      
      // Update status to uploading
      setFiles(prev => prev.map((f, i) => 
        i === fileIndex ? { ...f, status: 'uploading' } : f
      ));

      try {
        await uploadMutation.mutateAsync({
          file: fileItem.file,
          metadata: {
            ...metadata,
            title: metadata.title || fileItem.file.name.replace(/\.[^/.]+$/, '')
          }
        });
      } catch (error) {
        // Error handling is done in onError callback
      }
    }
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending':
        return <FileText className="h-5 w-5 text-gray-400" />;
      case 'uploading':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const allFilesProcessed = files.length > 0 && files.every(f => f.status === 'success' || f.status === 'error');
  const hasSuccessfulUploads = files.some(f => f.status === 'success');

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Documents</h1>
        <p className="mt-2 text-gray-600">
          Upload text documents for analysis and version management
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Drop Zone */}
          <div className="card-enterprise">
            <div className="card-body">
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                
                {isDragActive ? (
                  <p className="text-lg text-blue-600 font-medium">
                    Drop the files here...
                  </p>
                ) : (
                  <div>
                    <p className="text-lg text-gray-900 font-medium mb-2">
                      Drag and drop files here, or click to select
                    </p>
                    <p className="text-gray-500">
                      Supports .txt, .md, .pdf, .doc, .docx files up to 5MB
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="card-enterprise">
              <div className="card-header flex items-center justify-between">
                <h3 className="text-lg font-medium">Files to Upload</h3>
                <span className="text-sm text-gray-500">
                  {files.length} file{files.length !== 1 ? 's' : ''}
                </span>
              </div>
              <div className="card-body">
                <div className="space-y-3">
                  {files.map((fileItem, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(fileItem.status)}
                        <div>
                          <p className="font-medium text-gray-900">
                            {fileItem.file.name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {(fileItem.file.size / 1024).toFixed(1)} KB
                          </p>
                          {fileItem.error && (
                            <p className="text-sm text-red-600">{fileItem.error}</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {fileItem.status === 'success' && fileItem.documentId && (
                          <button
                            onClick={() => navigate(`/documents/${fileItem.documentId}`)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            View Document
                          </button>
                        )}
                        <button
                          onClick={() => removeFile(index)}
                          disabled={fileItem.status === 'uploading'}
                          className="text-gray-400 hover:text-red-500 disabled:opacity-50"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Upload Button */}
                <div className="mt-6 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    {files.filter(f => f.status === 'pending').length} pending uploads
                  </div>
                  <div className="space-x-3">
                    {allFilesProcessed && hasSuccessfulUploads && (
                      <button
                        onClick={() => navigate('/documents')}
                        className="btn-secondary"
                      >
                        View All Documents
                      </button>
                    )}
                    <button
                      onClick={uploadFiles}
                      disabled={uploadMutation.isPending || files.every(f => f.status !== 'pending')}
                      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {uploadMutation.isPending ? (
                        <>
                          <Loader className="h-4 w-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          Upload Files
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Metadata Sidebar */}
        <div className="space-y-6">
          <div className="card-enterprise">
            <div className="card-header">
              <h3 className="text-lg font-medium">Document Metadata</h3>
            </div>
            <div className="card-body space-y-4">
              <div>
                <label className="form-label">Title</label>
                <input
                  type="text"
                  value={metadata.title}
                  onChange={(e) => setMetadata(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Auto-generated from filename"
                  className="form-input"
                />
                <p className="form-help">Leave empty to use filename</p>
              </div>

              <div>
                <label className="form-label">Author</label>
                <input
                  type="text"
                  value={metadata.author}
                  onChange={(e) => setMetadata(prev => ({ ...prev, author: e.target.value }))}
                  placeholder="Document author"
                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Domain</label>
                <input
                  type="text"
                  value={metadata.domain}
                  onChange={(e) => setMetadata(prev => ({ ...prev, domain: e.target.value }))}
                  placeholder="e.g., Legal, Technical, Marketing"
                  className="form-input"
                />
              </div>

              <div>
                <label className="form-label">Tags</label>
                <input
                  type="text"
                  value={metadata.tags}
                  onChange={(e) => setMetadata(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="Comma-separated tags"
                  className="form-input"
                />
                <p className="form-help">Separate tags with commas</p>
              </div>

              <div>
                <label className="form-label">Notes</label>
                <textarea
                  value={metadata.notes}
                  onChange={(e) => setMetadata(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Additional notes about this document..."
                  rows={3}
                  className="form-input"
                />
              </div>
            </div>
          </div>

          {/* Upload Tips */}
          <div className="card-enterprise">
            <div className="card-header">
              <h3 className="text-lg font-medium">Upload Tips</h3>
            </div>
            <div className="card-body">
              <ul className="text-sm text-gray-600 space-y-2">
                <li>• Supported formats: TXT, MD, PDF, DOC, DOCX</li>
                <li>• Maximum file size: 5MB</li>
                <li>• Documents are automatically analyzed</li>
                <li>• Version history is maintained</li>
                <li>• Metadata helps with organization</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;