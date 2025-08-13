// # frontend/src/hooks/useAuth.ts
/**
 * DocuReview Pro - Authentication Hook
 * Simple auth hook for future authentication implementation
 */
import { useState, useEffect } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export const useAuth = (): AuthState => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false
  });

  useEffect(() => {
    // For now, we'll simulate a logged-in admin user
    // In the future, this would check for actual authentication tokens
    const mockUser: User = {
      id: '1',
      name: 'System Administrator',
      email: 'admin@docureview.pro',
      role: 'admin'
    };

    // Simulate loading delay
    const timer = setTimeout(() => {
      setAuthState({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true
      });
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  return authState;
};