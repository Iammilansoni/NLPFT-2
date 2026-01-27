/**
 * Default embedding model constants
 * 
 * The system uses dynamically registered Ollama models.
 * This file provides only the fallback default when no models are registered.
 * 
 * Users can:
 * - Pull models from Ollama
 * - Register models (auto-detects dimension)
 * - Select any registered model for embeddings
 */

// Default embedding model (fallback when no user preference)
export const DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text';
export const DEFAULT_EMBEDDING_DIMENSION = 768;

/**
 * Embedding model information returned from API
 */
export interface EmbeddingModelInfo {
  model_id: string;
  display_name: string;
  dimension: number;
  is_registered: boolean;
  is_local: boolean;
  size?: string;
}

/**
 * Check if two models are compatible (same dimension)
 */
export function areModelsCompatible(dim1: number, dim2: number): boolean {
  return dim1 === dim2;
}

/**
 * Format model display name
 */
export function formatModelName(modelId: string): string {
  return modelId
    .split(/[-_]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Get dimension label
 */
export function getDimensionLabel(dimension: number): string {
  return `${dimension}D`;
}
