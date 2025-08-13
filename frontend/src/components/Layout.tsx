// frontend/src/components/Layout.tsx
/**
 * DocuReview Pro - Main Layout Component
 * Enterprise layout with sidebar navigation and header
 */
import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { 
  FileText, 
  GitCompare, 
  Search, 
  Upload, 
  BarChart3, 
  Settings,
  Menu,
  X,
  Home,
  Database
} from 'lucide-react';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {}

const Layout: React.FC<LayoutProps> = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Navigation items configuration
  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: Home,
      current: false,
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: FileText,
      current: false,
      children: [
        { name: 'All Documents', href: '/documents' },
        { name: 'Upload New', href: '/documents/upload' },
      ],
    },
    {
      name: 'Compare',
      href: '/compare',
      icon: GitCompare,
      current: false,
    },
    {
      name: 'Search',
      href: '/search',
      icon: Search,
      current: false,
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
      current: false,
    },
    {
      name: 'Admin',
      href: '/admin',
      icon: Database,
      current: false,
      children: [
        { name: 'SQL Executor', href: '/admin/sql' },
        { name: 'System Logs', href: '/admin/logs' },
        { name: 'Statistics', href: '/admin/stats' },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
        </div>
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar 
          navigationItems={navigationItems}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      {/* Main content area */}
      <div className="lg:pl-64 flex flex-col flex-1 min-h-screen">
        {/* Header */}
        <Header 
          onMenuClick={() => setSidebarOpen(true)}
          sidebarOpen={sidebarOpen}
        />
        
        {/* Page content */}
        <main className="flex-1 pb-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Outlet />
          </div>
        </main>
        
        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 py-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center text-sm text-gray-500">
              <div>
                <span className="font-medium text-gray-900">DocuReview Pro</span>
                <span className="ml-2">v1.0.0</span>
              </div>
              <div className="flex space-x-6">
                <a href="#" className="hover:text-gray-700">Documentation</a>
                <a href="#" className="hover:text-gray-700">Support</a>
                <a href="#" className="hover:text-gray-700">API</a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Layout;