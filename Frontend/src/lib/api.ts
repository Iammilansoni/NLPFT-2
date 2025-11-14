/**
 * API Client for NLPForge Backend
 * Type-safe API wrapper with error handling
 */

import type {
  SearchRequest,
  SearchResponse,
  TemplateModel,
  TemplateCreateRequest,
  TemplateUpdateRequest,
  TemplateSyncResponse,
  TemplateReloadResponse,
  TemplateStatsResponse,
  DatasetListResponse,
  DatasetUploadResponse,
  DatasetGenerateRequest,
  DatasetGenerateResponse,
  QueryRequest,
  QueryResponse,
  ApiError,
} from './api-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorData: ApiError;
        try {
          errorData = await response.json();
        } catch {
          errorData = {
            error: response.statusText,
            detail: `HTTP ${response.status}`,
          };
        }
        throw {
          ...errorData,
          status: response.status,
        };
      }

      return await response.json();
    } catch (error) {
      if (error && typeof error === 'object' && 'status' in error) {
        throw error;
      }
      throw {
        error: 'Network Error',
        detail: error instanceof Error ? error.message : 'Unknown error',
        status: 0,
      };
    }
  }

  // ============================================================================
  // Search API
  // ============================================================================

  async search(params: SearchRequest): Promise<SearchResponse> {
    const queryParams = new URLSearchParams();
    queryParams.append('query', params.query);
    if (params.top_k) queryParams.append('top_k', params.top_k.toString());
    if (params.intent?.length) {
      params.intent.forEach(i => queryParams.append('intent', i));
    }
    if (params.min_similarity !== undefined) {
      queryParams.append('min_similarity', params.min_similarity.toString());
    }
    if (params.from_date) queryParams.append('from_date', params.from_date);
    if (params.to_date) queryParams.append('to_date', params.to_date);
    if (params.template_version) {
      queryParams.append('template_version', params.template_version);
    }

    return this.request<SearchResponse>(
      `/api/v1/search/search?${queryParams.toString()}`
    );
  }

  // ============================================================================
  // Template API
  // ============================================================================

  async listTemplates(): Promise<TemplateModel[]> {
    return this.request<TemplateModel[]>('/api/v1/templates/');
  }

  async getTemplate(intent: string): Promise<TemplateModel> {
    return this.request<TemplateModel>(`/api/v1/templates/${intent}`);
  }

  async createTemplate(data: TemplateCreateRequest): Promise<TemplateModel> {
    return this.request<TemplateModel>('/api/v1/templates/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTemplate(
    intent: string,
    data: TemplateUpdateRequest
  ): Promise<TemplateModel> {
    return this.request<TemplateModel>(`/api/v1/templates/${intent}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTemplate(intent: string): Promise<void> {
    return this.request<void>(`/api/v1/templates/${intent}`, {
      method: 'DELETE',
    });
  }

  async syncTemplates(): Promise<TemplateSyncResponse> {
    return this.request<TemplateSyncResponse>('/api/v1/templates/sync', {
      method: 'POST',
    });
  }

  async reloadTemplates(): Promise<TemplateReloadResponse> {
    return this.request<TemplateReloadResponse>('/api/v1/templates/reload', {
      method: 'POST',
    });
  }

  async getTemplateStats(): Promise<TemplateStatsResponse> {
    return this.request<TemplateStatsResponse>('/api/v1/templates/stats');
  }

  // ============================================================================
  // Dataset API
  // ============================================================================

  async listDatasets(): Promise<DatasetListResponse> {
    return this.request<DatasetListResponse>('/api/v1/dataset/list');
  }

  async uploadDataset(file: File): Promise<DatasetUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return fetch(`${this.baseUrl}/api/v1/dataset/upload`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json();
        throw error;
      }
      return response.json();
    });
  }

  async generateDataset(
    data: DatasetGenerateRequest
  ): Promise<DatasetGenerateResponse> {
    const formData = new FormData();
    formData.append('seed_prompt', data.seed_prompt);
    if (data.examples) formData.append('examples', data.examples.toString());
    if (data.api_name) formData.append('api_name', data.api_name);
    if (data.endpoint) formData.append('endpoint', data.endpoint);

    return fetch(`${this.baseUrl}/api/v1/dataset/generate`, {
      method: 'POST',
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json();
        throw error;
      }
      return response.json();
    });
  }

  async downloadDataset(filename: string): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/dataset/download?filename=${encodeURIComponent(filename)}`
    );
    if (!response.ok) {
      throw new Error('Failed to download dataset');
    }
    return response.blob();
  }

  // ============================================================================
  // Query API
  // ============================================================================

  async query(data: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // Run API (Query Execution & Results)
  // ============================================================================

  async createRun(text: string, options?: any): Promise<{ run_id: string }> {
    return this.request('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify({ text, ...options }),
    });
  }

  async getRunStatus(runId: string): Promise<any> {
    return this.request(`/api/v1/run/${runId}/status`, {
      method: 'GET',
    });
  }

  async getRunResults(runId: string): Promise<any> {
    return this.request(`/api/v1/run/${runId}/results`, {
      method: 'GET',
    });
  }

  async startSeleniumTest(runId: string): Promise<{ started: boolean }> {
    return this.request(`/api/v1/test/run/${runId}/start`, {
      method: 'POST',
    });
  }

  async cancelRun(runId: string): Promise<{ cancelled: boolean }> {
    return this.request(`/api/v1/run/${runId}/cancel`, {
      method: 'POST',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
