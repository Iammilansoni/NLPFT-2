'use client';

import { ReactNode, useState } from 'react';
import {
  UserPlus,
  LogIn,
  Mail,
  CheckCircle,
  LayoutDashboard,
  FileText,
  Plus,
  Edit3,
  Save,
  Send,
  UserCheck,
  Settings,
  Bot,
  Key,
  TestTube,
  Brain,
  Database,
  Sparkles,
  FileSpreadsheet,
  Loader2,
  FileOutput,
  Cpu,
  Package,
  Search,
  MessageSquare,
  Layers,
  Zap,
  BarChart3,
  Home,
  Code,
  ArrowRight,
  ArrowDown,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * CompleteUserJourney Component
 * 
 * A comprehensive visual diagram showing the complete end-to-end user flow
 * from authentication to semantic search results in NLPForge.
 */

interface JourneyPhase {
  id: string;
  title: string;
  icon: ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  steps: JourneyStep[];
}

interface JourneyStep {
  number: number;
  title: string;
  description: string;
  icon: ReactNode;
}

const phases: JourneyPhase[] = [
  {
    id: 'auth',
    title: 'Authentication',
    icon: <LogIn className="w-5 h-5" />,
    color: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    borderColor: 'border-emerald-200 dark:border-emerald-800',
    steps: [
      { number: 1, title: 'Sign Up', description: 'Create account with email & password', icon: <UserPlus className="w-4 h-4" /> },
      { number: 2, title: 'Verify Email', description: 'Enter OTP sent to your email', icon: <Mail className="w-4 h-4" /> },
      { number: 3, title: 'Sign In', description: 'Login with your credentials', icon: <LogIn className="w-4 h-4" /> },
      { number: 4, title: 'Dashboard', description: 'Access main dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    ],
  },
  {
    id: 'templates',
    title: 'Template Creation',
    icon: <FileText className="w-5 h-5" />,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    borderColor: 'border-blue-200 dark:border-blue-800',
    steps: [
      { number: 1, title: 'Navigate', description: 'Go to Templates page', icon: <FileText className="w-4 h-4" /> },
      { number: 2, title: 'Create New', description: 'Click "New Template" button', icon: <Plus className="w-4 h-4" /> },
      { number: 3, title: 'Fill Details', description: 'API name, description (500+ words), samples (3+)', icon: <Edit3 className="w-4 h-4" /> },
      { number: 4, title: 'Save Draft', description: 'Save template for later editing', icon: <Save className="w-4 h-4" /> },
      { number: 5, title: 'Submit Review', description: 'Request expert approval', icon: <Send className="w-4 h-4" /> },
      { number: 6, title: 'Get Approved', description: 'Expert reviews and approves', icon: <UserCheck className="w-4 h-4" /> },
    ],
  },
  {
    id: 'settings',
    title: 'Model Configuration',
    icon: <Settings className="w-5 h-5" />,
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-50 dark:bg-orange-950/30',
    borderColor: 'border-orange-200 dark:border-orange-800',
    steps: [
      { number: 1, title: 'Open Settings', description: 'Navigate to Settings page', icon: <Settings className="w-4 h-4" /> },
      { number: 2, title: 'Configure LLM', description: 'Select provider (OpenAI, Gemini, Ollama)', icon: <Bot className="w-4 h-4" /> },
      { number: 3, title: 'Enter API Key', description: 'Add API credentials securely', icon: <Key className="w-4 h-4" /> },
      { number: 4, title: 'Test Connection', description: 'Verify LLM is working', icon: <TestTube className="w-4 h-4" /> },
      { number: 5, title: 'Select Embedding', description: 'Choose embedding model', icon: <Brain className="w-4 h-4" /> },
      { number: 6, title: 'Set Default', description: 'Activate as default model', icon: <CheckCircle className="w-4 h-4" /> },
    ],
  },
  {
    id: 'dataset',
    title: 'Dataset Generation',
    icon: <Database className="w-5 h-5" />,
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-50 dark:bg-purple-950/30',
    borderColor: 'border-purple-200 dark:border-purple-800',
    steps: [
      { number: 1, title: 'Navigate', description: 'Go to Datasets page', icon: <Database className="w-4 h-4" /> },
      { number: 2, title: 'Generate New', description: 'Click "Generate Dataset"', icon: <Sparkles className="w-4 h-4" /> },
      { number: 3, title: 'Select Template', description: 'Choose approved template', icon: <FileText className="w-4 h-4" /> },
      { number: 4, title: 'Configure', description: 'Set examples, prompt, distribution', icon: <Edit3 className="w-4 h-4" /> },
      { number: 5, title: 'Generate', description: 'LLM creates diverse test cases', icon: <Loader2 className="w-4 h-4" /> },
      { number: 6, title: 'CSV Created', description: 'Download or view dataset', icon: <FileSpreadsheet className="w-4 h-4" /> },
    ],
  },
  {
    id: 'embedding',
    title: 'Embedding Process',
    icon: <Cpu className="w-5 h-5" />,
    color: 'text-cyan-600 dark:text-cyan-400',
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/30',
    borderColor: 'border-cyan-200 dark:border-cyan-800',
    steps: [
      { number: 1, title: 'Embed Dataset', description: 'Click "Embed" on dataset', icon: <Brain className="w-4 h-4" /> },
      { number: 2, title: 'Processing', description: 'Vectors being generated', icon: <Loader2 className="w-4 h-4" /> },
      { number: 3, title: 'Store in Redis', description: 'HNSW index created', icon: <Package className="w-4 h-4" /> },
      { number: 4, title: 'Complete', description: 'Dataset ready for search', icon: <CheckCircle className="w-4 h-4" /> },
    ],
  },
  {
    id: 'search',
    title: 'Semantic Search',
    icon: <Search className="w-5 h-5" />,
    color: 'text-pink-600 dark:text-pink-400',
    bgColor: 'bg-pink-50 dark:bg-pink-950/30',
    borderColor: 'border-pink-200 dark:border-pink-800',
    steps: [
      { number: 1, title: 'Navigate', description: 'Go to Query page', icon: <Search className="w-4 h-4" /> },
      { number: 2, title: 'Enter Query', description: 'Type natural language question', icon: <MessageSquare className="w-4 h-4" /> },
      { number: 3, title: 'Vector Search', description: 'Stage 1: Similarity matching', icon: <Layers className="w-4 h-4" /> },
      { number: 4, title: 'Re-Ranking', description: 'Stage 2: Cross-encoder scoring', icon: <Zap className="w-4 h-4" /> },
      { number: 5, title: 'Results', description: 'View matched APIs', icon: <BarChart3 className="w-4 h-4" /> },
    ],
  },
  {
    id: 'output',
    title: 'Results & Output',
    icon: <FileOutput className="w-5 h-5" />,
    color: 'text-lime-600 dark:text-lime-400',
    bgColor: 'bg-lime-50 dark:bg-lime-950/30',
    borderColor: 'border-lime-200 dark:border-lime-800',
    steps: [
      { number: 1, title: 'Dashboard', description: 'View on main dashboard', icon: <Home className="w-4 h-4" /> },
      { number: 2, title: 'JSON Output', description: 'Structured API response', icon: <Code className="w-4 h-4" /> },
      { number: 3, title: 'Complete!', description: 'Use in your application', icon: <CheckCircle className="w-4 h-4" /> },
    ],
  },
];

interface PhaseCardProps {
  phase: JourneyPhase;
  isExpanded: boolean;
  onToggle: () => void;
  phaseIndex: number;
  isLast: boolean;
}

function PhaseCard({ phase, isExpanded, onToggle, phaseIndex, isLast }: PhaseCardProps) {
  return (
    <div className="relative">
      {/* Connection Line */}
      {!isLast && (
        <div className="absolute left-1/2 -bottom-6 transform -translate-x-1/2 z-0 hidden md:block">
          <ArrowDown className="w-5 h-5 text-muted-foreground/40" />
        </div>
      )}
      
      <div 
        className={cn(
          "rounded-xl border-2 overflow-hidden transition-all duration-300 cursor-pointer",
          phase.borderColor,
          isExpanded ? "shadow-lg" : "shadow-sm hover:shadow-md"
        )}
        onClick={onToggle}
      >
        {/* Header */}
        <div className={cn("px-5 py-4 flex items-center justify-between", phase.bgColor)}>
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center",
              "bg-white dark:bg-gray-800 shadow-sm border",
              phase.borderColor
            )}>
              <span className={phase.color}>{phase.icon}</span>
            </div>
            <div>
              <h3 className={cn("font-semibold", phase.color)}>{phase.title}</h3>
              <p className="text-xs text-muted-foreground">{phase.steps.length} steps</p>
            </div>
          </div>
          <div className={cn("transition-transform duration-300", isExpanded ? "rotate-180" : "")}>
            <ChevronDown className="w-5 h-5 text-muted-foreground" />
          </div>
        </div>
        
        {/* Steps (Collapsible) */}
        <div className={cn(
          "overflow-hidden transition-all duration-300",
          isExpanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
        )}>
          <div className="px-5 py-4 bg-card space-y-3">
            {phase.steps.map((step, idx) => (
              <div key={step.number} className="flex items-start gap-3">
                <div className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
                  "bg-muted border border-border"
                )}>
                  <span className="text-xs font-medium text-muted-foreground">{step.number}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={phase.color}>{step.icon}</span>
                    <span className="font-medium text-sm text-foreground">{step.title}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{step.description}</p>
                </div>
                {idx < phase.steps.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-muted-foreground/30 flex-shrink-0 mt-1" />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function CompleteUserJourney() {
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set(['auth']));

  const togglePhase = (phaseId: string) => {
    setExpandedPhases(prev => {
      const next = new Set(prev);
      if (next.has(phaseId)) {
        next.delete(phaseId);
      } else {
        next.add(phaseId);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedPhases(new Set(phases.map(p => p.id)));
  };

  const collapseAll = () => {
    setExpandedPhases(new Set());
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Controls */}
      <div className="flex justify-end gap-2 mb-6">
        <button
          onClick={expandAll}
          className="text-xs px-3 py-1.5 rounded-md bg-muted hover:bg-muted/80 text-muted-foreground transition-colors"
        >
          Expand All
        </button>
        <button
          onClick={collapseAll}
          className="text-xs px-3 py-1.5 rounded-md bg-muted hover:bg-muted/80 text-muted-foreground transition-colors"
        >
          Collapse All
        </button>
      </div>

      {/* Journey Phases */}
      <div className="space-y-8">
        {phases.map((phase, index) => (
          <PhaseCard
            key={phase.id}
            phase={phase}
            isExpanded={expandedPhases.has(phase.id)}
            onToggle={() => togglePhase(phase.id)}
            phaseIndex={index}
            isLast={index === phases.length - 1}
          />
        ))}
      </div>

      {/* Quick Flow Summary */}
      <div className="mt-10 p-5 rounded-xl border border-border bg-muted/30">
        <h4 className="text-sm font-semibold text-foreground mb-4 text-center">Quick Reference Flow</h4>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {phases.map((phase, index) => (
            <div key={phase.id} className="flex items-center gap-2">
              <div className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium",
                phase.bgColor,
                phase.color
              )}>
                {phase.title.split(' ')[0]}
              </div>
              {index < phases.length - 1 && (
                <ArrowRight className="w-3 h-3 text-muted-foreground/50" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CompleteUserJourney;
