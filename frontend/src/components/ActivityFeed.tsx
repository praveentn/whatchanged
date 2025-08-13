// # frontend/src/components/ActivityFeed.tsx
/**
 * DocuReview Pro - Activity Feed Component
 * Display recent system activity and operations
 */
import React from 'react';
import { 
  FileText, 
  Upload, 
  GitCompare, 
  Search, 
  Clock,
  User,
  Activity as ActivityIcon
} from 'lucide-react';

interface ActivityItem {
  id: string;
  type: 'upload' | 'analysis' | 'comparison' | 'search';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
}

const ActivityFeed: React.FC = () => {
  // Mock activity data - in real app, this would come from an API
  const activities: ActivityItem[] = [
    {
      id: '1',
      type: 'upload',
      title: 'Document Uploaded',
      description: 'Requirements_v2.txt was uploaded and is being analyzed',
      timestamp: '2 minutes ago',
      user: 'John Doe'
    },
    {
      id: '2',
      type: 'comparison',
      title: 'Documents Compared',
      description: 'Compared API_Spec_v1.txt with API_Spec_v2.txt',
      timestamp: '15 minutes ago',
      user: 'Jane Smith'
    },
    {
      id: '3',
      type: 'analysis',
      title: 'Analysis Complete',
      description: 'Design_Document.txt analysis finished with 15 intent types found',
      timestamp: '1 hour ago'
    },
    {
      id: '4',
      type: 'search',
      title: 'Semantic Search',
      description: 'Search performed for "authentication requirements"',
      timestamp: '2 hours ago',
      user: 'Mike Johnson'
    }
  ];

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'upload':
        return <Upload className="h-4 w-4 text-blue-500" />;
      case 'analysis':
        return <ActivityIcon className="h-4 w-4 text-green-500" />;
      case 'comparison':
        return <GitCompare className="h-4 w-4 text-purple-500" />;
      case 'search':
        return <Search className="h-4 w-4 text-orange-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="card-enterprise">
      <div className="card-header">
        <h3 className="text-lg font-medium">Recent Activity</h3>
      </div>
      <div className="card-body">
        <div className="flow-root">
          <ul className="-mb-8">
            {activities.map((activity, index) => (
              <li key={activity.id}>
                <div className="relative pb-8">
                  {index !== activities.length - 1 && (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}
                  <div className="relative flex space-x-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100">
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex min-w-0 flex-1 justify-between space-x-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {activity.title}
                        </p>
                        <p className="text-sm text-gray-500">
                          {activity.description}
                        </p>
                        {activity.user && (
                          <div className="flex items-center mt-1 text-xs text-gray-400">
                            <User className="h-3 w-3 mr-1" />
                            {activity.user}
                          </div>
                        )}
                      </div>
                      <div className="whitespace-nowrap text-right text-sm text-gray-500">
                        <div className="flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {activity.timestamp}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
        
        {activities.length === 0 && (
          <div className="text-center py-8">
            <ActivityIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Recent Activity</h4>
            <p className="text-gray-600">Activity will appear here as you use the system</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityFeed;
