"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import api from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

/**
 * Model mismatch error returned when search/embedding uses different model than dataset
 */
export interface ModelMismatchError {
  status: number;
  error: "MODEL_MISMATCH";
  detail: string;
  current_model: string;
  dataset_model: string;
  dataset_id: string;
}

/**
 * Dataset embedding status from backend
 */
export interface EmbeddingStatus {
  dataset_id: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: number;
  total_rows: number;
  embedded_rows: number;
  embedding_model: string | null;
  embedding_dimension: number | null;
  started_at: string | null;
  completed_at: string | null;
  estimated_completion: string | null;
  error_message: string | null;
  task_id: string | null;
}

/**
 * Search result from backend
 */
export interface SearchResult {
  csv_row_id: string;
  query: string;
  api: string;
  endpoint?: string;
  method?: string;
  scenario_type: string;
  test_category: string;
  notes?: string;
  similarity_score: number;
  request?: Record<string, unknown>;
  response?: Record<string, unknown>;
}

/**
 * Search response from backend
 */
export interface SearchResponse {
  success: boolean;
  query: string;
  dataset_id: string;
  template_id: string;
  embedding_model: string;
  embedding_dimension: number;
  total_results: number;
  results: SearchResult[];
  search_time_ms?: number;
}

/**
 * Hook for managing dataset embeddings with MODEL_MISMATCH handling
 */
export function useEmbeddings() {
  const { toast } = useToast();

  // State
  const [isSearching, setIsSearching] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [embeddingStatus, setEmbeddingStatus] = useState<EmbeddingStatus | null>(null);
  const [modelMismatchError, setModelMismatchError] = useState<ModelMismatchError | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

  // Polling interval ref
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Search dataset with model validation
   * Returns MODEL_MISMATCH error if models don't match
   */
  const searchDataset = useCallback(async (
    datasetId: string,
    query: string,
    options?: {
      topK?: number;
      filterScenarioType?: string;
      filterTestCategory?: string;
    }
  ): Promise<SearchResponse | null> => {
    try {
      setIsSearching(true);
      setModelMismatchError(null);
      setSearchResults([]);

      const response = await api.post<SearchResponse>(`/api/v1/datasets/${datasetId}/search`, {
        dataset_id: datasetId,
        query,
        top_k: options?.topK ?? 10,
        filter_scenario_type: options?.filterScenarioType,
        filter_test_category: options?.filterTestCategory,
      });

      setSearchResults(response.results);
      return response;
    } catch (error: any) {
      // Check if it's a MODEL_MISMATCH error (409 Conflict)
      if (error.status === 409 && error.error === "MODEL_MISMATCH") {
        setModelMismatchError(error as ModelMismatchError);
        return null;
      }

      // Handle other errors
      const message = error.detail || error.message || "Search failed";
      toast({
        title: "Search Error",
        description: message,
        variant: "destructive",
      });
      return null;
    } finally {
      setIsSearching(false);
    }
  }, [toast]);

  /**
   * Get embedding status for a dataset
   */
  const getEmbeddingStatus = useCallback(async (datasetId: string): Promise<EmbeddingStatus | null> => {
    try {
      const response = await api.get<EmbeddingStatus>(`/api/v1/datasets/${datasetId}/embedding-status`);
      setEmbeddingStatus(response);
      return response;
    } catch (error: any) {
      console.error("Failed to get embedding status:", error);
      return null;
    }
  }, []);

  /**
   * Start re-embedding a dataset
   */
  const reembedDataset = useCallback(async (
    datasetId: string,
    options?: {
      model?: string;
      force?: boolean;
      chunkSize?: number;
    }
  ): Promise<{ taskId: string; estimatedSeconds: number } | null> => {
    try {
      const response = await api.post<{
        task_id: string;
        new_model: string;
        estimated_time_seconds: number;
      }>(`/api/v1/datasets/${datasetId}/reembed`, {
        model: options?.model,
        force: options?.force ?? true,
        chunk_size: options?.chunkSize ?? 100,
      });

      toast({
        title: "Re-embedding Started",
        description: `Dataset is being re-embedded with ${response.new_model}`,
      });

      return {
        taskId: response.task_id,
        estimatedSeconds: response.estimated_time_seconds,
      };
    } catch (error: any) {
      const message = error.detail || error.message || "Failed to start re-embedding";
      toast({
        title: "Re-embed Error",
        description: message,
        variant: "destructive",
      });
      return null;
    }
  }, [toast]);

  /**
   * Poll embedding status until completed
   */
  const pollEmbeddingStatus = useCallback(async (
    datasetId: string,
    onProgress?: (status: EmbeddingStatus) => void,
    onComplete?: (status: EmbeddingStatus) => void
  ) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    setIsPolling(true);

    const poll = async () => {
      const status = await getEmbeddingStatus(datasetId);

      if (status) {
        onProgress?.(status);

        if (status.status === "completed" || status.status === "failed") {
          // Stop polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          setIsPolling(false);

          if (status.status === "completed") {
            toast({
              title: "Embedding Complete",
              description: `Successfully embedded ${status.embedded_rows} rows`,
            });
            onComplete?.(status);
          } else {
            toast({
              title: "Embedding Failed",
              description: status.error_message || "Unknown error",
              variant: "destructive",
            });
          }
        }
      }
    };

    // Initial poll
    await poll();

    // Start interval polling
    pollingIntervalRef.current = setInterval(poll, 2000);

    // Return cleanup function
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      setIsPolling(false);
    };
  }, [getEmbeddingStatus, toast]);

  /**
   * Clear model mismatch error
   */
  const clearModelMismatchError = useCallback(() => {
    setModelMismatchError(null);
  }, []);

  /**
   * Switch user's embedding model
   */
  const switchEmbeddingModel = useCallback(async (model: string): Promise<boolean> => {
    try {
      await api.post("/api/v1/datasets/settings/embedding-model", { model_name: model });

      toast({
        title: "Model Updated",
        description: `Default embedding model set to ${model}`,
      });

      return true;
    } catch (error: any) {
      toast({
        title: "Error",
        description: "Failed to update embedding model",
        variant: "destructive",
      });
      return false;
    }
  }, [toast]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  return {
    // State
    isSearching,
    isPolling,
    embeddingStatus,
    modelMismatchError,
    searchResults,

    // Actions
    searchDataset,
    getEmbeddingStatus,
    reembedDataset,
    pollEmbeddingStatus,
    clearModelMismatchError,
    switchEmbeddingModel,
  };
}

export default useEmbeddings;
