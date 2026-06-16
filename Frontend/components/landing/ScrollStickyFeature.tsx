'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileCode, Sparkles, SearchCode } from 'lucide-react'

const FEATURES = [
  {
    step: '01',
    icon: FileCode,
    title: 'Define Once.',
    highlight: 'Use Forever.',
    body: 'Write your API description in plain English. NLPForge creates a versioned, shareable template that your entire team can use as a single source of truth.',
    stat: { value: '1×', label: 'definition, unlimited tests' },
    color: '#3b82f6',
    code: `{
  "api_name":  "POST /auth/login",
  "intent":    "Authenticate user with
               email + password",
  "method":    "POST",
  "endpoint":  "/auth/login"
}`,
  },
  {
    step: '02',
    icon: Sparkles,
    title: 'Describe.',
    highlight: 'Get 1,000 Tests.',
    body: 'Choose any LLM — Gemini, GPT-4, Claude, or local Ollama. NLPForge generates edge cases, error states, and happy paths automatically in seconds.',
    stat: { value: '1,000+', label: 'test cases in under 60s' },
    color: '#8b5cf6',
    code: `Generated 1,000 test cases
──────────────────────────
  ✓  700  valid credential pairs
  ✓  200  edge cases (empty fields)
  ✓  100  extreme values (XSS etc)

  Model:  gemini-2.0-flash
  Time:   47.2 seconds`,
  },
  {
    step: '03',
    icon: SearchCode,
    title: 'Ask in English.',
    highlight: 'Get the API.',
    body: 'No query language. No grep. No docs hunting. Type what you mean and NLPForge vector-searches your entire dataset returning the exact API with confidence score.',
    stat: { value: '<50ms', label: 'semantic retrieval latency' },
    color: '#10b981',
    code: `Query: "user forgot password"

→ Stage 1: Redis VSS   (8ms)
→ Stage 2: Re-ranker   (12ms)

Result:     POST /auth/reset-password
Confidence: 0.97  ████████████░`,
  },
]

const INTERVAL_MS = 3200

export function ScrollStickyFeature() {
  const [activeIndex, setActiveIndex] = useState(0)
  const [visible, setVisible] = useState(false)
  const [progress, setProgress] = useState(0)
  const sectionRef = useRef<HTMLElement>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Intersection observer — only animate when in view
  useEffect(() => {
    const el = sectionRef.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.3 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  // Auto-advance interval
  useEffect(() => {
    if (!visible) {
      if (timerRef.current) clearInterval(timerRef.current)
      if (progressRef.current) clearInterval(progressRef.current)
      return
    }

    setProgress(0)

    // Progress bar tick (every 30ms for smooth animation)
    progressRef.current = setInterval(() => {
      setProgress(p => Math.min(100, p + (30 / INTERVAL_MS) * 100))
    }, 30)

    // Advance step
    timerRef.current = setInterval(() => {
      setProgress(0)
      setActiveIndex(i => (i + 1) % FEATURES.length)
    }, INTERVAL_MS)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (progressRef.current) clearInterval(progressRef.current)
    }
  }, [visible, activeIndex])

  const goTo = (i: number) => {
    // Manual override — restart cycle from chosen step
    if (timerRef.current) clearInterval(timerRef.current)
    if (progressRef.current) clearInterval(progressRef.current)
    setActiveIndex(i)
    setProgress(0)

    // Restart auto-advance from this step
    progressRef.current = setInterval(() => {
      setProgress(p => Math.min(100, p + (30 / INTERVAL_MS) * 100))
    }, 30)
    timerRef.current = setInterval(() => {
      setProgress(0)
      setActiveIndex(j => (j + 1) % FEATURES.length)
    }, INTERVAL_MS)
  }

  const active = FEATURES[activeIndex]

  return (
    <section
      ref={sectionRef}
      className="relative py-12 md:py-16 border-t border-border/40 bg-gradient-to-b from-muted/20 to-background overflow-hidden"
    >
      {/* Section label */}
      <div className="max-w-6xl mx-auto px-6 mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-px flex-1 bg-border/60" />
          <span className="text-sm font-semibold tracking-[0.15em] uppercase text-muted-foreground px-3">
            How NLPForge Works
          </span>
          <div className="h-px flex-1 bg-border/60" />
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-14 items-center">

          {/* ── LEFT: Text content ── */}
          <div className="space-y-8">

            {/* Step rail + progress */}
            <div className="flex items-center gap-4">
              {FEATURES.map((f, i) => (
                <button
                  key={f.step}
                  onClick={() => goTo(i)}
                  className="flex flex-col gap-1.5 group"
                  aria-label={`Step ${f.step}`}
                >
                  <span
                    className="text-[10px] font-mono font-bold transition-colors duration-300"
                    style={{ color: i === activeIndex ? active.color : 'hsl(var(--muted-foreground))' }}
                  >
                    {f.step}
                  </span>
                  <div className="relative h-1 w-12 rounded-full bg-border overflow-hidden">
                    <motion.div
                      className="absolute inset-y-0 left-0 rounded-full"
                      style={{ background: f.color }}
                      animate={{
                        width: i === activeIndex ? `${progress}%` : i < activeIndex ? '100%' : '0%'
                      }}
                      transition={{ duration: 0 }}
                    />
                  </div>
                </button>
              ))}
            </div>

            {/* Title — animates on change */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeIndex + '-title'}
                initial={{ opacity: 0, x: -24, filter: 'blur(6px)' }}
                animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
                exit={{ opacity: 0, x: 24, filter: 'blur(6px)' }}
                transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-1"
              >
                <h2 className="text-4xl md:text-5xl font-black tracking-tight text-foreground leading-tight">
                  {active.title}
                </h2>
                <h2
                  className="text-4xl md:text-5xl font-black tracking-tight leading-tight"
                  style={{ color: active.color }}
                >
                  {active.highlight}
                </h2>
              </motion.div>
            </AnimatePresence>

            {/* Body */}
            <AnimatePresence mode="wait">
              <motion.p
                key={activeIndex + '-body'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="text-muted-foreground text-lg leading-relaxed max-w-md"
              >
                {active.body}
              </motion.p>
            </AnimatePresence>

            {/* Stat chip */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeIndex + '-stat'}
                initial={{ opacity: 0, scale: 0.92 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.92 }}
                transition={{ duration: 0.35, delay: 0.15 }}
                className="inline-flex items-center gap-3 px-5 py-3 rounded-2xl border"
                style={{ borderColor: `${active.color}40`, background: `${active.color}0d` }}
              >
                <span
                  className="text-3xl font-black tabular-nums"
                  style={{ color: active.color }}
                >
                  {active.stat.value}
                </span>
                <span className="text-sm text-muted-foreground">{active.stat.label}</span>
              </motion.div>
            </AnimatePresence>

            {/* Step dot nav */}
            <div className="flex items-center gap-2 pt-2">
              {FEATURES.map((f, i) => (
                <button
                  key={f.step}
                  onClick={() => goTo(i)}
                  className="w-2 h-2 rounded-full transition-all duration-300"
                  style={{
                    background: f.color,
                    opacity: i === activeIndex ? 1 : 0.25,
                    transform: i === activeIndex ? 'scale(1.5)' : 'scale(1)',
                  }}
                  aria-label={`Step ${f.step}`}
                />
              ))}
            </div>
          </div>

          {/* ── RIGHT: Code panel ── */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeIndex + '-code'}
              initial={{ opacity: 0, y: 28, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -16, scale: 0.97 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="relative"
            >
              {/* Glow */}
              <div
                className="absolute -inset-6 rounded-3xl blur-3xl opacity-20 pointer-events-none transition-all duration-700"
                style={{ background: `radial-gradient(circle, ${active.color}, transparent 70%)` }}
              />

              {/* Terminal */}
              <div className="relative rounded-2xl border border-border/60 bg-card overflow-hidden shadow-2xl">
                {/* Title bar */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-border/40 bg-muted/30">
                  <div className="w-3 h-3 rounded-full bg-red-400/70" />
                  <div className="w-3 h-3 rounded-full bg-amber-400/70" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400/70" />
                  <span className="ml-2 text-xs font-mono text-muted-foreground">nlpforge ~ step {active.step}</span>
                  <div
                    className="ml-auto w-2 h-2 rounded-full animate-pulse"
                    style={{ background: active.color }}
                  />
                </div>

                {/* Code */}
                <div className="p-6">
                  <pre className="text-sm font-mono leading-relaxed text-foreground/90 whitespace-pre overflow-x-auto">
                    {active.code}
                  </pre>
                </div>

                {/* Accent bottom border */}
                <div
                  className="absolute bottom-0 left-0 right-0 h-0.5 transition-all duration-700"
                  style={{ background: `linear-gradient(to right, transparent, ${active.color}, transparent)` }}
                />
              </div>
            </motion.div>
          </AnimatePresence>

        </div>
      </div>
    </section>
  )
}
