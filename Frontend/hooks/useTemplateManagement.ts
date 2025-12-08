/**
 * React Query Hooks for Template Management
 * Provides data fetching, caching, and mutation hooks
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import {
  templateApi,
  Template,
  CreateTemplateRequest,
  CreateParametersRequest,
  CreateExpectedResponsesRequest,
  CreateMetadataRequest,
  Parameter,
  ParameterSchema,
  ExpectedResponse,
  TemplateStatus,
} from '@/lib/template-api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const templateKeys = {
  all: ['templates'] as const,
  lists: () => [...templateKeys.all, 'list'] as const,
  list: (filters?: { status?: TemplateStatus; user_id?: string }) =>
    [...templateKeys.lists(), filters] as const,
  details: () => [...templateKeys.all, 'detail'] as const,
  detail: (id: string) => [...templateKeys.details(), id] as const,
  parameters: (id: string) => [...templateKeys.detail(id), 'parameters'] as const,
  expectedResponses: (id: string) => [...templateKeys.detail(id), 'expected_responses'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Fetch single template by ID
 */
export function useTemplate(
  templateId: string,
  options?: Omit<UseQueryOptions<Template, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Template, Error>({
    queryKey: templateKeys.detail(templateId),
    queryFn: () => templateApi.getTemplate(templateId),
    enabled: !!templateId,
    ...options,
  });
}

/**
 * Fetch list of templates with optional filters
 */
export function useTemplatesList(
  filters?: { status?: TemplateStatus; user_id?: string; domain_tags?: string[] },
  options?: Omit<UseQueryOptions<Template[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Template[], Error>({
    queryKey: templateKeys.list(filters),
    queryFn: () => templateApi.listTemplates(filters),
    ...options,
  });
}

/**
 * Fetch parameters for a template
 */
export function useTemplateParameters(
  templateId: string,
  options?: Omit<UseQueryOptions<Parameter[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Parameter[], Error>({
    queryKey: templateKeys.parameters(templateId),
    queryFn: () => templateApi.getParameters(templateId),
    enabled: !!templateId,
    ...options,
  });
}

/**
 * Fetch expected responses for a template
 */
export function useTemplateExpectedResponses(
  templateId: string,
  options?: Omit<UseQueryOptions<ExpectedResponse[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<ExpectedResponse[], Error>({
    queryKey: templateKeys.expectedResponses(templateId),
    queryFn: () => templateApi.getExpectedResponses(templateId),
    enabled: !!templateId,
    ...options,
  });
}

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Create new template mutation (strict validation)
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, parameters }: { data: CreateTemplateRequest; parameters?: ParameterSchema[] }) => 
      templateApi.createTemplate(data, parameters),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

/**
 * Create draft template mutation (relaxed validation)
 * Use this for saving incomplete work in progress
 */
export function useCreateDraftTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, parameters }: { data: CreateTemplateRequest; parameters?: ParameterSchema[] }) => 
      templateApi.createDraftTemplate(data, parameters),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

/**
 * Update template mutation (strict validation)
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      templateId, 
      data,
      parameters 
    }: { 
      templateId: string; 
      data: Partial<CreateTemplateRequest>;
      parameters?: ParameterSchema[];
    }) => templateApi.updateTemplate(templateId, data, parameters),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(variables.templateId) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

/**
 * Update draft template mutation (relaxed validation)
 * Use this for saving incomplete work in progress
 */
export function useUpdateDraftTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      templateId, 
      data,
      parameters 
    }: { 
      templateId: string; 
      data: Partial<CreateTemplateRequest>;
      parameters?: ParameterSchema[];
    }) => templateApi.updateDraftTemplate(templateId, data, parameters),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(variables.templateId) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

/**
 * Create parameters mutation
 */
export function useCreateParameters() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      templateId, 
      data 
    }: { 
      templateId: string; 
      data: CreateParametersRequest 
    }) => templateApi.createParameters(templateId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: templateKeys.parameters(variables.templateId) 
      });
    },
  });
}

/**
 * Create expected responses mutation
 */
export function useCreateExpectedResponses() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      templateId, 
      data 
    }: { 
      templateId: string; 
      data: CreateExpectedResponsesRequest 
    }) => templateApi.createExpectedResponses(templateId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: templateKeys.expectedResponses(variables.templateId) 
      });
    },
  });
}

/**
 * Create metadata mutation
 */
export function useCreateMetadata() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      templateId, 
      data 
    }: { 
      templateId: string; 
      data: CreateMetadataRequest 
    }) => templateApi.createMetadata(templateId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: templateKeys.detail(variables.templateId) 
      });
    },
  });
}

/**
 * Approve template mutation (admin/reviewer only)
 */
export function useApproveTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => templateApi.approveTemplate(templateId),
    onSuccess: (_, templateId) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(templateId) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

/**
 * Create audit log mutation
 */
export function useCreateAuditLog() {
  return useMutation({
    mutationFn: (data: {
      action: string;
      user_id: string;
      template_id: string;
      payload?: Record<string, any>;
    }) => templateApi.createAuditLog(data),
  });
}

/**
 * Delete template mutation
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => templateApi.deleteTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}
