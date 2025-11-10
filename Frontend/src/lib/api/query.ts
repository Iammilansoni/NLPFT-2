/**
 * Query API Service
 * Handle natural language query processing and dataset generation
 */

import { apiGet, apiPost, API_ENDPOINTS } from './client'
import type {
  QueryRequest,
  QueryResponse,
  StatsResponse,
} from './types'

export const queryApi = {
  /**
   * Process a natural language query
   * Extracts intent, generates dataset if needed, and performs semantic search
   */
  async processQuery(request: QueryRequest): Promise<QueryResponse> {
    return apiPost<QueryResponse>(API_ENDPOINTS.query, request)
  },

  /**
   * Get statistics about the vector database
   */
  async getStats(): Promise<StatsResponse> {
    return apiGet<StatsResponse>(API_ENDPOINTS.stats)
  },

  /**
   * Reindex a specific intent
   * Regenerates embeddings for the given intent
   */
  async reindex(intent: string): Promise<{
    message: string
    deleted: number
    generated: number
    embedded: number
  }> {
    return apiPost(API_ENDPOINTS.reindex(intent))
  },
}
