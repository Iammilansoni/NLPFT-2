"use client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowRight, Sparkles, CheckCircle2, Code2 } from "lucide-react";
import Link from "next/link";

export function AIShowcase() {
  return (
    <section className="py-28 theme-transition relative">
      <div className="mx-auto max-w-7xl">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 rounded-full border-2 border-purple-300/60 dark:border-purple-500/40 bg-gradient-to-r from-white/95 to-purple-50/95 dark:from-slate-800/95 dark:to-purple-900/95 px-7 py-3 text-sm font-bold tracking-wide backdrop-blur-xl shadow-2xl mb-8 hover:scale-105 transition-transform duration-300">
            <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400 animate-pulse" />
            <span className="bg-gradient-to-r from-purple-700 to-pink-700 dark:from-purple-300 dark:to-pink-300 bg-clip-text text-transparent">See It In Action</span>
          </div>
          
          <h2 className="text-5xl md:text-6xl font-black tracking-tight mb-8">
            <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 dark:from-purple-400 dark:via-pink-400 dark:to-indigo-400 bg-clip-text text-transparent drop-shadow-2xl">
              AI-Powered Conversion
            </span>
          </h2>
          
          <p className="text-2xl text-muted max-w-4xl mx-auto leading-relaxed font-medium">
            Watch how our intelligent NLP engine transforms natural language into structured test automation steps in real-time.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-16 items-start mb-20">
          <div className="space-y-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-black text-2xl shadow-2xl shadow-blue-500/40">
                1
              </div>
              <h3 className="text-3xl font-black">Natural Language Input</h3>
            </div>
            
            <Card className="p-10 glass-medium border-3 border-blue-300/60 dark:border-blue-500/40 shadow-2xl shadow-blue-500/20 hover:shadow-blue-500/30 transition-all duration-300 rounded-3xl backdrop-blur-xl hover:border-blue-400/80 dark:hover:border-blue-400/60 group">
              <div className="flex items-start gap-4 mb-6">
                <Code2 className="h-7 w-7 text-blue-600 dark:text-blue-400 mt-1 group-hover:scale-110 transition-transform" />
                <div className="flex-1">
                  <p className="text-sm font-bold text-muted uppercase tracking-widest mb-4">User Input</p>
                  <div className="bg-gradient-to-br from-slate-50 to-blue-50/30 dark:from-slate-900/80 dark:to-blue-900/20 p-7 rounded-2xl border-2 border-slate-200 dark:border-slate-700">
                    <p className="text-lg leading-loose font-medium">
                      &ldquo;When the user clicks the login button, verify that the authentication system validates the credentials and redirects to the dashboard page&rdquo;
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            <div className="flex items-center gap-6 px-6">
              <div className="flex-1 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent rounded-full" />
              <Sparkles className="h-8 w-8 text-blue-600 dark:text-blue-400 animate-pulse" />
              <div className="flex-1 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent rounded-full" />
            </div>
          </div>

          <div className="space-y-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 text-white font-black text-2xl shadow-2xl shadow-green-500/40">
                2
              </div>
              <h3 className="text-3xl font-black">Structured Test Output</h3>
            </div>
            
            <Card className="p-10 glass-medium border-3 border-green-300/60 dark:border-green-500/40 shadow-2xl shadow-green-500/20 hover:shadow-green-500/30 transition-all duration-300 rounded-3xl backdrop-blur-xl hover:border-green-400/80 dark:hover:border-green-400/60 group">
              <div className="flex items-start gap-4 mb-6">
                <CheckCircle2 className="h-7 w-7 text-green-600 dark:text-green-400 mt-1 group-hover:scale-110 transition-transform" />
                <div className="flex-1">
                  <p className="text-sm font-bold text-muted uppercase tracking-widest mb-4">Automated Output</p>
                  <div className="bg-gradient-to-br from-slate-50 to-green-50/30 dark:from-slate-900/80 dark:to-green-900/20 p-7 rounded-2xl border-2 border-slate-200 dark:border-slate-700 space-y-5">
                    {outputSteps.map((step, index) => (
                      <div key={index} className="flex items-start gap-4 group/step">
                        <div className="flex items-center justify-center w-8 h-8 rounded-xl bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/40 dark:to-emerald-900/40 text-green-700 dark:text-green-400 text-sm font-black flex-shrink-0 shadow-lg group-hover/step:scale-110 transition-transform">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-base font-mono font-bold text-green-800 dark:text-green-300 group-hover/step:text-green-600 dark:group-hover/step:text-green-200 transition-colors">
                            {step.action}
                          </p>
                          <p className="text-sm text-muted mt-2 font-medium">{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-20">
          {stats.map((stat, index) => (
            <div 
              key={stat.label}
              className="text-center p-10 rounded-3xl glass-medium border-2 border-purple-200/50 dark:border-purple-500/30 hover:scale-110 hover:shadow-2xl hover:shadow-purple-500/30 transition-all duration-300 backdrop-blur-xl group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="text-5xl font-black bg-gradient-to-r from-purple-600 to-pink-600 dark:from-purple-400 dark:to-pink-400 bg-clip-text text-transparent mb-4 group-hover:scale-110 transition-transform drop-shadow-2xl">
                {stat.value}
              </div>
              <div className="text-base font-bold text-muted uppercase tracking-widest">
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        <div className="text-center">
          <Button 
            asChild 
            size="lg" 
            className="btn-primary px-14 py-8 text-xl font-black interactive focus-ring group shadow-2xl shadow-purple-500/40 hover:shadow-purple-500/60 rounded-2xl"
          >
            <Link href="/convert" className="inline-flex items-center gap-4">
              <Sparkles className="h-7 w-7 icon-decorative group-hover:rotate-12 group-hover:scale-125 transition-transform" />
              Try the AI Converter Now
              <ArrowRight className="h-6 w-6 icon-decorative group-hover:translate-x-2 transition-transform" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

const outputSteps = [
  {
    action: 'CLICK(element: "login-button")',
    description: 'Click the login button element'
  },
  {
    action: 'VERIFY(service: "auth", action: "validate_credentials")',
    description: 'Verify authentication system validates credentials'
  },
  {
    action: 'WAIT(condition: "navigation_complete")',
    description: 'Wait for page navigation to complete'
  },
  {
    action: 'ASSERT(location: "/dashboard")',
    description: 'Assert that current page is dashboard'
  }
];

const stats = [
  { value: '95%+', label: 'Accuracy Rate' },
  { value: '10x', label: 'Faster Testing' },
  { value: '50ms', label: 'Avg Response' },
  { value: '1000+', label: 'Patterns Learned' }
];
