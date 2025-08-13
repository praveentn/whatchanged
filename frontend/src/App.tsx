// # frontend/src/App.tsx
/**
 * DocuReview Pro - Main React Application
 * Enterprise Document Version Management & Analysis Frontend
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Layout components
import { Layout } from './components';

// Page components  
import {
  Dashboard,
  DocumentList,
  DocumentDetail,
  DocumentUpload,
  DocumentComparison,
  SearchPage,
  AdminPanel,
  AnalysisResults
} from './pages';

// Hooks and utilities
import { useAuth } from './hooks';

// Styles
import './index.css';

// Create React Query client with optimized configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (replaces cacheTime)
    },
    mutations: {
      retry: 1,
    },
  },
});

// Main App component
function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 font-medium">Loading DocuReview Pro...</p>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Main application routes */}
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              
              {/* Document management */}
              <Route path="documents" element={<DocumentList />} />
              <Route path="documents/upload" element={<DocumentUpload />} />
              <Route path="documents/:id" element={<DocumentDetail />} />
              <Route path="documents/:id/analysis" element={<AnalysisResults />} />
              
              {/* Document comparison */}
              <Route path="compare" element={<DocumentComparison />} />
              <Route path="compare/:slugA/:versionA/:slugB/:versionB" element={<DocumentComparison />} />
              
              {/* Search */}
              <Route path="search" element={<SearchPage />} />
              
              {/* Admin */}
              <Route path="admin" element={<AdminPanel />} />
              <Route path="admin/sql" element={<AdminPanel />} />
              <Route path="admin/logs" element={<AdminPanel />} />
              <Route path="admin/stats" element={<AdminPanel />} />
            </Route>
            
            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
        
        {/* Global notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              style: {
                background: '#10B981',
              },
            },
            error: {
              style: {
                background: '#EF4444',
              },
            },
          }}
        />
      </Router>
    </QueryClientProvider>
  );
}

export default App;