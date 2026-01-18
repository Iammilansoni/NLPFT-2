import axios, { AxiosInstance } from 'axios';
import { getApiBase } from './runtime-config';

export const apiClient: AxiosInstance = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// Response interceptor: Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear and redirect if needed
      if (typeof window !== 'undefined') {
        const hasToken = localStorage.getItem('nlpforge_access_token');

        // Only clear and redirect if we actually had a token (meaning it's expired)
        if (hasToken) {
          localStorage.removeItem('nlpforge_access_token');
          localStorage.removeItem('nlpforge_user');

          // Redirect to login if not already on auth page
          if (!window.location.pathname.startsWith('/auth')) {
            window.location.href = '/auth/login';
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
