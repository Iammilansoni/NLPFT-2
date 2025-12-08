/**
 * Dataset API Client
 * TypeScript types and API client for dataset generation operations
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== Types ====================

export interface GenerateDatasetRequest {
  user_id: string;
  template_id: string;
  rows?: number;
  llm_model?: string;
  custom_prompt?: string;
  temperature?: number;
}

export interface GenerateDatasetResponse {
  dataset_id: string;
  job_id: string;
  status: string;
  message: string;
  estimated_time_seconds: number;
}

export type DatasetStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DatasetStatusResponse {
  dataset_id: string;
  job_id: string;
  status: DatasetStatus;
  progress: number; // 0.0 to 1.0
  rows_generated: number;
  total_rows: number;
  error_message?: string;
  download_url?: string;
  created_at: string;
  completed_at?: string;
}

export interface EmbedDatasetRequest {
  dataset_id: string;
  embedding_model?: string;
  vector_db_collection?: string;
}

export interface EmbedDatasetResponse {
  dataset_id: string;
  status: string;
  vectors_created: number;
  collection_name: string;
}

export interface Dataset {
  dataset_id: string;
  template_id: string;
  user_id: string;
  rows_requested: number;
  rows_generated: number;
  status: DatasetStatus;
  llm_model: string;
  custom_prompt?: string;
  embedding_model?: string;
  vector_db_collection?: string;
  csv_path?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  embedded_at?: string;
  download_url?: string;
}

export interface ListDatasetsResponse {
  total: number;
  limit: number;
  offset: number;
  datasets: Dataset[];
}

export interface ListDatasetsParams {
  user_id?: string;
  template_id?: string;
  status?: DatasetStatus;
  limit?: number;
  offset?: number;
}

// ==================== API Client ====================

export class DatasetApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token interceptor
    this.client.interceptors.request.use((config) => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  /**
   * Generate dataset using LLM
   */
  async generateDataset(data: GenerateDatasetRequest): Promise<GenerateDatasetResponse> {
    const response = await this.client.post<GenerateDatasetResponse>(
      '/api/v1/datasets/generate',
      {
        user_id: data.user_id,
        template_id: data.template_id,
        rows: data.rows || 500,
        llm_model: data.llm_model || 'gpt-4',
        custom_prompt: data.custom_prompt,
        temperature: data.temperature || 0.7,
      }
    );
    return response.data;
  }

  /**
   * Get dataset generation status
   */
  async getDatasetStatus(datasetId: string): Promise<DatasetStatusResponse> {
    const response = await this.client.get<DatasetStatusResponse>(
      `/api/v1/datasets/${datasetId}/status`
    );
    return response.data;
  }

  /**
   * Download dataset CSV
   */
  async downloadDataset(datasetId: string): Promise<Blob> {
    const response = await this.client.get(`/api/v1/datasets/${datasetId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Trigger download in browser
   */
  triggerDownload(datasetId: string, filename?: string): void {
    const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : '';
    const url = `${API_BASE_URL}/api/v1/datasets/${datasetId}/download`;
    
    // Create temporary link
    const link = document.createElement('a');
    link.href = token ? `${url}?token=${token}` : url;
    link.download = filename || `dataset_${datasetId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Embed dataset and store in Redis vector DB
   */
  async embedDataset(data: EmbedDatasetRequest): Promise<EmbedDatasetResponse> {
    const response = await this.client.post<EmbedDatasetResponse>(
      '/api/v1/datasets/embed',
      {
        dataset_id: data.dataset_id,
        embedding_model: data.embedding_model || 'sentence-transformers/all-MiniLM-L6-v2',
        vector_db_collection: data.vector_db_collection || 'api_templates',
      }
    );
    return response.data;
  }

  /**
   * List datasets with filters
   */
  async listDatasets(params?: ListDatasetsParams): Promise<ListDatasetsResponse> {
    const response = await this.client.get<ListDatasetsResponse>('/api/v1/datasets/list', {
      params: {
        user_id: params?.user_id,
        template_id: params?.template_id,
        status: params?.status,
        limit: params?.limit || 50,
        offset: params?.offset || 0,
      },
    });
    return response.data;
  }

  /**
   * Delete dataset
   */
  async deleteDataset(datasetId: string): Promise<{ message: string }> {
    const response = await this.client.delete(`/api/v1/datasets/${datasetId}`);
    return response.data;
  }
}

// Export singleton instance
export const datasetApi = new DatasetApiClient();
