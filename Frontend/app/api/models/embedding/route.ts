/**
 * Mock API - Models Embedding Endpoint
 */

import { NextResponse } from 'next/server';
import type { EmbeddingModel, APIResponse } from '@/lib/types';

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

export async function GET() {
  await new Promise(resolve => setTimeout(resolve, 200));

  const response: APIResponse<EmbeddingModel[]> = {
    status: 'success',
    data: EMBEDDING_MODELS,
  };

  return NextResponse.json(response);
}
