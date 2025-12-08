/**
 * Pipeline Steps Data
 * 
 * Mock data for the hero section pipeline visualization.
 * Each step represents a stage in the AI-powered testing workflow.
 */

export interface PipelineStep {
  id: string;
  title: string;
  icon: string;
  description?: string;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  { 
    id: 'login', 
    title: 'Login', 
    icon: '🔐',
    description: 'Secure authentication'
  },
  { 
    id: 'api_template', 
    title: 'API Template', 
    icon: '⚙️',
    description: 'Define once, reuse forever'
  },
  { 
    id: 'ai_data', 
    title: 'AI Test Data', 
    icon: '🤖',
    description: 'LLM-powered generation'
  },
  { 
    id: 'csv_context', 
    title: 'CSV + Context', 
    icon: '📄',
    description: 'Rich metadata storage'
  },
  { 
    id: 'embeddings', 
    title: 'Embeddings', 
    icon: '🧠',
    description: 'Vector transformation'
  },
  { 
    id: 'redis', 
    title: 'Redis Vectors', 
    icon: '⚡',
    description: 'Lightning-fast retrieval'
  },
  { 
    id: 'semantic', 
    title: 'Semantic Search', 
    icon: '🔎',
    description: 'Intent-aware matching'
  },
  { 
    id: 'api_ui_tests', 
    title: 'API + UI Tests', 
    icon: '🌐',
    description: 'Automated execution'
  },
  { 
    id: 'insights', 
    title: 'Insights', 
    icon: '📈',
    description: 'Real-time analytics'
  },
];
