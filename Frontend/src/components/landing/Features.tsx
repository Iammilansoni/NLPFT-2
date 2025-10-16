"use client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, Zap, BookText, Shield, Database, Monitor, ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export function Features() {
  return (
    <section className="py-28 theme-transition relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div 
          className="absolute top-1/4 left-0 w-full h-2 opacity-30"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, #3b82f6 20%, #10b981 40%, #8b5cf6 60%, #ec4899 80%, transparent 100%)',
            boxShadow: '0 0 40px #3b82f6, 0 0 80px #10b981',
            animation: 'shimmer 8s linear infinite',
            filter: 'blur(20px)'
          }}
        />
        
        <div 
          className="absolute top-2/3 left-0 w-full h-2 opacity-25"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, #ec4899 15%, #f59e0b 35%, #06b6d4 55%, #8b5cf6 75%, transparent 100%)',
            boxShadow: '0 0 40px #ec4899, 0 0 80px #06b6d4',
            animation: 'shimmer 10s linear infinite reverse',
            filter: 'blur(20px)'
          }}
        />
        
        <div 
          className="absolute top-0 left-1/4 w-2 h-full opacity-20"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, #10b981 30%, #3b82f6 50%, #8b5cf6 70%, transparent 100%)',
            boxShadow: '0 0 40px #10b981, 0 0 60px #3b82f6',
            animation: 'shimmer 12s linear infinite',
            filter: 'blur(25px)'
          }}
        />
        
        <div 
          className="absolute top-0 right-1/3 w-2 h-full opacity-20"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, #f59e0b 25%, #ec4899 50%, #06b6d4 75%, transparent 100%)',
            boxShadow: '0 0 40px #f59e0b, 0 0 60px #ec4899',
            animation: 'shimmer 15s linear infinite reverse',
            filter: 'blur(25px)'
          }}
        />
        
        <div 
          className="absolute top-0 left-0 w-full h-full opacity-15"
          style={{
            background: 'radial-gradient(ellipse at 20% 30%, #3b82f620 0%, transparent 50%)',
            animation: 'pulse 4s ease-in-out infinite'
          }}
        />
        
        <div 
          className="absolute top-0 left-0 w-full h-full opacity-15"
          style={{
            background: 'radial-gradient(ellipse at 80% 60%, #ec489920 0%, transparent 50%)',
            animation: 'pulse 5s ease-in-out infinite 1s'
          }}
        />
        
        <div 
          className="absolute top-0 left-0 w-full h-full opacity-15"
          style={{
            background: 'radial-gradient(ellipse at 50% 80%, #10b98120 0%, transparent 50%)',
            animation: 'pulse 6s ease-in-out infinite 2s'
          }}
        />
      </div>
      
      <div className="mx-auto max-w-6xl text-center mb-20">
        <div className="inline-flex items-center gap-2 rounded-full border-2 border-blue-300/60 dark:border-blue-500/40 bg-gradient-to-r from-white/95 to-blue-50/95 dark:from-slate-800/95 dark:to-blue-900/95 px-7 py-3 text-sm font-bold tracking-wide backdrop-blur-xl shadow-2xl mb-8 hover:scale-105 transition-transform duration-300">
          <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400 animate-pulse" />
          <span className="bg-gradient-to-r from-blue-700 to-indigo-700 dark:from-blue-300 dark:to-indigo-300 bg-clip-text text-transparent">Enterprise Features</span>
        </div>
        
        <h2 className="text-5xl md:text-6xl font-black tracking-tight mb-8">
          <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-400 dark:via-indigo-400 dark:to-purple-400 bg-clip-text text-transparent drop-shadow-2xl">
            Powerful Features for
          </span>
          <br />
          <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 dark:from-purple-400 dark:via-pink-400 dark:to-rose-400 bg-clip-text text-transparent drop-shadow-2xl">
            Modern Teams
          </span>
        </h2>
        
        <p className="text-2xl text-muted max-w-4xl mx-auto leading-relaxed font-medium">
          Everything you need to streamline test automation, monitor system health,
          and manage domain knowledge in one integrated platform.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, index) => (
          <Card
            key={feature.title}
            className="relative overflow-hidden border-3 border-transparent bg-[color:var(--card)] shadow-2xl transition-all duration-500 group transform-3d perspective-1000 glass-medium backdrop-blur-xl rounded-3xl hover:scale-105 p-2"
            style={{
              animationDelay: `${index * 100}ms`,
              animation: 'slideUp 0.6s ease-out forwards'
            }}
            aria-labelledby={`feature-${feature.title}`}
          >
            <div 
              aria-hidden="true" 
              className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700" 
            >
              <div 
                className="absolute -top-32 -right-32 h-96 w-96 rounded-full blur-3xl transition-all duration-700 group-hover:scale-150"
                style={{
                  background: `radial-gradient(circle, ${feature.color}40 0%, ${feature.color}20 40%, transparent 70%)`,
                  animation: 'pulse 3s ease-in-out infinite'
                }}
              />
              
              <div 
                className="absolute -bottom-32 -left-32 h-80 w-80 rounded-full blur-3xl transition-all duration-700 group-hover:scale-125"
                style={{
                  background: `radial-gradient(circle, ${feature.color}30 0%, ${feature.color}15 50%, transparent 70%)`,
                  animation: 'pulse 3s ease-in-out infinite 1s'
                }}
              />
              
              <div 
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-64 w-64 rounded-full blur-2xl transition-all duration-700 group-hover:scale-110"
                style={{
                  background: `radial-gradient(circle, ${feature.color}25 0%, transparent 60%)`,
                  animation: 'pulse 2s ease-in-out infinite 0.5s'
                }}
              />
            </div>

            <div 
              aria-hidden="true"
              className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
              style={{
                boxShadow: `0 0 60px ${feature.color}40, inset 0 0 40px ${feature.color}10`
              }}
            />

            <CardHeader className="relative pb-6">
              <div className="flex items-start justify-between mb-6">
                <div 
                  className="rounded-2xl p-5 shadow-2xl group-hover:scale-125 group-hover:rotate-6 transition-all duration-300"
                  style={{
                    background: `linear-gradient(135deg, ${feature.color}20, ${feature.color}35)`
                  }}
                >
                  <feature.icon 
                    className="h-9 w-9 icon-decorative" 
                    style={{ color: feature.color }}
                    aria-hidden="true" 
                  />
                </div>
                
                {feature.badge && (
                  <span className="text-sm font-black px-4 py-2 rounded-full bg-gradient-to-r from-blue-500/30 to-indigo-500/30 text-blue-700 dark:text-blue-300 border-2 border-blue-500/40 shadow-lg">
                    {feature.badge}
                  </span>
                )}
              </div>

              <CardTitle id={`feature-${feature.title}`} className="text-3xl font-black mb-3 transition-colors duration-300"
                style={{
                  color: 'var(--foreground)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = feature.color;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--foreground)';
                }}
              >
                {feature.title}
              </CardTitle>
            </CardHeader>

            <CardContent className="relative">
              <CardDescription className="text-lg text-muted mb-8 leading-relaxed font-medium">
                {feature.description}
              </CardDescription>

              <div className="space-y-4 mb-8">
                {feature.highlights.map((highlight) => (
                  <div key={highlight} className="flex items-start gap-4 text-base group/item">
                    <CheckCircle2 
                      className="h-6 w-6 mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400 group-hover/item:scale-125 transition-transform" 
                      aria-hidden="true" 
                    />
                    <span className="text-muted group-hover/item:text-foreground transition-colors font-medium">
                      {highlight}
                    </span>
                  </div>
                ))}
              </div>

              <Button 
                asChild 
                variant="outline" 
                className="w-full group/btn border-3 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 interactive focus-ring py-6 text-base font-bold rounded-xl hover:shadow-xl hover:shadow-blue-500/20"
              >
                <Link href={feature.link} aria-label={`Explore ${feature.title}`} className="inline-flex items-center justify-center gap-3">
                  <span className="font-bold">Explore Feature</span>
                  <ArrowRight className="h-5 w-5 group-hover/btn:translate-x-2 transition-transform" aria-hidden="true" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}


const features = [
  {
    title: 'AI Rule Engine',
    description: 'Convert natural language descriptions into structured test steps with advanced pattern matching and success metrics.',
    icon: Zap,
    color: '#3b82f6', 
    badge: 'AI-Powered',
    highlights: ['Smart pattern recognition', 'Real-time parsing metrics', 'Customizable rule templates'],
    link: '/convert'
  },
  {
    title: 'System Health Monitoring',
    description: 'Comprehensive real-time monitoring of application health, database performance, and system resources.',
    icon: Activity,
    color: '#10b981', 
    badge: 'Live',
    highlights: ['Live performance metrics', 'Automated health checks', 'Alert notifications'],
    link: '/health'
  },
  {
    title: 'Dictionary Management',
    description: 'Centralized domain terminology management with intelligent categorization and search capabilities.',
    icon: BookText,
    color: '#8b5cf6', 
    badge: null,
    highlights: ['Intelligent categorization', 'Advanced search & filtering', 'Version control support'],
    link: '/dictionary'
  },
  {
    title: 'Dashboard Analytics',
    description: 'Unified dashboard providing insights into system performance, rule engine efficiency, and operational metrics.',
    icon: Monitor,
    color: '#06b6d4', 
    badge: 'Analytics',
    highlights: ['Real-time analytics', 'Performance insights', 'Historical data trends'],
    link: '/dashboard'
  },
  {
    title: 'Enterprise Security',
    description: 'Built with security-first principles including authentication, authorization, and comprehensive audit trails.',
    icon: Shield,
    color: '#f59e0b', 
    badge: 'Secure',
    highlights: ['Role-based access control', 'Audit logging', 'Data encryption'],
    link: '/dashboard'
  },
  {
    title: 'Database Integration',
    description: 'Seamless integration with enterprise databases and data sources for comprehensive data management.',
    icon: Database,
    color: '#ec4899', 
    badge: null,
    highlights: ['Multiple database support', 'Connection pooling', 'Query optimization'],
    link: '/dashboard'
  }
];
