"use client";
import { Card } from "@/components/ui/card";
import { Star, Quote, TrendingUp, Users, Award, Target } from "lucide-react";

export function SocialProof() {
  return (
    <section className="py-28 theme-transition relative">
      <div className="mx-auto max-w-7xl">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 rounded-full border-2 border-amber-300/60 dark:border-amber-500/40 bg-gradient-to-r from-white/95 to-amber-50/95 dark:from-slate-800/95 dark:to-amber-900/95 px-7 py-3 text-sm font-bold tracking-wide backdrop-blur-xl shadow-2xl mb-8 hover:scale-105 transition-transform duration-300">
            <Award className="h-5 w-5 text-amber-600 dark:text-amber-400 animate-pulse" />
            <span className="bg-gradient-to-r from-amber-700 to-orange-700 dark:from-amber-300 dark:to-orange-300 bg-clip-text text-transparent">Trusted Worldwide</span>
          </div>
          
          <h2 className="text-5xl md:text-6xl font-black tracking-tight mb-8">
            <span className="bg-gradient-to-r from-amber-600 via-orange-600 to-red-600 dark:from-amber-400 dark:via-orange-400 dark:to-red-400 bg-clip-text text-transparent drop-shadow-2xl">
              Loved by Developers
            </span>
          </h2>
          
          <p className="text-2xl text-muted max-w-4xl mx-auto leading-relaxed font-medium">
            Join thousands of development teams who have transformed their testing workflows with NLPForge.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
          {stats.map((stat, index) => (
            <div 
              key={stat.label}
              className="p-10 rounded-3xl glass-medium border-2 border-amber-200/50 dark:border-amber-500/30 hover:scale-110 hover:shadow-2xl hover:shadow-amber-500/30 transition-all duration-300 text-center backdrop-blur-xl group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div 
                className="inline-flex items-center justify-center w-20 h-20 rounded-2xl mb-6 shadow-2xl group-hover:scale-125 group-hover:rotate-6 transition-all duration-300"
                style={{
                  background: `linear-gradient(135deg, ${stat.color}30, ${stat.color}50)`
                }}
              >
                <stat.icon 
                  className="h-10 w-10" 
                  style={{ color: stat.color }}
                />
              </div>
              <div className="text-5xl font-black mb-4 bg-gradient-to-r bg-clip-text text-transparent drop-shadow-2xl group-hover:scale-110 transition-transform"
                style={{
                  backgroundImage: `linear-gradient(135deg, ${stat.color}, ${stat.color}DD)`
                }}
              >
                {stat.value}
              </div>
              <div className="text-base font-bold text-muted uppercase tracking-widest">
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {testimonials.map((testimonial, index) => (
            <Card 
              key={testimonial.name}
              className="p-10 glass-medium border-3 border-transparent shadow-2xl transition-all duration-500 group relative rounded-3xl backdrop-blur-xl hover:scale-105 overflow-hidden"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <div 
                aria-hidden="true" 
                className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700" 
              >
                <div 
                  className="absolute -top-32 -right-32 h-96 w-96 rounded-full blur-3xl transition-all duration-700 group-hover:scale-150"
                  style={{
                    background: `radial-gradient(circle, ${testimonial.color}40 0%, ${testimonial.color}20 40%, transparent 70%)`,
                    animation: 'pulse 3s ease-in-out infinite'
                  }}
                />
                
                <div 
                  className="absolute -bottom-32 -left-32 h-80 w-80 rounded-full blur-3xl transition-all duration-700 group-hover:scale-125"
                  style={{
                    background: `radial-gradient(circle, ${testimonial.color}30 0%, ${testimonial.color}15 50%, transparent 70%)`,
                    animation: 'pulse 3s ease-in-out infinite 1s'
                  }}
                />
                
                <div 
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-64 w-64 rounded-full blur-2xl transition-all duration-700 group-hover:scale-110"
                  style={{
                    background: `radial-gradient(circle, ${testimonial.color}25 0%, transparent 60%)`,
                    animation: 'pulse 2s ease-in-out infinite 0.5s'
                  }}
                />
              </div>

              <div 
                aria-hidden="true"
                className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                style={{
                  boxShadow: `0 0 60px ${testimonial.color}40, inset 0 0 40px ${testimonial.color}10`
                }}
              />

              <div className="absolute top-6 right-6 opacity-10 group-hover:opacity-25 transition-opacity duration-500 z-10">
                <Quote className="h-20 w-20 transition-colors duration-500"
                  style={{
                    color: testimonial.color
                  }}
                />
              </div>

              <div className="flex gap-2 mb-6 relative z-10">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star 
                    key={star} 
                    className="h-7 w-7 fill-amber-500 group-hover:scale-125 transition-all duration-300" 
                    style={{
                      color: testimonial.color
                    }}
                  />
                ))}
              </div>

              <p className="text-lg text-muted leading-relaxed mb-8 relative z-10 font-medium">
                &ldquo;{testimonial.quote}&rdquo;
              </p>

              <div className="flex items-center gap-5 pt-6 border-t-2 border-border relative z-10">
                <div 
                  className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-black text-xl shadow-2xl group-hover:scale-125 transition-transform"
                  style={{
                    background: `linear-gradient(135deg, ${testimonial.color}, ${testimonial.color}DD)`
                  }}
                >
                  {testimonial.initials}
                </div>
                <div>
                  <p className="font-black text-foreground text-lg">{testimonial.name}</p>
                  <p className="text-base text-muted font-medium">{testimonial.role}</p>
                  <p className="text-sm text-muted font-medium">{testimonial.company}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="mt-20 p-12 rounded-3xl glass-medium border-3 border-amber-400/60 dark:border-amber-500/50 text-center shadow-2xl shadow-amber-500/20 backdrop-blur-xl">
          <div className="flex flex-col md:flex-row items-center justify-center gap-12">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-2xl hover:scale-125 hover:rotate-6 transition-all duration-300">
                <Target className="h-10 w-10 text-white" />
              </div>
              <div className="text-left">
                <p className="text-5xl font-black text-foreground mb-2">98.5%</p>
                <p className="text-base text-muted font-bold">Customer Satisfaction</p>
              </div>
            </div>
            
            <div className="w-0.5 h-16 bg-border hidden md:block" />
            
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-2xl hover:scale-125 hover:rotate-6 transition-all duration-300">
                <TrendingUp className="h-10 w-10 text-white" />
              </div>
              <div className="text-left">
                <p className="text-5xl font-black text-foreground mb-2">10M+</p>
                <p className="text-base text-muted font-bold">Tests Executed</p>
              </div>
            </div>
            
            <div className="w-0.5 h-16 bg-border hidden md:block" />
            
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-2xl hover:scale-125 hover:rotate-6 transition-all duration-300">
                <Users className="h-10 w-10 text-white" />
              </div>
              <div className="text-left">
                <p className="text-5xl font-black text-foreground mb-2">500+</p>
                <p className="text-base text-muted font-bold">Enterprise Clients</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const stats = [
  { value: '10K+', label: 'Active Users', icon: Users, color: '#3b82f6' },
  { value: '99.9%', label: 'Uptime SLA', icon: TrendingUp, color: '#10b981' },
  { value: '4.9/5', label: 'User Rating', icon: Star, color: '#f59e0b' },
  { value: '24/7', label: 'Support', icon: Award, color: '#8b5cf6' }
];

const testimonials = [
  {
    quote: 'NLPForge has revolutionized our testing workflow. What used to take hours now takes minutes. The AI is incredibly accurate and saves our team countless hours every week.',
    name: 'Sarah Chen',
    role: 'QA Lead',
    company: 'TechCorp Inc.',
    initials: 'SC',
    color: '#3b82f6'
  },
  {
    quote: 'The natural language processing is mind-blowing. Our non-technical team members can now write test cases without learning complex syntax. Game changer for our organization.',
    name: 'Michael Rodriguez',
    role: 'Engineering Manager',
    company: 'CloudScale Solutions',
    initials: 'MR',
    color: '#10b981'
  },
  {
    quote: 'We integrated NLPForge into our CI/CD pipeline seamlessly. The monitoring dashboard gives us real-time insights we never had before. Highly recommended!',
    name: 'Emily Watson',
    role: 'DevOps Engineer',
    company: 'DataFlow Systems',
    initials: 'EW',
    color: '#8b5cf6'
  }
];
