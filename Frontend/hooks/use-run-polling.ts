import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { RunStatus, RunResults } from '@/lib/api-types'

interface UseRunPollingOptions {
  runId: string | null
  enabled?: boolean
  onComplete?: (results: RunResults) => void
  onError?: (error: Error) => void
}

interface UseRunPollingReturn {
  status: RunStatus | undefined
  results: RunResults | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
  isComplete: boolean
  progress: number
  currentStep: string | undefined
}

/**
 * Custom hook to poll run status and automatically fetch results when complete.
 * 
 * @example
 * ```tsx
 * const { status, results, isComplete, progress } = useRunPolling({
 *   runId: 'run_123',
 *   enabled: true,
 *   onComplete: (results) => console.log('Run complete!', results)
 * })
 * ```
 */
export function useRunPolling({
  runId,
  enabled = true,
  onComplete,
  onError
}: UseRunPollingOptions): UseRunPollingReturn {
  // Poll run status
  const statusQuery = useQuery({
    queryKey: ['run-status', runId],
    queryFn: async () => {
      if (!runId) throw new Error('No run ID provided')
      return await apiClient.getRunStatus(runId)
    },
    enabled: !!runId && enabled,
    refetchInterval: (query) => {
      // Stop polling when complete or error
      const data = query.state.data
      if (!data) return 1000
      const completedStates = ['complete', 'error', 'failed', 'selenium_done']
      if (completedStates.includes(data.step)) {
        return false
      }
      return 1000 // Poll every 1 second while running
    },
    refetchIntervalInBackground: false,
    staleTime: 0, // Always consider status stale
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })

  // Auto-fetch results when run completes
  const resultsQuery = useQuery({
    queryKey: ['run-results', runId],
    queryFn: async () => {
      if (!runId) throw new Error('No run ID provided')
      return await apiClient.getRunResults(runId)
    },
    enabled: statusQuery.data?.step === 'complete' || statusQuery.data?.step === 'selenium_done',
    staleTime: Infinity, // Results don't change once complete
  })

  // Call onComplete callback when results are available
  if (resultsQuery.data && onComplete && !resultsQuery.isFetching) {
    onComplete(resultsQuery.data)
  }

  // Call onError callback on errors
  if ((statusQuery.error || resultsQuery.error) && onError) {
    onError(statusQuery.error || resultsQuery.error || new Error('Unknown error'))
  }

  const isComplete = statusQuery.data?.step === 'complete' || statusQuery.data?.step === 'selenium_done'
  const isError = statusQuery.data?.step === 'error' || statusQuery.data?.step === 'failed'

  return {
    status: statusQuery.data,
    results: resultsQuery.data,
    isLoading: statusQuery.isLoading || (isComplete && resultsQuery.isLoading),
    isError: statusQuery.isError || resultsQuery.isError || isError,
    error: (statusQuery.error || resultsQuery.error) as Error | null,
    isComplete,
    progress: statusQuery.data?.progress ?? 0,
    currentStep: statusQuery.data?.step,
  }
}

/**
 * Map step names to progress percentages
 */
export function getStepProgress(step: string | undefined): number {
  if (!step) return 0

  const stepMap: Record<string, number> = {
    'queued': 0.05,
    'parse_intent': 0.2,
    'dataset_generated': 0.4,
    'embeddings_done': 0.6,
    'vector_search_done': 0.8,
    'ready': 0.9,
    'selenium_running': 0.95,
    'selenium_done': 1.0,
    'complete': 1.0,
    'error': 0,
    'failed': 0,
  }

  return stepMap[step] ?? 0
}

/**
 * Get human-readable step descriptions
 */
export function getStepDescription(step: string | undefined): string {
  if (!step) return 'Initializing...'

  const descriptions: Record<string, string> = {
    'queued': 'Your request is queued',
    'parse_intent': 'Understanding your request...',
    'dataset_generated': 'Creating dataset...',
    'embeddings_done': 'Computing embeddings...',
    'vector_search_done': 'Performing vector search...',
    'ready': 'Ready! JSON meaning found',
    'selenium_running': 'Running Selenium tests...',
    'selenium_done': 'Selenium tests complete',
    'complete': 'Complete',
    'error': 'An error occurred',
    'failed': 'Run failed',
  }

  return descriptions[step] ?? 'Processing...'
}
