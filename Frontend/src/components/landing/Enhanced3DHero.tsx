'use client';

/**
 * Enhanced 3D Hero - Alternative landing hero component
 * Currently not used in favor of the unified Hero component
 * 
 * To enable 3D rendering, install:
 * npm install gsap @react-three/fiber @react-three/drei three
 */

import { Button } from '@/components/ui/button';
import { ArrowRight, Sparkles } from 'lucide-react';

export function Enhanced3DHero() {
  return (
    <section 
      className="relative min-h-[90vh] flex items-center justify-center overflow-hidden"
      aria-labelledby="hero-headline"
    >
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-background/50 to-background pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Test Automation</span>
          </div>

          {/* Headline */}
          <h1
            id="hero-headline"
            className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight"
          >
            Convert Natural Language
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/60">
              Into Automated Tests
            </span>
          </h1>

          {/* Description */}
          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Transform your testing workflow with NLPForge&apos;s intelligent rule engine. 
            87.8% success rate in converting plain English to structured test steps.
          </p>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button size="lg" variant="default">
              Get Started
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline">
              View Documentation
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto pt-12">
            {[
              { value: '87.8%', label: 'Success Rate' },
              { value: '20+', label: 'Functions' },
              { value: '<100ms', label: 'Response Time' },
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-primary">{stat.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
