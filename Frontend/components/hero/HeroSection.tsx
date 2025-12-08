'use client';

import React, { useState, useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Sparkles, ArrowRight, PlayCircle, Command } from 'lucide-react';
import { AuroraBackground } from './AuroraBackground';
import { PIPELINE_STEPS } from './pipeline-data';
import { RainbowButton } from '@/components/ui/rainbow-button';
import { LampContainer } from '@/components/ui/lamp';

export function HeroSection() {
  const [isClient, setIsClient] = useState(false);
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 500], [0, 200]);
  const y2 = useTransform(scrollY, [0, 500], [0, -150]);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Triple the steps to ensure smooth infinite scrolling
  const marqueeSteps = [...PIPELINE_STEPS, ...PIPELINE_STEPS, ...PIPELINE_STEPS];

  return (
    <AuroraBackground className="min-h-screen relative overflow-hidden flex flex-col justify-center">
      <div className="relative z-10 container mx-auto px-4 md:px-8 pt-20 pb-12 flex flex-col items-center text-center">
        
      <LampContainer>
        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0.5, y: 100 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.3,
            duration: 0.8,
            ease: "easeInOut",
          }}
          className="text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6 bg-gradient-to-br from-foreground via-foreground/90 to-foreground/50 bg-clip-text text-transparent leading-[1.1] relative z-50"
        >
          Automate API Testing <br />
          <span className="relative inline-block">
            <span className="absolute inset-0 bg-gradient-to-r from-primary via-purple-500 to-pink-500 blur-2xl opacity-20 animate-pulse" />
            <span className="relative bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-500 to-pink-500 animate-gradient-x bg-[length:200%_auto]">
              With Intelligence
            </span>
          </span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="text-base sm:text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed relative z-20"
        >
          Stop writing fragile scripts. Generate thousands of semantic test cases instantly using our LLM-powered pipeline and Redis vector search.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex flex-col sm:flex-row items-center gap-4 relative z-20"
        >
          <RainbowButton className="w-full sm:w-auto">
            <span className="flex items-center justify-center gap-2">
              Start Free Trial
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </span>
          </RainbowButton>
          
          <button className="group px-8 py-4 bg-background/50 backdrop-blur-sm border border-border text-foreground rounded-full font-semibold text-lg hover:bg-background/80 hover:border-primary/30 transition-all duration-300 flex items-center justify-center gap-2 w-full sm:w-auto">
            <PlayCircle className="w-5 h-5 text-primary" />
            Watch Demo
            <span className="ml-2 text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border group-hover:border-primary/30 transition-colors">
              <Command className="w-3 h-3 inline mr-1" />K
            </span>
          </button>
        </motion.div>
      </LampContainer>

        {/* Horizontal Marquee Pipeline */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="w-full max-w-[100vw] overflow-hidden relative py-10"
        >
          {/* Fade Overlays */}
          <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-background to-transparent z-20 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-background to-transparent z-20 pointer-events-none" />

          {/* Background Connecting Line */}
          <div className="absolute top-1/2 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/20 to-transparent -translate-y-1/2 z-0" />

          <motion.div
            className="flex gap-0 w-max items-center"
            animate={{ x: [0, -1000] }} // Adjust based on content width
            transition={{
              x: {
                duration: 30,
                repeat: Infinity,
                ease: "linear",
              },
            }}
          >
            {marqueeSteps.map((step, i) => (
              <div key={`marquee-${i}`} className="flex items-center">
                <PipelineCard step={step} index={i} />
                {/* Connector Arrow */}
                <div className="w-16 h-[2px] bg-gradient-to-r from-primary/20 to-primary/50 relative flex items-center justify-center mx-2">
                  <div className="absolute right-0 w-2 h-2 border-t-2 border-r-2 border-primary/50 rotate-45 transform translate-y-[-1px]" />
                  <motion.div 
                    className="w-full h-full bg-primary/50 origin-left"
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: [0, 1, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
                  />
                </div>
              </div>
            ))}
          </motion.div>
        </motion.div>

      </div>

      {/* Background Floating Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div 
          style={{ y: y2 }}
          className="absolute top-[20%] left-[10%] w-72 h-72 bg-purple-500/10 rounded-full blur-[100px]" 
        />
        <motion.div 
          style={{ y: y1 }}
          className="absolute bottom-[20%] right-[10%] w-96 h-96 bg-blue-500/10 rounded-full blur-[100px]" 
        />
      </div>
    </AuroraBackground>
  );
}

// Helper Component for Cards
function PipelineCard({ step, index }: { step: any, index: number }) {
  const Icon = step.icon;
  return (
    <motion.div
      whileHover={{ 
        scale: 1.05,
        boxShadow: `0 0 30px ${step.glowColor}40`
      }}
      className="relative flex-shrink-0 w-64 p-6 rounded-2xl bg-background/40 backdrop-blur-md border border-white/10 transition-all duration-300 group overflow-hidden"
      style={{
        boxShadow: `0 0 0 1px ${step.glowColor}20`
      }}
    >
      {/* Gradient Background on Hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${step.color} opacity-0 group-hover:opacity-10 transition-opacity duration-500`} />
      
      {/* Icon with Glow */}
      <div className="relative w-12 h-12 rounded-xl bg-background/50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 border border-white/10 shadow-inner">
        <Icon 
          className="w-6 h-6" 
          style={{ color: step.glowColor }}
        />
        <div 
          className="absolute inset-0 rounded-xl opacity-20 blur-md transition-opacity duration-300 group-hover:opacity-40"
          style={{ backgroundColor: step.glowColor }}
        />
      </div>

      {/* Content */}
      <h3 className="font-bold text-lg text-foreground mb-1 group-hover:text-primary transition-colors">
        {step.title}
      </h3>
      <p className="text-xs text-muted-foreground font-medium leading-relaxed">
        {step.description}
      </p>

      {/* Bottom Accent Line */}
      <div 
        className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${step.color} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left`} 
      />
    </motion.div>
  );
}
