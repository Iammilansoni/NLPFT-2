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

// Determine if we're on the server or client
const isServer = typeof window === 'undefined';

// Use internal Docker service URL for server-side, public URL for client-side
const getBaseURL = () => {
  if (isServer) {
    // Server-side: use internal Docker network
    return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
  }
  // Client-side: use public URL
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const apiClient = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});


apiClient.interceptors.request.use(
  (config) => {
    
    config.params = { ...config.params, _t: Date.now() };
    return config;
  },
  (error) => Promise.reject(error)
);


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


export const healthApi = {
  getHealth: async (): Promise<HealthStatus> => {
    try {
      const response: AxiosResponse<HealthStatus> = await apiClient.get('/api/v1/health');
      console.log('✅ Backend health response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Backend health API error:', error);
      console.warn('Backend not available - throwing error for fallback mode');
      
      throw error;
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


export const convertApi = {
  convertText: async (request: ConvertRequest): Promise<ConvertResponse> => {
    try {
      console.log('🔄 Converting text:', request.text);
      
      const requestWithFormat = {
        ...request,
        target_format: request.target_format || 'nlp_steps'
      };
      const response = await apiClient.post('/api/v1/convert', requestWithFormat);
      console.log('✅ Backend convert response:', response.data);
      
      
      const backendResponse = response.data;
      const metadata = backendResponse.metadata || {};
      
      
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
      
      return {
        ...mockConvertResponse,
        steps: mockConvertResponse.steps.map(step => ({
          ...step,
          matched_text: request.text.substring(0, 50) 
        }))
      };
    }
  },
};


export const dictionaryApi = {
  getFunctions: async (): Promise<DictionaryFunction[]> => {
    try {
      const response: AxiosResponse<DictionaryListResponse> = await apiClient.get('/api/v1/dictionary?page_size=100');
      
      const apiFunctions = response.data.functions || [];
      
      
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
    } catch (error) {
      console.error('❌ Dictionary API error:', error);
      console.warn('Backend not available - throwing error for fallback mode');
      throw error;
    }
  },

  getFunctionsWithMetadata: async (): Promise<{ functions: DictionaryFunction[], totalCount: number }> => {
    try {
      const response: AxiosResponse<DictionaryListResponse> = await apiClient.get('/api/v1/dictionary?page_size=100');
      const apiFunctions = response.data.functions || [];
      
      
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
    } catch (error) {
      console.error('❌ Dictionary metadata API error:', error);
      console.warn('Backend not available - throwing error for fallback mode');
      throw error;
    }
  },

  getFunction: async (id: string): Promise<DictionaryFunction> => {
    try {
      const response: AxiosResponse<ApiFunctionResponse> = await apiClient.get(`/api/v1/dictionary/${id}`);
      const apiFunc = response.data;
      
      
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
      
      const mockFunc = mockFunctions.find(f => f._id === id);
      if (!mockFunc) {
        throw new Error(`Function not found: ${id}`);
      }
      return mockFunc;
    }
  },

  createFunction: async (func: Omit<DictionaryFunction, '_id' | 'created_at' | 'updated_at'>): Promise<DictionaryFunction> => {
    try {
      
      interface StructuredArgument {
        type: string;
        required?: boolean;
        description?: string;
        default?: unknown;
      }
      
      const argumentsArray = Object.entries(func.args || {}).map(([name, value]) => {
        
        if (typeof value === 'object' && value !== null && 'type' in value) {
          
          const structuredValue = value as StructuredArgument;
          return {
            name,
            type: structuredValue.type || 'str',
            required: structuredValue.required ?? true,
            description: structuredValue.description || `${name} parameter`,
            default: structuredValue.default
          };
        } else {
          
          return {
            name,
            type: typeof value === 'string' ? value : 'str',
            required: true,
            description: `${name} parameter`
          };
        }
      });

      
      const apiRequest = {
        name: func.function_name,
        description: func.description,
        templates: func.templates || [],
        arguments: argumentsArray,
        tags: func.tags || [],
        category: func.category || 'general',
        
        ...(func.examples && func.examples.length > 0 && {
          aliases: func.examples 
        })
      };
      
      console.log('🔄 Creating function with payload:', apiRequest);
      
      const response: AxiosResponse<CreateFunctionResponse> = await apiClient.post('/api/v1/dictionary', apiRequest);
      const apiResponse = response.data;
      
      console.log('✅ Function created successfully:', apiResponse);
      
      
      return {
        _id: apiResponse.function_id,
        function_name: apiResponse.name || func.function_name,
        description: func.description || '',
        templates: func.templates || [],
        examples: func.examples || [],
        args: func.args || {},
        tags: func.tags || [],
        category: func.category || 'general',
        confidence_threshold: func.confidence_threshold || 0.7,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    } catch (error) {
      console.error('❌ Failed to create function:', error);
      
      return {
        _id: Math.random().toString(36).substr(2, 9),
        function_name: func.function_name,
        description: func.description || '',
        templates: func.templates || [],
        examples: func.examples || [],
        args: func.args || {},
        tags: func.tags || [],
        category: func.category || 'general',
        confidence_threshold: func.confidence_threshold || 0.7,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
  },

  updateFunction: async (id: string, func: Partial<DictionaryFunction>): Promise<DictionaryFunction> => {
    try {
      
      const apiRequest: Record<string, unknown> = {};
      if (func.function_name) apiRequest.name = func.function_name;
      if (func.description) apiRequest.description = func.description;
      if (func.templates) apiRequest.templates = func.templates;
      if (func.tags) apiRequest.tags = func.tags;
      if (func.category) apiRequest.category = func.category;
      
      
      if (func.args) {
        interface StructuredArgument {
          type: string;
          required?: boolean;
          description?: string;
          default?: unknown;
        }
        
        const argumentsArray = Object.entries(func.args).map(([name, value]) => {
          if (typeof value === 'object' && value !== null && 'type' in value) {
            const structuredValue = value as StructuredArgument;
            return {
              name,
              type: structuredValue.type || 'str',
              required: structuredValue.required ?? true,
              description: structuredValue.description || `${name} parameter`,
              default: structuredValue.default
            };
          } else {
            return {
              name,
              type: typeof value === 'string' ? value : 'str',
              required: true,
              description: `${name} parameter`
            };
          }
        });
        apiRequest.arguments = argumentsArray;
      }
      
      console.log('🔄 Updating function with payload:', apiRequest);
      
      await apiClient.put(`/api/v1/dictionary/${id}`, apiRequest);
      
      console.log('✅ Function updated successfully');
      
      
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
    } catch (error) {
      console.error('❌ Failed to update function:', error);
      
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
    
    return dictionaryApi.getFunctions();
  },
};


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


export const formatTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  
  const hours = d.getHours().toString().padStart(2, '0');
  const minutes = d.getMinutes().toString().padStart(2, '0');
  const seconds = d.getSeconds().toString().padStart(2, '0');
  
  return `${hours}:${minutes}:${seconds}`;
};

export const formatDateTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  
  const year = d.getFullYear();
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  
  return `${year}-${month}-${day} ${formatTime(d)}`;
};


export const api = {
  
  getHealth: healthApi.getHealth,
  getReadiness: healthApi.getReadiness,
  getLiveness: healthApi.getLiveness,
  
  
  convertText: convertApi.convertText,
  
  
  getFunctions: dictionaryApi.getFunctions,
  getFunctionsWithMetadata: dictionaryApi.getFunctionsWithMetadata,
  getFunction: dictionaryApi.getFunction,
  createFunction: dictionaryApi.createFunction,
  updateFunction: dictionaryApi.updateFunction,
  deleteFunction: dictionaryApi.deleteFunction,
  importFunctions: dictionaryApi.importFunctions,
  exportFunctions: dictionaryApi.exportFunctions,
  
  
  downloadJson,
  formatBytes,
  formatUptime,
  formatTime,
  formatDateTime,
};
