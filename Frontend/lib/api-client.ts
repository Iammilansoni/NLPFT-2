import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { getApiBase } from './runtime-config';

export const apiClient: AxiosInstance = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Track if a token refresh is in progress to prevent concurrent refreshes
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    } else {
      // Neither error nor valid token — reject to prevent hanging promises
      reject(new Error('Failed to refresh token: no token available'));
    }
  });
  failedQueue = [];
}

// Request interceptor: Set dynamic baseURL at request time (not module load time)
// This ensures window.location.hostname is available
apiClient.interceptors.request.use(
  (config) => {
    if (!config.baseURL) {
      config.baseURL = getApiBase();
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Request interceptor: Add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('nlpforge_access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't try to refresh if the failed request was the refresh endpoint itself
      if (originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(error);
      }

      if (typeof window === 'undefined') {
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem('nlpforge_refresh_token');
      if (!refreshToken) {
        // No refresh token - clear auth and redirect
        localStorage.removeItem('nlpforge_access_token');
        localStorage.removeItem('nlpforge_user');
        if (!window.location.pathname.startsWith('/auth')) {
          window.location.href = '/auth/login';
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request while refresh is in progress
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt token refresh
        const response = await apiClient.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        });

        const newAccessToken = response.data.access_token;
        const newRefreshToken = response.data.refresh_token;

        // Validate token before persisting — abort refresh if missing/empty
        if (!newAccessToken || typeof newAccessToken !== 'string') {
          const tokenError = new Error('Refresh response missing valid access_token');
          processQueue(tokenError, null);
          localStorage.removeItem('nlpforge_access_token');
          localStorage.removeItem('nlpforge_refresh_token');
          localStorage.removeItem('nlpforge_user');
          if (!window.location.pathname.startsWith('/auth')) {
            window.location.href = '/auth/login';
          }
          return Promise.reject(tokenError);
        }

        localStorage.setItem('nlpforge_access_token', newAccessToken);
        if (newRefreshToken) {
          localStorage.setItem('nlpforge_refresh_token', newRefreshToken);
        }

        // Retry queued requests
        processQueue(null, newAccessToken);

        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);

        // Refresh failed - clear auth and redirect
        localStorage.removeItem('nlpforge_access_token');
        localStorage.removeItem('nlpforge_refresh_token');
        localStorage.removeItem('nlpforge_user');
        if (!window.location.pathname.startsWith('/auth')) {
          window.location.href = '/auth/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
