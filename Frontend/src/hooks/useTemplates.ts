/**
 * React Query Hooks for Template API
 * Custom hooks for template management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { templateApi } from '@/lib/api/templates'
import type { TemplateCreateRequest, TemplateUpdateRequest } from '@/lib/api/types'

/**
 * Query Keys for React Query cache management
 */
export const templateKeys = {
  all: ['templates'] as const,
  list: () => [...templateKeys.all, 'list'] as const,
  detail: (intent: string) => [...templateKeys.all, 'detail', intent] as const,
  stats: () => [...templateKeys.all, 'stats'] as const,
}

/**
 * Hook to list all templates
 */
export function useTemplates() {
  return useQuery({
    queryKey: templateKeys.list(),
    queryFn: () => templateApi.list(),
    staleTime: 60000, // Consider fresh for 1 minute
  })
}

/**
 * Hook to get a specific template
 */
export function useTemplate(intent: string) {
  return useQuery({
    queryKey: templateKeys.detail(intent),
    queryFn: () => templateApi.get(intent),
    enabled: !!intent,
  })
}

/**
 * Hook to create a template
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (template: TemplateCreateRequest) => templateApi.create(template),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.list() })
      queryClient.invalidateQueries({ queryKey: templateKeys.stats() })
    },
  })
}

/**
 * Hook to update a template
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ intent, updates }: { intent: string; updates: TemplateUpdateRequest }) =>
      templateApi.update(intent, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.list() })
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(variables.intent) })
    },
  })
}

/**
 * Hook to delete a template
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (intent: string) => templateApi.delete(intent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.list() })
      queryClient.invalidateQueries({ queryKey: templateKeys.stats() })
    },
  })
}

/**
 * Hook to sync templates from JSON
 */
export function useSyncTemplates() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => templateApi.sync(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.list() })
      queryClient.invalidateQueries({ queryKey: templateKeys.stats() })
    },
  })
}

/**
 * Hook to reload templates
 */
export function useReloadTemplates() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => templateApi.reload(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.all })
    },
  })
}

/**
 * Hook to get template statistics
 */
export function useTemplateStats() {
  return useQuery({
    queryKey: templateKeys.stats(),
    queryFn: () => templateApi.getStats(),
    staleTime: 30000,
  })
}
