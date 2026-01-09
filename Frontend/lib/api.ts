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
import { getApiBase } from './runtime-config';

const RAW_API_BASE = getApiBase();
const API_BASE_URL = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : '';

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

    console.log('[API] Request:', endpoint);
    console.log('[API] Token:', token ? token.substring(0, 20) + '...' : 'No token');

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

      console.log('[API] Response:', response.status, endpoint);

      if (!response.ok) {
        // Handle 401 Unauthorized
        if (response.status === 401) {
          console.log('[API] 401 Unauthorized - Token might be invalid or expired');
          console.log('Token was:', token ? 'present' : 'missing');

          if (typeof window !== 'undefined') {
            // Don't immediately redirect - let's see what's happening first
            console.log('[API] Would redirect to login, but holding off for debugging');
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
  // Two-Stage Ranking API (KNN Search + FlashRank Reranking)
  // ============================================================================

  /**
   * Two-Stage AI Ranking Engine
   * 
   * Stage 1: Vector Retrieval (Top-K) from Redis Vector DB using KNN search
   * Stage 2: FlashRank Reranking with ms-marco-MiniLM-L-12-v2 cross-encoder
   * 
   * @param query - Search query text
   * @param topK - Number of candidates to retrieve (default: 5)
   * @returns Ranked results with FlashRank scores
   */
  async rankQuery(query: string, topK: number = 5): Promise<{
    query: string;
    ranked_results: Array<{
      rank: number;
      score: number;
      text: string;
    }>;
  }> {
    return this.request(`/api/v1/ranking/rank?query=${encodeURIComponent(query)}&top_k=${topK}`);
  }

  /**
   * Detailed Two-Stage AI Ranking with full metadata
   * 
   * Returns both Stage 1 and Stage 2 results with complete information including:
   * - Stage 1 vector retrieval results with similarity scores
   * - Stage 2 reranked results with full metadata (API, endpoint, request/response)
   * 
   * @param query - Search query text
   * @param topK - Number of candidates to retrieve (default: 5)
   */
  async rankQueryDetailed(query: string, topK: number = 5): Promise<{
    query: string;
    stage1_results: Array<{
      api: string;
      query: string;
      endpoint: string;
      method: string;
      request: any;
      response: any;
      cosine_similarity: number;
    }>;
    ranked_results: Array<{
      rank: number;
      score: number;
      text: string;
      api: string;
      endpoint: string;
      method: string;
      request: any;
      response: any;
      original_similarity: number;
      vector_score: number;
    }>;
  }> {
    return this.request('/api/v1/ranking/rank/detailed', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    });
  }

  /**
   * Get reranker model information
   */
  async getRerankerInfo(): Promise<{
    model_name: string;
    model_type: string;
    framework: string;
    loaded: boolean;
  }> {
    return this.request('/api/v1/ranking/rank/info');
  }

  /**
   * Semantic API Retrieval Pipeline
   * 
   * Returns stage-by-stage results:
   * - Stage 1: Vector Search (Redis)
   * - Stage 2: Re-ranking (grouped by t_id)
   * - Final Output: Best match from PostgreSQL
   * - Slot Extraction: Extracted values from query
   * 
   * @param query - Natural language query
   * @param topK - Number of candidates to retrieve (default: 10)
   * @param intentType - Optional query intent hint
   * @param includeAlternatives - Whether to include alternative APIs
   * @param includeSlotExtraction - Whether to extract values from query (default: true)
   */
  async semanticRetrieve(
    query: string,
    topK: number = 10,
    intentType?: string,
    includeAlternatives: boolean = false,
    includeSlotExtraction: boolean = true
  ): Promise<{
    success: boolean;
    // Stage 1: Vector Search Results
    stage1_vector_search: Array<{
      query: string;
      similarity_score: number;
      t_id: string;
    }>;
    // Stage 2: Re-ranking Results
    stage2_reranking: Array<{
      t_id: string;
      avg_similarity: number;
      avg_confidence_score: number;
      final_score: number;
      rank: number;
      match_count: number;
    }>;
    // Final Output (from PostgreSQL)
    final_output: {
      t_id: string;
      api_name: string;
      endpoint: string;
      method: string;
      confidence_score: number;
      request_schema: any;
      response_schema: any;
      extracted_request_body?: Record<string, any>;
    } | null;
    // Metadata
    metadata: {
      query: string;
      top_k: number;
      total_candidates: number;
      processing_time_ms: number;
      t_id?: string;
      match_count?: number;
      avg_similarity?: number;
      avg_confidence?: number;
      intent_alignment?: number;
      dominant_intent?: string;
      domain_tags?: string[];
      matched_queries?: string[];
    };
    // Slot Extraction Result
    extracted_request_body?: Record<string, any>;
    // Legacy fields for backward compatibility
    api_name?: string;
    endpoint?: string;
    method?: string;
    base_url?: string;
    confidence?: number;
    alternatives?: Array<{
      t_id: string;
      api_name: string;
      endpoint: string;
      method: string;
      avg_similarity: number;
      match_count: number;
    }>;
    error?: string;
  }> {
    return this.request('/api/v1/ranking/semantic-retrieve', {
      method: 'POST',
      body: JSON.stringify({
        query,
        top_k: topK,
        intent_type: intentType,
        include_alternatives: includeAlternatives,
        include_slot_extraction: includeSlotExtraction
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

    // Get auth token
    const token = typeof window !== 'undefined' ? localStorage.getItem('nlpforge_access_token') : null;

    return fetch(`${this.baseUrl}/api/v1/datasets/upload`, {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
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

  async embedDataset(filename: string, embeddingModel?: string): Promise<any> {
    return this.request<any>('/api/v1/datasets/embed', {
      method: 'POST',
      body: JSON.stringify({
        filename,
        embedding_model: embeddingModel,
      }),
    });
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

  async query(data: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/api/v1/query/query', {
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
   * Check model compatibility between user settings and dataset
   * Returns whether search can proceed without dimension mismatch
   */
  async checkModelCompatibility(datasetId: string): Promise<{
    compatible: boolean;
    user_model: string;
    user_dimension: number;
    dataset_model: string | null;
    dataset_dimension: number | null;
    can_search: boolean;
    message: string;
    recommendation?: string;
  }> {
    return this.request(`/api/v1/model-validation/check-compatibility/${datasetId}`);
  }

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
   * Switch to use the dataset's embedding model temporarily
   * Updates user settings to match dataset model
   */
  async switchToDatasetModel(datasetId: string): Promise<{
    success: boolean;
    previous_model: string;
    new_model: string;
    new_dimension: number;
    message: string;
  }> {
    return this.request(`/api/v1/model-validation/switch-to-dataset-model/${datasetId}`, {
      method: 'POST',
    });
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

  /**
   * Multi-model semantic search with governance
   * Uses model-isolated Redis indices
   */
  async multiModelSemanticSearch(
    query: string,
    options?: {
      datasetId?: string;
      topK?: number;
      minSimilarity?: number;
      useDatasetModel?: boolean;
    }
  ): Promise<{
    success: boolean;
    query: string;
    model_used: string;
    dimension: number;
    stage1_vector_search: Array<{
      query: string;
      similarity_score: number;
      t_id: string;
    }>;
    stage2_reranking: Array<{
      t_id: string;
      avg_similarity: number;
      avg_confidence_score: number;
      final_score: number;
      rank: number;
      match_count: number;
    }>;
    final_output: {
      t_id: string;
      api_name: string;
      endpoint: string;
      method: string;
      confidence_score: number;
      request_schema: any;
      response_schema: any;
    } | null;
    metadata: {
      query: string;
      top_k: number;
      total_candidates: number;
      processing_time_ms: number;
    };
    error?: string;
  }> {
    return this.request('/api/v1/multi-model-query/semantic-search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        dataset_id: options?.datasetId,
        top_k: options?.topK ?? 10,
        min_similarity: options?.minSimilarity ?? 0.6,
        use_dataset_model: options?.useDatasetModel ?? false,
      }),
    });
  }

  /**
   * Embed dataset with multi-model governance
   */
  async multiModelEmbedDataset(
    datasetId: string,
    options?: {
      model?: string;
      useSettingsModel?: boolean;
    }
  ): Promise<{
    success: boolean;
    dataset_id: string;
    model_used: string;
    dimension: number;
    embedded_count: number;
    message: string;
  }> {
    return this.request(`/api/v1/multi-model-query/datasets/${datasetId}/embed`, {
      method: 'POST',
      body: JSON.stringify({
        model: options?.model,
        use_settings_model: options?.useSettingsModel ?? true,
      }),
    });
  }

  /**
   * Re-embed dataset with a different model
   */
  async multiModelReembedDataset(
    datasetId: string,
    targetModel: string,
    options?: {
      clearExisting?: boolean;
      chunkSize?: number;
    }
  ): Promise<{
    success: boolean;
    dataset_id: string;
    previous_model: string | null;
    new_model: string;
    new_dimension: number;
    embedded_count: number;
    message: string;
  }> {
    return this.request(`/api/v1/multi-model-query/datasets/${datasetId}/reembed`, {
      method: 'POST',
      body: JSON.stringify({
        target_model: targetModel,
        clear_existing: options?.clearExisting ?? true,
        chunk_size: options?.chunkSize ?? 100,
      }),
    });
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
