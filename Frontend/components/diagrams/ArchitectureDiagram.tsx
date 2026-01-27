'use client';

import { 
  Globe, 
  Server, 
  Cog, 
  Cpu, 
  Zap, 
  Bot, 
  Database, 
  HardDrive,
  type LucideIcon
} from 'lucide-react';
import { ReactNode } from 'react';

/**
 * ArchitectureDiagram Component
 * 
 * Visual representation of the NLPForge system architecture
 * showing all components, services, and their connections
 * Uses professional Lucide icons with proper dark theme support
 */

interface ServiceBoxProps {
  title: string;
  items: string[];
  color: 'blue' | 'green' | 'purple' | 'amber' | 'rose';
  icon: ReactNode;
}

function ServiceBox({ title, items, color, icon }: ServiceBoxProps) {
  const colorClasses = {
    blue: 'bg-blue-50/80 border-blue-200/80 dark:bg-blue-950/40 dark:border-blue-700/50',
    green: 'bg-green-50/80 border-green-200/80 dark:bg-green-950/40 dark:border-green-700/50',
    purple: 'bg-purple-50/80 border-purple-200/80 dark:bg-purple-950/40 dark:border-purple-700/50',
    amber: 'bg-amber-50/80 border-amber-200/80 dark:bg-amber-950/40 dark:border-amber-700/50',
    rose: 'bg-rose-50/80 border-rose-200/80 dark:bg-rose-950/40 dark:border-rose-700/50',
  };

  const headerColors = {
    blue: 'bg-blue-100/90 text-blue-900 dark:bg-blue-900/60 dark:text-blue-100',
    green: 'bg-green-100/90 text-green-900 dark:bg-green-900/60 dark:text-green-100',
    purple: 'bg-purple-100/90 text-purple-900 dark:bg-purple-900/60 dark:text-purple-100',
    amber: 'bg-amber-100/90 text-amber-900 dark:bg-amber-900/60 dark:text-amber-100',
    rose: 'bg-rose-100/90 text-rose-900 dark:bg-rose-900/60 dark:text-rose-100',
  };

  const iconColors = {
    blue: 'text-blue-600 dark:text-blue-300',
    green: 'text-green-600 dark:text-green-300',
    purple: 'text-purple-600 dark:text-purple-300',
    amber: 'text-amber-600 dark:text-amber-300',
    rose: 'text-rose-600 dark:text-rose-300',
  };

  const bulletColors = {
    blue: 'bg-blue-400 dark:bg-blue-400',
    green: 'bg-green-400 dark:bg-green-400',
    purple: 'bg-purple-400 dark:bg-purple-400',
    amber: 'bg-amber-400 dark:bg-amber-400',
    rose: 'bg-rose-400 dark:bg-rose-400',
  };

  return (
    <div className={`rounded-xl border-2 overflow-hidden shadow-sm ${colorClasses[color]}`}>
      <div className={`px-4 py-3 font-semibold flex items-center gap-2.5 ${headerColors[color]}`}>
        <span className={iconColors[color]}>{icon}</span>
        <span className="text-sm">{title}</span>
      </div>
      <div className="p-4">
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li key={index} className="flex items-center gap-2.5 text-sm text-foreground/80 dark:text-foreground/90">
              <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${bulletColors[color]}`} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

interface ConnectionLineProps {
  direction: 'down' | 'right' | 'both';
}

function ConnectionLine({ direction }: ConnectionLineProps) {
  if (direction === 'down') {
    return (
      <div className="flex justify-center py-3">
        <div className="flex flex-col items-center gap-1">
          <div className="w-0.5 h-4 bg-gradient-to-b from-primary/60 to-primary/30 dark:from-primary/70 dark:to-primary/40 rounded-full" />
          <div className="w-2 h-2 rotate-45 border-b-2 border-r-2 border-primary/40 dark:border-primary/50 -mt-1" />
        </div>
      </div>
    );
  }
  
  if (direction === 'right') {
    return (
      <div className="hidden md:flex items-center px-2">
        <div className="h-0.5 w-8 bg-gradient-to-r from-primary/60 to-primary/30 dark:from-primary/70 dark:to-primary/40 rounded-full" />
      </div>
    );
  }
  
  return null;
}

interface LayerBadgeProps {
  label: string;
  color: 'blue' | 'green' | 'purple' | 'amber';
}

function LayerBadge({ label, color }: LayerBadgeProps) {
  const colors = {
    blue: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/50 dark:text-blue-200 dark:border-blue-700/50',
    green: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/50 dark:text-green-200 dark:border-green-700/50',
    purple: 'bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900/50 dark:text-purple-200 dark:border-purple-700/50',
    amber: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/50 dark:text-amber-200 dark:border-amber-700/50',
  };

  return (
    <span className={`px-3 py-1.5 rounded-full text-xs font-medium border ${colors[color]}`}>
      {label}
    </span>
  );
}

export function ArchitectureDiagram() {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Frontend Layer */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-center text-foreground flex items-center justify-center gap-2">
          <LayerBadge label="Client Layer" color="blue" />
        </h3>
        <ServiceBox
          title="Frontend (Next.js 14)"
          icon={<Globe className="w-4 h-4" />}
          color="blue"
          items={[
            'Dashboard & Analytics',
            'Template Builder',
            'Dataset Management',
            'Query Interface',
            'Settings & Configuration',
            'Authentication Flow'
          ]}
        />
      </div>

      <ConnectionLine direction="down" />

      {/* Backend Layer */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-center text-foreground flex items-center justify-center gap-2">
          <LayerBadge label="API Layer" color="green" />
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          <ServiceBox
            title="API Routes (FastAPI)"
            icon={<Server className="w-4 h-4" />}
            color="green"
            items={[
              '/auth - Authentication',
              '/templates - Template CRUD',
              '/datasets - Dataset Generation',
              '/embeddings - Vector Operations',
              '/ranking - Semantic Search',
              '/telemetry - Metrics & Logs'
            ]}
          />
          <ServiceBox
            title="Service Layer"
            icon={<Cog className="w-4 h-4" />}
            color="green"
            items={[
              'Embedding Service',
              'Ranking Engine',
              'Slot Extraction',
              'Dataset Generator',
              'Audit Service',
              'Intent Classifier'
            ]}
          />
        </div>
      </div>

      <ConnectionLine direction="down" />

      {/* AI/ML Layer */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-center text-foreground flex items-center justify-center gap-2">
          <LayerBadge label="AI/ML Layer" color="purple" />
        </h3>
        <div className="grid md:grid-cols-3 gap-4">
          <ServiceBox
            title="Ollama (Local)"
            icon={<Cpu className="w-4 h-4" />}
            color="purple"
            items={[
              'Embedding Models',
              'LLM Inference',
              'Privacy-First'
            ]}
          />
          <ServiceBox
            title="FlashRank"
            icon={<Zap className="w-4 h-4" />}
            color="purple"
            items={[
              'Cross-Encoder',
              'Re-ranking',
              'ms-marco Model'
            ]}
          />
          <ServiceBox
            title="LLM Providers"
            icon={<Bot className="w-4 h-4" />}
            color="purple"
            items={[
              'Google Gemini',
              'OpenAI GPT',
              'Anthropic Claude'
            ]}
          />
        </div>
      </div>

      <ConnectionLine direction="down" />

      {/* Storage Layer */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-center text-foreground flex items-center justify-center gap-2">
          <LayerBadge label="Storage Layer" color="amber" />
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          <ServiceBox
            title="PostgreSQL"
            icon={<Database className="w-4 h-4" />}
            color="amber"
            items={[
              'User Accounts',
              'Templates',
              'Datasets',
              'Audit Logs'
            ]}
          />
          <ServiceBox
            title="Redis Stack"
            icon={<HardDrive className="w-4 h-4" />}
            color="rose"
            items={[
              'Vector Index',
              'Embeddings Storage',
              'RediSearch',
              'Caching'
            ]}
          />
        </div>
      </div>
    </div>
  );
}

export default ArchitectureDiagram;
