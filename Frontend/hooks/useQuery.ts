/**
 * React Query Hooks for Query API
 * Custom hooks for data fetching and mutations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryApi } from '@/lib/api/query'
import type { QueryRequest } from '@/lib/api/types'

/**
 * Query Keys for React Query cache management
 */
export const queryKeys = {
  stats: ['query', 'stats'] as const,
  reindex: (intent: string) => ['query', 'reindex', intent] as const,
}

/**
 * Hook to process a natural language query
 */
export function useProcessQuery() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: QueryRequest) => queryApi.processQuery(request),
    onSuccess: () => {
      // Invalidate stats after successful query
      queryClient.invalidateQueries({ queryKey: queryKeys.stats })
    },
  })
}

/**
 * Hook to get vector database statistics
 */
export function useQueryStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: () => queryApi.getStats(),
    staleTime: 5000, // Consider data fresh for 5 seconds
    refetchInterval: 10000, // Auto-refresh every 10 seconds for real-time updates
  })
}

/**
 * Hook to reindex an intent
 */
export function useReindexIntent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (intent: string) => queryApi.reindex(intent),
    onSuccess: () => {
      // Invalidate stats after reindexing
      queryClient.invalidateQueries({ queryKey: queryKeys.stats })
    },
  })
}
