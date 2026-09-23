/**
 * API Client for NLPForge Backend
 * Type-safe API wrapper with error handling
 */

import { redirectToLogin } from '@/lib/auth-redirect';
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
  ApiErrorResponse,
  SemanticRetrieveResponse,
} from './api-types';
import { getApiBase } from './runtime-config';

class ApiClient {
  private get baseUrl(): string {
    // Evaluate getApiBase() on each access to get dynamic hostname
    return getApiBase().replace(/\/$/, '');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      ...options,
      credentials: 'include',   // sends HttpOnly auth cookies automatically
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        if (response.status === 401 && typeof window !== 'undefined') {
          // The Axios api-client handles silent refresh for Axios calls.
          // For raw-fetch callers, redirect when truly unauthenticated.
          redirectToLogin();
        }

        let errorData: ApiErrorResponse;
        try {
          errorData = await response.json();
        } catch {
          errorData = { error: response.statusText, detail: `HTTP ${response.status}` };
        }
        throw { ...errorData, status: response.status };
      }

      return await response.json();
    } catch (error) {
      if (error && typeof error === 'object' && 'status' in error) throw error;
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
  // Two-Stage Ranking API (KNN Search + FlashRank Reranking)
  // ============================================================================

  /**
   * Route a natural-language request to an API template and extract its body.
   * POST /api/v1/query/semantic-search -- see Backend/app/services/multi_model_semantic_service.py
   */
  async semanticRetrieve(
    query: string,
    topK: number = 25,
    _intentType?: string,
    includeAlternatives: boolean = false,
    includeSlotExtraction: boolean = true
  ): Promise<SemanticRetrieveResponse> {
    return this.request<SemanticRetrieveResponse>('/api/v1/query/semantic-search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        top_k: topK,
        include_alternatives: includeAlternatives,
        include_slot_extraction: includeSlotExtraction,
      }),
    });
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
      base_url: template.base_url || '',
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
      credentials: 'include',    // HttpOnly cookie sent automatically
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
        user_prompt: data.custom_prompt || 'Generate comprehensive test cases with realistic variations',
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

  /**
   * Rename a dataset
   */
  async renameDataset(datasetId: string, newName: string): Promise<{
    success: boolean;
    dataset_id: string;
    old_name: string;
    new_name: string;
    message: string;
  }> {
    return this.request(`/api/v1/datasets/db/${datasetId}/rename`, {
      method: 'PATCH',
      body: JSON.stringify({ name: newName }),
    });
  }

  /**
   * Delete a dataset and all its rows
   */
  async deleteDataset(datasetId: string): Promise<{
    success: boolean;
    message: string;
    deleted_rows: number;
  }> {
    return this.request(`/api/v1/datasets/db/${datasetId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Embed a dataset to Redis for vector search
   */
  async embedDatasetById(datasetId: string, model?: string): Promise<{
    success: boolean;
    dataset_id: string;
    embedding_status: string;
    model: string;
    message: string;
  }> {
    const params = model ? `?model=${encodeURIComponent(model)}` : '';
    return this.request(`/api/v1/datasets/db/${datasetId}/embed${params}`, {
      method: 'POST',
    });
  }

  /**
   * Get paginated rows for a dataset
   */
  async getDatasetRows(datasetId: string, skip: number = 0, limit: number = 50): Promise<{
    dataset_id: string;
    total: number;
    skip: number;
    limit: number;
    rows: Array<{
      csv_id: string;
      query: string;
      api_name?: string;
      endpoint?: string;
      request?: any;
      response?: any;
      scenario_type?: string;
      is_embedded: boolean;
    }>;
  }> {
    return this.request(`/api/v1/datasets/db/${datasetId}/rows?skip=${skip}&limit=${limit}`);
  }

  /**
   * Get dataset details
   */
  async getDatasetDetails(datasetId: string): Promise<{
    dataset_id: string;
    name: string;
    template_id?: string;
    total_rows: number;
    embedded_rows: number;
    embedding_status: string;
    embedding_model?: string;
    created_at: string;
  }> {
    return this.request(`/api/v1/datasets/db/${datasetId}`);
  }


  // ============================================================================
  // Query API
  // ============================================================================

  // ============================================================================
  // Run API (Query Execution & Results)
  // ============================================================================

  // ============================================================================
  // User Settings API
  // ============================================================================

  async getUserSettings(): Promise<any> {
    return this.request('/api/v1/user/settings', {
      method: 'GET',
    });
  }

  async updateUserSettings(data: { default_embedding_model?: string; embedding_dimension?: number }): Promise<any> {
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
  ): Promise<{ task_id: string; message: string; dataset_id: string }> {
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
  // Multi-Model Embedding Validation API
  // ============================================================================

  /**
   * Preflight check before search - validates model alignment
   * Call this BEFORE performing any semantic search
   */
  async preflightCheck(datasetId?: string): Promise<{
    ready: boolean;
    user_model: string;
    user_dimension: number;
    datasets_checked: number;
    compatible_datasets: number;
    incompatible_datasets: Array<{
      dataset_id: string;
      dataset_name: string;
      dataset_model: string;
      dataset_dimension: number;
    }>;
    message: string;
  }> {
    const params = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : '';
    return this.request(`/api/v1/model-validation/preflight-check${params}`);
  }

  /**
   * Get list of all available embedding models
   */
  async getAvailableModels(): Promise<{
    models: Array<{
      model_id: string;
      dimension: number;
      redis_index_name: string;
      redis_namespace: string;
    }>;
    default_model: string;
  }> {
    return this.request('/api/v1/model-validation/available-models');
  }

  // ============================================================================
  // LLM Configuration API
  // ============================================================================

  /**
   * List all LLM provider configurations for the current user
   */
  async listLLMConfigs(activeOnly: boolean = true): Promise<{
    configs: Array<{
      config_id: string;
      name: string;
      provider: string;
      model_name: string;
      base_url?: string;
      model_type: string;
      config_params: Record<string, any>;
      is_default: boolean;
      is_active: boolean;
      has_api_key: boolean;
      api_key_masked?: string;
      last_tested_at?: string;
      last_test_success?: boolean;
      last_test_message?: string;
      last_test_latency_ms?: number;
      created_at: string;
      updated_at?: string;
    }>;
  }> {
    const params = activeOnly ? '' : '?active_only=false';
    const configs = await this.request<any[]>(`/api/v1/llm-config${params}`);
    return { configs };
  }

  /**
   * Get a specific LLM configuration
   */
  async getLLMConfig(configId: string): Promise<{
    config_id: string;
    name: string;
    provider: string;
    model_name: string;
    base_url?: string;
    model_type: string;
    config_params: Record<string, any>;
    is_default: boolean;
    is_active: boolean;
    has_api_key: boolean;
    api_key_masked?: string;
    last_tested_at?: string;
    last_test_success?: boolean;
    last_test_message?: string;
    last_test_latency_ms?: number;
    created_at: string;
    updated_at?: string;
  }> {
    return this.request(`/api/v1/llm-config/${configId}`);
  }

  /**
   * Create a new LLM provider configuration
   */
  async createLLMConfig(data: {
    name: string;
    provider: string;
    model_name: string;
    api_key?: string;
    base_url?: string;
    model_type?: string;
    config_params?: Record<string, any>;
    is_default?: boolean;
  }): Promise<{
    config_id: string;
    name: string;
    provider: string;
    model_name: string;
    is_default: boolean;
    created_at: string;
  }> {
    return this.request('/api/v1/llm-config', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Update an LLM configuration
   */
  async updateLLMConfig(
    configId: string,
    data: {
      name?: string;
      model_name?: string;
      api_key?: string;
      base_url?: string;
      model_type?: string;
      config_params?: Record<string, any>;
      is_active?: boolean;
    }
  ): Promise<any> {
    return this.request(`/api/v1/llm-config/${configId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete an LLM configuration
   */
  async deleteLLMConfig(configId: string): Promise<void> {
    return this.request(`/api/v1/llm-config/${configId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Set an LLM configuration as default
   */
  async setDefaultLLMConfig(configId: string): Promise<{ message: string }> {
    return this.request(`/api/v1/llm-config/${configId}/set-default`, {
      method: 'POST',
    });
  }

  /**
   * Test LLM configuration connectivity
   */
  async testLLMConfig(configId: string): Promise<{
    success: boolean;
    message: string;
    latency_ms?: number;
    model_info?: Record<string, any>;
    error_code?: string;
  }> {
    return this.request(`/api/v1/llm-config/${configId}/test`, {
      method: 'POST',
    });
  }

  /**
   * Get default LLM configuration
   */
  async getDefaultLLMConfig(): Promise<{
    config_id: string;
    name: string;
    provider: string;
    model_name: string;
  } | null> {
    return this.request('/api/v1/llm-config/default');
  }

  /**
   * Get list of supported LLM providers
   */
  async getLLMProviders(): Promise<{
    providers: Record<string, {
      name: string;
      description: string;
      requires_api_key: boolean;
      supports_custom_base_url: boolean;
      default_models: string[];
      implemented?: boolean;
    }>;
    implemented: string[];
  }> {
    return this.request('/api/v1/llm-config/providers');
  }

  /**
   * List available Ollama LLM models
   */
  async listOllamaLLMModels(): Promise<{
    models: Array<{
      id: string;
      name: string;
      description?: string;
      context_length: number;
      is_local: boolean;
    }>;
    local_count: number;
  }> {
    return this.request('/api/v1/llm-config/ollama/models');
  }

  /**
   * Pull an Ollama LLM model
   */
  async pullOllamaLLMModel(modelName: string): Promise<{
    status: string;
    message: string;
  }> {
    return this.request(`/api/v1/llm-config/ollama/pull?model_name=${encodeURIComponent(modelName)}`, {
      method: 'POST',
    });
  }

  // ============================================================================
  // Embedding Model API
  // ============================================================================

  /**
   * The embedding model this deployment routes with.
   *
   * There is exactly one: it is set per deployment (EXECUTION_MODE) because every
   * indexed vector and every query must come from the same model. Returned in the
   * list shape older callers expect.
   */
  async listEmbeddingModels(): Promise<{
    models: Array<{
      name: string;
      display_name: string;
      size: string;
      is_local: boolean;
      is_registered: boolean;
      dimension: number | null;
      family: string | null;
      is_likely_embedding?: boolean;
    }>;
    count: number;
    local_count: number;
    registered_count: number;
  }> {
    const health = await this.request<{ runtime?: { embedder?: { model: string; dimension: number } } }>(
      '/api/v1/health'
    );
    const embedder = health.runtime?.embedder;
    const models = embedder
      ? [{
          name: embedder.model,
          display_name: embedder.model,
          size: '',
          is_local: true,
          is_registered: true,
          dimension: embedder.dimension,
          family: null,
          is_likely_embedding: true,
        }]
      : [];
    return { models, count: models.length, local_count: models.length, registered_count: models.length };
  }

  /**
   * Pull an Ollama embedding model
   * Note: This operation can take several minutes for larger models.
   * Uses a 10-minute timeout to accommodate large model downloads.
   */
  async pullEmbeddingModel(modelName: string): Promise<{
    model_id: string;
    dimension: number;
    display_name: string;
    redis_index: string;
    status: string;
  }> {
    const params = new URLSearchParams({ model_name: modelName });
    const url = `${this.baseUrl}/api/v1/embeddings/models/pull?${params}`;
    
    // SECURITY: auth via HttpOnly cookie (credentials: 'include' below).
    // No client-side token handling.

    // Use AbortController for timeout (10 minutes for large model pulls)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minute timeout
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        // Handle 401 Unauthorized - same as main request method
        if (response.status === 401) {
          if (typeof window !== 'undefined') {
            // Clear the cached profile (non-sensitive) and re-authenticate.
            localStorage.removeItem('nlpforge_user');
            redirectToLogin();
          }
        }
        
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { error: `HTTP ${response.status}`, detail: `HTTP ${response.status}` };
        }
        throw { ...errorData, status: response.status };
      }
      
      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw { detail: 'Model pull timed out. The model may still be downloading in the background.' };
      }
      throw error;
    }
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
