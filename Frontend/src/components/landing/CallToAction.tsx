"use client";
import { Button } from "@/components/ui/button";
import { ArrowRight, Rocket, Users, Globe, Sparkles, Star } from "lucide-react";
import Link from "next/link";

export function CallToAction() {
  return (
    <section className="py-28 theme-transition relative">
      <div className="mx-auto max-w-6xl">
        <div className="relative overflow-hidden rounded-[2.5rem] mb-20 glass-medium shadow-2xl shadow-blue-500/30 border-3 border-blue-300/50 dark:border-blue-500/40 backdrop-blur-xl">
          <div aria-hidden="true" className="pointer-events-none absolute inset-0">
            <div className="absolute -top-32 -left-32 h-[30rem] w-[30rem] rounded-full bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 opacity-30 blur-3xl decorative animate-float3d" />
            <div className="absolute -bottom-32 -right-32 h-[30rem] w-[30rem] rounded-full bg-gradient-to-br from-cyan-500 via-blue-500 to-indigo-600 opacity-30 blur-3xl decorative animate-pulse3d" />
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 h-80 w-80 rounded-full bg-gradient-to-r from-violet-400 to-fuchsia-500 opacity-25 blur-3xl decorative animate-tilt" />
          </div>

          <div className="relative text-center px-10 py-20 sm:px-20 sm:py-24">
            <div className="inline-flex items-center gap-3 rounded-full border-2 border-blue-300/70 dark:border-blue-400/50 bg-gradient-to-r from-white/95 to-blue-50/95 dark:from-slate-800/95 dark:to-blue-900/95 px-8 py-4 text-base font-bold mb-10 shadow-2xl backdrop-blur-xl animate-bounce-slow hover:scale-110 transition-transform">
              <Star className="h-7 w-7 text-yellow-500 fill-yellow-500 animate-pulse" aria-hidden="true" />
              <span className="text-[color:var(--foreground)] text-lg font-black">Limited Time Offer</span>
              <Sparkles className="h-7 w-7 text-blue-600 dark:text-blue-400 animate-pulse" aria-hidden="true" />
            </div>

            <h2 className="text-5xl md:text-6xl font-black mb-8 leading-tight">
              <span className="block mb-4">Ready to Transform</span>
              <span className="block bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-400 dark:via-indigo-400 dark:to-purple-400 bg-clip-text text-transparent drop-shadow-2xl">
                Your Workflow?
              </span>
            </h2>

            <p className="text-2xl text-muted max-w-4xl mx-auto mb-12 leading-relaxed font-medium">
              Join thousands of teams already using NLPForge to streamline their test automation workflows 
              and improve system reliability with AI-powered natural language processing.
            </p>

            <div className="flex flex-col gap-6 sm:flex-row sm:justify-center mb-16">
              <Button 
                asChild 
                size="lg" 
                className="btn-primary px-16 py-8 text-xl font-black interactive focus-ring group shadow-2xl shadow-blue-500/50 hover:shadow-blue-500/70 rounded-2xl"
              >
                <Link href="/dashboard" aria-label="Get Started Now" className="inline-flex items-center gap-4">
                  <Rocket className="h-8 w-8 icon-decorative group-hover:rotate-12 group-hover:scale-125 transition-transform" aria-hidden="true" />
                  Get Started Now
                  <ArrowRight className="h-7 w-7 icon-decorative group-hover:translate-x-2 transition-transform" aria-hidden="true" />
                </Link>
              </Button>

              <Button 
                asChild 
                variant="outline" 
                size="lg" 
                className="btn-ghost px-16 py-8 text-xl font-black interactive focus-ring border-3 hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-xl hover:shadow-blue-500/20 rounded-2xl"
              >
                <Link href="/convert" aria-label="Try Free Demo" className="inline-flex items-center gap-3">
                  <Sparkles className="h-7 w-7 icon-decorative group-hover:rotate-12 transition-transform" aria-hidden="true" />
                  Try Free Demo
                </Link>
              </Button>
            </div>

            <div className="flex items-center justify-center gap-12 flex-wrap text-base text-muted font-bold">
              <div className="flex items-center gap-4">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div 
                      key={i} 
                      className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 border-3 border-white dark:border-slate-800 shadow-lg"
                    />
                  ))}
                </div>
                <span className="font-black text-lg">10,000+ Users</span>
              </div>
              <div className="w-0.5 h-8 bg-border" />
              <div className="flex items-center gap-3">
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Star key={i} className="h-6 w-6 text-yellow-500 fill-yellow-500" />
                  ))}
                </div>
                <span className="font-black text-lg">4.9/5 Rating</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-10 md:grid-cols-3">
          {benefits.map((benefit, index) => (
            <div 
              key={benefit.title} 
              className="text-center p-10 rounded-3xl glass-medium border-3 border-blue-200/50 dark:border-blue-500/30 hover:scale-110 hover:shadow-2xl hover:shadow-blue-500/30 transition-all duration-300 group backdrop-blur-xl"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="inline-flex items-center justify-center rounded-2xl p-7 mb-8 shadow-2xl group-hover:scale-125 group-hover:rotate-6 transition-all duration-300"
                style={{
                  background: `linear-gradient(135deg, ${benefit.color}30, ${benefit.color}50)`
                }}
              >
                <benefit.icon 
                  className="h-14 w-14 icon-decorative" 
                  style={{ color: benefit.color }}
                  aria-hidden="true" 
                />
              </div>
              
              <h3 className="text-2xl font-black text-[color:var(--foreground)] mb-4">
                {benefit.title}
              </h3>
              
              <p className="text-lg text-muted leading-relaxed font-medium">
                {benefit.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const benefits = [
  { 
    title: 'Enterprise Ready', 
    description: 'Built for scale with enterprise-grade security, monitoring, and performance optimization.', 
    icon: Globe,
    color: '#3b82f6' 
  },
  { 
    title: 'Team Collaboration', 
    description: 'Designed for teams with shared dictionaries, centralized monitoring, and collaborative workflows.', 
    icon: Users,
    color: '#10b981' 
  },
  { 
    title: 'Instant Results', 
    description: 'Start seeing results immediately with our intuitive interface and pre-configured templates.', 
    icon: Rocket,
    color: '#8b5cf6' 
  },
];
