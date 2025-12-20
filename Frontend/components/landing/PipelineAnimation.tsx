'use client';

import { motion } from 'framer-motion';
import { Database, FileJson, Cpu, Zap, Search, BarChart3 } from 'lucide-react';

const steps = [
  {
    id: 'input',
    title: 'API Spec',
    icon: FileJson,
    color: 'text-blue-400',
    bg: 'bg-blue-400/10',
    border: 'border-blue-400/20',
  },
  {
    id: 'process',
    title: 'AI Processing',
    icon: Cpu,
    color: 'text-sky-400',
    bg: 'bg-sky-400/10',
    border: 'border-sky-400/20',
  },
  {
    id: 'generate',
    title: 'Test Gen',
    icon: Database,
    color: 'text-pink-400',
    bg: 'bg-pink-400/10',
    border: 'border-pink-400/20',
  },
  {
    id: 'execute',
    title: 'Execution',
    icon: Zap,
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    border: 'border-amber-400/20',
  },
  {
    id: 'analyze',
    title: 'Insights',
    icon: BarChart3,
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    border: 'border-emerald-400/20',
  },
];

export const PipelineAnimation = () => {
  return (
    <div className="w-full max-w-5xl mx-auto py-20 relative">
      {/* Connecting Line */}
      <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-primary/20 to-transparent -translate-y-1/2 hidden md:block" />

      {/* Animated Pulse on Line */}
      <motion.div
        className="absolute top-1/2 left-0 h-0.5 w-20 bg-gradient-to-r from-transparent via-primary to-transparent -translate-y-1/2 hidden md:block blur-sm"
        animate={{
          left: ['0%', '100%'],
          opacity: [0, 1, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      <div className="grid grid-cols-1 md:grid-cols-5 gap-8 relative z-10">
        {steps.map((step, index) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.2 }}
            className="relative group"
          >
            <div className={`
              flex flex-col items-center justify-center p-6 rounded-2xl
              border backdrop-blur-sm transition-all duration-300
              ${step.bg} ${step.border}
              hover:scale-105 hover:shadow-lg hover:shadow-primary/5
            `}>
              <div className={`mb-4 p-3 rounded-xl bg-background/50 ${step.color}`}>
                <step.icon className="w-8 h-8" />
              </div>
              <h3 className="font-semibold text-sm md:text-base text-foreground/90">
                {step.title}
              </h3>

              {/* Hover Glow Effect */}
              <div className={`
                absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100
                transition-opacity duration-500 pointer-events-none
                bg-gradient-to-b from-white/5 to-transparent
              `} />
            </div>

            {/* Mobile Connector */}
            {index < steps.length - 1 && (
              <div className="md:hidden absolute left-1/2 bottom-[-2rem] w-0.5 h-8 bg-border -translate-x-1/2" />
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};
