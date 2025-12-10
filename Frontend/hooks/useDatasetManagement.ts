/**
 * Dataset Management Hooks
 * React Query hooks for dataset generation and management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  datasetApi,
  GenerateDatasetRequest,
  EmbedDatasetRequest,
  ListDatasetsParams,
} from '@/lib/dataset-api';

// ==================== Query Keys ====================

export const datasetKeys = {
  all: ['datasets'] as const,
  lists: () => [...datasetKeys.all, 'list'] as const,
  list: (filters: ListDatasetsParams) => [...datasetKeys.lists(), filters] as const,
  details: () => [...datasetKeys.all, 'detail'] as const,
  detail: (id: string) => [...datasetKeys.details(), id] as const,
  status: (id: string) => [...datasetKeys.all, 'status', id] as const,
};

// ==================== Queries ====================

/**
 * Get dataset status (with polling support)
 */
export function useDatasetStatus(datasetId: string, polling: boolean = false) {
  return useQuery({
    queryKey: datasetKeys.status(datasetId),
    queryFn: () => datasetApi.getDatasetStatus(datasetId),
    enabled: !!datasetId,
    refetchInterval: polling ? 2000 : false, // Poll every 2 seconds if enabled
    refetchIntervalInBackground: true,
  });
}

/**
 * List datasets with filters
 */
export function useDatasetsList(params?: ListDatasetsParams) {
  return useQuery({
    queryKey: datasetKeys.list(params || {}),
    queryFn: () => datasetApi.listDatasets(params),
  });
}

// ==================== Mutations ====================

/**
 * Generate new dataset
 */
export function useGenerateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateDatasetRequest) => datasetApi.generateDataset(data),
    onSuccess: (response) => {
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: datasetKeys.lists() });
      
      // Set initial status in cache using task_id (fallback to dataset_id for backward compatibility)
      const taskId = response.task_id || response.dataset_id || '';
      queryClient.setQueryData(datasetKeys.status(taskId), {
        task_id: response.task_id,
        dataset_id: response.dataset_id,
        job_id: response.job_id,
        status: 'running',
        progress: 0,
        message: response.message || 'Starting generation...',
        rows_generated: 0,
        total_rows: response.requested || 0,
        created_at: new Date().toISOString(),
      });
    },
  });
}

/**
 * Embed dataset into vector database
 */
export function useEmbedDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EmbedDatasetRequest) => datasetApi.embedDataset(data),
    onSuccess: (_, variables) => {
      // Invalidate dataset status
      queryClient.invalidateQueries({ queryKey: datasetKeys.status(variables.dataset_id) });
      queryClient.invalidateQueries({ queryKey: datasetKeys.lists() });
    },
  });
}

/**
 * Delete dataset
 */
export function useDeleteDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (datasetId: string) => datasetApi.deleteDataset(datasetId),
    onSuccess: (_, datasetId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: datasetKeys.status(datasetId) });
      queryClient.invalidateQueries({ queryKey: datasetKeys.lists() });
    },
  });
}

/**
 * Download dataset CSV
 */
export function useDownloadDataset() {
  return useMutation({
    mutationFn: async ({ datasetId, filename }: { datasetId: string; filename?: string }) => {
      datasetApi.triggerDownload(datasetId, filename);
      return { success: true };
    },
  });
}
