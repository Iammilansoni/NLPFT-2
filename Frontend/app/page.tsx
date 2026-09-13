'use client';

import { LandingNav } from '@/components/landing/LandingNav';
import { HeroSection } from '@/components/hero/HeroSection';
import { AnimatedTagline } from '@/components/landing/AnimatedTagline';
import { ProblemSolution } from '@/components/landing/ProblemSolution';
import { ScrollStickyFeature } from '@/components/landing/ScrollStickyFeature';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { FeatureHighlights } from '@/components/landing/FeatureHighlights';
import { LiveSearchDemo } from '@/components/landing/LiveSearchDemo';
import { MetricsProof } from '@/components/landing/MetricsProof';
import { TargetUsers } from '@/components/landing/TargetUsers';
import { CTABanner } from '@/components/landing/CTABanner';
import { LandingFooter } from '@/components/landing/LandingFooter';

/**
 * Landing Page — NLPForge
 *
 * Visual hierarchy (Vivo-inspired premium scroll experience):
 * 1.  Hero               — headline + CTA + product preview
 * 2.  AnimatedTagline    — Rotating big word: Generate / Discover / Embed / Automate
 * 3.  ProblemSolution    — Before vs After comparison
 * 4.  ScrollStickyFeature— Sticky left panel with 3 scroll-through feature steps
 * 5.  HowItWorks         — 3-step cards
 * 6.  FeatureHighlights  — Deep feature cards
 * 7.  LiveSearchDemo     — Live animated semantic search terminal
 * 8.  MetricsProof       — Animated counters + testimonials
 * 9.  TargetUsers        — QA / AI / Engineering persona cards
 * 10. CTABanner          — Conversion block
 * 11. Footer
 */
export default function Home() {
  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <LandingNav />
      <main>
        <HeroSection />
        <AnimatedTagline />
        <ProblemSolution />
        <ScrollStickyFeature />
        <HowItWorks />
        <FeatureHighlights />
        <LiveSearchDemo />
        <MetricsProof />
        <TargetUsers />
        <CTABanner />
      </main>
      <LandingFooter />
    </div>
  );
}

