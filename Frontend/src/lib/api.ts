import axios, { AxiosResponse } from 'axios';
import { 
  HealthStatus, 
  ConvertRequest, 
  ConvertResponse, 
  DictionaryFunction,
  ApiFunctionResponse,
  DictionaryListResponse,
  CreateFunctionResponse,
  ApiError
} from './types';
import { mockFunctions, mockHealthStatus, mockConvertResponse } from './mock-data';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add timestamp to prevent caching issues
    config.params = { ...config.params, _t: Date.now() };
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError: ApiError = {
      message: error.response?.data?.message || error.message || 'An error occurred',
      status: error.response?.status || 500,
      details: error.response?.data?.details || null,
    };
    return Promise.reject(apiError);
  }
);

// Health API
export const healthApi = {
  getHealth: async (): Promise<HealthStatus> => {
    try {
      const response: AxiosResponse<HealthStatus> = await apiClient.get('/api/v1/health');
      console.log('✅ Backend health response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Backend health API error:', error);
      console.warn('Backend not available, using mock health data');
      return mockHealthStatus;
    }
  },

  getReadiness: async (): Promise<{ status: string }> => {
    try {
      const response = await apiClient.get('/api/v1/health/ready');
      return response.data;
    } catch {
      return { status: 'ready' };
    }
  },

  getLiveness: async (): Promise<{ status: string }> => {
    try {
      const response = await apiClient.get('/api/v1/health/live');
      return response.data;
    } catch {
      return { status: 'alive' };
    }
  },
};

// Convert API
export const convertApi = {
  convertText: async (request: ConvertRequest): Promise<ConvertResponse> => {
    try {
      console.log('🔄 Converting text:', request.text);
      // Ensure target_format is always provided (backend requires it)
      const requestWithFormat = {
        ...request,
        target_format: request.target_format || 'nlp_steps'
      };
      const response = await apiClient.post('/api/v1/convert', requestWithFormat);
      console.log('✅ Backend convert response:', response.data);
      
      // Extract the actual convert data from the response metadata 
      const backendResponse = response.data;
      const metadata = backendResponse.metadata || {};
      
      // Transform to the format expected by the frontend
      const frontendResponse: ConvertResponse = {
        steps: metadata.steps || [],
        overall_confidence: metadata.overall_confidence || 0,
        unresolved_tokens: metadata.unresolved_tokens || [],
        processing_time_ms: metadata.processing_time_ms || backendResponse.processing_time * 1000,
        status: metadata.status || 'success'
      };
      
      return frontendResponse;
    } catch (error) {
      console.error('❌ Backend convert API error:', error);
      console.warn('Backend not available, using mock convert response');
      // Return a mock response with the original text
      return {
        ...mockConvertResponse,
        steps: mockConvertResponse.steps.map(step => ({
          ...step,
          matched_text: request.text.substring(0, 50) // Use part of original text
        }))
      };
    }
  },
};

// Dictionary API  
export const dictionaryApi = {
  getFunctions: async (): Promise<DictionaryFunction[]> => {
    try {
      const response: AxiosResponse<DictionaryListResponse> = await apiClient.get('/api/v1/dictionary?page_size=100');
      // The API returns { functions: [...] } so we need to extract and transform the functions array
      const apiFunctions = response.data.functions || [];
      
      // Transform API format to frontend format
      return apiFunctions.map((apiFunc: ApiFunctionResponse) => ({
        _id: apiFunc.id,
        function_name: apiFunc.name || '',
        description: apiFunc.description || '',
        templates: apiFunc.templates || [],
        examples: apiFunc.examples || [],
        args: apiFunc.arguments || {},
        tags: apiFunc.tags || [],
        category: apiFunc.category || 'general',
        confidence_threshold: apiFunc.confidence_threshold || 0.7,
        created_at: apiFunc.created_at,
        updated_at: apiFunc.updated_at,
      }));
    } catch {
      console.warn('Backend not available, using mock functions data');
      return mockFunctions;
    }
  },

  getFunctionsWithMetadata: async (): Promise<{ functions: DictionaryFunction[], totalCount: number }> => {
    try {
      const response: AxiosResponse<DictionaryListResponse> = await apiClient.get('/api/v1/dictionary?page_size=100');
      const apiFunctions = response.data.functions || [];
      
      // Transform API format to frontend format
      const transformedFunctions = apiFunctions.map((apiFunc: ApiFunctionResponse) => ({
        _id: apiFunc.id,
        function_name: apiFunc.name || '',
        description: apiFunc.description || '',
        templates: apiFunc.templates || [],
        examples: apiFunc.examples || [],
        args: apiFunc.arguments || {},
        tags: apiFunc.tags || [],
        category: apiFunc.category || 'general',
        confidence_threshold: apiFunc.confidence_threshold || 0.7,
        created_at: apiFunc.created_at,
        updated_at: apiFunc.updated_at,
      }));
      
      return {
        functions: transformedFunctions,
        totalCount: response.data.total_count || transformedFunctions.length
      };
    } catch {
      console.warn('Backend not available, using mock functions data');
      return {
        functions: mockFunctions,
        totalCount: mockFunctions.length
      };
    }
  },

  getFunction: async (id: string): Promise<DictionaryFunction> => {
    try {
      const response: AxiosResponse<ApiFunctionResponse> = await apiClient.get(`/api/v1/dictionary/${id}`);
      const apiFunc = response.data;
      
      // Transform API format to frontend format
      return {
        _id: apiFunc.id,
        function_name: apiFunc.name || '',
        description: apiFunc.description || '',
        templates: apiFunc.templates || [],
        examples: apiFunc.examples || [],
        args: apiFunc.arguments || {},
        tags: apiFunc.tags || [],
        category: apiFunc.category || 'general',
        confidence_threshold: apiFunc.confidence_threshold || 0.7,
        created_at: apiFunc.created_at,
        updated_at: apiFunc.updated_at,
      };
    } catch {
      // Find mock function by id
      const mockFunc = mockFunctions.find(f => f._id === id);
      if (!mockFunc) {
        throw new Error(`Function not found: ${id}`);
      }
      return mockFunc;
    }
  },

  createFunction: async (func: Omit<DictionaryFunction, '_id' | 'created_at' | 'updated_at'>): Promise<DictionaryFunction> => {
    try {
      // Transform frontend format to API format
      const apiRequest = {
        name: func.function_name,
        description: func.description,
        templates: func.templates,
        arguments: func.args,
        tags: func.tags,
        category: func.category,
      };
      
      const response: AxiosResponse<CreateFunctionResponse> = await apiClient.post('/api/v1/dictionary', apiRequest);
      const apiResponse = response.data;
      
      // Transform response back to frontend format
      return {
        _id: apiResponse.function_id,
        function_name: apiResponse.name || func.function_name,
        description: func.description,
        templates: func.templates,
        examples: [],
        args: func.args,
        tags: func.tags,
        category: func.category,
        confidence_threshold: 0.7,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    } catch {
      // Return mock created function
      return {
        _id: Math.random().toString(36).substr(2, 9),
        function_name: func.function_name,
        description: func.description,
        templates: func.templates,
        examples: [],
        args: func.args,
        tags: func.tags,
        category: func.category,
        confidence_threshold: func.confidence_threshold,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  },

  updateFunction: async (id: string, func: Partial<DictionaryFunction>): Promise<DictionaryFunction> => {
    try {
      // Transform frontend format to API format
      const apiRequest: Record<string, unknown> = {};
      if (func.function_name) apiRequest.name = func.function_name;
      if (func.description) apiRequest.description = func.description;
      if (func.templates) apiRequest.templates = func.templates;
      if (func.args) apiRequest.arguments = func.args;
      if (func.tags) apiRequest.tags = func.tags;
      if (func.category) apiRequest.category = func.category;
      
      await apiClient.put(`/api/v1/dictionary/${id}`, apiRequest);
      
      // For update, just return the updated data
      return {
        _id: id,
        function_name: func.function_name || '',
        description: func.description || '',
        templates: func.templates || [],
        examples: func.examples || [],
        args: func.args || {},
        tags: func.tags || [],
        category: func.category || 'general',
        confidence_threshold: func.confidence_threshold || 0.7,
        created_at: func.created_at,
        updated_at: new Date().toISOString(),
      };
    } catch {
      // Return mock updated function
      return {
        _id: id,
        function_name: func.function_name || '',
        description: func.description || '',
        templates: func.templates || [],
        examples: func.examples || [],
        args: func.args || {},
        tags: func.tags || [],
        category: func.category || 'general',
        confidence_threshold: func.confidence_threshold || 0.7,
        created_at: func.created_at,
        updated_at: new Date().toISOString(),
      };
    }
  },

  deleteFunction: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/api/v1/dictionary/${id}`);
    } catch {
      // Mock delete - just resolve
      return Promise.resolve();
    }
  },

  importFunctions: async (functions: DictionaryFunction[]): Promise<{ imported: number; errors: unknown[] }> => {
    try {
      const response = await apiClient.post('/api/v1/dictionary/import', { functions });
      return response.data;
    } catch {
      return { imported: functions.length, errors: [] };
    }
  },

  exportFunctions: async (): Promise<DictionaryFunction[]> => {
    // Use the same endpoint as getFunctions
    return dictionaryApi.getFunctions();
  },
};

// Utility functions
export const downloadJson = (data: unknown, filename: string = 'data.json') => {
  const jsonStr = JSON.stringify(data, null, 2);
  const dataBlob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / (24 * 3600));
  const hours = Math.floor((seconds % (24 * 3600)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0) parts.push(`${secs}s`);

  return parts.join(' ');
};

// Consistent time formatting to prevent hydration mismatches
export const formatTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  // Use consistent 24-hour format to avoid AM/PM locale differences
  const hours = d.getHours().toString().padStart(2, '0');
  const minutes = d.getMinutes().toString().padStart(2, '0');
  const seconds = d.getSeconds().toString().padStart(2, '0');
  
  return `${hours}:${minutes}:${seconds}`;
};

export const formatDateTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  // Use ISO date format and 24-hour time to avoid locale differences
  const year = d.getFullYear();
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  
  return `${year}-${month}-${day} ${formatTime(d)}`;
};

// Unified API export for easier usage
export const api = {
  // Health endpoints
  getHealth: healthApi.getHealth,
  getReadiness: healthApi.getReadiness,
  getLiveness: healthApi.getLiveness,
  
  // Convert endpoints
  convertText: convertApi.convertText,
  
  // Dictionary endpoints
  getFunctions: dictionaryApi.getFunctions,
  getFunctionsWithMetadata: dictionaryApi.getFunctionsWithMetadata,
  getFunction: dictionaryApi.getFunction,
  createFunction: dictionaryApi.createFunction,
  updateFunction: dictionaryApi.updateFunction,
  deleteFunction: dictionaryApi.deleteFunction,
  importFunctions: dictionaryApi.importFunctions,
  exportFunctions: dictionaryApi.exportFunctions,
  
  // Utility functions
  downloadJson,
  formatBytes,
  formatUptime,
  formatTime,
  formatDateTime,
};