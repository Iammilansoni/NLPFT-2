/**
 * API Type Definitions
 * TypeScript types matching backend Pydantic models
 */

// ============= Query API Types =============

export interface QueryRequest {
  query: string
  generate_dataset?: boolean
  num_examples?: number
  top_k?: number
}

export interface QueryResponse {
  query: string
  intent: string
  slots: Record<string, any>
  confidence: number
  best_matches: BestMatch[]
  dataset_generated: boolean
  dataset_info?: DatasetInfo
  search_results: SearchResult[]
}

export interface BestMatch {
  api: string
  score: number
  confidence: number
}

export interface DatasetInfo {
  intent: string
  num_examples: number
  paths: {
    csv: string
    json: string
  }
  redis_keys?: number
}

export interface SearchResult {
  query: string
  intent: string
  similarity: number
  confidence?: number
  slots?: Record<string, any>
  api_name?: string
  endpoint?: string
}

export interface StatsResponse {
  total_embeddings: number
  intents: Record<string, number>
  model: string
  index_name: string
}

// ============= Template API Types =============

export interface Parameter {
  name: string
  type: string
  required: boolean
  description?: string
}

export interface Template {
  api_name: string
  description: string
  endpoint: string
  method: string
  intent_keywords: string[]
  parameters: Parameter[]
  example_queries: string[]
  response_format?: Record<string, any>
}

export interface TemplateCreateRequest {
  api_name: string
  description: string
  endpoint: string
  method: string
  intent_keywords: string[]
  parameters: Parameter[]
  example_queries?: string[]
  response_format?: Record<string, any>
}

export interface TemplateUpdateRequest {
  description?: string
  endpoint?: string
  method?: string
  intent_keywords?: string[]
  parameters?: Parameter[]
  example_queries?: string[]
  response_format?: Record<string, any>
}

export interface SyncResponse {
  success: boolean
  message: string
  added: number
  updated: number
  total: number
}

export interface ReloadResponse {
  success: boolean
  message: string
  services_reloaded: string[]
  templates_count: number
}

export interface TemplateStatsResponse {
  total_templates: number
  template_names: string[]
  cache_stats: Record<string, any>
}

// ============= Search API Types =============

export interface SemanticSearchRequest {
  query: string
  top_k?: number
}

export interface SemanticSearchResult {
  query: string
  api: string
  endpoint: string
  request: Record<string, any>
  response: Record<string, any>
  cosine_distance: number
  cosine_similarity: number
}

export interface SemanticSearchResponse {
  input_query: string
  top_k: number
  results: SemanticSearchResult[]
}

// ============= Dataset API Types =============

export interface DatasetListItem {
  name: string
  path: string
  size: number
  modified: string
}

export interface DatasetGenerateRequest {
  intent: string
  num_examples?: number
  use_gemini?: boolean
  merge_existing?: boolean
}

export interface DatasetGenerateResponse {
  intent: string
  num_examples: number
  paths: {
    csv: string
    json: string
  }
  message: string
}

// ============= General Types =============

export interface ErrorResponse {
  error: string
  detail?: string
  timestamp: string
  request_id?: string
}

export interface HealthResponse {
  name: string
  version: string
  status: string
  docs: string
  health: string
}
