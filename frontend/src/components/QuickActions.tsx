// # frontend/src/components/QuickActions.tsx
/**
 * DocuReview Pro - Quick Actions Component
 * Dashboard quick action buttons for common tasks
 */
import React from 'react';
import { Link } from 'react-router-dom';
import {
  Upload,
  GitCompare,
  Search,
  FileText,
  BarChart3,
  Settings,
  Zap,
  ArrowRight
} from 'lucide-react';

const QuickActions: React.FC = () => {
  const actions = [
    {
      name: 'Upload Document',
      description: 'Add a new document for analysis',
      href: '/documents/upload',
      icon: Upload,
      color: 'bg-blue-500 hover:bg-blue-600',
      textColor: 'text-white'
    },
    {
      name: 'Compare Documents',
      description: 'Compare different versions or documents',
      href: '/compare',
      icon: GitCompare,
      color: 'bg-green-500 hover:bg-green-600',
      textColor: 'text-white'
    },
    {
      name: 'Search Documents',
      description: 'Find documents using AI-powered search',
      href: '/search',
      icon: Search,
      color: 'bg-purple-500 hover:bg-purple-600',
      textColor: 'text-white'
    },
    {
      name: 'View All Documents',
      description: 'Browse your document library',
      href: '/documents',
      icon: FileText,
      color: 'bg-gray-100 hover:bg-gray-200',
      textColor: 'text-gray-900'
    },
    {
      name: 'Analytics',
      description: 'View usage and performance metrics',
      href: '/admin/stats',
      icon: BarChart3,
      color: 'bg-orange-100 hover:bg-orange-200',
      textColor: 'text-orange-900'
    },
    {
      name: 'Admin Panel',
      description: 'System administration and SQL queries',
      href: '/admin',
      icon: Settings,
      color: 'bg-gray-100 hover:bg-gray-200',
      textColor: 'text-gray-900'
    }
  ];

  return (
    <div className="card-enterprise">
      <div className="card-header flex items-center">
        <Zap className="h-5 w-5 text-blue-600 mr-2" />
        <h3 className="text-lg font-medium">Quick Actions</h3>
      </div>
      <div className="card-body">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.name}
                to={action.href}
                className={`group relative p-4 rounded-lg transition-all duration-200 ${action.color} ${action.textColor}`}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="ml-4 flex-1">
                    <h4 className="text-sm font-medium">{action.name}</h4>
                    <p className={`mt-1 text-xs ${
                      action.textColor === 'text-white' ? 'text-white/80' : 'text-gray-600'
                    }`}>
                      {action.description}
                    </p>
                  </div>
                  <ArrowRight className={`h-4 w-4 transition-transform group-hover:translate-x-1 ${
                    action.textColor === 'text-white' ? 'text-white/60' : 'text-gray-400'
                  }`} />
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default QuickActions;