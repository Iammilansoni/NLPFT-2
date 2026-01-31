'use client';

import { ReactNode } from 'react';
import {
  LogIn,
  FileText,
  Settings,
  Database,
  Cpu,
  Search,
  CheckCircle,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * CompleteUserJourney Component
 * 
 * A clean flowchart-style diagram showing the user journey in NLPForge.
 * Uses a horizontal flow on desktop and vertical on mobile.
 */

interface FlowNode {
  id: string;
  title: string;
  subtitle: string;
  icon: ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  glowColor: string;
}

const flowNodes: FlowNode[] = [
  {
    id: 'auth',
    title: 'Sign In',
    subtitle: 'Login / Register',
    icon: <LogIn className="w-5 h-5" />,
    color: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/50',
    borderColor: 'border-emerald-300 dark:border-emerald-700',
    glowColor: 'shadow-emerald-500/20',
  },
  {
    id: 'template',
    title: 'Templates',
    subtitle: 'Create API specs',
    icon: <FileText className="w-5 h-5" />,
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/50',
    borderColor: 'border-blue-300 dark:border-blue-700',
    glowColor: 'shadow-blue-500/20',
  },
  {
    id: 'settings',
    title: 'Configure',
    subtitle: 'LLM & Embeddings',
    icon: <Settings className="w-5 h-5" />,
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-50 dark:bg-orange-950/50',
    borderColor: 'border-orange-300 dark:border-orange-700',
    glowColor: 'shadow-orange-500/20',
  },
  {
    id: 'dataset',
    title: 'Generate',
    subtitle: 'Create datasets',
    icon: <Database className="w-5 h-5" />,
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-50 dark:bg-purple-950/50',
    borderColor: 'border-purple-300 dark:border-purple-700',
    glowColor: 'shadow-purple-500/20',
  },
  {
    id: 'embedding',
    title: 'Embed',
    subtitle: 'Vector indexing',
    icon: <Cpu className="w-5 h-5" />,
    color: 'text-cyan-600 dark:text-cyan-400',
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/50',
    borderColor: 'border-cyan-300 dark:border-cyan-700',
    glowColor: 'shadow-cyan-500/20',
  },
  {
    id: 'search',
    title: 'Query',
    subtitle: 'Semantic search',
    icon: <Search className="w-5 h-5" />,
    color: 'text-pink-600 dark:text-pink-400',
    bgColor: 'bg-pink-50 dark:bg-pink-950/50',
    borderColor: 'border-pink-300 dark:border-pink-700',
    glowColor: 'shadow-pink-500/20',
  },
  {
    id: 'results',
    title: 'Results',
    subtitle: 'API matches',
    icon: <CheckCircle className="w-5 h-5" />,
    color: 'text-lime-600 dark:text-lime-400',
    bgColor: 'bg-lime-50 dark:bg-lime-950/50',
    borderColor: 'border-lime-300 dark:border-lime-700',
    glowColor: 'shadow-lime-500/20',
  },
];

function FlowNodeCard({ node, isLast }: { node: FlowNode; isLast: boolean }) {
  return (
    <div className="flex items-center gap-2 md:gap-3">
      {/* Node */}
      <div
        className={cn(
          "relative flex flex-col items-center justify-center",
          "w-20 h-20 sm:w-24 sm:h-24 md:w-28 md:h-28",
          "rounded-2xl border-2 transition-all duration-300",
          "hover:scale-105 hover:shadow-xl cursor-default",
          node.bgColor,
          node.borderColor,
          `shadow-lg ${node.glowColor}`
        )}
      >
        {/* Icon */}
        <div className={cn(
          "w-10 h-10 sm:w-11 sm:h-11 md:w-12 md:h-12 rounded-xl",
          "flex items-center justify-center mb-1",
          "bg-white dark:bg-gray-800 shadow-sm",
          "border",
          node.borderColor
        )}>
          <span className={node.color}>{node.icon}</span>
        </div>
        
        {/* Title */}
        <span className={cn(
          "text-xs sm:text-sm font-semibold text-center",
          node.color
        )}>
          {node.title}
        </span>
        
        {/* Subtitle (hidden on small screens) */}
        <span className="hidden sm:block text-[10px] text-muted-foreground text-center leading-tight px-1">
          {node.subtitle}
        </span>
      </div>
      
      {/* Arrow Connector - Hidden on last node */}
      {!isLast && (
        <div className="flex items-center">
          {/* Line */}
          <div className="w-4 sm:w-6 md:w-8 lg:w-12 h-0.5 bg-gradient-to-r from-muted-foreground/40 to-muted-foreground/20" />
          {/* Arrow */}
          <ArrowRight className="w-4 h-4 text-muted-foreground/50 -ml-1" />
        </div>
      )}
    </div>
  );
}

export function CompleteUserJourney() {
  return (
    <div className="w-full">
      {/* Title */}
      <h3 className="text-lg font-semibold text-foreground text-center mb-6">
        User Flow
      </h3>
      
      {/* Horizontal Flowchart - Scrollable on mobile */}
      <div className="overflow-x-auto pb-4">
        <div className="flex items-center justify-start lg:justify-center min-w-max px-4">
          {flowNodes.map((node, idx) => (
            <FlowNodeCard
              key={node.id}
              node={node}
              isLast={idx === flowNodes.length - 1}
            />
          ))}
        </div>
      </div>
      
      {/* Flow Summary Legend */}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          Start
        </span>
        <span className="hidden sm:inline">→</span>
        <span className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-purple-500" />
          Data Pipeline
        </span>
        <span className="hidden sm:inline">→</span>
        <span className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-lime-500" />
          Output
        </span>
      </div>
      
      {/* Vertical Flow for Mobile - Alternative view */}
      <div className="mt-8 block lg:hidden">
        <div className="relative pl-8">
          {/* Vertical Line */}
          <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gradient-to-b from-emerald-400 via-purple-400 to-lime-400" />
          
          {/* Flow Steps */}
          <div className="space-y-4">
            {flowNodes.map((node, idx) => (
              <div key={node.id} className="relative flex items-center gap-4">
                {/* Node Dot on Line */}
                <div className={cn(
                  "absolute -left-5 w-4 h-4 rounded-full border-2 bg-background",
                  node.borderColor
                )} />
                
                {/* Node Info */}
                <div className={cn(
                  "flex items-center gap-3 px-4 py-2 rounded-xl border",
                  node.bgColor,
                  node.borderColor
                )}>
                  <span className={node.color}>{node.icon}</span>
                  <div>
                    <span className={cn("font-medium text-sm", node.color)}>
                      {node.title}
                    </span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {node.subtitle}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompleteUserJourney;
