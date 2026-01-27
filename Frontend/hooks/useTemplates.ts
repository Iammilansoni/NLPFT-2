'use client';

/**
 * React Query Hooks for Templates API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { 
  TemplateModel, 
  TemplateCreateRequest, 
  TemplateUpdateRequest,
  TemplateStatsResponse 
} from '@/lib/api-types';

/**
 * Fetch all templates
 */
export function useTemplates() {
  return useQuery({
    queryKey: ['templates'],
    queryFn: () => apiClient.listTemplates(),
  });
}

/**
 * Fetch single template by ID
 */
export function useTemplate(templateId: string) {
  return useQuery({
    queryKey: ['templates', templateId],
    queryFn: () => apiClient.getTemplate(templateId),
    enabled: !!templateId,
  });
}

/**
 * Fetch template statistics
 */
export function useTemplateStats() {
  return useQuery({
    queryKey: ['templates', 'stats'],
    queryFn: () => apiClient.getTemplateStats(),
    staleTime: 5000, // Consider data fresh for 5 seconds
    refetchInterval: 10000, // Auto-refresh every 10 seconds for real-time updates
  });
}

/**
 * Create a new template
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TemplateCreateRequest) => apiClient.createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

/**
 * Update an existing template
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TemplateUpdateRequest }) =>
      apiClient.updateTemplate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      queryClient.invalidateQueries({ queryKey: ['templates', variables.id] });
    },
  });
}

/**
 * Delete a template
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => apiClient.deleteTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

/**
 * Approve a template
 */
export function useApproveTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      apiClient.approveTemplate(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

/**
 * Reject a template
 */
export function useRejectTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      apiClient.rejectTemplate(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

/**
 * Submit template for review
 */
export function useSubmitTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      apiClient.submitTemplateForReview(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

/**
 * Sync templates from source
 */
export function useSyncTemplates() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.syncTemplates(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}

/**
 * Reload templates cache
 */
export function useReloadTemplates() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.reloadTemplates(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });
}
