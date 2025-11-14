/**
 * Search API Service
 * Handle semantic search operations
 */

import { apiGet, API_ENDPOINTS } from './client'
import type {
  SemanticSearchRequest,
  SemanticSearchResponse,
} from './types'

export const searchApi = {
  /**
   * Perform semantic search on ingested API dataset
   */
  async search(request: SemanticSearchRequest): Promise<SemanticSearchResponse> {
    return apiGet<SemanticSearchResponse>(API_ENDPOINTS.search, {
      query: request.query,
      top_k: request.top_k || 5,
    })
  },
}
