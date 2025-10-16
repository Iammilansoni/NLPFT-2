'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { gsap } from 'gsap';
import { Button } from '@/components/ui/enhanced-button';
import { ArrowRight, Sparkles } from 'lucide-react';
import { useParallax } from '@/hooks/useParallax';


const Scene3DWrapper = dynamic(
  () => import('@/components/3d/Scene3DWrapper').then((mod) => mod.Scene3DWrapper),
  { ssr: false }
);

const LowPolyHero = dynamic(
  () => import('@/components/3d/LowPolyHero').then((mod) => mod.LowPolyHero),
  { ssr: false }
);


export function Enhanced3DHero() {
  const [isMounted, setIsMounted] = useState(false);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const descriptionRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const { x, y } = useParallax({ strength: 15 });

  useEffect(() => {
    setIsMounted(true);

    
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.fromTo(
      headlineRef.current,
      { opacity: 0, y: 50 },
      { opacity: 1, y: 0, duration: 1, delay: 0.3 }
    )
      .fromTo(
        descriptionRef.current,
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, duration: 0.8 },
        '-=0.5'
      )
      .fromTo(
        ctaRef.current,
        { opacity: 0, scale: 0.9 },
        { opacity: 1, scale: 1, duration: 0.6 },
        '-=0.4'
      );

    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      tl.kill();
    }

    return () => {
      tl.kill();
    };
  }, []);

  return (
    <section 
      className="relative min-h-[90vh] flex items-center justify-center overflow-hidden"
      aria-labelledby="hero-headline"
    >
      {isMounted && (
        <div className="absolute inset-0 opacity-40">
          <Scene3DWrapper
            fallback={
              <div className="w-full h-full bg-gradient-to-br from-primary/10 via-primary/5 to-transparent" />
            }
          >
            <LowPolyHero scale={2} rotationSpeed={0.002} />
          </Scene3DWrapper>
        </div>
      )}

      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background pointer-events-none" />

      <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          className="max-w-4xl mx-auto space-y-8"
          style={{
            transform: `translate(${x}px, ${y}px)`,
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium"
          >
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Test Automation</span>
          </motion.div>

          <h1
            ref={headlineRef}
            id="hero-headline"
            className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight"
          >
            Convert Natural Language
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/60">
              Into Automated Tests
            </span>
          </h1>

          <p
            ref={descriptionRef}
            className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed"
          >
            Transform your testing workflow with NLPForge&apos;s intelligent rule engine. 
            87.8% success rate in converting plain English to structured test steps.
          </p>

          {/* CTA */}
          <div ref={ctaRef} className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button size="xl" variant="default">
              Get Started
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button size="xl" variant="outline">
              View Documentation
            </Button>
          </div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5, duration: 0.8 }}
            className="grid grid-cols-3 gap-8 max-w-2xl mx-auto pt-12"
          >
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
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          delay: 2,
          duration: 0.8,
          repeat: Infinity,
          repeatType: 'reverse',
        }}
        aria-hidden="true"
      >
        <div className="w-6 h-10 border-2 border-primary/30 rounded-full flex items-start justify-center p-2">
          <div className="w-1.5 h-3 bg-primary rounded-full" />
        </div>
      </motion.div>
    </section>
  );
}
