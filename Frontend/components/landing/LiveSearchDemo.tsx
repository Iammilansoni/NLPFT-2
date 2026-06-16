'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Zap } from 'lucide-react'
import Link from 'next/link'

const QUERIES = [
  { q: 'forgot password',            api: 'POST /auth/reset-password',      confidence: 97, ms: 18 },
  { q: 'get current user profile',   api: 'GET /users/me',                  confidence: 99, ms: 12 },
  { q: 'invalid login attempt',      api: 'POST /auth/login → 401',         confidence: 94, ms: 22 },
  { q: 'upload profile picture',     api: 'POST /users/avatar',             confidence: 96, ms: 16 },
  { q: 'search for product by name', api: 'GET /products?q={name}',         confidence: 98, ms: 14 },
  { q: 'checkout shopping cart',     api: 'POST /orders/checkout',          confidence: 95, ms: 20 },
]

const CHAR_MS = 38 // ms per character typed

function useTypewriter(text: string, running: boolean) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    if (!running) return

    let i = 0
    const id = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) {
        setDone(true)
        clearInterval(id)
      }
    }, CHAR_MS)
    return () => clearInterval(id)
  }, [text, running])

  return { displayed, done }
}

function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="relative h-1.5 w-full rounded-full bg-muted/50">
      <motion.div
        className="absolute inset-y-0 left-0 rounded-full"
        style={{ background: color }}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      />
    </div>
  )
}

export function LiveSearchDemo() {
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)
  const [idx, setIdx] = useState(0)
  const [phase, setPhase] = useState<'typing' | 'result' | 'pause'>('typing')

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.4 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  const current = QUERIES[idx]
  const { displayed, done } = useTypewriter(current.q, visible && phase === 'typing')

  // Phase machine
  useEffect(() => {
    if (!visible) return
    if (phase === 'typing' && done) {
      const t = setTimeout(() => setPhase('result'), 400)
      return () => clearTimeout(t)
    }
    if (phase === 'result') {
      const t = setTimeout(() => setPhase('pause'), 1600)
      return () => clearTimeout(t)
    }
    if (phase === 'pause') {
      const t = setTimeout(() => {
        setIdx(i => (i + 1) % QUERIES.length)
        setPhase('typing')
      }, 800)
      return () => clearTimeout(t)
    }
  }, [phase, done, visible])

  return (
    <section
      ref={ref}
      className="relative py-12 md:py-16 border-t border-border/40 overflow-hidden bg-background"
    >
      {/* Animated background lines */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-[0.04]">
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute left-0 right-0 h-px bg-foreground"
            style={{ top: `${(i + 1) * 12}%` }}
            animate={{ opacity: [0.3, 0.7, 0.3] }}
            transition={{ duration: 3 + i * 0.4, repeat: Infinity, ease: 'easeInOut' }}
          />
        ))}
      </div>

      <div className="relative max-w-4xl mx-auto px-6">
        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-14"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground mb-5">
            <Zap className="h-3.5 w-3.5 text-primary" />
            Live Demo
          </div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground mb-3">
            Watch it find your API
          </h2>
          <p className="text-muted-foreground text-lg max-w-md mx-auto">
            Type anything. Get the right API back in milliseconds.
          </p>
        </motion.div>

        {/* Terminal demo card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="relative rounded-2xl border border-border/60 bg-card shadow-2xl overflow-hidden"
        >
          {/* Glow */}
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-80 h-40 bg-primary/10 blur-3xl rounded-full pointer-events-none" />

          {/* Bar */}
          <div className="flex items-center gap-2 px-5 py-3.5 border-b border-border/40 bg-muted/30">
            <div className="w-3 h-3 rounded-full bg-red-400/70" />
            <div className="w-3 h-3 rounded-full bg-amber-400/70" />
            <div className="w-3 h-3 rounded-full bg-emerald-400/70" />
            <span className="ml-2 text-xs font-mono text-muted-foreground">NLPForge — Semantic Search</span>
            <div className="ml-auto flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">LIVE</span>
            </div>
          </div>

          <div className="p-7 space-y-6">
            {/* Search input */}
            <div
              className="flex items-center gap-3 px-5 py-3.5 rounded-xl border border-border/60 bg-muted/30"
            >
              <span className="text-primary font-mono text-sm">$</span>
              <span className="flex-1 font-mono text-sm text-foreground">
                {displayed}
                <span
                  className="inline-block w-0.5 h-4 bg-primary ml-0.5 align-middle animate-pulse"
                  style={{ opacity: phase === 'typing' ? 1 : 0 }}
                />
              </span>
              {phase !== 'typing' && (
                <AnimatePresence>
                  <motion.span
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-[10px] font-mono text-muted-foreground"
                  >
                    {current.ms}ms
                  </motion.span>
                </AnimatePresence>
              )}
            </div>

            {/* Result */}
            <AnimatePresence mode="wait">
              {phase === 'result' || phase === 'pause' ? (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.35 }}
                  className="space-y-4"
                >
                  {/* Match result */}
                  <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-500" />
                        <span className="text-xs text-muted-foreground font-mono">Best Match</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-muted-foreground">Confidence</span>
                        <span className="text-sm font-bold text-primary">{current.confidence}%</span>
                      </div>
                    </div>
                    <p className="font-mono text-base font-semibold text-foreground">
                      {current.api}
                    </p>
                    <Bar pct={current.confidence} color="hsl(217 91% 55%)" />
                  </div>

                  {/* Stage breakdown */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg border border-border/40 bg-muted/30 p-3.5 space-y-1">
                      <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Stage 1 — Vector</p>
                      <p className="text-sm font-semibold text-foreground">Redis VSS</p>
                      <p className="text-xs text-muted-foreground">{Math.round(current.ms * 0.44)}ms · top 10 recalled</p>
                    </div>
                    <div className="rounded-lg border border-border/40 bg-muted/30 p-3.5 space-y-1">
                      <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Stage 2 — Re-rank</p>
                      <p className="text-sm font-semibold text-foreground">Cross-Encoder</p>
                      <p className="text-xs text-muted-foreground">{current.ms - Math.round(current.ms * 0.44)}ms · final selection</p>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="searching"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-28 flex items-center justify-center"
                >
                  <div className="flex gap-2 items-center text-muted-foreground text-sm font-mono">
                    {[0, 1, 2].map(i => (
                      <motion.div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-primary"
                        animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.18 }}
                      />
                    ))}
                    <span className="ml-2">searching vectors...</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
          className="flex justify-center mt-10"
        >
          <Link href="/auth/register"
            className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary/80 transition-colors group"
          >
            Try it with your own APIs
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
