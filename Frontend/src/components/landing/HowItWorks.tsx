"use client";
import { Card } from "@/components/ui/card";
import { FileText, Brain, Zap, CheckCircle2, ArrowRight } from "lucide-react";

export function HowItWorks() {
  return (
    <section className="py-24 theme-transition bg-gradient-to-b from-transparent via-blue-50/30 to-transparent dark:via-slate-900/30">
      <div className="mx-auto max-w-7xl">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200/50 dark:border-indigo-400/30 bg-white/90 dark:bg-slate-800/90 px-6 py-2.5 text-sm font-medium tracking-wide backdrop-blur-md shadow-lg mb-6">
            <Zap className="h-4 w-4 text-indigo-600 dark:text-indigo-400 animate-pulse" />
            <span className="text-indigo-900 dark:text-indigo-100 font-semibold">Simple Process</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">
            <span className="bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-600 dark:from-indigo-400 dark:via-blue-400 dark:to-cyan-400 bg-clip-text text-transparent">
              How It Works
            </span>
          </h2>
          
          <p className="text-xl text-muted max-w-3xl mx-auto leading-relaxed">
            Transform your testing workflow in four simple steps with our intelligent NLP platform.
          </p>
        </div>

        <div className="relative">
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-1 bg-gradient-to-r from-blue-200 via-indigo-300 to-purple-200 dark:from-blue-900 dark:via-indigo-900 dark:to-purple-900 -translate-y-1/2 -z-10" />
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={step.title} className="relative">
                <Card className="p-8 h-full glass-morphism border-2 hover:border-blue-500/50 dark:hover:border-blue-400/50 shadow-xl hover:shadow-2xl transition-all duration-300 group transform-3d hover:scale-105">
                  <div className="absolute -top-4 -left-4 w-12 h-12 rounded-full bg-gradient-to-br shadow-lg flex items-center justify-center text-white font-bold text-xl border-4 border-white dark:border-slate-900 group-hover:scale-110 transition-transform"
                    style={{
                      background: `linear-gradient(135deg, ${step.color}DD, ${step.color})`
                    }}
                  >
                    {index + 1}
                  </div>

                  <div className="mb-6 flex justify-center">
                    <div 
                      className="w-20 h-20 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform"
                      style={{
                        background: `linear-gradient(135deg, ${step.color}20, ${step.color}35)`
                      }}
                    >
                      <step.icon 
                        className="h-10 w-10" 
                        style={{ color: step.color }}
                      />
                    </div>
                  </div>

                  <div className="text-center">
                    <h3 className="text-xl font-bold mb-3 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {step.title}
                    </h3>
                    <p className="text-muted leading-relaxed mb-4">
                      {step.description}
                    </p>
                    
                    <div className="space-y-2">
                      {step.features.map((feature) => (
                        <div key={feature} className="flex items-center gap-2 text-sm text-muted justify-center">
                          <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                          <span>{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {index < steps.length - 1 && (
                    <div className="hidden lg:block absolute top-1/2 -right-8 -translate-y-1/2 z-10">
                      <ArrowRight className="h-8 w-8 text-blue-500 dark:text-blue-400 animate-pulse" />
                    </div>
                  )}
                </Card>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-16 text-center">
          <p className="text-lg text-muted max-w-2xl mx-auto">
            <span className="font-semibold text-foreground">No coding required.</span> Our AI handles the complexity while you focus on describing what you need tested.
          </p>
        </div>
      </div>
    </section>
  );
}

const steps = [
  {
    title: 'Write Description',
    description: 'Describe your test scenario in plain English, just like you would explain it to a colleague.',
    icon: FileText,
    color: '#3b82f6', 
    features: ['Natural language', 'No syntax rules', 'Quick input']
  },
  {
    title: 'AI Processing',
    description: 'Our advanced NLP engine analyzes your input, identifies patterns, and extracts test requirements.',
    icon: Brain,
    color: '#8b5cf6', 
    features: ['Pattern matching', 'Context aware', 'Smart parsing']
  },
  {
    title: 'Generate Steps',
    description: 'Automatically convert your description into structured, executable test automation steps.',
    icon: Zap,
    color: '#10b981', 
    features: ['Auto-generated', 'Best practices', 'Optimized flow']
  },
  {
    title: 'Execute & Monitor',
    description: 'Run your tests immediately and monitor results in real-time with comprehensive analytics.',
    icon: CheckCircle2,
    color: '#f59e0b', 
    features: ['Instant execution', 'Live monitoring', 'Detailed reports']
  }
];
