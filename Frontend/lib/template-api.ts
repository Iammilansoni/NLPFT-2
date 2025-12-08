/**
 * API Client for Template Management
 * Handles all template-related API calls with proper typing
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// TYPE DEFINITIONS (matching Postgres schema)
// ============================================================================

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
export type TemplateStatus = 'draft' | 'review' | 'approved';
export type SecurityClassification = 'public' | 'internal' | 'secret' | 'highly-restricted';
export type UserRole = 'user' | 'reviewer' | 'admin';

export interface Template {
  template_id: string;
  user_id: string;
  api_name: string;
  description: string;
  base_url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  json_schema: Record<string, any>;
  sample_requests?: SampleRequest[];
  side_effects?: string | null;
  security_classification: SecurityClassification;
  domain_tags: string[];
  status: TemplateStatus;
  reviewer_notes?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface Parameter {
  parameter_id?: string;
  user_id: string;
  template_id: string;
  name: string;
  type: string;
  value?: string;
  example?: string;
  description?: string;
  required: boolean;
}

export interface ExpectedResponse {
  response_id?: string;
  user_id: string;
  template_id: string;
  status: number;
  fields: Record<string, any>;
}

export interface Metadata {
  metadata_id?: string;
  user_id: string;
  template_id: string;
  confidence?: number;
  remarks?: string;
  created_at?: string;
}

export interface SampleRequest {
  request: Record<string, any>;
  expected_response: Record<string, any>;
  note?: string;
}

export interface AuditLog {
  action: string;
  user_id: string;
  template_id: string;
  payload?: Record<string, any>;
}

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

export interface CreateTemplateRequest {
  user_id: string;
  api_name: string;
  description: string;
  base_url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  json_schema: Record<string, any>;
  sample_requests?: SampleRequest[];
  side_effects?: string | null;
  security_classification: SecurityClassification;
  domain_tags: string[];
  status: TemplateStatus;
  reviewer_notes?: string | null;
}

export interface ParameterSchema {
  name: string;
  type: string;
  description?: string;
  example?: string;
  required?: boolean;
}

// Backend expects this schema format for EnterpriseTemplateCreate
export interface BackendTemplateRequest {
  api_name: string;
  description: string;
  base_url: string;
  endpoint: string;
  method: HttpMethod;
  parameters: ParameterSchema[];
  sample_requests: Array<{
    scenario: string;
    request: Record<string, any>;
    expected_response?: Record<string, any>;
  }>;
  sample_responses: Array<Record<string, any>>;
  json_schema?: Record<string, any>;
  response_schema?: Record<string, any>;
  domain_tags: string[];
  security_classification: SecurityClassification;
  auth_config?: Record<string, any>;
  headers?: Record<string, string>;
  rate_limit?: Record<string, any>;
  assertions?: Array<Record<string, any>>;
}

export interface CreateTemplateResponse {
  template_id: string;
  message?: string;
}

export interface CreateParametersRequest {
  parameters: Omit<Parameter, 'parameter_id'>[];
}

export interface CreateExpectedResponsesRequest {
  expected_responses: Omit<ExpectedResponse, 'response_id'>[];
}

export interface CreateMetadataRequest {
  confidence?: number;
  remarks?: string;
}

// ============================================================================
// API CLIENT CLASS
// ============================================================================

class TemplateApiClient {
  private getAuthHeaders(): Record<string, string> {
    // TODO: Replace with your actual auth token retrieval
    const token = typeof window !== 'undefined' 
      ? localStorage.getItem('nlpforge_access_token') 
      : null;
    
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  /**
   * Transform frontend request to backend format
   */
  private transformToBackendFormat(data: CreateTemplateRequest, parameters?: ParameterSchema[]): BackendTemplateRequest {
    // Extract endpoint from base_url or use default
    let endpoint = '/api';
    try {
      const url = new URL(data.base_url);
      endpoint = url.pathname || '/api';
    } catch {
      // Keep default endpoint
    }

    // Transform sample_requests to backend format with scenario labels
    const scenarios = ['valid', 'edge', 'error'];
    const transformedSamples = (data.sample_requests || []).map((sr, idx) => ({
      scenario: scenarios[idx] || 'valid',
      request: sr.request,
      expected_response: sr.expected_response,
    }));

    // Extract sample_responses from sample_requests
    const sampleResponses = (data.sample_requests || []).map(sr => sr.expected_response);

    return {
      api_name: data.api_name,
      description: data.description,
      base_url: data.base_url,
      endpoint: endpoint,
      method: data.method,
      parameters: parameters || [{ name: 'default', type: 'string', description: 'Default parameter', required: false }],
      sample_requests: transformedSamples,
      sample_responses: sampleResponses,
      json_schema: data.json_schema,
      domain_tags: data.domain_tags,
      security_classification: data.security_classification,
      headers: data.headers,
    };
  }

  /**
   * Transform data for draft endpoints (relaxed validation)
   */
  private transformToDraftFormat(data: CreateTemplateRequest, parameters?: ParameterSchema[]): Record<string, any> {
    // Extract endpoint from base_url or use default
    let endpoint = '/api';
    try {
      if (data.base_url) {
        const url = new URL(data.base_url);
        endpoint = url.pathname || '/api';
      }
    } catch {
      // Keep default endpoint
    }

    // Transform sample_requests to backend format
    const transformedSamples = (data.sample_requests || []).map((sr, idx) => ({
      scenario: ['valid', 'edge', 'error'][idx] || 'valid',
      request: sr.request || {},
      expected_response: sr.expected_response || {},
    }));

    // Extract sample_responses from sample_requests
    const sampleResponses = (data.sample_requests || []).map(sr => sr.expected_response || {});

    return {
      api_name: data.api_name || 'Untitled Template',
      description: data.description || '',
      base_url: data.base_url || '',
      endpoint: endpoint,
      method: data.method || 'POST',
      parameters: parameters || [],
      sample_requests: transformedSamples,
      sample_responses: sampleResponses,
      json_schema: data.json_schema || {},
      domain_tags: data.domain_tags || [],
      security_classification: data.security_classification || 'public',
      headers: data.headers || {},
    };
  }

  /**
   * Create a new template (strict validation)
   */
  async createTemplate(data: CreateTemplateRequest, parameters?: ParameterSchema[]): Promise<CreateTemplateResponse> {
    const backendData = this.transformToBackendFormat(data, parameters);
    const response = await axios.post<CreateTemplateResponse>(
      `${API_BASE_URL}/api/v1/templates`,
      backendData,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Create a draft template (relaxed validation)
   * Use this for saving incomplete work in progress
   */
  async createDraftTemplate(data: CreateTemplateRequest, parameters?: ParameterSchema[]): Promise<CreateTemplateResponse> {
    const backendData = this.transformToDraftFormat(data, parameters);
    try {
      const response = await axios.post<CreateTemplateResponse>(
        `${API_BASE_URL}/api/v1/templates/draft`,
        backendData,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error: any) {
      // Extract and throw a more useful error message
      const detail = error?.response?.data?.detail;
      if (detail) {
        throw { message: typeof detail === 'string' ? detail : JSON.stringify(detail), detail };
      }
      throw error;
    }
  }

  /**
   * Get template by ID
   */
  async getTemplate(templateId: string): Promise<Template> {
    const response = await axios.get<Template>(
      `${API_BASE_URL}/api/v1/templates/${templateId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Update existing template (strict validation)
   */
  async updateTemplate(
    templateId: string, 
    data: Partial<CreateTemplateRequest>,
    parameters?: ParameterSchema[]
  ): Promise<Template> {
    // Transform the data to backend format for updates
    const transformedData: Record<string, any> = {};
    
    if (data.api_name) transformedData.api_name = data.api_name;
    if (data.description) transformedData.description = data.description;
    if (data.base_url) transformedData.base_url = data.base_url;
    if (data.method) transformedData.method = data.method;
    if (data.headers) transformedData.headers = data.headers;
    if (data.json_schema) transformedData.json_schema = data.json_schema;
    if (data.security_classification) transformedData.security_classification = data.security_classification;
    if (data.domain_tags) transformedData.domain_tags = data.domain_tags;
    if (data.side_effects !== undefined) transformedData.side_effects = data.side_effects;
    
    // Transform sample_requests to backend format
    if (data.sample_requests) {
      const scenarios = ['valid', 'edge', 'error'];
      transformedData.sample_requests = data.sample_requests.map((sr, idx) => ({
        scenario: scenarios[idx] || 'valid',
        request: sr.request,
        expected_response: sr.expected_response,
      }));
      transformedData.sample_responses = data.sample_requests.map(sr => sr.expected_response);
    }
    
    // Include parameters if provided
    if (parameters && parameters.length > 0) {
      transformedData.parameters = parameters;
    }
    
    // Extract endpoint from base_url
    if (data.base_url) {
      try {
        const url = new URL(data.base_url);
        transformedData.endpoint = url.pathname || '/api';
      } catch {
        transformedData.endpoint = '/api';
      }
    }
    
    const response = await axios.put<Template>(
      `${API_BASE_URL}/api/v1/templates/${templateId}`,
      transformedData,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Update a draft template (relaxed validation)
   * Use this for saving incomplete work in progress
   */
  async updateDraftTemplate(
    templateId: string, 
    data: Partial<CreateTemplateRequest>,
    parameters?: ParameterSchema[]
  ): Promise<Template> {
    const transformedData = this.transformToDraftFormat(data as CreateTemplateRequest, parameters);
    
    try {
      const response = await axios.put<Template>(
        `${API_BASE_URL}/api/v1/templates/draft/${templateId}`,
        transformedData,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error: any) {
      // Extract and throw a more useful error message
      const detail = error?.response?.data?.detail;
      if (detail) {
        throw { message: typeof detail === 'string' ? detail : JSON.stringify(detail), detail };
      }
      throw error;
    }
  }

  /**
   * List all templates (with optional filters)
   */
  async listTemplates(filters?: {
    status?: TemplateStatus;
    user_id?: string;
    domain_tags?: string[];
  }): Promise<Template[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.user_id) params.append('user_id', filters.user_id);
    if (filters?.domain_tags) {
      filters.domain_tags.forEach(tag => params.append('domain_tags', tag));
    }

    const response = await axios.get<Template[]>(
      `${API_BASE_URL}/api/v1/templates?${params.toString()}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Bulk create parameters for a template
   */
  async createParameters(
    templateId: string, 
    data: CreateParametersRequest
  ): Promise<{ success: boolean; count: number }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/templates/${templateId}/parameters`,
      data,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Get parameters for a template
   */
  async getParameters(templateId: string): Promise<Parameter[]> {
    const response = await axios.get<Parameter[]>(
      `${API_BASE_URL}/api/v1/templates/${templateId}/parameters`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Create expected responses for a template
   */
  async createExpectedResponses(
    templateId: string,
    data: CreateExpectedResponsesRequest
  ): Promise<{ success: boolean; count: number }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/templates/${templateId}/expected_responses`,
      data,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Get expected responses for a template
   */
  async getExpectedResponses(templateId: string): Promise<ExpectedResponse[]> {
    const response = await axios.get<ExpectedResponse[]>(
      `${API_BASE_URL}/api/v1/templates/${templateId}/expected_responses`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Create metadata entry for a template
   */
  async createMetadata(
    templateId: string,
    data: CreateMetadataRequest
  ): Promise<Metadata> {
    const response = await axios.post<Metadata>(
      `${API_BASE_URL}/api/v1/templates/${templateId}/metadata`,
      data,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Approve a template (admin/reviewer only)
   */
  async approveTemplate(templateId: string): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/templates/${templateId}/approve`,
      {},
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Create audit log entry
   */
  async createAuditLog(data: AuditLog): Promise<{ success: boolean }> {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/audit/logs`,
      data,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  /**
   * Delete template
   */
  async deleteTemplate(templateId: string): Promise<{ success: boolean }> {
    const response = await axios.delete(
      `${API_BASE_URL}/api/v1/templates/${templateId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }
}

// Export singleton instance
export const templateApi = new TemplateApiClient();
export default templateApi;
