'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const PHRASES = [
  {
    word: 'Generate',
    sub: '1,000+ API test cases from a single plain-English description',
    color: '#3b82f6',
    glow: 'rgba(59,130,246,0.18)',
    tag: 'Dataset Engine',
  },
  {
    word: 'Discover',
    sub: 'Any API in your ecosystem with natural language semantic search',
    color: '#8b5cf6',
    glow: 'rgba(139,92,246,0.18)',
    tag: 'Vector Search',
  },
  {
    word: 'Embed',
    sub: 'Neural vector representations into your NLP evaluation pipeline',
    color: '#06b6d4',
    glow: 'rgba(6,182,212,0.18)',
    tag: 'Embeddings',
  },
  {
    word: 'Automate',
    sub: 'NLP dataset creation for every API you own — at scale',
    color: '#10b981',
    glow: 'rgba(16,185,129,0.18)',
    tag: 'CI/CD Ready',
  },
]

const DURATION = 3000

export function AnimatedTagline() {
  const [index, setIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.2 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    if (!visible) return

    const tick = () => {
      setIndex(i => (i + 1) % PHRASES.length)
      setProgress(0)
    }

    intervalRef.current = setInterval(tick, DURATION)

    // Smooth progress bar
    const step = 50
    progressRef.current = setInterval(() => {
      setProgress(p => Math.min(p + (step / DURATION) * 100, 100))
    }, step)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (progressRef.current) clearInterval(progressRef.current)
    }
  }, [visible, index])

  const current = PHRASES[index]

  return (
    <section
      ref={ref}
      className="relative overflow-hidden py-20 md:py-28 border-t border-border/40"
      style={{ background: 'var(--background)' }}
    >
      {/* === BACKGROUND LAYERS === */}

      {/* Dynamic color ambient */}
      <div
        className="absolute inset-0 pointer-events-none transition-all duration-1000"
        style={{
          background: `radial-gradient(ellipse 70% 60% at 50% 50%, ${current.glow} 0%, transparent 70%)`,
        }}
      />

      {/* Dot grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle, ${current.color}22 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          opacity: 0.4,
        }}
      />

      {/* Top fade */}
      <div className="absolute top-0 left-0 right-0 h-24 pointer-events-none"
        style={{ background: 'linear-gradient(to bottom, var(--background), transparent)' }} />
      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
        style={{ background: 'linear-gradient(to top, var(--background), transparent)' }} />

      {/* Floating orbs */}
      <motion.div
        className="absolute top-12 left-[10%] w-48 h-48 rounded-full pointer-events-none"
        style={{ background: `radial-gradient(circle, ${current.glow}, transparent)`, filter: 'blur(40px)' }}
        animate={{ y: [0, -20, 0], x: [0, 10, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute bottom-12 right-[10%] w-64 h-64 rounded-full pointer-events-none"
        style={{ background: `radial-gradient(circle, ${current.glow}, transparent)`, filter: 'blur(50px)' }}
        animate={{ y: [0, 20, 0], x: [0, -10, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
      />

      {/* === CONTENT === */}
      <div className="relative max-w-5xl mx-auto px-6 text-center">

        {/* Eyebrow label */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-center gap-3 mb-8"
        >
          <div className="h-px w-12 bg-gradient-to-r from-transparent to-border" />
          <span className="text-xs font-bold tracking-[0.3em] uppercase text-muted-foreground">
            Built for Developer Velocity
          </span>
          <div className="h-px w-12 bg-gradient-to-l from-transparent to-border" />
        </motion.div>

        {/* Active tag badge */}
        <AnimatePresence mode="wait">
          <motion.div
            key={current.tag}
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.85 }}
            transition={{ duration: 0.3 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold mb-6 border"
            style={{
              color: current.color,
              borderColor: `${current.color}44`,
              backgroundColor: `${current.color}12`,
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: current.color }}
            />
            {current.tag}
          </motion.div>
        </AnimatePresence>

        {/* Giant rotating word */}
        <div className="relative h-[100px] md:h-[140px] lg:h-[180px] flex items-center justify-center overflow-hidden mb-2">
          <AnimatePresence mode="wait">
            <motion.h2
              key={current.word}
              initial={{ opacity: 0, y: 80, filter: 'blur(16px)', scale: 0.9 }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)', scale: 1 }}
              exit={{ opacity: 0, y: -80, filter: 'blur(16px)', scale: 0.9 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="absolute font-black tracking-tight leading-none select-none"
              style={{
                fontSize: 'clamp(64px, 12vw, 148px)',
                color: current.color,
                textShadow: `0 0 80px ${current.glow}, 0 0 120px ${current.glow}`,
              }}
            >
              {current.word}
            </motion.h2>
          </AnimatePresence>
        </div>

        {/* Glowing underline */}
        <AnimatePresence mode="wait">
          <motion.div
            key={`line-${current.color}`}
            initial={{ scaleX: 0, opacity: 0 }}
            animate={{ scaleX: 1, opacity: 1 }}
            exit={{ scaleX: 0, opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto mb-8 h-[3px] rounded-full"
            style={{
              width: 'min(280px, 60%)',
              background: `linear-gradient(to right, transparent, ${current.color}, transparent)`,
              boxShadow: `0 0 20px ${current.color}88`,
            }}
          />
        </AnimatePresence>

        {/* Subtitle */}
        <AnimatePresence mode="wait">
          <motion.p
            key={current.sub}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.45, ease: 'easeOut' }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed mb-10"
          >
            {current.sub}
          </motion.p>
        </AnimatePresence>

        {/* Progress bar + dot indicators */}
        <div className="flex flex-col items-center gap-4">

          {/* Dot row */}
          <div className="flex items-center gap-3">
            {PHRASES.map((p, i) => (
              <button
                key={p.word}
                onClick={() => { setIndex(i); setProgress(0) }}
                aria-label={p.word}
                className="relative flex items-center justify-center transition-all duration-300"
                style={{ width: i === index ? 32 : 8, height: 8 }}
              >
                <motion.div
                  layout
                  className="rounded-full h-full w-full"
                  style={{
                    backgroundColor: i === index ? current.color : 'currentColor',
                    opacity: i === index ? 1 : 0.2,
                  }}
                  transition={{ duration: 0.3 }}
                />
                {/* Progress fill on active */}
                {i === index && (
                  <motion.div
                    className="absolute left-0 top-0 h-full rounded-full"
                    style={{ backgroundColor: '#ffffff55', width: `${progress}%` }}
                  />
                )}
              </button>
            ))}
          </div>

          {/* Phrase list pills */}
          <div className="flex flex-wrap items-center justify-center gap-2 mt-2">
            {PHRASES.map((p, i) => (
              <button
                key={p.word}
                onClick={() => { setIndex(i); setProgress(0) }}
                aria-label={`Show "${p.word}" tagline`}
                aria-pressed={i === index}
                className="text-xs px-3 py-1 rounded-full border transition-all duration-300 font-medium"
                style={{
                  borderColor: i === index ? `${p.color}66` : 'transparent',
                  color: i === index ? p.color : 'var(--muted-foreground)',
                  backgroundColor: i === index ? `${p.color}12` : 'transparent',
                }}
              >
                {p.word}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
