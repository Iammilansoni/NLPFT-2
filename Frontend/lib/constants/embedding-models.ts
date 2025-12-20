/**
 * Shared constants for Ollama embedding models across the application
 * Keep this in sync with backend embedding_model_registry.py
 * 
 * All models run locally via Ollama at http://localhost:11434
 * No GPU required - optimized for CPU inference
 * 
 * Multi-Model Embedding System with 3 Models:
 * - nomic-embed-text (768D) - Recommended default
 * - all-minilm (384D) - Fastest, lightweight
 * - mxbai-embed-large (1024D) - Highest accuracy
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
    // UI display properties
    color: 'blue' | 'green' | 'red' | 'purple';
    icon: 'zap' | 'rocket' | 'target' | 'brain';
    tagline: string;
    whyChoose: string;
}

// Multi-model embedding system with 3 models
export const EMBEDDING_MODELS: EmbeddingModelOption[] = [
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
        bestFor: ['General semantic search', 'RAG applications', 'High-quality embeddings', 'Most production workloads'],
        pullCmd: 'ollama pull nomic-embed-text',
        color: 'green',
        icon: 'rocket',
        tagline: '🚀 High-Quality, Balanced Embedding Model',
        whyChoose: 'The recommended model offering the best balance between speed, context window (8192 tokens), and accuracy.',
    },
    {
        value: 'all-minilm',
        label: 'All-MiniLM',
        dimension: 384,
        description: '⚡ Ultra-Fast, Lightweight',
        parameters: '~22 Million',
        contextLength: '512 tokens',
        speed: 'fast',
        accuracy: 'good',
        recommended: false,
        bestFor: ['Real-time applications', 'Resource-constrained environments', 'Quick prototyping', 'High-throughput scenarios'],
        pullCmd: 'ollama pull all-minilm',
        color: 'blue',
        icon: 'zap',
        tagline: '⚡ Fastest Model for Real-Time Search',
        whyChoose: 'Best choice when speed is critical. Smallest dimension (384D) means fastest indexing and search.',
    },
    {
        value: 'mxbai-embed-large',
        label: 'MxBai-Embed-Large',
        dimension: 1024,
        description: '🎯 Superior Accuracy, Premium',
        parameters: '~335 Million',
        contextLength: '512 tokens',
        speed: 'moderate',
        accuracy: 'superior',
        recommended: false,
        bestFor: ['Maximum accuracy needs', 'Complex semantic queries', 'Enterprise applications', 'Quality-critical workloads'],
        pullCmd: 'ollama pull mxbai-embed-large',
        color: 'purple',
        icon: 'brain',
        tagline: '🎯 Highest Accuracy for Complex Queries',
        whyChoose: 'Best semantic understanding. Use when accuracy matters more than speed.',
    },
];

// Default embedding model for the project
export const DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text';
export const DEFAULT_EMBEDDING_DIMENSION = 768;

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

/**
 * Get all available model IDs
 */
export function getAllModelIds(): string[] {
    return EMBEDDING_MODELS.map(m => m.value);
}

/**
 * Check if model ID is valid
 */
export function isValidModelId(modelId: string): boolean {
    return EMBEDDING_MODELS.some(m => m.value === modelId);
}

/**
 * Get models by dimension
 */
export function getModelsByDimension(dimension: number): EmbeddingModelOption[] {
    return EMBEDDING_MODELS.filter(m => m.dimension === dimension);
}

/**
 * Get dimension groups for display
 */
export function getDimensionGroups(): { dimension: number; models: EmbeddingModelOption[] }[] {
    const groups: Map<number, EmbeddingModelOption[]> = new Map();
    
    EMBEDDING_MODELS.forEach(model => {
        const existing = groups.get(model.dimension) || [];
        groups.set(model.dimension, [...existing, model]);
    });
    
    return Array.from(groups.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([dimension, models]) => ({ dimension, models }));
}
