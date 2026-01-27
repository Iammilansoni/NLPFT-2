'use client';

import { 
  ArrowRight, 
  MessageSquareText, 
  Brain, 
  Search, 
  Zap, 
  Crosshair, 
  CheckCircle 
} from 'lucide-react';
import { ReactNode } from 'react';

/**
 * UserFlowDiagram Component
 * 
 * Visual representation of the NLPForge processing pipeline
 * showing how natural language queries are transformed into API test cases
 * Uses professional Lucide icons with proper dark theme support
 */

interface FlowStepProps {
  number: number;
  title: string;
  description: string;
  icon: ReactNode;
  isLast?: boolean;
}

function FlowStep({ number, title, description, icon, isLast }: FlowStepProps) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border hover:border-primary/40 hover:shadow-md transition-all duration-200">
      <div className="flex flex-col items-center">
        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/15 to-primary/5 dark:from-primary/25 dark:to-primary/10 border border-primary/20 dark:border-primary/30 flex items-center justify-center text-primary shadow-sm">
          {icon}
        </div>
        <div className="w-8 h-8 -mt-2 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs shadow-md border-2 border-background">
          {number}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-foreground text-sm">{title}</h4>
        <p className="text-xs text-muted-foreground leading-relaxed mt-0.5">{description}</p>
      </div>
      {!isLast && (
        <ArrowRight className="w-5 h-5 text-primary/40 hidden lg:block flex-shrink-0" />
      )}
    </div>
  );
}

export function UserFlowDiagram() {
  const steps = [
    {
      number: 1,
      title: 'Natural Language Input',
      description: 'User describes what they want to test in plain English',
      icon: <MessageSquareText className="w-6 h-6" />,
    },
    {
      number: 2,
      title: 'Semantic Understanding',
      description: 'Query is converted to embeddings using AI models',
      icon: <Brain className="w-6 h-6" />,
    },
    {
      number: 3,
      title: 'Vector Search',
      description: 'Find similar API templates using similarity search',
      icon: <Search className="w-6 h-6" />,
    },
    {
      number: 4,
      title: 'Re-ranking',
      description: 'FlashRank cross-encoder refines the results',
      icon: <Zap className="w-6 h-6" />,
    },
    {
      number: 5,
      title: 'Slot Extraction',
      description: 'LLM extracts values from the query',
      icon: <Crosshair className="w-6 h-6" />,
    },
    {
      number: 6,
      title: 'API Test Case',
      description: 'Complete executable test case ready to run',
      icon: <CheckCircle className="w-6 h-6" />,
    },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {steps.map((step, index) => (
          <FlowStep
            key={step.number}
            {...step}
            isLast={index === steps.length - 1}
          />
        ))}
      </div>
      
      {/* Mobile Flow Connector */}
      <div className="mt-6 lg:hidden flex justify-center">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <MessageSquareText className="w-4 h-4" />
          <ArrowRight className="w-3 h-3 text-primary/40" />
          <Brain className="w-4 h-4" />
          <ArrowRight className="w-3 h-3 text-primary/40" />
          <Search className="w-4 h-4" />
          <ArrowRight className="w-3 h-3 text-primary/40" />
          <Zap className="w-4 h-4" />
          <ArrowRight className="w-3 h-3 text-primary/40" />
          <Crosshair className="w-4 h-4" />
          <ArrowRight className="w-3 h-3 text-primary/40" />
          <CheckCircle className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}

export default UserFlowDiagram;
