import { z } from 'zod';

export const querySchema = z.object({
  query: z.string().min(3, 'Query must be at least 3 characters').max(500, 'Query is too long'),
  generate_dataset: z.boolean().optional(),
  num_examples: z.number().int().min(10).max(200).optional(),
  top_k: z.number().int().min(1).max(20).optional(),
});

export const templateSchema = z.object({
  intent: z.string().min(2).max(50),
  api_name: z.string().min(2).max(100),
  description: z.string().min(10).max(500),
  endpoint: z.string().min(1).max(255),
  method: z.enum(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']),
  intent_keywords: z.array(z.string()).min(1),
  parameters: z.array(
    z.object({
      name: z.string().min(1),
      type: z.string().min(1),
      required: z.boolean(),
      description: z.string().optional(),
      default: z.any().optional(),
    })
  ),
  example_queries: z.array(z.string()).min(1),
  response_format: z.record(z.string()).optional(),
});

export const datasetGenerateSchema = z.object({
  seed_prompt: z.string().min(10).max(1000),
  examples: z.number().int().min(10).max(200),
  api_name: z.string().min(2).max(100),
  endpoint: z.string().min(1).max(255),
});

export const searchSchema = z.object({
  query: z.string().min(1).max(500),
  top_k: z.number().int().min(1).max(20).optional(),
  intent: z.array(z.string()).optional(),
  min_similarity: z.number().min(0).max(1).optional(),
});

export type QueryFormData = z.infer<typeof querySchema>;
export type TemplateFormData = z.infer<typeof templateSchema>;
export type DatasetGenerateFormData = z.infer<typeof datasetGenerateSchema>;
export type SearchFormData = z.infer<typeof searchSchema>;
