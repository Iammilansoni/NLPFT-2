/**
 * API Types for NLPForge Backend Integration
 * Aligned with backend endpoints and response formats
 */

// ============================================================================
// Search API Types
// ============================================================================

export interface SearchRequest {
  query: string;
  top_k?: number;
  intent?: string[];
  min_similarity?: number;
  from_date?: string;
  to_date?: string;
  template_version?: string;
  embedding_model?: string; // Add embedding model selection
}

export interface SearchResultItem {
  query: string;
  api: string;
  endpoint: string;
  request: Record<string, any>;
  response: Record<string, any>;
  cosine_distance: number;
  cosine_similarity: number;
  intent?: string;
  confidence?: number;
  template_name?: string;
  template_version?: string;
  created_at?: string;
  hash_id?: string;
}

export interface SearchResponse {
  input_query: string;
  top_k: number;
  results: SearchResultItem[];
}

// ============================================================================
// Template API Types
// ============================================================================

export interface ParameterModel {
  name: string;
  type: string;
  value?: string;
  example?: string;
  required: boolean;
  description?: string;
}

export interface TemplateModel {
  template_id?: string;
  api_name: string;
  description: string;
  endpoint: string;
  base_url?: string;
  method: string;
  intent_keywords: string[];
  parameters: ParameterModel[];
  example_queries: string[];
  response_format?: Record<string, any>;
  status?: 'active' | 'draft' | 'deprecated' | 'review' | 'approved' | 'rejected';
  confidence?: number;
  version?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
}

export interface TemplateCreateRequest {
  api_name: string;
  description: string;
  endpoint: string;
  method: string;
  intent_keywords: string[];
  parameters: ParameterModel[];
  example_queries?: string[];
  response_format?: Record<string, any>;
}

export interface TemplateUpdateRequest {
  description?: string;
  endpoint?: string;
  method?: string;
  intent_keywords?: string[];
  parameters?: ParameterModel[];
  example_queries?: string[];
  response_format?: Record<string, any>;
  status?: 'active' | 'draft' | 'deprecated';
}

export interface TemplateSyncResponse {
  success: boolean;
  message: string;
  added: number;
  updated: number;
  total: number;
}

export interface TemplateReloadResponse {
  success: boolean;
  message: string;
  services_reloaded: string[];
  templates_count: number;
}

export interface TemplateStatsResponse {
  total_templates: number;
  by_status: {
    draft: number;
    review: number;
    approved: number;
    rejected: number;
  };
}

// ============================================================================
// Dataset API Types
// ============================================================================

export interface DatasetRow {
  id?: string;
  case_name?: string;
  intent: string;
  query: string;
  slots?: Record<string, any>;
  request_json?: Record<string, any>;
  expected_json?: Record<string, any>;
  template_version?: string;
  similarity?: number;
  hash_id?: string;
  created_at?: string;
  updated_at?: string;
  tags?: string[];
}

export interface DatasetListResponse {
  datasets: string[];
}

export interface DatasetUploadResponse {
  message: string;
  file?: string;
  result?: {
    inserted: number;
    total: number;
  };
}

export interface DatasetGenerateRequest {
  template_id: string;
  num_examples?: number;
  custom_prompt?: string;
  focus_areas?: string[];
  scenario_distribution?: Record<string, number>;
  // Legacy fields (deprecated)
  seed_prompt?: string;
  examples?: number;
  api_name?: string;
  endpoint?: string;
  intent?: string;
  include_negatives?: boolean;
  include_boundaries?: boolean;
  include_security?: boolean;
  model?: string;
}

export interface DatasetGenerateResponse {
  message: string;
  csv_path: string;
  ingestion?: {
    inserted: number;
    total: number;
  };
  dataset_info?: {
    intent: string;
    total_examples: number;
    base_examples: number;
    generated_examples: number;
  };
}

export interface DatasetExportRequest {
  format: 'csv';
  intent?: string;
  from_date?: string;
  to_date?: string;
  ids?: string[];
}

// ============================================================================
// Query API Types (Main endpoint)
// ============================================================================

export interface QueryRequest {
  query: string;
  generate_dataset?: boolean;
  num_examples?: number;
  top_k?: number;
}

export interface QueryResponse {
  query: string;
  intent: string;
  slots: Record<string, any>;
  confidence: number;
  best_matches: Array<{
    api: string;
    score: number;
    confidence: number;
  }>;
  dataset_generated?: boolean;
  dataset_info?: {
    intent: string;
    total_examples: number;
    base_examples: number;
    generated_examples: number;
    paths: {
      csv: string;
      json: string;
    };
    redis_keys: number;
  };
  search_results?: SearchResultItem[];
}

// ============================================================================
// Common Types
// ============================================================================

export interface ApiError {
  error: string;
  detail?: string;
  timestamp?: string;
  request_id?: string;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type SortDirection = 'asc' | 'desc';

export interface SortParams {
  sort_by?: string;
  sort_direction?: SortDirection;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface SearchFilters {
  intent?: string[];
  min_similarity?: number;
  max_similarity?: number;
  from_date?: string;
  to_date?: string;
  template_version?: string;
}

export interface TemplateFilters {
  status?: ('active' | 'draft' | 'deprecated' | 'review' | 'approved' | 'rejected')[];
  intent?: string[];
  min_confidence?: number;
  max_confidence?: number;
}

export interface DatasetFilters {
  intent?: string[];
  template_version?: string[];
  from_date?: string;
  to_date?: string;
  has_similarity?: boolean;
}

// ============================================================================
// Run API Types (Query Execution & Results)
// ============================================================================

export type RunStep =
  | 'queued'
  | 'parse_intent'
  | 'dataset_generated'
  | 'embeddings_done'
  | 'vector_search_done'
  | 'ready'
  | 'selenium_running'
  | 'selenium_done'
  | 'complete'
  | 'error'
  | 'failed';

export interface RunStatus {
  run_id: string;
  step: RunStep;
  progress: number; // 0.0 - 1.0
  logs?: string[];
  error?: string;
  started_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface MeaningJSON {
  intent: string;
  template: string;
  slots: Record<string, any>;
  confidence: number;
  evidence: {
    similar_cases: Array<{
      id: string;
      similarity: number;
      text?: string;
    }>;
  };
}

export interface SeleniumResults {
  pass_rate: number;
  total_tests: number;
  passed: number;
  failed: number;
  skipped?: number;
  duration_ms: number;
  started_at: string;
  completed_at: string;
  artifacts: Array<{
    type: 'screenshot' | 'video' | 'log' | 'report';
    url: string;
    name: string;
    size_bytes?: number;
  }>;
  test_cases: Array<{
    id: string;
    name: string;
    status: 'passed' | 'failed' | 'skipped';
    duration_ms: number;
    error?: string;
    screenshot_url?: string;
  }>;
}

export interface RunResults {
  run_id: string;
  meaning_json: MeaningJSON;
  template: TemplateModel;
  dataset_stats: {
    total_cases: number;
    generated_at: string;
    size_bytes?: number;
  };
  selenium_results?: SeleniumResults;
  created_at: string;
  completed_at?: string;
}

export interface CreateRunRequest {
  text: string;
  options?: {
    generate_dataset?: boolean;
    compute_embeddings?: boolean;
    run_selenium?: boolean;
    dataset_size?: number;
  };
}

export interface CreateRunResponse {
  run_id: string;
  status: 'queued' | 'running';
  message?: string;
}

