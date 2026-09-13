/**
 * api-client.ts — Axios instance with HttpOnly cookie auth + silent refresh.
 *
 * Security model:
 *  - NO tokens are stored in localStorage or JS-accessible memory.
 *  - credentials: 'include' (withCredentials) sends cookies automatically.
 *  - On 401 the interceptor hits /auth/refresh once; all concurrent 401s
 *    are queued and replayed after a single successful refresh (single-flight).
 *  - If refresh fails, user is redirected to /auth/login.
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { getApiBase } from './runtime-config';

export const apiClient: AxiosInstance = axios.create({
  timeout: 30000,
  withCredentials: true,          // send HttpOnly cookies on every request
  headers: { 'Content-Type': 'application/json' },
});

// ── Single-flight refresh state ───────────────────────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: () => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown): void {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve();
  });
  failedQueue = [];
}

// ── Request interceptor: dynamic baseURL ──────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    if (!config.baseURL) config.baseURL = getApiBase();
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: 401 → silent refresh → retry ───────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Only handle 401 once per request; skip if it was the refresh call itself
    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login')
    ) {
      return Promise.reject(error);
    }

    if (typeof window === 'undefined') return Promise.reject(error);

    // If a refresh is already in-flight, queue this request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: () => resolve(apiClient(originalRequest)),
          reject,
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Hit the refresh endpoint — backend reads the HttpOnly refresh cookie
      // and sets a new access cookie. No body needed.
      await apiClient.post('/api/v1/auth/refresh');

      processQueue(null);
      return apiClient(originalRequest);        // replay original request
    } catch (refreshError) {
      processQueue(refreshError);

      // Refresh token is expired / invalid — force logout
      if (!window.location.pathname.startsWith('/auth')) {
        window.location.href = '/auth/login';
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;
