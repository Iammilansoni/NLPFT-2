/**
 * React Query Hooks for Search API
 * Custom hooks for semantic search
 */

import { useMutation } from '@tanstack/react-query'
import { searchApi } from '@/lib/api/search'
import type { SemanticSearchRequest } from '@/lib/api/types'

/**
 * Hook to perform semantic search
 */
export function useSemanticSearch() {
  return useMutation({
    mutationFn: (request: SemanticSearchRequest) => searchApi.search(request),
  })
}
