import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
      console.log('[API Client] 401 Unauthorized error:', error.config?.url);
      console.log('Token in request:', error.config?.headers?.Authorization);

      // Token expired or invalid - but don't auto-redirect
      // Let the component handle it
      if (typeof window !== 'undefined') {
        const hasToken = localStorage.getItem('nlpforge_access_token');
        console.log('Has token in localStorage:', !!hasToken);

        // Only clear and redirect if we actually had a token (meaning it's expired)
        if (hasToken) {
          console.log('[API Client] Token exists but got 401 - token might be expired');
          localStorage.removeItem('nlpforge_access_token');
          localStorage.removeItem('nlpforge_user');

          // Redirect to login if not already on auth page
          if (!window.location.pathname.startsWith('/auth')) {
            console.log('Redirecting to login due to expired token');
            window.location.href = '/auth/login';
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
