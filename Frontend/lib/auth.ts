/**
 * auth.ts — Authentication service
 *
 * Cookie-based: tokens live in HttpOnly cookies set by the server.
 * This service only manages the user PROFILE object (non-sensitive).
 * No access_token or refresh_token is ever stored on the client.
 */

import apiClient from './api-client';

export interface User {
  user_id: string;
  email: string;
  username: string;
  is_expert?: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

/** Shape returned by login/register — only the user object; tokens are in cookies. */
export interface AuthResponse {
  user: User;
}

export interface ForgotPasswordRequest { email: string }
export interface ResetPasswordRequest  { token: string; new_password: string; confirm_password: string }
export interface ChangePasswordRequest { current_password: string; new_password: string; confirm_password: string }

class AuthService {
  private readonly USER_KEY = 'nlpforge_user';   // profile only — not a token

  /** Register. Backend sets auth cookies; we persist the user profile. */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);
    this.setUser(response.data.user);
    return response.data;
  }

  /** Login. Backend sets HttpOnly cookies; response body has user profile only. */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login/json', data);
    this.setUser(response.data.user);
    return response.data;
  }

  /** Logout. Backend clears both cookies; we clear the local user profile. */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } catch {
      // Even if the server call fails, clear local state
    } finally {
      this.removeUser();
    }
  }

  /** Fetch current user from the server (validates the access cookie). */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    this.setUser(response.data);
    return response.data;
  }

  async forgotPassword(data: ForgotPasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/auth/forgot-password', data);
    return response.data;
  }

  async resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/auth/reset-password', data);
    return response.data;
  }

  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/auth/change-password', data);
    return response.data;
  }

  async checkHealth(): Promise<{ status: string; service: string }> {
    const response = await apiClient.get('/api/v1/auth/health');
    return response.data;
  }

  /**
   * Promote a user to expert status. ADMIN ONLY — the backend rejects
   * non-admin callers with 403. Targets a user by email (no self-promotion).
   */
  async promoteToExpert(email: string): Promise<User> {
    const response = await apiClient.post<User>('/api/v1/auth/promote-expert', { email });
    return response.data;
  }

  // ── User profile (non-sensitive; only cached for UX, never used for auth) ──

  setUser(user: User): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
  }

  getUser(): User | null {
    if (typeof window !== 'undefined') {
      const raw = localStorage.getItem(this.USER_KEY);
      return raw ? JSON.parse(raw) : null;
    }
    return null;
  }

  removeUser(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.USER_KEY);
    }
  }

  /**
   * isAuthenticated: checks for a cached user profile.
   * The real authority is the server (cookie). This is only used to decide
   * whether to render the loading spinner on cold page loads.
   */
  isAuthenticated(): boolean {
    return !!this.getUser();
  }
}

export const authService = new AuthService();
export default authService;
