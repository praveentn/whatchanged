// frontend/src/components/UtilityComponents.tsx
/**
 * DocuReview Pro - Utility Components
 * Collection of reusable UI components
 */
import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Loader2,
  AlertCircle,
  CheckCircle,
  Info,
  Upload,
  FileText,
  Search,
  GitCompare,
  BarChart3,
  Clock,
  Users,
  Activity
} from 'lucide-react';
import clsx from 'clsx';

// Loading Spinner Component
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <Loader2 
      className={clsx(
        'animate-spin text-blue-600',
        sizeClasses[size],
        className
      )} 
    />
  );
};

// Stat Card Component
interface StatCardProps {
  title: string;
  value: number | string;
  change?: number;
  changeLabel?: string;
  icon: React.ComponentType<any>;
  loading?: boolean;
  trend?: 'up' | 'down' | 'neutral';
  format?: 'number' | 'percentage' | 'bytes';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  loading = false,
  trend = 'neutral',
  format = 'number'
}) => {
  const formatValue = (val: number | string) => {
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'percentage':
        return `${val.toFixed(1)}%`;
      case 'bytes':
        return `${val.toFixed(1)} MB`;
      default:
        return val.toLocaleString();
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {loading ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    formatValue(value)
                  )}
                </div>
                {change !== undefined && changeLabel && !loading && (
                  <div className="ml-2 flex items-baseline text-sm">
                    {getTrendIcon()}
                    <span className="ml-1 text-gray-600">
                      {change} {changeLabel}
                    </span>
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

// Alert Component
interface AlertProps {
  type: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  onDismiss?: () => void;
}

export const Alert: React.FC<AlertProps> = ({ 
  type, 
  title, 
  children, 
  onDismiss 
}) => {
  const styles = {
    info: {
      container: 'bg-blue-50 border-blue-200',
      icon: 'text-blue-600',
      title: 'text-blue-800',
      text: 'text-blue-700',
      Icon: Info,
    },
    success: {
      container: 'bg-green-50 border-green-200',
      icon: 'text-green-600',
      title: 'text-green-800',
      text: 'text-green-700',
      Icon: CheckCircle,
    },
    warning: {
      container: 'bg-yellow-50 border-yellow-200',
      icon: 'text-yellow-600',
      title: 'text-yellow-800',
      text: 'text-yellow-700',
      Icon: AlertCircle,
    },
    error: {
      container: 'bg-red-50 border-red-200',
      icon: 'text-red-600',
      title: 'text-red-800',
      text: 'text-red-700',
      Icon: AlertCircle,
    },
  };

  const style = styles[type];
  const { Icon } = style;

  return (
    <div className={clsx('border rounded-lg p-4', style.container)}>
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={clsx('h-5 w-5', style.icon)} />
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={clsx('text-sm font-medium', style.title)}>
              {title}
            </h3>
          )}
          <div className={clsx('text-sm', title ? 'mt-2' : '', style.text)}>
            {children}
          </div>
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <button
              onClick={onDismiss}
              className={clsx(
                'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2',
                style.icon,
                'hover:bg-opacity-20'
              )}
            >
              <span className="sr-only">Dismiss</span>
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Empty State Component
interface EmptyStateProps {
  icon: React.ComponentType<any>;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action
}) => {
  return (
    <div className="text-center py-12">
      <Icon className="mx-auto h-12 w-12 text-gray-400" />
      <h3 className="mt-2 text-sm font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-500">{description}</p>
      {action && (
        <div className="mt-6">
          <button
            onClick={action.onClick}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {action.label}
          </button>
        </div>
      )}
    </div>
  );
};

// Quick Actions Component
export const QuickActions: React.FC = () => {
  const actions = [
    {
      name: 'Upload Document',
      description: 'Add a new document for analysis',
      icon: Upload,
      href: '/documents/upload',
      color: 'bg-blue-500',
    },
    {
      name: 'Compare Versions',
      description: 'Compare different document versions',
      icon: GitCompare,
      href: '/compare',
      color: 'bg-green-500',
    },
    {
      name: 'Search Content',
      description: 'Find documents and content',
      icon: Search,
      href: '/search',
      color: 'bg-purple-500',
    },
    {
      name: 'View Analytics',
      description: 'Analyze document trends and metrics',
      icon: BarChart3,
      href: '/analytics',
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <a
              key={action.name}
              href={action.href}
              className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-blue-500 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
            >
              <div>
                <span className={clsx(
                  'rounded-lg inline-flex p-3 ring-4 ring-white',
                  action.color
                )}>
                  <Icon className="h-6 w-6 text-white" />
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium text-gray-900">
                  <span className="absolute inset-0" />
                  {action.name}
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  {action.description}
                </p>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
};

// Recent Documents Component
interface RecentDocumentsProps {
  documents: any[];
  loading: boolean;
}

export const RecentDocuments: React.FC<RecentDocumentsProps> = ({ 
  documents, 
  loading 
}) => {
  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Documents</h3>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse flex space-x-4">
              <div className="rounded-full bg-gray-300 h-10 w-10"></div>
              <div className="flex-1 space-y-2 py-1">
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                <div className="h-3 bg-gray-300 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Recent Documents</h3>
        <a href="/documents" className="text-sm text-blue-600 hover:text-blue-700">
          View all
        </a>
      </div>
      
      {documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload your first document to get started with analysis."
          action={{
            label: "Upload Document",
            onClick: () => window.location.href = '/documents/upload'
          }}
        />
      ) : (
        <div className="flow-root">
          <ul className="-my-5 divide-y divide-gray-200">
            {documents.slice(0, 5).map((doc) => (
              <li key={doc.id} className="py-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                      <FileText className="h-6 w-6 text-blue-600" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {doc.title}
                    </p>
                    <p className="text-sm text-gray-500">
                      Version {doc.version} • {doc.status} • {doc.bytes} bytes
                    </p>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <time dateTime={doc.updated_at}>
                      {new Date(doc.updated_at).toLocaleDateString()}
                    </time>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Activity Feed Component
export const ActivityFeed: React.FC = () => {
  const activities = [
    {
      id: 1,
      type: 'upload',
      title: 'Document uploaded',
      description: 'API Documentation v2.1',
      time: '2 minutes ago',
      icon: Upload,
      iconBackground: 'bg-blue-500',
    },
    {
      id: 2,
      type: 'analysis',
      title: 'Analysis completed',
      description: 'Requirements Document v1.0',
      time: '15 minutes ago',
      icon: Activity,
      iconBackground: 'bg-green-500',
    },
    {
      id: 3,
      type: 'comparison',
      title: 'Comparison generated',
      description: 'v1.0 vs v1.1 comparison',
      time: '1 hour ago',
      icon: GitCompare,
      iconBackground: 'bg-purple-500',
    },
    {
      id: 4,
      type: 'user',
      title: 'User joined',
      description: 'john.doe@company.com',
      time: '2 hours ago',
      icon: Users,
      iconBackground: 'bg-orange-500',
    },
  ];

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
      <div className="flow-root">
        <ul className="-mb-8">
          {activities.map((activity, activityIdx) => (
            <li key={activity.id}>
              <div className="relative pb-8">
                {activityIdx !== activities.length - 1 ? (
                  <span
                    className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                ) : null}
                <div className="relative flex items-start space-x-3">
                  <div className="relative">
                    <span
                      className={clsx(
                        activity.iconBackground,
                        'h-10 w-10 rounded-full flex items-center justify-center ring-8 ring-white'
                      )}
                    >
                      <activity.icon className="h-5 w-5 text-white" />
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {activity.title}
                      </p>
                      <p className="text-sm text-gray-500">
                        {activity.description}
                      </p>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      <time>{activity.time}</time>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Simple Analytics Chart Component
interface AnalyticsChartProps {
  data: Array<{ date: string; uploads: number; analyses: number }>;
  height?: number;
}

export const AnalyticsChart: React.FC<AnalyticsChartProps> = ({ 
  data, 
  height = 200 
}) => {
  // This is a simplified placeholder - in a real app you'd use a proper charting library
  return (
    <div className="w-full" style={{ height }}>
      <div className="flex items-end justify-between h-full space-x-2">
        {data.map((item, index) => {
          const maxValue = Math.max(...data.map(d => Math.max(d.uploads, d.analyses)));
          const uploadHeight = (item.uploads / maxValue) * (height - 40);
          const analysisHeight = (item.analyses / maxValue) * (height - 40);
          
          return (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div className="w-full flex justify-center space-x-1 mb-2">
                <div
                  className="bg-blue-500 rounded-t"
                  style={{ height: uploadHeight, width: '40%' }}
                  title={`Uploads: ${item.uploads}`}
                />
                <div
                  className="bg-green-500 rounded-t"
                  style={{ height: analysisHeight, width: '40%' }}
                  title={`Analyses: ${item.analyses}`}
                />
              </div>
              <div className="text-xs text-gray-500 text-center">
                {new Date(item.date).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric' 
                })}
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex justify-center space-x-4 mt-4 text-sm">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
          <span className="text-gray-600">Uploads</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
          <span className="text-gray-600">Analyses</span>
        </div>
      </div>
    </div>
  );
};

export default {
  LoadingSpinner,
  StatCard,
  Alert,
  EmptyState,
  QuickActions,
  RecentDocuments,
  ActivityFeed,
  AnalyticsChart,
};