'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, PlayCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ProductPreview } from './ProductPreview';

/**
 * HeroSection - Enterprise-grade landing hero
 * 
 * Redesigned to follow "Enterprise Calm" design language:
 * - Split layout: Left text (60%) + Right product preview (40%)
 * - Subtle staggered animations (respects reduced motion)
 * - Specific product terminology, no generic AI clichés
 * - Full viewport height (minus nav)
 * - Magenta Orb Grid background pattern
 */
export function HeroSection() {
  return (
    <section className="relative min-h-[100svh] flex items-center pt-16">
      {/* Magenta Orb Grid Background - Light Mode (reduced intensity) */}
      <div
        className="absolute inset-0 dark:hidden pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(100,116,139,0.12) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(100,116,139,0.12) 1px, transparent 1px),
            radial-gradient(circle at 50% 60%, rgba(236,72,153,0.15) 0%, rgba(168,85,247,0.06) 40%, transparent 70%)
          `,
          backgroundSize: "40px 40px, 40px 40px, 100% 100%",
          backgroundColor: "white",
        }}
        aria-hidden="true"
      />

      {/* Magenta Orb Grid Background - Dark Mode (reduced intensity) */}
      <div
        className="absolute inset-0 hidden dark:block pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(148,163,184,0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(148,163,184,0.1) 1px, transparent 1px),
            radial-gradient(circle at 50% 60%, rgba(236,72,153,0.12) 0%, rgba(168,85,247,0.05) 40%, transparent 70%)
          `,
          backgroundSize: "40px 40px, 40px 40px, 100% 100%",
          backgroundColor: "hsl(222, 25%, 6%)",
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Column - Text Content */}
          <div className="max-w-xl lg:max-w-none animate-fade-in-up">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground mb-6">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span>LLM-Powered API Testing</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[3.25rem] font-bold tracking-tight text-foreground leading-[1.15] mb-6">
              Generate API Test Cases
              <br />
              <span className="text-primary">From Natural Language</span>
            </h1>

            {/* Subheadline */}
            <p className="text-base sm:text-lg text-muted-foreground max-w-lg leading-relaxed mb-8">
              Define your API templates once. NLPForge generates thousands of
              semantic test cases using LLM-powered data generation and Redis
              vector search. Stop writing fragile test scripts.
            </p>

            {/* CTA Buttons - Strong hierarchy */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 mb-10">
              <Button asChild size="lg" className="h-12 px-8 text-base font-semibold group shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:rounded-xl transition-all duration-200">
                <Link href="/dashboard">
                  Start Testing
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>

              <Button
                asChild
                variant="ghost"
                size="lg"
                className="h-12 px-6 text-base font-medium text-muted-foreground hover:text-foreground"
              >
                <Link href="/templates">
                  <PlayCircle className="w-4 h-4 mr-2" />
                  View Templates
                </Link>
              </Button>
            </div>

            {/* Feature Pills */}
            <div className="flex flex-wrap items-center gap-2.5">
              <FeaturePill>LLM-powered generation</FeaturePill>
              <FeaturePill>Vector semantic search</FeaturePill>
              <FeaturePill>Multi-model embedding</FeaturePill>
            </div>
          </div>

          {/* Right Column - Product Preview with soft vignette */}
          <div className="lg:pl-8 animate-fade-in-up animation-delay-200 relative">
            {/* Soft radial vignette behind preview */}
            <div
              className="absolute -inset-12 rounded-full pointer-events-none opacity-60 dark:opacity-40"
              style={{
                background: 'radial-gradient(circle, rgba(236,72,153,0.08) 0%, rgba(168,85,247,0.04) 30%, transparent 70%)'
              }}
              aria-hidden="true"
            />
            <ProductPreview />
          </div>
        </div>
      </div>

      {/* Animation Styles - Using CSS for performance and reduced-motion respect */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease-out forwards;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
          opacity: 0;
        }
        
        @media (prefers-reduced-motion: reduce) {
          .animate-fade-in-up {
            animation: none;
            opacity: 1;
            transform: none;
          }
          .animation-delay-200 {
            animation: none;
            opacity: 1;
          }
        }
      `}</style>
    </section>
  );
}

function FeaturePill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center px-3 py-1.5 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground transition-colors hover:bg-muted">
      {children}
    </span>
  );
}

export default HeroSection;
