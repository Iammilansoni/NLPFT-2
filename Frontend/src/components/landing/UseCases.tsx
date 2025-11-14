"use client";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShoppingCart, Plane, Heart, Building2, ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export function UseCases() {
  return (
    <section className="py-28 theme-transition bg-gradient-to-b from-transparent via-purple-50/30 to-transparent dark:via-slate-900/30 relative">
      <div className="mx-auto max-w-7xl">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 rounded-full border-2 border-purple-300/60 dark:border-purple-500/40 bg-gradient-to-r from-white/95 to-purple-50/95 dark:from-slate-800/95 dark:to-purple-900/95 px-7 py-3 text-sm font-bold tracking-wide backdrop-blur-xl shadow-2xl mb-8 hover:scale-105 transition-transform duration-300">
            <Building2 className="h-5 w-5 text-purple-600 dark:text-purple-400 animate-pulse" />
            <span className="bg-gradient-to-r from-purple-700 to-pink-700 dark:from-purple-300 dark:to-pink-300 bg-clip-text text-transparent">Industry Solutions</span>
          </div>
          
          <h2 className="text-5xl md:text-6xl font-black tracking-tight mb-8">
            <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 dark:from-purple-400 dark:via-pink-400 dark:to-rose-400 bg-clip-text text-transparent drop-shadow-2xl">
              Built for Every Industry
            </span>
          </h2>
          
          <p className="text-2xl text-muted max-w-4xl mx-auto leading-relaxed font-medium">
            From e-commerce to healthcare, teams across industries trust NLPForge to streamline their testing workflows.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-20">
          {useCases.map((useCase, index) => (
            <Card 
              key={useCase.title}
              className="overflow-hidden glass-medium border-3 hover:border-purple-400/70 dark:hover:border-purple-500/60 shadow-2xl hover:shadow-purple-500/30 transition-all duration-300 group rounded-3xl backdrop-blur-xl hover:scale-105"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div 
                className="p-8 relative overflow-hidden"
                style={{
                  background: `linear-gradient(135deg, ${useCase.color}20, ${useCase.color}35)`
                }}
              >
                <div className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-30 -mr-20 -mt-20 blur-2xl"
                  style={{ backgroundColor: useCase.color }}
                />
                
                <div className="relative flex items-start gap-5">
                  <div 
                    className="flex-shrink-0 w-20 h-20 rounded-2xl flex items-center justify-center shadow-2xl group-hover:scale-125 group-hover:rotate-6 transition-all duration-300"
                    style={{
                      background: `linear-gradient(135deg, ${useCase.color}CC, ${useCase.color})`
                    }}
                  >
                    <useCase.icon className="h-10 w-10 text-white" />
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="text-3xl font-black mb-3 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                      {useCase.title}
                    </h3>
                    <p className="text-sm font-bold text-muted uppercase tracking-widest">
                      {useCase.industry}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-8">
                <p className="text-lg text-muted leading-relaxed mb-8 font-medium">
                  {useCase.description}
                </p>

                <div className="space-y-4 mb-8">
                  <p className="text-base font-black text-foreground uppercase tracking-widest mb-4">
                    Key Benefits
                  </p>
                  {useCase.benefits.map((benefit) => (
                    <div key={benefit} className="flex items-start gap-4 group/item">
                      <CheckCircle2 className="h-7 w-7 flex-shrink-0 mt-0.5 group-hover/item:scale-125 transition-transform shadow-lg"
                        style={{ color: useCase.color }}
                      />
                      <span className="text-base text-muted group-hover/item:text-foreground transition-colors font-medium">
                        {benefit}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-50 to-purple-50/30 dark:from-slate-900/80 dark:to-purple-900/20 border-2 border-slate-200 dark:border-slate-700 mb-8 hover:shadow-lg transition-shadow">
                  <p className="text-sm font-black text-muted uppercase tracking-widest mb-3">
                    Example Test Case
                  </p>
                  <p className="text-base font-mono text-foreground font-medium leading-relaxed">
                    {useCase.example}
                  </p>
                </div>

                <Button 
                  asChild 
                  variant="outline" 
                  className="w-full group/btn border-3 hover:bg-purple-50 dark:hover:bg-purple-950/30 interactive focus-ring py-6 text-base font-bold rounded-xl hover:shadow-xl transition-all"
                  style={{ 
                    borderColor: `${useCase.color}60`,
                    '--tw-border-opacity': 0.6 
                  } as React.CSSProperties}
                >
                  <Link href="/convert" className="inline-flex items-center justify-center gap-3">
                    <span className="font-black">Try This Use Case</span>
                    <ArrowRight className="h-5 w-5 group-hover/btn:translate-x-2 transition-transform" />
                  </Link>
                </Button>
              </div>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <p className="text-xl text-muted mb-8 font-medium">
            Don&apos;t see your industry? <span className="font-black text-foreground text-2xl">NLPForge adapts to any testing scenario.</span>
          </p>
          <Button 
            asChild 
            size="lg" 
            className="btn-primary px-14 py-8 text-xl font-black interactive focus-ring group shadow-2xl shadow-purple-500/40 hover:shadow-purple-500/60 rounded-2xl"
          >
            <Link href="/convert" className="inline-flex items-center gap-4">
              Explore All Use Cases
              <ArrowRight className="h-6 w-6 icon-decorative group-hover:translate-x-2 transition-transform" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

const useCases = [
  {
    title: 'E-Commerce Testing',
    industry: 'Retail & Commerce',
    icon: ShoppingCart,
    color: '#3b82f6', 
    description: 'Automate complex shopping flows, payment processing, and inventory management tests with natural language descriptions.',
    benefits: [
      'Test checkout flows end-to-end',
      'Validate payment gateway integrations',
      'Verify cart and inventory updates',
      'Monitor user authentication flows'
    ],
    example: 'Add product to cart, apply discount code, verify total calculation, and complete checkout'
  },
  {
    title: 'Travel & Booking',
    industry: 'Travel & Hospitality',
    icon: Plane,
    color: '#10b981', 
    description: 'Streamline testing for booking systems, itinerary management, and customer reservation workflows.',
    benefits: [
      'Automate multi-step booking flows',
      'Test date range validations',
      'Verify pricing calculations',
      'Validate confirmation emails'
    ],
    example: 'Search for flights from NYC to LAX, select departure and return dates, add passenger details, and confirm booking'
  },
  {
    title: 'Healthcare Systems',
    industry: 'Healthcare & Medical',
    icon: Heart,
    color: '#ef4444', 
    description: 'Ensure patient data integrity, appointment scheduling, and compliance with healthcare regulations.',
    benefits: [
      'Test HIPAA compliance workflows',
      'Validate patient record updates',
      'Verify appointment scheduling',
      'Monitor access control systems'
    ],
    example: 'Create new patient record, schedule appointment, update medical history, and generate prescription'
  },
  {
    title: 'Enterprise SaaS',
    industry: 'B2B Software & SaaS',
    icon: Building2,
    color: '#8b5cf6', 
    description: 'Test complex enterprise features, multi-tenant systems, and role-based access controls efficiently.',
    benefits: [
      'Validate user permission systems',
      'Test multi-tenant isolation',
      'Verify API integrations',
      'Monitor performance metrics'
    ],
    example: 'Create organization, add team members with different roles, configure permissions, and verify access controls'
  }
];
