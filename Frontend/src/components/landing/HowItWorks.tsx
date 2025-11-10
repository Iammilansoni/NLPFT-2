'use client'

import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Brain, Database, Search, PlayCircle, ArrowRight } from 'lucide-react'
import Link from 'next/link'

const steps = [
  {
    icon: Brain,
    title: 'Understand Query',
    description: 'NER and QA models extract intent, entities, and context from natural language',
    badge: 'NLP',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Database,
    title: 'Generate Dataset',
    description: 'Gemini AI creates smart test data with rules-based validation and enrichment',
    badge: 'AI',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: Search,
    title: 'Embed & Search',
    description: 'Redis vector store with cosine similarity finds the best matching templates',
    badge: 'Vector DB',
    color: 'from-green-500 to-emerald-500',
  },
  {
    icon: PlayCircle,
    title: 'Run & Report',
    description: 'Execute tests, capture results, and provide detailed pass/fail analysis with latency metrics',
    badge: 'Testing',
    color: 'from-orange-500 to-red-500',
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-20 md:py-32 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-muted/20 to-background -z-10" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(124,58,237,0.05),transparent_50%)] -z-10" />
      
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 space-y-4"
        >
          <Badge variant="outline" className="px-4 py-1.5">
            How It Works
          </Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold font-heading">
            From Query to{' '}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Validated Test
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Four intelligent steps transform your natural language into production-ready API tests
          </p>
        </motion.div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4 relative">
          {/* Connection lines for desktop */}
          <div className="hidden lg:block absolute top-1/4 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-border to-transparent -z-10" />

          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: index * 0.15, ease: [0.22, 1, 0.36, 1] }}
            >
              <Card className="h-full border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-glow group relative overflow-hidden card-gradient">
                {/* Hover spotlight effect */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <div className={`absolute inset-0 bg-gradient-to-br ${step.color} opacity-5`} />
                </div>
                
                <CardContent className="p-6 space-y-5 relative z-10">
                  {/* Enhanced Icon */}
                  <div className="relative">
                    <motion.div 
                      className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center text-white shadow-glow`}
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      transition={{ type: "spring", stiffness: 400 }}
                    >
                      <step.icon className="h-8 w-8" />
                    </motion.div>
                    <div className="absolute -top-3 -right-3">
                      <Badge className="text-xs font-bold bg-gradient-to-br from-primary to-accent text-white border-0 shadow-lg h-8 w-8 rounded-full flex items-center justify-center p-0">
                        {index + 1}
                      </Badge>
                    </div>
                    {/* Connecting line for desktop */}
                    {index < steps.length - 1 && (
                      <div className="hidden lg:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-border via-primary/30 to-transparent" />
                    )}
                  </div>

                  {/* Enhanced Content */}
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-xl font-bold font-heading group-hover:text-primary transition-colors">
                        {step.title}
                      </h3>
                      <Badge variant="outline" className="text-xs shrink-0 bg-primary/5 border-primary/30">
                        {step.badge}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {step.description}
                    </p>
                  </div>

                  {/* Progress indicator */}
                  <div className="pt-2">
                    <div className="h-1 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: "100%" }}
                        viewport={{ once: true }}
                        transition={{ duration: 1, delay: index * 0.15 + 0.5 }}
                        className={`h-full bg-gradient-to-r ${step.color} rounded-full`}
                      />
                    </div>
                  </div>

                  {/* Arrow indicator for mobile */}
                  {index < steps.length - 1 && (
                    <div className="lg:hidden flex justify-center pt-2">
                      <ArrowRight className="h-5 w-5 text-primary animate-pulse" />
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="text-center mt-12"
        >
          <Link
            href="/docs"
            className="inline-flex items-center text-sm font-medium text-primary hover:underline"
          >
            Learn more about our architecture
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
