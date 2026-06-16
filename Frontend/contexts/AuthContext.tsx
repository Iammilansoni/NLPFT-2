/**
 * AuthContext.tsx — Global auth state backed by HttpOnly cookies.
 *
 * Strategy:
 *  - On mount: attempt GET /auth/me. If the access cookie is valid, we get the
 *    user. If expired, the Axios interceptor silently calls /auth/refresh and
 *    retries. If refresh also fails, user is treated as logged-out.
 *  - No tokens are read from or written to localStorage / document.cookie.
 *  - The user PROFILE is cached in localStorage only for UX (avoids flicker).
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
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]         = useState<User | null>(null);
  const [isLoading, setLoading] = useState(true);
  const router = useRouter();

  // ── Boot: validate session against the server ─────────────────────────────
  useEffect(() => {
    const init = async () => {
      // ── One-time migration cleanup ──────────────────────────────────────────
      // Remove pre-cookie-migration tokens from localStorage so they can't be
      // accidentally sent by legacy raw-fetch components still in the codebase.
      if (typeof window !== 'undefined') {
        localStorage.removeItem('nlpforge_access_token');
        localStorage.removeItem('nlpforge_refresh_token');
      }

      // Show a cached profile immediately to avoid layout flicker
      const cached = authService.getUser();
      if (cached) setUser(cached);

      try {
        // GET /auth/me — the Axios interceptor will silently refresh if needed
        const freshUser = await authService.getCurrentUser();
        setUser(freshUser);
      } catch {
        // No valid session (refresh also failed) — clear stale profile
        authService.removeUser();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  // ── Login ─────────────────────────────────────────────────────────────────
  const login = async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await authService.login(data);   // sets cookies + caches user
    setUser(response.user);
    return response;
  };

  // ── Register ──────────────────────────────────────────────────────────────
  const register = async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await authService.register(data);
    setUser(response.user);
    return response;
  };

  // ── Logout ────────────────────────────────────────────────────────────────
  const logout = async (): Promise<void> => {
    await authService.logout();   // clears HttpOnly cookies server-side
    setUser(null);
    router.push('/auth/login');
  };

  // ── Refresh profile from server ───────────────────────────────────────────
  const refreshUser = async (): Promise<void> => {
    try {
      const freshUser = await authService.getCurrentUser();
      setUser(freshUser);
    } catch {
      await logout();
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
      refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
