/**
 * Authentication Context
 * Provides global authentication state and methods
 */

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import authService, { User, LoginRequest, RegisterRequest, AuthResponse } from '@/lib/auth';

// Cookie max-age matches access token lifetime (30 minutes)
const COOKIE_MAX_AGE_SECONDS = 30 * 60;

/**
 * Sync auth token to cookie for Next.js middleware.
 * Consistent Secure flag and max-age across login/register flows.
 */
function syncAuthCookie(token: string): void {
  if (typeof document === 'undefined') return;

  const isSecure = typeof window !== 'undefined' && window.location.protocol === 'https:';
  const cookieString = `nlpforge_access_token=${token}; path=/; max-age=${COOKIE_MAX_AGE_SECONDS}; SameSite=Lax${isSecure ? '; Secure' : ''}`;
  document.cookie = cookieString;
}

function clearAuthCookie(): void {
  if (typeof document === 'undefined') return;
  document.cookie = 'nlpforge_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
}

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

          // Sync cookie on page load (may have expired)
          syncAuthCookie(token);

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
    const response = await authService.login(data);
    setUser(response.user);
    syncAuthCookie(response.access_token);
    return response;
  };

  const register = async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await authService.register(data);
    setUser(response.user);
    syncAuthCookie(response.access_token);
    return response;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    clearAuthCookie();
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
