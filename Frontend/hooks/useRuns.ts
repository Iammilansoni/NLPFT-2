/**
 * React Query Hooks for Test Runs API
 * Custom hooks for test run management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { runsApi } from '@/lib/api/runs'
import type { TestRun, TestRunCreateRequest } from '@/lib/api/types'

/**
 * Query Keys for React Query cache management
 */
export const runsKeys = {
  all: ['runs'] as const,
  list: (limit?: number, status?: string) => [...runsKeys.all, 'list', limit, status] as const,
  detail: (id: number) => [...runsKeys.all, 'detail', id] as const,
}

/**
 * Hook to get recent test runs for dashboard
 */
export function useRecentRuns(limit: number = 10, status?: string) {
  return useQuery({
    queryKey: runsKeys.list(limit, status),
    queryFn: () => runsApi.getRecent(limit, status),
    staleTime: 10000, // Consider fresh for 10 seconds
    refetchInterval: 30000, // Refetch every 30 seconds for real-time updates
  })
}

/**
 * Hook to get a specific test run
 */
export function useTestRun(id: number) {
  return useQuery({
    queryKey: runsKeys.detail(id),
    queryFn: () => runsApi.get(id),
    enabled: !!id,
  })
}

/**
 * Hook to create a test run
 */
export function useCreateTestRun() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (testRun: TestRunCreateRequest) => runsApi.create(testRun),
    onSuccess: () => {
      // Invalidate runs list to refetch
      queryClient.invalidateQueries({ queryKey: runsKeys.all })
    },
  })
}

/**
 * Hook to update a test run
 */
export function useUpdateTestRun() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: { status?: string; error_message?: string; tests_count?: number } }) =>
      runsApi.update(id, updates),
    onSuccess: (_, variables) => {
      // Invalidate both the list and the specific run
      queryClient.invalidateQueries({ queryKey: runsKeys.all })
      queryClient.invalidateQueries({ queryKey: runsKeys.detail(variables.id) })
    },
  })
}



