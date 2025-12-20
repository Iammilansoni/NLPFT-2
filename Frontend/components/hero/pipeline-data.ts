import {
  Lock,
  LayoutTemplate,
  Boxes,
  FileSpreadsheet,
  BrainCircuit,
  Gauge,
  Search,
  Globe,
  LineChart
} from 'lucide-react';

/**
 * Pipeline Step Configuration
 * 
 * Defines the test automation pipeline steps displayed in the hero section.
 * Each step represents a stage in the NLPForge testing workflow.
 */

export interface PipelineStep {
  id: string;
  title: string;
  icon: any; // Lucide Icon Component
  description: string;
  color: string; // Tailwind gradient classes
  glowColor: string; // CSS color for shadow/glow
}

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 'login',
    title: 'Login',
    icon: Lock,
    description: 'Secure authentication flow',
    color: 'from-emerald-400 to-cyan-500',
    glowColor: '#10b981' // emerald-500
  },
  {
    id: 'api_template',
    title: 'API Template',
    icon: LayoutTemplate,
    description: 'Define API endpoints',
    color: 'from-blue-400 to-indigo-500',
    glowColor: '#3b82f6' // blue-500
  },
  {
    id: 'ai_data',
    title: 'AI Test Data',
    icon: Boxes,
    description: 'LLM-powered generation',
    color: 'from-blue-400 to-sky-500',
    glowColor: '#3b82f6' // blue-500
  },
  {
    id: 'csv_context',
    title: 'CSV + Context',
    icon: FileSpreadsheet,
    description: 'Contextual test scenarios',
    color: 'from-fuchsia-400 to-pink-500',
    glowColor: '#d946ef' // fuchsia-500
  },
  {
    id: 'embeddings',
    title: 'Embeddings',
    icon: BrainCircuit,
    description: 'Vector representations',
    color: 'from-rose-400 to-orange-500',
    glowColor: '#f43f5e' // rose-500
  },
  {
    id: 'redis',
    title: 'Redis Vectors',
    icon: Gauge,
    description: 'Lightning-fast storage',
    color: 'from-amber-400 to-yellow-500',
    glowColor: '#f59e0b' // amber-500
  },
  {
    id: 'semantic',
    title: 'Semantic Search',
    icon: Search,
    description: 'Intelligent matching',
    color: 'from-lime-400 to-green-500',
    glowColor: '#84cc16' // lime-500
  },
  {
    id: 'api_ui_tests',
    title: 'API + UI Tests',
    icon: Globe,
    description: 'Full coverage',
    color: 'from-cyan-400 to-sky-500',
    glowColor: '#06b6d4' // cyan-500
  },
  {
    id: 'insights',
    title: 'Insights',
    icon: LineChart,
    description: 'Real-time analytics',
    color: 'from-teal-400 to-emerald-500',
    glowColor: '#14b8a6' // teal-500
  }
];

export const HERO_STATS = [
  { label: 'Tests Generated', value: 50000, suffix: '+' },
  { label: 'Accuracy Rate', value: 99.9, suffix: '%' },
  { label: 'Vectors Stored', value: 1000000, suffix: '+', format: 'compact' }
];

export const TRUST_FEATURES = [
  { icon: '🤖', text: 'LLM-powered test generation' },
  { icon: '⚡', text: 'Redis vector store + fast search' },
  { icon: '📊', text: 'Real-time dashboards' }
];
