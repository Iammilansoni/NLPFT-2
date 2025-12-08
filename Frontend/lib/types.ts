// API Types for NLPForge Frontend

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  checks: {
    status: string;
    database: {
      status: string;
      response_time_ms: number;
      connection_pool: string;
    };
    rule_engine: {
      status: string;
      response_time_ms: number;
      active_patterns: number;
      total_parses: number;
      successful_parses: number;
      failed_parses: number;
      test_parse_successful: boolean;
    };
    system: {
      status: string;
      memory: {
        status: string;
        usage_percent: number;
        available_mb: number;
        total_mb: number;
      };
      cpu: {
        status: string;
        usage_percent: number;
      };
      process_id: number;
    };
    application: {
      status: string;
      version: string;
      uptime_seconds: number;
      uptime_formatted: string;
    };
    health_check: {
      duration_ms: number;
      timestamp: string;
    };
  };
}

export interface ConvertRequest {
  text: string;
  target_format?: string;
}

export interface ConvertStep {
  function: string;
  args: Record<string, unknown>;
  confidence: number;
  provenance?: string;
  template?: string;
  matched_text?: string;
  order?: number;
}

export interface ConvertResponse {
  steps: ConvertStep[];
  overall_confidence: number;
  unresolved_tokens: string[];
  processing_time_ms: number;
  status: string;
}

export interface DictionaryFunction {
  _id?: string;
  function_name: string;
  description: string;
  templates: string[];
  examples: string[];
  args: Record<string, unknown>;
  tags: string[];
  category: string;
  confidence_threshold: number;
  created_at?: string;
  updated_at?: string;
}

// API response types to handle the backend format
export interface ApiFunctionResponse {
  id: string;
  name: string;
  display_name?: string;
  category: string;
  description: string;
  templates: string[];
  examples: string[];
  arguments: Record<string, unknown>;
  tags: string[];
  confidence_threshold?: number;
  created_at?: string;
  updated_at?: string;
}

export interface DictionaryListResponse {
  functions: ApiFunctionResponse[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface CreateFunctionResponse {
  message: string;
  function_id: string;
  name: string;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: unknown;
}

export interface EmbeddingModel {
  id: string;
  name: string;
  dimension: number;
  context_length: number;
  cpu_friendly: boolean;
  description: string;
  provider: string;
}

export interface DatasetLLM {
  id: string;
  name: string;
  provider: string;
  context_length: number;
  cost_per_1k: number;
  description: string;
}

export interface APIResponse<T> {
  status: string;
  data: T;
  message?: string;
}