'use client';

import { useState } from 'react';
import {
  Lock,
  LayoutTemplate,
  Bot,
  Database,
  Binary,
  Search,
  Zap,
  ArrowRight,
  ArrowDown,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// --- Types ---
interface Step {
  title: string;
  desc: string;
}

interface Phase {
  id: number;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
  ringColor: string;
  steps: Step[];
}

// --- Data Configuration ---
const phases: Phase[] = [
  {
    id: 1,
    title: 'Authentication',
    subtitle: 'Secure Access',
    icon: Lock,
    color: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    borderColor: 'border-emerald-200 dark:border-emerald-800',
    ringColor: 'ring-emerald-400/50',
    steps: [
      { title: 'Sign Up', desc: 'Create account with email & password' },
      { title: 'Verify Email', desc: 'Enter OTP sent to your email' },
      { title: 'Sign In', desc: 'Login with your credentials' },
      { title: 'Dashboard', desc: 'Access main dashboard' },
    ],
  },
  {
    id: 2,
    title: 'Template',
    subtitle: 'Define Structure',
    icon: LayoutTemplate,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    borderColor: 'border-blue-200 dark:border-blue-800',
    ringColor: 'ring-blue-400/50',
    steps: [
      { title: 'Navigate', desc: 'Go to Templates page' },
      { title: 'Create New', desc: 'Click "New Template"' },
      { title: 'Fill Details', desc: 'API name, desc (500+ words), samples' },
      { title: 'Save Draft', desc: 'Save for later editing' },
      { title: 'Submit Review', desc: 'Request expert approval' },
      { title: 'Get Approved', desc: 'Expert reviews and approves' },
    ],
  },
  {
    id: 3,
    title: 'Model Config',
    subtitle: 'LLM Setup',
    icon: Bot,
    color: 'text-violet-600 dark:text-violet-400',
    bgColor: 'bg-violet-50 dark:bg-violet-950/30',
    borderColor: 'border-violet-200 dark:border-violet-800',
    ringColor: 'ring-violet-400/50',
    steps: [
      { title: 'Open Settings', desc: 'Navigate to Settings page' },
      { title: 'Configure LLM', desc: 'Select provider (OpenAI, Gemini)' },
      { title: 'Enter API Key', desc: 'Add API credentials securely' },
      { title: 'Test Connection', desc: 'Verify LLM is working' },
      { title: 'Select Embedding', desc: 'Choose embedding model' },
      { title: 'Set Default', desc: 'Activate as default model' },
    ],
  },
  {
    id: 4,
    title: 'Dataset Gen',
    subtitle: 'AI Generation',
    icon: Database,
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    borderColor: 'border-amber-200 dark:border-amber-800',
    ringColor: 'ring-amber-400/50',
    steps: [
      { title: 'Navigate', desc: 'Go to Datasets page' },
      { title: 'Generate New', desc: 'Click "Generate Dataset"' },
      { title: 'Select Template', desc: 'Choose approved template' },
      { title: 'Configure', desc: 'Set examples, prompt, distribution' },
      { title: 'Generate', desc: 'LLM creates diverse test cases' },
      { title: 'CSV Created', desc: 'Download or view dataset' },
    ],
  },
  {
    id: 5,
    title: 'Embeddings',
    subtitle: 'Vectorization',
    icon: Binary,
    color: 'text-pink-600 dark:text-pink-400',
    bgColor: 'bg-pink-50 dark:bg-pink-950/30',
    borderColor: 'border-pink-200 dark:border-pink-800',
    ringColor: 'ring-pink-400/50',
    steps: [
      { title: 'Embed Dataset', desc: 'Click "Embed" on dataset' },
      { title: 'Processing', desc: 'Vectors being generated' },
      { title: 'Store in Redis', desc: 'HNSW index created' },
      { title: 'Complete', desc: 'Dataset ready for search' },
    ],
  },
  {
    id: 6,
    title: 'Search',
    subtitle: 'Semantic Query',
    icon: Search,
    color: 'text-indigo-600 dark:text-indigo-400',
    bgColor: 'bg-indigo-50 dark:bg-indigo-950/30',
    borderColor: 'border-indigo-200 dark:border-indigo-800',
    ringColor: 'ring-indigo-400/50',
    steps: [
      { title: 'Navigate', desc: 'Go to Query page' },
      { title: 'Enter Query', desc: 'Type natural language question' },
      { title: 'Vector Search', desc: 'Stage 1: Similarity matching' },
      { title: 'Re-Ranking', desc: 'Stage 2: Cross-encoder scoring' },
      { title: 'Results', desc: 'View matched APIs' },
    ],
  },
  {
    id: 7,
    title: 'Results',
    subtitle: 'Output Ready',
    icon: Zap,
    color: 'text-teal-600 dark:text-teal-400',
    bgColor: 'bg-teal-50 dark:bg-teal-950/30',
    borderColor: 'border-teal-200 dark:border-teal-800',
    ringColor: 'ring-teal-400/50',
    steps: [
      { title: 'Dashboard', desc: 'View on main dashboard' },
      { title: 'JSON Output', desc: 'Structured API response' },
      { title: 'Complete!', desc: 'Use in your application' },
    ],
  },
];

// --- Sub-Components ---

function FlowNode({ phase, isRightAligned = false }: { phase: Phase; isRightAligned?: boolean }) {
  const [isHovered, setIsHovered] = useState(false);
  const Icon = phase.icon;

  return (
    <div className="relative group z-10">
      {/* Interaction Target */}
      <div
        className="relative cursor-pointer transition-transform duration-300 hover:scale-105"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Card Body */}
        <div
          className={cn(
            'w-24 h-24 rounded-2xl border-2 flex flex-col items-center justify-center gap-2 transition-all duration-300 shadow-sm',
            phase.bgColor,
            phase.borderColor,
            isHovered ? `shadow-xl ring-4 ${phase.ringColor}` : 'hover:shadow-md'
          )}
        >
          <div className={cn("p-2 rounded-full bg-white dark:bg-gray-900 shadow-sm", phase.color)}>
             <Icon className="w-5 h-5" />
          </div>
          <span className={cn('text-[11px] font-bold text-center leading-tight px-1', phase.color)}>
            {phase.title}
          </span>
          
          {/* Step Count Badge */}
          <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-[10px] font-bold flex items-center justify-center shadow-lg border-2 border-white dark:border-gray-800">
            {phase.steps.length}
          </div>
        </div>

        {/* Floating Tooltip */}
        {isHovered && (
          <div className={cn(
            "absolute z-50 bottom-full mb-4 w-64 pointer-events-none animate-in fade-in zoom-in-95 duration-200",
            // Intelligent positioning: if it's right aligned in the layout, shift tooltip left so it doesn't overflow screen
            isRightAligned ? "right-0" : "left-1/2 -translate-x-1/2"
          )}>
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
              {/* Tooltip Header */}
              <div className={cn("px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center gap-3", phase.bgColor)}>
                <Icon className={cn("w-4 h-4", phase.color)} />
                <div>
                  <h4 className="font-bold text-sm text-gray-900 dark:text-white">{phase.title}</h4>
                  <p className="text-[10px] uppercase tracking-wider opacity-80 font-semibold">{phase.subtitle}</p>
                </div>
              </div>
              
              {/* Steps List */}
              <div className="p-3 bg-white dark:bg-gray-950 space-y-3">
                {phase.steps.map((step, idx) => (
                  <div key={idx} className="flex gap-3">
                    <div className="flex flex-col items-center">
                        <div className={cn('w-1.5 h-1.5 rounded-full mt-1.5', phase.bgColor.replace('bg-', 'bg-slate-400 dark:bg-slate-600 '))} />
                        {idx !== phase.steps.length - 1 && <div className="w-px h-full bg-gray-100 dark:bg-gray-800 my-0.5" />}
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-gray-800 dark:text-gray-200">{step.title}</p>
                      <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-relaxed">{step.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Tooltip Arrow */}
            <div className={cn(
              "absolute top-full w-4 h-4 bg-white dark:bg-gray-900 border-r border-b border-gray-200 dark:border-gray-800 transform rotate-45 -mt-2",
              isRightAligned ? "right-10" : "left-1/2 -translate-x-1/2"
            )} />
          </div>
        )}
      </div>
    </div>
  );
}

function Connector({ type, direction = 'right' }: { type: 'straight' | 'corner', direction?: 'right' | 'left' }) {
    if (type === 'corner') {
        return (
            <div className="h-24 w-12 flex items-center justify-center relative">
                 <div className="absolute top-1/2 left-1/2 w-[2px] h-full -translate-x-1/2 -translate-y-1/2 bg-gradient-to-b from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600" />
                 <ArrowDown className="absolute bottom-0 text-gray-300 dark:text-gray-600 w-4 h-4" />
            </div>
        )
    }

    return (
      <div className="flex items-center justify-center px-2 w-16">
        <div className={cn(
            "w-full h-[2px] rounded-full bg-gray-200 dark:bg-gray-800 relative",
            direction === 'left' ? "bg-gradient-to-l" : "bg-gradient-to-r",
            "from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600"
        )}>
           <ArrowRight className={cn(
               "absolute top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 dark:text-gray-500",
               direction === 'left' ? "left-0 rotate-180" : "right-0"
           )} />
        </div>
      </div>
    );
}

// --- Main Component ---

export default function UserJourneyFlow() {
  // We split the 7 steps into two rows for the "Snake" effect
  // Row 1: Left -> Right (Items 0, 1, 2, 3)
  const row1 = phases.slice(0, 4);
  
  // Row 2: Right -> Left (Items 4, 5, 6)
  // We reverse them for rendering, so they flow visually from right to left
  const row2 = phases.slice(4).reverse();

  return (
    <div className="w-full max-w-5xl mx-auto p-8 bg-white dark:bg-black/5 rounded-3xl border border-gray-100 dark:border-gray-800/50">
      
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-gray-700 to-gray-900 dark:from-white dark:via-gray-200 dark:to-white bg-clip-text text-transparent mb-3">
          Workflow Architecture
        </h2>
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
           <Info className="w-4 h-4" />
           <span>Hover over nodes to view detailed process steps</span>
        </div>
      </div>

      {/* Diagram Container */}
      <div className="flex flex-col items-center select-none">
        
        {/* ROW 1: Left to Right */}
        <div className="flex items-center">
          {row1.map((phase, idx) => (
            <div key={phase.id} className="flex items-center">
              <FlowNode phase={phase} />
              {/* Add connector if not the last item in this row */}
              {idx < row1.length - 1 && <Connector type="straight" direction="right" />}
            </div>
          ))}
        </div>

        {/* Vertical Connector (Snake Turn) */}
        {/* Placed at the far right to connect Row 1 end to Row 2 start */}
        <div className="w-full max-w-[calc(4*6rem+3*4rem)] flex justify-end pr-6 -my-4 z-0">
             <Connector type="corner" />
        </div>

        {/* ROW 2: Right to Left */}
        <div className="flex items-center">
          {/* Add spacer to align with the grid above if needed, or use justify-end on container */}
          <div className="w-32 hidden md:block" /> 
          
          {row2.map((phase, idx) => (
            <div key={phase.id} className="flex items-center">
                {/* Connector comes BEFORE the node because we are moving Right to Left visually */}
               {idx > 0 && <Connector type="straight" direction="left" />}
               <FlowNode phase={phase} isRightAligned={true} />
            </div>
          ))}
        </div>

      </div>

      {/* Legend / Footer */}
      <div className="mt-16 pt-8 border-t border-gray-100 dark:border-gray-800 flex justify-between items-center text-xs text-gray-400">
        <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>End-to-End Encryption</span>
        </div>
        <div className="flex gap-4">
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-400"></div> Auth</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-violet-400"></div> AI Models</span>
            <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-teal-400"></div> API</span>
        </div>
      </div>
    </div>
  );
}