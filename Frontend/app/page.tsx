'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { ThemeToggle } from '@/components/theme-toggle';
import { ColorPicker } from '@/components/color-picker';
import { HeroSection } from '@/components/hero/HeroSection';
import { MouseFollower } from '@/components/ui/MouseFollower';
import { ParticleCursor } from '@/components/ui/ParticleCursor';
import { ArrowRight, Sparkles, Twitter, Github } from 'lucide-react';
import { Footer } from "@/components/ui/modem-animated-footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-background overflow-x-hidden selection:bg-primary/20 selection:text-primary">
      <MouseFollower />
      <ParticleCursor />
      
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/60 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/50 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl tracking-tight">NLPForge</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              Features
            </Link>
            <Link href="#pricing" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              Pricing
            </Link>
            <Link href="#docs" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              Docs
            </Link>
          </nav>

          <div className="flex items-center gap-4">
            <ColorPicker />
            <ThemeToggle />
            <Link href="/dashboard">
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-95">
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        {/* Hero Section */}
        <HeroSection />
      </main>
    </div>
  );
}
