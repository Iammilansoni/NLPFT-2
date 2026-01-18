'use client'

import { useEffect, useRef, useState, MouseEvent } from 'react'
import Link from 'next/link'
import { MotionConfig, motion, useReducedMotion, useScroll, useTransform } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Cpu, Play, ArrowRight, Shield, Award, TrendingUp, Gauge, CheckCircle2, Network } from 'lucide-react'
import { cn } from '@/lib/utils'

// import { HeroDemo } from './HeroDemo'

const STATS = [
  { value: '10K+', label: 'Test cases / template', Icon: TrendingUp },
  { value: '<50ms', label: 'Vector search', Icon: Gauge },
  { value: '95%+', label: 'Match accuracy', Icon: CheckCircle2 },
]

const TRUST = [
  { name: 'Redis Vector', Icon: Shield },
  { name: 'Ollama LLM', Icon: Award },
]

export function Hero() {
  const prefersReduced = useReducedMotion()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const { scrollYProgress } = useScroll({ target: containerRef, offset: ['start start', 'end start'] })
  const parallax = useTransform(scrollYProgress, [0, 1], [0, 26])

  // spotlight mouse position (for non-reduced motion users)
  const [spot, setSpot] = useState({ x: '50%', y: '50%' })
  function onPointerMove(e: MouseEvent) {
    if (prefersReduced) return
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    const px = ((e.clientX - rect.left) / rect.width) * 100
    const py = ((e.clientY - rect.top) / rect.height) * 100
    setSpot({ x: `${px}%`, y: `${py}%` })
  }

  return (
    <MotionConfig reducedMotion={prefersReduced ? 'always' : 'user'}>
      <section
        ref={containerRef}
        aria-label="NLPForge hero"
        onPointerMove={onPointerMove}
        className="relative overflow-hidden bg-background/0"
      >
        {/* Subtle decorative gradients + spotlight */}
        <div className="absolute inset-0 -z-10 pointer-events-none">
          <div
            aria-hidden
            className="absolute inset-0 bg-gradient-to-br from-transparent to-primary/6"
          />
          {/* spotlight follows mouse (CSS var) */}
          <div
            aria-hidden
            className="absolute inset-0 transition-[background] duration-150"
            style={{
              background: `radial-gradient(520px circle at ${spot.x} ${spot.y}, rgba(6,182,212,0.10), transparent 20%)`
            }}
          />
          {/* lightweight grid texture */}
          <div
            aria-hidden
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage:
                'linear-gradient(rgba(124,58,237,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.03) 1px, transparent 1px)',
              backgroundSize: '80px 80px',
              maskImage: 'radial-gradient(ellipse 70% 60% at 50% 50%, black, transparent)'
            }}
          />
        </div>

        <motion.div style={{ y: parallax }} className="container mx-auto px-4 py-16 md:py-24 lg:py-32">
          <div className="grid gap-10 lg:grid-cols-2 items-center">
            {/* LEFT: copy / CTAs */}
            <div className="relative z-10 space-y-6">
              <Badge className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/8 text-sm font-semibold shadow-sm backdrop-blur-sm">
                <Cpu className="h-4 w-4 text-primary" />
                LLM-Powered API Testing
              </Badge>

              <motion.h1
                initial={{ opacity: 0, x: -18 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]"
              >
                Generate API Tests{' '}
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient">
                  From Natural Language
                </span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
                className="text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed"
              >
                Define your API templates once. NLPForge generates thousands of semantic test cases using LLM-powered data generation and Redis vector search. Stop writing fragile test scripts.
              </motion.p>

              {/* CTA row */}
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link href="/dashboard" className="relative inline-block group">
                    <div className="absolute -inset-1 rounded-2xl blur-xl opacity-60 group-hover:opacity-100 transition-opacity duration-300"
                      style={{ background: 'linear-gradient(90deg, rgba(6,182,212,0.3), rgba(124,58,237,0.3))' }} />
                    <Button size="lg" className="relative h-14 px-8 py-3 rounded-2xl font-semibold inline-flex items-center gap-3 text-base">
                      <Play className="h-5 w-5" />
                      Start Testing
                      <ArrowRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>

                  <Link 
                    href="/templates" 
                    className="inline-flex items-center gap-3 h-14 px-6 rounded-2xl border border-border/50 bg-card/60 hover:bg-card/80 hover:border-primary/40 transition-all text-base font-medium backdrop-blur-sm group"
                    aria-label="View templates"
                  >
                    <Network className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    View Templates
                  </Link>
                </div>

                {/* micro-note */}
                <div className="mt-4 text-sm text-muted-foreground max-w-xl leading-relaxed">
                  <span className="font-medium text-foreground">Three simple steps:</span> Create API templates → Generate datasets with AI → Search with natural language queries.
                </div>
              </motion.div>

              {/* Stats / trust row */}
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="pt-8 border-t border-border/30"
              >
                <div className="flex flex-col gap-6">
                  {/* Stats */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {STATS.map((s, i) => (
                      <motion.div
                        key={s.label}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.4, delay: 0.25 + i * 0.05 }}
                        className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-br from-card/80 to-card/60 border border-border/40 backdrop-blur-sm hover:border-primary/30 transition-all shadow-sm hover:shadow-md"
                      >
                        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <s.Icon className="h-5 w-5 text-primary" />
                        </div>
                        <div className="min-w-0">
                          <div className="text-lg font-bold text-foreground whitespace-nowrap">{s.value}</div>
                          <div className="text-xs text-muted-foreground whitespace-nowrap">{s.label}</div>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {/* Trust badges */}
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Trusted by:</div>
                    {TRUST.map((t, i) => (
                      <motion.div
                        key={t.name}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.4, delay: 0.4 + i * 0.05 }}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-card/60 border border-border/30 backdrop-blur-sm hover:border-primary/20 transition-all"
                      >
                        <t.Icon className="h-4 w-4 text-primary" />
                        <div className="text-xs font-semibold">{t.name}</div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>

            {/* RIGHT: Interactive Demo */}
            <motion.div
              initial={{ opacity: 0, x: 20, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="relative z-10 hidden lg:block"
            >
              {/* Demo Card - MacBook-style frame */}
              <div className="relative">
                {/* Glow effect */}
                <div className="absolute -inset-4 bg-gradient-to-r from-primary/20 via-accent/20 to-primary/20 rounded-3xl blur-2xl opacity-50" />
                
                {/* Card container */}
                <Card className="relative overflow-hidden rounded-2xl border border-border/50 bg-card/80 backdrop-blur-sm shadow-2xl">
                  {/* Window controls */}
                  <div className="flex items-center gap-2 px-4 py-3 border-b border-border/50 bg-muted/30">
                    <div className="flex gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-red-500/80" />
                      <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                      <div className="w-3 h-3 rounded-full bg-green-500/80" />
                    </div>
                    <span className="flex-1 text-center text-xs text-muted-foreground font-mono">NLPForge - Test Generator</span>
                  </div>
                  
                  {/* Demo content */}
                  <div className="p-5 min-h-[320px]">
                    <DemoInline />
                  </div>
                </Card>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* bottom fade */}
        <div className="absolute inset-x-0 bottom-0 h-28 pointer-events-none bg-gradient-to-t from-background to-transparent" />
      </section>
    </MotionConfig>
  )
}

/* ----------------- DemoInline - lightweight inline demo (typewriter + mini steps + JSON preview) ----------------- */

const TYPEWRITER_PHRASES = [
  'Find all user authentication APIs',
  'Search for payment processing endpoints',
  'Show me APIs that handle file uploads',
  'Get inventory management endpoints',
  'Find APIs for order tracking',
]

function DemoInline() {
  const [text, setText] = useState('')
  const [phraseIndex, setPhraseIndex] = useState(0)
  const full = TYPEWRITER_PHRASES[phraseIndex]
  const [step, setStep] = useState(0)
  const prefersReduced = useReducedMotion()
  const [confidence, setConfidence] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)

  // typewriter with cycling phrases
  useEffect(() => {
    if (prefersReduced) {
      setText(full)
      setStep(1)
      return
    }

    if (!isDeleting && text.length < full.length) {
      // Typing
      const id = setTimeout(() => setText(full.slice(0, text.length + 1)), 35)
      return () => clearTimeout(id)
    } else if (!isDeleting && text.length === full.length) {
      // Pause at end, then start deleting
      const start = setTimeout(() => setStep(1), 400)
      const deleteStart = setTimeout(() => setIsDeleting(true), 4000)
      return () => { clearTimeout(start); clearTimeout(deleteStart) }
    } else if (isDeleting && text.length > 0) {
      // Deleting
      const id = setTimeout(() => setText(text.slice(0, -1)), 20)
      return () => clearTimeout(id)
    } else if (isDeleting && text.length === 0) {
      // Move to next phrase
      setIsDeleting(false)
      setStep(0)
      setConfidence(0)
      setPhraseIndex((prev) => (prev + 1) % TYPEWRITER_PHRASES.length)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, isDeleting, full])

  useEffect(() => {
    if (step > 0 && step < 5) {
      const id = setTimeout(() => setStep((s) => s + 1), prefersReduced ? 200 : 500)
      return () => clearTimeout(id)
    }
    if (step >= 5) {
      // fake confidence fill
      let cur = 50
      const id = setInterval(() => {
        cur = Math.min(96, cur + Math.floor(Math.random() * 8))
        setConfidence(cur)
        if (cur >= 96) clearInterval(id)
      }, 60)
      return () => clearInterval(id)
    }
  }, [step, prefersReduced])

  const steps = [
    'Parsing natural language query',
    'Generating embeddings',
    'Vector similarity search',
    'Matching API templates',
    'Results ready'
  ]

  return (
    <div className="space-y-3">
      <div className="rounded-md p-3 bg-muted/10 border border-border/30 font-mono text-sm min-h-[56px]">
        <span className="text-primary font-medium">{text}</span>
        {text.length === full.length && <span className="ml-1 text-muted-foreground">Γûî</span>}
      </div>

      <div className="grid gap-2">
        {steps.slice(0, Math.min(step, steps.length)).map((s, i) => (
          <div key={s} className="flex items-center gap-3 text-sm">
            <div className={cn('h-7 w-7 rounded-md flex items-center justify-center', i < step - 1 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-primary/10 text-primary')}>
              {i < step - 1 ? <CheckCircle2 className="h-4 w-4" /> : <Network className="h-4 w-4" />}
            </div>
            <div className="flex-1">
              <div className="font-medium text-sm">{s}</div>
              <div className="text-xs text-muted-foreground"> {i < step - 1 ? 'complete' : i === step - 1 ? 'in progress' : ''} </div>
            </div>
            <div className="text-xs font-semibold">
              {i < step - 1 ? 'Γ£ô' : i === step - 1 ? '...' : ''}
            </div>
          </div>
        ))}
      </div>

      {step >= steps.length && (
        <div className="mt-3 rounded-md border border-border/30 bg-white/4 p-3">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs text-muted-foreground">Detected JSON</div>
              <pre className="mt-2 text-xs bg-transparent p-2 rounded-md font-mono text-sm overflow-auto max-h-40">
                {`{
  "intent": "login",
  "template": "user_login",
  "slots": {
    "base_url": "https://demo.com",
    "username": "milan",
    "password": "Mila@123"
  },
  "confidence": ${confidence}
}`}
              </pre>
            </div>

            <div className="w-36 flex flex-col items-end gap-2">
              <div className="text-xs text-muted-foreground">Confidence</div>
              <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-green-400">{confidence}%</div>
              <Link href="/run/new">
                <Button size="sm" className="h-10 px-4 text-sm">Run with Selenium</Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
