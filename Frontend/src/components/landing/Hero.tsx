"use client";
import { Button } from "@/components/ui/button";
import { Activity, ArrowRight, Sparkles, Zap, TrendingUp, Shield } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef } from "react";

export function Hero() {
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!heroRef.current) return;
      const { clientX, clientY } = e;
      const { innerWidth, innerHeight } = window;
      const x = (clientX / innerWidth - 0.5) * 20;
      const y = (clientY / innerHeight - 0.5) * 20;
      
      heroRef.current.style.setProperty('--mouse-x', `${x}px`);
      heroRef.current.style.setProperty('--mouse-y', `${y}px`);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <section
      ref={heroRef}
      className="relative isolate overflow-hidden rounded-[2.5rem] p-12 sm:p-20 mb-24 glass-morphism theme-transition"
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.05) 100%)',
        boxShadow: '0 25px 80px rgba(0,0,0,0.15), 0 10px 30px rgba(59,130,246,0.1), inset 0 1px 0 rgba(255,255,255,0.4)'
      }}
      aria-labelledby="hero-title"
      role="region"
    >
      <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]" aria-hidden="true">
        <div className="absolute inset-0" style={{
          backgroundImage: 'linear-gradient(rgba(59,130,246,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.4) 1px, transparent 1px)',
          backgroundSize: '50px 50px'
        }} />
      </div>

      <div className="pointer-events-none absolute inset-0 transform-3d perspective-1000" aria-hidden="true">
        <div 
          className="absolute -top-32 -left-16 h-96 w-96 rounded-full bg-gradient-to-br from-blue-400 via-indigo-500 to-purple-600 decorative animate-float3d depth-1 opacity-30 blur-3xl"
          style={{ transform: 'translate(var(--mouse-x, 0), var(--mouse-y, 0))' }}
        />
        <div 
          className="absolute bottom-0 right-0 h-[28rem] w-[28rem] rounded-full bg-gradient-to-br from-cyan-300 via-blue-500 to-indigo-700 decorative animate-pulse3d depth-2 opacity-25 blur-3xl"
          style={{ transform: 'translate(calc(var(--mouse-x, 0) * -0.5), calc(var(--mouse-y, 0) * -0.5))' }}
        />
        <div 
          className="absolute top-1/3 right-1/4 w-80 h-80 rounded-full bg-gradient-to-r from-violet-300 via-fuchsia-400 to-pink-500 decorative animate-tilt depth-3 opacity-20 blur-3xl"
          style={{ transform: 'translate(calc(var(--mouse-x, 0) * 0.3), calc(var(--mouse-y, 0) * 0.3))' }}
        />
      </div>

      <div className="relative mx-auto max-w-5xl text-center flex flex-col items-center gap-8">
        <div className="inline-flex items-center gap-2 rounded-full border-2 border-blue-300/60 dark:border-blue-500/40 bg-gradient-to-r from-white/95 to-blue-50/95 dark:from-slate-800/95 dark:to-blue-900/95 px-7 py-3 text-sm font-bold tracking-wide backdrop-blur-xl shadow-2xl interactive transform-3d hover:scale-110 transition-all duration-300">
          <Sparkles className="h-5 w-5 text-blue-600 dark:text-blue-400 icon-decorative animate-pulse" aria-hidden="true" />
          <span className="bg-gradient-to-r from-blue-700 to-indigo-700 dark:from-blue-300 dark:to-indigo-300 bg-clip-text text-transparent">🚀 Enterprise NLP Platform</span>
        </div>

        <h1 id="hero-title" className="font-extrabold tracking-tight text-center text-[clamp(2.75rem,6vw,5rem)] leading-[1.05] mb-2">
          <span className="block mb-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-400 dark:via-indigo-400 dark:to-purple-400 bg-clip-text text-transparent drop-shadow-2xl">Transform Language Into</span>
          <span className="block relative overflow-hidden whitespace-nowrap">
            <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 dark:from-purple-400 dark:via-pink-400 dark:to-rose-400 bg-clip-text text-transparent animate-gradient bg-[length:200%_auto] drop-shadow-2xl inline-block"
              style={{
                animation: 'typewriter 4s steps(22) infinite, gradient 3s ease infinite',
                borderRight: '0.15em solid',
                borderColor: 'rgb(147 51 234)',
                paddingRight: '0.1em'
              }}>
              Automated Intelligence
            </span>
          </span>
        </h1>

        <p className="max-w-4xl text-xl leading-relaxed text-muted sm:text-2xl font-medium opacity-90">
          Harness the power of AI to convert natural language into structured test automation. 
          Monitor system health in real-time and manage enterprise-grade dictionaries—all from one unified platform.
        </p>

        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-center mt-6">
          <Button asChild size="lg" className="btn-primary interactive focus-ring px-12 py-7 text-xl font-bold group shadow-2xl hover:shadow-blue-500/50 transition-all duration-300">
            <Link href="/dashboard" aria-label="View Dashboard" className="inline-flex items-center gap-3">
              <Activity className="h-7 w-7 icon-decorative group-hover:rotate-12 transition-transform duration-300" aria-hidden="true" />
              <span>Launch Dashboard</span>
              <ArrowRight className="h-6 w-6 icon-decorative group-hover:translate-x-2 transition-transform duration-300" aria-hidden="true" />
            </Link>
          </Button>

          <Button asChild variant="outline" size="lg" className="btn-ghost interactive focus-ring px-12 py-7 text-xl font-bold border-2 hover:border-blue-600 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-all duration-300">
            <Link href="/convert" aria-label="Try AI Converter" className="inline-flex items-center gap-3">
              <Zap className="h-6 w-6 icon-decorative" aria-hidden="true" />
              Try AI Converter
            </Link>
          </Button>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-3 w-full max-w-5xl">
          {stats.map((stat, index) => (
            <div 
              key={stat.label} 
              className="text-center p-8 rounded-3xl glass-morphism hover:scale-110 transition-all duration-500 group border-2 border-white/20 dark:border-slate-700/30 shadow-xl hover:shadow-2xl"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <div className="flex justify-center mb-4">
                <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/40 dark:to-indigo-900/40 shadow-lg group-hover:scale-110 transition-transform duration-300">
                  <stat.icon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
              <div className="text-4xl md:text-5xl font-black bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-3 group-hover:scale-105 transition-transform duration-300">
                {stat.value}
              </div>
              <div className="text-sm font-bold text-muted uppercase tracking-widest">
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 flex items-center gap-6 text-sm text-muted flex-wrap justify-center">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-green-600 dark:text-green-400" />
            <span>Enterprise Security</span>
          </div>
          <div className="w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span>Real-time Analytics</span>
          </div>
          <div className="w-px h-4 bg-border" />
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-purple-600 dark:text-purple-400" />
            <span>AI-Powered</span>
          </div>
        </div>
      </div>
    </section>
  );
}

const stats = [
  { value: '99.9%', label: 'Uptime Reliability', icon: TrendingUp },
  { value: '< 50ms', label: 'Response Time', icon: Zap },
  { value: '24/7', label: 'System Monitoring', icon: Activity },
];
