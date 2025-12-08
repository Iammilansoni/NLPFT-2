/**
 * Mock API - Models Endpoints
 * Returns realistic sample data for embedding models and dataset LLMs
 */

import { NextRequest, NextResponse } from 'next/server';
import type { EmbeddingModel, DatasetLLM, APIResponse } from '@/lib/types';

// Mock embedding models data
const EMBEDDING_MODELS: EmbeddingModel[] = [
  {
    id: 'minilm-384',
    name: 'MiniLM-L6-v2',
    dimension: 384,
    context_length: 256,
    cpu_friendly: true,
    description: 'Fast and efficient, ideal for quick searches and CPU-only deployments',
    provider: 'sentence-transformers',
  },
  {
    id: 'sbert-768',
    name: 'SBERT-base',
    dimension: 768,
    context_length: 512,
    cpu_friendly: true,
    description: 'Balanced accuracy and performance, great for general-purpose use',
    provider: 'sentence-transformers',
  },
  {
    id: 'highacc-1536',
    name: 'HighAccuracy-large',
    dimension: 1536,
    context_length: 8192,
    cpu_friendly: false,
    description: 'Maximum accuracy for critical applications, requires GPU',
    provider: 'openai',
  },
];

// Mock dataset LLMs data
const DATASET_LLMS: DatasetLLM[] = [
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    provider: 'openai',
    context_length: 128000,
    cost_per_1k: 0.01,
    description: 'Most capable model, best for complex dataset generation',
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    provider: 'openai',
    context_length: 16385,
    cost_per_1k: 0.0015,
    description: 'Fast and cost-effective, good for most use cases',
  },
  {
    id: 'claude-3-opus',
    name: 'Claude 3 Opus',
    provider: 'anthropic',
    context_length: 200000,
    cost_per_1k: 0.015,
    description: 'Excellent reasoning and context understanding',
  },
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type');

  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300));

  if (type === 'embedding' || request.url.includes('/embedding')) {
    const response: APIResponse<EmbeddingModel[]> = {
      status: 'success',
      data: EMBEDDING_MODELS,
      message: 'Embedding models retrieved successfully',
    };
    return NextResponse.json(response);
  }

  if (type === 'llm' || request.url.includes('/llm')) {
    const response: APIResponse<DatasetLLM[]> = {
      status: 'success',
      data: DATASET_LLMS,
      message: 'Dataset LLMs retrieved successfully',
    };
    return NextResponse.json(response);
  }

  // Default: return all models
  const response: APIResponse<{ embedding: EmbeddingModel[]; llm: DatasetLLM[] }> = {
    status: 'success',
    data: {
      embedding: EMBEDDING_MODELS,
      llm: DATASET_LLMS,
    },
  };

  return NextResponse.json(response);
}
