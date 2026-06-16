'use client'

import { motion } from 'framer-motion'
import { FileCode, Sparkles, SearchCode, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

const STEPS = [
  {
    number: '01',
    icon: FileCode,
    title: 'Define Your API Template',
    description:
      'Describe your API endpoint in plain English. Define its method, base URL, parameters, and expected behavior. NLPForge turns your description into a structured, versioned template.',
    code: `POST /auth/login
intent: "Authenticate user"
params: email, password
description: "Validates credentials
and returns JWT token"`,
    border: 'border-border/60 hover:border-blue-500/40',
    iconColor: 'text-blue-500',
    iconBg: 'bg-blue-500/10',
    numColor: 'text-blue-500/30 dark:text-blue-400/20',
  },
  {
    number: '02',
    icon: Sparkles,
    title: 'Generate Thousands of Test Cases',
    description:
      'Pick any LLM provider (Gemini, GPT-4, Claude, Ollama). NLPForge generates hundreds of semantically diverse, realistic test cases covering happy paths, edge cases, and error scenarios.',
    code: `LLM: Gemini 2.5 Flash
Rows: 500
Distribution:
  70% valid inputs
  20% edge cases
  10% extreme values`,
    border: 'border-border/60 hover:border-violet-500/40',
    iconColor: 'text-violet-500',
    iconBg: 'bg-violet-500/10',
    numColor: 'text-violet-500/30 dark:text-violet-400/20',
  },
  {
    number: '03',
    icon: SearchCode,
    title: 'Search with Natural Language',
    description:
      'Ask in plain English. NLPForge uses Redis vector search + neural re-ranking to return the most semantically relevant API test case in under 50ms — with a confidence score.',
    code: `Query: "login with wrong password"
→ Stage 1: Vector search (8ms)
→ Stage 2: Re-ranking (12ms)
→ confidence: 0.96
→ POST /auth/login`,
    border: 'border-border/60 hover:border-emerald-500/40',
    iconColor: 'text-emerald-500',
    iconBg: 'bg-emerald-500/10',
    numColor: 'text-emerald-500/30 dark:text-emerald-400/20',
  },
]

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
}

const cardVariants = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
}

export function HowItWorks() {
  return (
    <section className="relative py-12 md:py-16 border-t overflow-hidden">
      {/* Subtle background */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-background via-muted/20 to-background" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16 space-y-4 max-w-2xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            How It Works
          </div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            From description to results{' '}
            <span className="text-primary">in three steps</span>
          </h2>
          <p className="text-muted-foreground text-lg leading-relaxed">
            No complex setup. No manual test writing. Just describe, generate, and search.
          </p>
        </motion.div>

        {/* Steps */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-60px' }}
          className="grid gap-8 lg:grid-cols-3"
        >
          {STEPS.map((step, idx) => (
            <motion.div
              key={step.number}
              variants={cardVariants}
              className={`relative rounded-2xl border bg-card p-7 transition-all duration-300 ${step.border}`}
            >
              {/* Step number (large, faded) */}
              <span className={`absolute top-5 right-6 text-6xl font-black select-none ${step.numColor}`}>
                {step.number}
              </span>

              {/* Icon */}
              <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-5 ${step.iconBg}`}>
                <step.icon className={`h-6 w-6 ${step.iconColor}`} />
              </div>

              {/* Title */}
              <h3 className="text-lg font-semibold mb-3 pr-12 text-foreground">{step.title}</h3>

              {/* Description */}
              <p className="text-sm text-muted-foreground leading-relaxed mb-5">
                {step.description}
              </p>

              {/* Code snippet */}
              <div className="rounded-lg bg-muted/50 dark:bg-muted/30 border border-border/60 p-4">
                <div className="flex items-center gap-1.5 mb-3">
                  <div className="w-2 h-2 rounded-full bg-red-400/60" />
                  <div className="w-2 h-2 rounded-full bg-yellow-400/60" />
                  <div className="w-2 h-2 rounded-full bg-green-400/60" />
                </div>
                <pre className="text-[11px] font-mono text-foreground/80 whitespace-pre-wrap leading-relaxed overflow-hidden">
                  {step.code}
                </pre>
              </div>

              {/* Arrow connector (not on last) */}
              {idx < STEPS.length - 1 && (
                <div className="hidden lg:flex absolute -right-4 top-1/2 -translate-y-1/2 z-10 items-center justify-center w-8 h-8 rounded-full bg-background border border-border shadow-sm">
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex justify-center mt-14"
        >
          <Button asChild size="lg" className="h-12 px-8 text-base font-semibold group">
            <Link href="/templates/new">
              Create Your First Template
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </Link>
          </Button>
        </motion.div>
      </div>
    </section>
  )
}

export default HowItWorks
