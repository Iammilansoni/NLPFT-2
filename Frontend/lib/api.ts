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

    // Get auth token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('nlpforge_access_token') : null;

    console.log('🌐 API Request:', endpoint);
    console.log('🔑 Token:', token ? token.substring(0, 20) + '...' : 'No token');

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      console.log('📡 Response:', response.status, endpoint);

      if (!response.ok) {
        // Handle 401 Unauthorized
        if (response.status === 401) {
          console.log('❌ 401 Unauthorized - Token might be invalid or expired');
          console.log('Token was:', token ? 'present' : 'missing');

          if (typeof window !== 'undefined') {
            // Don't immediately redirect - let's see what's happening first
            console.log('⚠️ Would redirect to login, but holding off for debugging');
            // localStorage.removeItem('nlpforge_access_token');
            // localStorage.removeItem('nlpforge_user');
            // if (!window.location.pathname.startsWith('/auth')) {
            //   window.location.href = '/auth/login';
            // }
          }
        }

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
    if (params.embedding_model) {
      queryParams.append('embedding_model', params.embedding_model);
    }

    return this.request<SearchResponse>(
      `/api/v1/search/search?${queryParams.toString()}`
    );
  }

  async searchSimilarTestCases(
    query: string,
    topK: number = 5,
    embeddingModel?: string,
    minSimilarity?: number
  ): Promise<any[]> {
    // Use the proper vector search endpoint instead of embeddings/search
    const response = await this.search({
      query,
      top_k: topK,
      min_similarity: minSimilarity ?? 0.7, // Default similarity threshold
      embedding_model: embeddingModel,
    });

    // Return the results array from the search response
    return response.results || [];
  }

  // ============================================================================
  // Template API
  // ============================================================================

  async listTemplates(): Promise<TemplateModel[]> {
    const response = await this.request<any[]>('/api/v1/templates');
    // Map backend response to frontend TemplateModel format
    return (response || []).map(template => ({
      template_id: template.template_id || template.t_id || '',
      api_name: template.api_name || template.name || '',
      description: template.description || '',
      endpoint: template.endpoint || '',
      method: template.method || 'GET',
      intent_keywords: template.domain_tags || template.intent_keywords || [],
      parameters: template.parameters || [],
      example_queries: template.sample_requests?.map((r: any) => r.query || JSON.stringify(r)) || [],
      response_format: template.response_schema || template.json_schema || {},
      status: template.status || 'draft',
      confidence: template.confidence,
      version: template.version,
      created_at: template.created_at,
      updated_at: template.updated_at,
      created_by: template.user_id,
    }));
  }

  async getTemplate(templateId: string): Promise<TemplateModel & Record<string, any>> {
    const template = await this.request<any>(`/api/v1/templates/${templateId}`);
    // Map backend response to frontend TemplateModel format
    // Also preserve all original fields for edit mode
    return {
      // Standard TemplateModel fields
      template_id: template.template_id || template.t_id || templateId,
      api_name: template.api_name || template.name || '',
      description: template.description || '',
      endpoint: template.endpoint || '',
      method: template.method || 'GET',
      intent_keywords: template.domain_tags || template.intent_keywords || [],
      parameters: template.parameters || [],
      example_queries: template.sample_requests?.map((r: any) => r.query || JSON.stringify(r)) || [],
      response_format: template.response_schema || template.json_schema || {},
      status: template.status || 'draft',
      confidence: template.confidence,
      version: template.version,
      created_at: template.created_at,
      updated_at: template.updated_at,
      created_by: template.user_id,
      // Additional fields needed for edit mode
      base_url: template.base_url || '',
      json_schema: template.json_schema || {},
      response_schema: template.response_schema || {},
      sample_requests: template.sample_requests || [],
      sample_responses: template.sample_responses || [],
      headers: template.headers || {},
      domain_tags: template.domain_tags || [],
      security_classification: template.security_classification || 'public',
      expert_notes: template.expert_notes || '',
      reviewer_notes: template.reviewer_notes || template.expert_notes || '',
      side_effects: template.side_effects || '',
      auth_config: template.auth_config || {},
      rate_limit: template.rate_limit || {},
      assertions: template.assertions || [],
    };
  }

  async createTemplate(data: TemplateCreateRequest): Promise<TemplateModel> {
    return this.request<TemplateModel>('/api/v1/templates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTemplate(
    templateId: string,
    data: TemplateUpdateRequest
  ): Promise<TemplateModel> {
    return this.request<TemplateModel>(`/api/v1/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTemplate(templateId: string): Promise<void> {
    return this.request<void>(`/api/v1/templates/${templateId}`, {
      method: 'DELETE',
    });
  }

  async approveTemplate(templateId: string, approverNotes?: string): Promise<any> {
    return this.request<any>(`/api/v1/templates/${templateId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approver_notes: approverNotes }),
    });
  }

  async rejectTemplate(templateId: string, rejectionReason: string): Promise<any> {
    return this.request<any>(`/api/v1/templates/${templateId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejection_reason: rejectionReason }),
    });
  }

  async disableTemplate(templateId: string): Promise<any> {
    return this.request<any>(`/api/v1/templates/${templateId}/disable`, {
      method: 'POST',
    });
  }

  async enableTemplate(templateId: string): Promise<any> {
    return this.request<any>(`/api/v1/templates/${templateId}/enable`, {
      method: 'POST',
    });
  }

  async toggleTemplateVisibility(templateId: string): Promise<{ template_id: string; status: string; message: string }> {
    return this.request<any>(`/api/v1/templates/${templateId}/toggle-visibility`, {
      method: 'POST',
    });
  }

  async submitTemplateForReview(templateId: string, submissionNotes?: string): Promise<any> {
    const options: RequestInit = {
      method: 'POST',
    };
    // Only include body if submissionNotes is provided
    if (submissionNotes) {
      options.body = JSON.stringify({ submission_notes: submissionNotes });
    }
    return this.request<any>(`/api/v1/templates/${templateId}/submit`, options);
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

  async validateTemplate(templateId: string): Promise<any> {
    return this.request<any>(`/api/v1/templates/${templateId}/validate`);
  }

  async getTemplateStats(): Promise<TemplateStatsResponse> {
    return this.request<TemplateStatsResponse>('/api/v1/templates/stats');
  }

  // ============================================================================
  // Dataset API
  // ============================================================================

  async listDatasets(): Promise<DatasetListResponse> {
    return this.request<DatasetListResponse>('/api/v1/datasets');
  }

  async uploadDataset(file: File, autoEmbed: boolean = true): Promise<DatasetUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (autoEmbed) formData.append('auto_embed', 'true');

    return fetch(`${this.baseUrl}/api/v1/datasets/upload`, {
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
    return this.request<DatasetGenerateResponse>('/api/v1/datasets/generate', {
      method: 'POST',
      body: JSON.stringify({
        template_id: data.template_id,
        num_examples: data.num_examples || 100,
        custom_prompt: data.custom_prompt || 'Generate comprehensive test cases with realistic variations',
        focus_areas: data.focus_areas,
        scenario_distribution: data.scenario_distribution,
      }),
    });
  }

  async downloadDataset(filename: string): Promise<Blob> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/datasets/download?filename=${encodeURIComponent(filename)}`
    );
    if (!response.ok) {
      throw new Error('Failed to download dataset');
    }
    return response.blob();
  }

  async getDatasetStatus(taskId: string): Promise<any> {
    return this.request<any>(`/api/v1/datasets/status/${taskId}`);
  }

  async embedDataset(filename: string, embeddingModel?: string): Promise<any> {
    return this.request<any>('/api/v1/datasets/embed', {
      method: 'POST',
      body: JSON.stringify({
        filename,
        embedding_model: embeddingModel,
      }),
    });
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

  // ============================================================================
  // User Settings API
  // ============================================================================

  async getUserSettings(): Promise<any> {
    return this.request('/api/v1/user/settings', {
      method: 'GET',
    });
  }

  async updateUserSettings(data: { default_embedding_model?: string }): Promise<any> {
    return this.request('/api/v1/user/settings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // Audit Logs API
  // ============================================================================

  async getAuditLogs(params?: {
    action?: string;
    resource_type?: string;
    start_date?: string;
    end_date?: string;
    success_only?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params?.action) queryParams.append('action', params.action);
    if (params?.resource_type) queryParams.append('resource_type', params.resource_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.success_only !== undefined) {
      queryParams.append('success_only', params.success_only.toString());
    }
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const query = queryParams.toString();
    return this.request(`/api/v1/audit/logs${query ? `?${query}` : ''}`);
  }

  async getAuditLog(logId: string): Promise<any> {
    return this.request(`/api/v1/audit/logs/${logId}`);
  }

  async getAuditStats(days: number = 30): Promise<any> {
    return this.request(`/api/v1/audit/stats?days=${days}`);
  }

  // ============================================================================
  // Embedding Governance API
  // ============================================================================

  async setEmbeddingModel(modelName: string): Promise<any> {
    return this.request('/api/v1/datasets/settings/embedding-model', {
      method: 'POST',
      body: JSON.stringify({ model_name: modelName }),
    });
  }

  async reembedDataset(
    datasetId: string,
    options?: { model?: string; force?: boolean; chunk_size?: number }
  ): Promise<{ celery_task_id: string; message: string; dataset_id: string }> {
    return this.request(`/api/v1/datasets/${datasetId}/reembed`, {
      method: 'POST',
      body: JSON.stringify({
        model: options?.model,
        force: options?.force ?? true,
        chunk_size: options?.chunk_size ?? 100,
      }),
    });
  }

  async getEmbeddingStatus(datasetId: string): Promise<any> {
    return this.request(`/api/v1/datasets/${datasetId}/embedding-status`);
  }

  // ============================================================================
  // Generic Request Methods
  // ============================================================================

  async get<T = any>(endpoint: string, params?: Record<string, any>): Promise<T> {
    let url = endpoint;
    if (params) {
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
      const query = queryParams.toString();
      if (query) url += `?${query}`;
    }
    return this.request<T>(url);
  }

  async post<T = any>(endpoint: string, data?: any, options?: { params?: Record<string, any> }): Promise<T> {
    let url = endpoint;
    if (options?.params) {
      const queryParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
      const query = queryParams.toString();
      if (query) url += `?${query}`;
    }
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
