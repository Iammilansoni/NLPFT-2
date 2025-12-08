/**
 * Shared constants for Ollama embedding models across the application
 * Keep this in sync with backend models_config.py
 * 
 * All models run locally via Ollama at http://localhost:11434
 * No GPU required - optimized for CPU inference
 */

export interface EmbeddingModelOption {
    value: string;
    label: string;
    dimension: number;
    description: string;
    parameters: string;
    contextLength: string;
    speed: 'fast' | 'moderate' | 'slow';
    accuracy: 'good' | 'excellent' | 'superior';
    recommended?: boolean;
    bestFor: string[];
    pullCmd: string;
}

export const EMBEDDING_MODELS: EmbeddingModelOption[] = [
    {
        value: 'all-minilm',
        label: 'All-MiniLM',
        dimension: 384,
        description: '⚡ Super-Fast Lightweight Model',
        parameters: '~22 Million',
        contextLength: '256-512 tokens',
        speed: 'fast',
        accuracy: 'good',
        recommended: false,
        bestFor: ['Real-time applications', 'Low-latency search', 'Massive datasets'],
        pullCmd: 'ollama pull all-minilm',
    },
    {
        value: 'nomic-embed-text',
        label: 'Nomic-Embed-Text',
        dimension: 768,
        description: '🚀 High-Quality Balanced Default',
        parameters: '~137 Million',
        contextLength: '8192 tokens',
        speed: 'fast',
        accuracy: 'excellent',
        recommended: true,
        bestFor: ['General semantic search', 'RAG applications', 'Most production workloads'],
        pullCmd: 'ollama pull nomic-embed-text',
    },
    {
        value: 'mxbai-embed-large',
        label: 'MXBai-Embed-Large',
        dimension: 1024,
        description: '🎯 High-Precision Heavy-Duty Model',
        parameters: '~335 Million',
        contextLength: '512 tokens',
        speed: 'moderate',
        accuracy: 'superior',
        recommended: false,
        bestFor: ['Precision-critical search', 'Legal/Medical documents', 'Enterprise retrieval'],
        pullCmd: 'ollama pull mxbai-embed-large',
    },
];

export const DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text';

/**
 * Get model info by ID
 */
export function getEmbeddingModelInfo(modelId: string): EmbeddingModelOption | undefined {
    return EMBEDDING_MODELS.find(m => m.value === modelId);
}

/**
 * Get dimension for a model
 */
export function getDimensionForModel(modelId: string): number {
    const model = getEmbeddingModelInfo(modelId);
    return model?.dimension ?? 768; // Default to nomic-embed-text dimension
}

/**
 * Check if two models are compatible (same dimension)
 */
export function areModelsCompatible(model1: string, model2: string): boolean {
    return getDimensionForModel(model1) === getDimensionForModel(model2);
}
