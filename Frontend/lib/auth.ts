/**
 * Authentication API Service
 * Handles all authentication-related API calls
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

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: User;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

class AuthService {
  private readonly TOKEN_KEY = 'nlpforge_access_token';
  private readonly REFRESH_TOKEN_KEY = 'nlpforge_refresh_token';
  private readonly USER_KEY = 'nlpforge_user';

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);
    this.setToken(response.data.access_token);
    if (response.data.refresh_token) {
      this.setRefreshToken(response.data.refresh_token);
    }
    this.setUser(response.data.user);
    return response.data;
  }

  /**
   * Login with email and password
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login/json', data);
    this.setToken(response.data.access_token);
    if (response.data.refresh_token) {
      this.setRefreshToken(response.data.refresh_token);
    }
    this.setUser(response.data.user);
    return response.data;
  }

  /**
   * Logout user
   */
  logout(): void {
    this.removeToken();
    this.removeRefreshToken();
    this.removeUser();
  }

  /**
   * Get current user info from API
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    this.setUser(response.data);
    return response.data;
  }

  /**
   * Request password reset
   */
  async forgotPassword(data: ForgotPasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/auth/forgot-password', data);
    return response.data;
  }

  /**
   * Reset password with token
   */
  async resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/auth/reset-password', data);
    return response.data;
  }

  /**
   * Change password (requires authentication)
   */
  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/auth/change-password', data);
    return response.data;
  }

  /**
   * Check authentication service health
   */
  async checkHealth(): Promise<{ status: string; service: string }> {
    const response = await apiClient.get('/api/v1/auth/health');
    return response.data;
  }

  /**
   * Promote current user to expert status
   * Experts can approve/reject templates
   */
  async promoteToExpert(): Promise<User> {
    const response = await apiClient.post<User>('/api/v1/auth/promote-expert');
    this.setUser(response.data);
    return response.data;
  }

  // Token management
  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.TOKEN_KEY, token);
    }
  }

  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(this.TOKEN_KEY);
    }
    return null;
  }

  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.TOKEN_KEY);
    }
  }

  // Refresh token management
  // NOTE: Refresh tokens should ideally be stored in httpOnly cookies set by
  // the server. Until the backend sets httpOnly cookies on /login and /refresh
  // responses (and the /refresh endpoint reads the cookie instead of the body),
  // we keep localStorage as a transitional store but mark it clearly.
  // TODO: Once the backend sets httpOnly refresh-token cookies, remove these
  // localStorage helpers entirely and rely on credentials: 'include' / withCredentials.
  setRefreshToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
    }
  }

  getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }
    return null;
  }

  removeRefreshToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    }
  }

  /**
   * Refresh the access token using the stored refresh token.
   * Uses a single-flight lock so concurrent callers share one in-flight request.
   * Returns the new access token or null if refresh failed.
   */
  private refreshPromise: Promise<string | null> | null = null;

  async refreshAccessToken(): Promise<string | null> {
    // Single-flight: if a refresh is already in progress, piggyback on it
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._doRefresh();
    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async _doRefresh(): Promise<string | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await apiClient.post<AuthResponse>('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;

      this.setToken(access_token);
      if (newRefreshToken) {
        this.setRefreshToken(newRefreshToken);
      }
      if (response.data.user) {
        this.setUser(response.data.user);
      }

      return access_token;
    } catch {
      // Refresh token is invalid/expired - force logout
      this.logout();
      return null;
    }
  }

  // User management
  setUser(user: User): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
  }

  getUser(): User | null {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem(this.USER_KEY);
      return user ? JSON.parse(user) : null;
    }
    return null;
  }

  removeUser(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.USER_KEY);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

export const authService = new AuthService();
export default authService;
