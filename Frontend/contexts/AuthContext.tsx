/**
 * Authentication Context
 * Provides global authentication state and methods
 */

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import authService, { User, LoginRequest, RegisterRequest, AuthResponse } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<AuthResponse>;
  register: (data: RegisterRequest) => Promise<AuthResponse>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = authService.getToken();
        const storedUser = authService.getUser();

        if (token && storedUser) {
          // Set stored user immediately to prevent redirect
          setUser(storedUser);

          // Try to refresh user data from API in background
          try {
            const currentUser = await authService.getCurrentUser();
            setUser(currentUser);
          } catch (error) {
            // Keep using stored user
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        authService.logout();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (data: LoginRequest): Promise<AuthResponse> => {
    try {
      const response = await authService.login(data);

      setUser(response.user);

      // Sync token to cookies for middleware
      if (typeof document !== 'undefined') {
        // Set cookie without explicit domain - browser automatically scopes to current hostname
        // This works for both localhost and 10.0.0.1
        const cookieString = `nlpforge_access_token=${response.access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
        document.cookie = cookieString;

        // Verify cookie was set
        const cookies = document.cookie.split(';').map(c => c.trim());
        const tokenCookie = cookies.find(c => c.startsWith('nlpforge_access_token='));

        if (!tokenCookie) {
          throw new Error('Authentication cookie not set properly');
        }
      }

      return response;
    } catch (error) {
      throw error;
    }
  };

  const register = async (data: RegisterRequest): Promise<AuthResponse> => {
    try {
      const response = await authService.register(data);
      setUser(response.user);

      // Sync token to cookies for middleware (with secure flag in production)
      if (typeof document !== 'undefined') {
        const isSecureContext = typeof window !== 'undefined' && window.location.protocol === 'https:';
        const cookieString = `nlpforge_access_token=${response.access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax${isSecureContext ? '; Secure' : ''}`;
        document.cookie = cookieString;

        // Force cookie to be written immediately by reading it back
        const cookies = document.cookie.split(';').map(c => c.trim());
        const tokenCookie = cookies.find(c => c.startsWith('nlpforge_access_token='));

        if (!tokenCookie) {
          console.error('Failed to set authentication cookie');
          throw new Error('Authentication cookie not set properly');
        }
      }

      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);

    // Remove token from cookies
    if (typeof document !== 'undefined') {
      document.cookie = 'nlpforge_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }

    router.push('/auth/login');
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
