// app/components/hero/HeroDemo.tsx
'use client'

import React, { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import { GlassCard } from '@/components/ui/glass-card'
import {
  Terminal,
  Search,
  Database,
  Code2,
  Play,
  CheckCircle2,
  Loader2,
  FileCheck,
} from 'lucide-react'
import { cn } from '@/lib/utils'

type Step = {
  id: number
  title: string
  icon: React.ComponentType<any>
}

const STEPS: Step[] = [
  { id: 1, title: 'Analyzing natural language', icon: Terminal },
  { id: 2, title: 'Detecting intent: Login', icon: Search },
  { id: 3, title: 'Generating test cases', icon: Database },
  { id: 4, title: 'Creating embeddings', icon: Code2 },
  { id: 5, title: 'Running tests', icon: Play },
]

const TEST_RESULTS = [
  { name: 'Valid credentials', status: 'PASS', time: '1.2s' },
  { name: 'Invalid email format', status: 'PASS', time: '0.8s' },
  { name: 'Missing password', status: 'PASS', time: '0.9s' },
  { name: 'SQL injection test', status: 'PASS', time: '1.1s' },
]

const containerVariants = {
  hidden: { opacity: 0, y: 6 },
  show: { opacity: 1, y: 0, transition: { staggerChildren: 0.06 } },
}
const itemVariant = {
  hidden: { opacity: 0, x: -14 },
  show: { opacity: 1, x: 0, transition: { duration: 0.38, ease: [0.2, 0.9, 0.3, 1] } },
}

export function HeroDemo() {
  const [typed, setTyped] = useState('')
  const [typing, setTyping] = useState(true)
  const [stepIndex, setStepIndex] = useState(0) // 0 = not started; 1..N while progressing
  const [showResults, setShowResults] = useState(false)
  const [confidence, setConfidence] = useState(0)

  const fullText = 'Test login with email: user@example.com and password: P@ssw0rd'

  // ❗ Stable interval timer for stepper
  const stepTimerRef = useRef<number | null>(null)
  const STEP_DELAY = 800 // Complete in ~1 second per step

  // Typewriter
  useEffect(() => {
    if (typed.length < fullText.length) {
      const tId = window.setTimeout(
        () => setTyped(fullText.slice(0, typed.length + 1)),
        20 // Faster typing speed
      )
      return () => clearTimeout(tId)
    } else if (typing) {
      setTyping(false)
      const tId = window.setTimeout(() => setStepIndex(1), 300) // Faster transition to steps
      return () => clearTimeout(tId)
    }
  }, [typed, typing])

  // Interval-driven step progression (prevents stuck state)
  useEffect(() => {
    // Start when pipeline begins and interval not already running
    if (stepIndex < 1 || stepTimerRef.current) return

    stepTimerRef.current = window.setInterval(() => {
      setStepIndex((s) => {
        if (s < STEPS.length) return s + 1

        // Reached last step → stop and show results once
        if (stepTimerRef.current) {
          clearInterval(stepTimerRef.current)
          stepTimerRef.current = null
        }
        window.setTimeout(() => setShowResults(true), 300) // Faster results display
        return s
      })
    }, STEP_DELAY)

    return () => {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current)
        stepTimerRef.current = null
      }
    }
  }, [stepIndex, STEP_DELAY])

  // Confidence animation after results visible
  useEffect(() => {
    if (!showResults) return
    let cur = 60
    setConfidence(cur)
    const id = window.setInterval(() => {
      cur = Math.min(96, cur + Math.ceil(Math.random() * 4))
      setConfidence(cur)
      if (cur >= 96) clearInterval(id)
    }, 40) // Faster confidence animation
    return () => clearInterval(id)
  }, [showResults])

  // Optional: Replay demo handler (use somewhere if needed)
  // const replay = () => {
  //   if (stepTimerRef.current) {
  //     clearInterval(stepTimerRef.current)
  //     stepTimerRef.current = null
  //   }
  //   setTyped('')
  //   setTyping(true)
  //   setStepIndex(0)
  //   setShowResults(false)
  //   setConfidence(0)
  // }

  return (
    <div className="relative w-full">
      {/* soft outer glow */}
      <div
        className="absolute -inset-6 rounded-2xl blur-3xl opacity-60"
        style={{
          background:
            'linear-gradient(90deg, rgba(6,182,212,0.08), rgba(124,58,237,0.06))',
        }}
      />

      <GlassCard className="relative overflow-hidden p-0">
        <div className="rounded-2xl overflow-hidden border border-border/40">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3 bg-card/80 border-b border-border/50">
            <div className="flex items-center gap-3">
              <div className="flex gap-1">
                <span className="w-3 h-3 rounded-full bg-red-500/80" />
                <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <span className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <span className="text-sm font-semibold text-foreground">Live Demo</span>
            </div>
            <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-3 py-1">
              AI Active
            </Badge>
          </div>

          {/* Content */}
          <div className="p-6 md:p-8 bg-gradient-to-br from-card/95 to-card/85 min-h-[460px]">
            {/* Terminal / input */}
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <Terminal className="w-4 h-4 text-primary" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  Input
                </span>
              </div>

              <div className="rounded-lg border border-border/40 bg-muted/50 p-4 font-mono text-sm">
                <span className="text-primary font-medium">$</span>
                <span className="ml-3 text-foreground">{typed}</span>
                {typing && (
                  <motion.span
                    aria-hidden
                    animate={{ opacity: [1, 0.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className="inline-block w-2 h-5 bg-primary ml-2 rounded-sm align-middle"
                  />
                )}
              </div>
            </div>

            {/* Pipeline steps */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="space-y-3 mb-6"
              aria-live="polite"
            >
              {STEPS.map((s, i) => {
                const done = i < Math.max(0, stepIndex - 1)
                const running = i === Math.max(0, stepIndex - 1)
                const Icon = s.icon
                return (
                  <motion.div
                    key={s.id}
                    variants={itemVariant}
                    className={cn(
                      'flex items-center gap-4 p-3 rounded-lg border transition-all duration-500 relative overflow-hidden',
                      done
                        ? 'bg-emerald-50/50 border-emerald-200/60 shadow-lg'
                        : running
                        ? 'bg-primary/8 border-primary/40 shadow-xl'
                        : 'bg-card/50 border-border/40'
                    )}
                    animate={{
                      scale: running ? 1.02 : done ? 1.01 : 0.98,
                      y: done ? -3 : running ? -1 : 0,
                      backgroundColor: done 
                        ? 'rgba(16, 185, 129, 0.1)' 
                        : running 
                        ? 'rgba(59, 130, 246, 0.08)' 
                        : undefined
                    }}
                    transition={{
                      duration: 0.5,
                      ease: 'easeOut'
                    }}
                  >
                    {/* Animated background gradient for running state */}
                    {running && (
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5"
                        animate={{
                          x: ['-100%', '100%']
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: 'linear'
                        }}
                      />
                    )}
                    
                    {/* Success overlay animation */}
                    {done && (
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-emerald-400/5"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ 
                          duration: 0.6,
                          ease: 'easeOut',
                          delay: 0.1
                        }}
                      />
                    )}
                    <motion.div
                      className={cn(
                        'flex-shrink-0 w-11 h-11 rounded-lg flex items-center justify-center overflow-hidden relative',
                        done
                          ? 'bg-emerald-600/20 text-emerald-500 border border-emerald-500/30'
                          : running
                          ? 'bg-primary/15 text-primary border border-primary/30'
                          : 'bg-muted/10 text-muted-foreground border border-border/30'
                      )}
                      animate={{
                        boxShadow: done 
                          ? '0 0 20px rgba(16, 185, 129, 0.3)' 
                          : running 
                          ? '0 0 15px rgba(59, 130, 246, 0.25)' 
                          : '0 0 0px rgba(0, 0, 0, 0)'
                      }}
                      transition={{ duration: 0.5 }}
                    >
                      <motion.div
                        animate={{
                          scale: done ? [1, 1.3, 1.1] : running ? [1, 1.05, 1] : 1,
                          rotate: done ? [0, 180, 360] : 0
                        }}
                        transition={{
                          duration: done ? 0.8 : running ? 2 : 0,
                          ease: done ? 'easeOut' : 'easeInOut',
                          delay: done ? 0.1 : 0,
                          repeat: running ? Infinity : 0
                        }}
                      >
                        {done ? (
                          <motion.div
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ 
                              duration: 0.4, 
                              ease: 'backOut',
                              delay: 0.2 
                            }}
                          >
                            <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                          </motion.div>
                        ) : running ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ 
                              duration: 1.5, 
                              repeat: Infinity, 
                              ease: 'linear' 
                            }}
                          >
                            <Loader2 className="w-5 h-5 text-primary" />
                          </motion.div>
                        ) : (
                          <Icon className="w-5 h-5" />
                        )}
                      </motion.div>
                      
                      {/* Success pulse effect */}
                      {done && (
                        <motion.div
                          className="absolute inset-0 rounded-lg bg-emerald-500/20"
                          initial={{ scale: 1, opacity: 0.8 }}
                          animate={{ scale: 1.5, opacity: 0 }}
                          transition={{ 
                            duration: 0.6,
                            ease: 'easeOut',
                            delay: 0.1
                          }}
                        />
                      )}
                    </motion.div>

                    <div className="flex-1 min-w-0">
                      <motion.div
                        className={cn(
                          'text-sm font-medium',
                          done ? 'text-foreground' : running ? 'text-primary font-semibold' : 'text-foreground'
                        )}
                        animate={{
                          opacity: running ? 1 : 0.9
                        }}
                      >
                        {s.title}
                      </motion.div>
                      <motion.div
                        className="text-xs text-muted-foreground mt-1"
                        animate={{
                          opacity: running ? 1 : 0.7,
                          color: done ? '#10b981' : running ? '#3b82f6' : undefined
                        }}
                        transition={{ duration: 0.3 }}
                      >
                        <motion.span
                          animate={{
                            scale: done ? [1, 1.2, 1] : 1
                          }}
                          transition={{
                            duration: 0.4,
                            ease: 'backOut',
                            delay: done ? 0.2 : 0
                          }}
                        >
                          {done ? '✅ complete' : running ? '⚡ in progress' : '⏳ waiting'}
                        </motion.span>
                      </motion.div>
                    </div>

                    <motion.div
                      className="flex items-center justify-center text-xs font-mono text-muted-foreground"
                      animate={{
                        opacity: running ? 1 : done ? 1 : 0,
                        scale: running ? [1, 1.1, 1] : done ? [1, 1.2, 1] : 1
                      }}
                      transition={{
                        duration: running ? 1.5 : 0.5,
                        repeat: running ? Infinity : 0,
                        ease: 'easeInOut'
                      }}
                    >
                      {done ? (
                        <motion.span
                          initial={{ scale: 0, rotate: -180 }}
                          animate={{ scale: 1, rotate: 0 }}
                          transition={{ 
                            duration: 0.5, 
                            ease: 'backOut',
                            delay: 0.1 
                          }}
                          className="text-emerald-500 font-bold"
                        >
                          ✓
                        </motion.span>
                      ) : running ? (
                        <motion.span
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ 
                            duration: 1.2, 
                            repeat: Infinity,
                            ease: 'easeInOut'
                          }}
                          className="text-primary"
                        >
                          ...
                        </motion.span>
                      ) : ''}
                    </motion.div>
                  </motion.div>
                )
              })}
            </motion.div>

            {/* Results */}
            <AnimatePresence>
              {showResults && (
                <motion.div
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.98 }}
                  transition={{ 
                    duration: 0.6,
                    ease: 'backOut'
                  }}
                >
                  <div className="rounded-lg border border-border/40 bg-gradient-to-br from-emerald-50/10 to-emerald-500/6 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="h-12 w-12 rounded-lg bg-emerald-600/20 flex items-center justify-center border border-emerald-200/30 shadow-sm">
                          <SparklePlaceholder />
                        </div>
                        <div>
                          <div className="text-sm font-semibold">Detected intent</div>
                          <div className="text-foreground font-bold">Login</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            Auto-generated JSON ready — review or run tests
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-3">
                        <div className="text-xs text-muted-foreground">Confidence</div>
                        <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-emerald-600">
                          {confidence}%
                        </div>
                        <div className="w-36">
                          <div className="h-3 bg-muted rounded-full overflow-hidden border border-border/30 relative">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${confidence}%` }}
                              transition={{ 
                                duration: 1.2,
                                ease: 'easeOut'
                              }}
                              className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 shadow-lg relative"
                            >
                              {/* Animated shine effect */}
                              <motion.div
                                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                                animate={{
                                  x: ['-100%', '100%']
                                }}
                                transition={{
                                  duration: 1.5,
                                  repeat: Infinity,
                                  delay: 1
                                }}
                              />
                            </motion.div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* JSON preview + Actions */}
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="md:col-span-2">
                        <div className="text-xs text-muted-foreground mb-2">Detected JSON</div>
                        <pre className="bg-transparent rounded-md p-3 font-mono text-xs text-foreground overflow-auto border border-border/30 max-h-44">
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

                      <div className="flex flex-col gap-3 items-stretch">
                        <div className="text-xs text-muted-foreground">Actions</div>
                        <div className="flex-1 flex flex-col gap-3">
                          <button className="h-12 rounded-lg bg-gradient-to-r from-primary to-accent text-white font-semibold shadow-md">
                            Run with Selenium
                          </button>
                          <button className="h-10 rounded-lg border border-border/40 bg-card/60 text-sm">
                            Download JSON
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Recent results */}
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-sm font-semibold">Recent test results</div>
                        <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                          4 / 4 Passed
                        </Badge>
                      </div>

                      <div className="rounded-md border border-border/40 overflow-hidden">
                        {TEST_RESULTS.map((r, i) => (
                          <motion.div
                            key={r.name}
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.06 }}
                            className="flex items-center justify-between p-3 border-b border-border/30 last:border-b-0 hover:bg-muted/30"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 rounded-lg bg-emerald-600/10 flex items-center justify-center border border-emerald-200/30">
                                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                              </div>
                              <div>
                                <div className="text-sm font-medium">{r.name}</div>
                                <div className="text-xs text-muted-foreground">{r.status}</div>
                              </div>
                            </div>

                            <div className="flex items-center gap-4">
                              <div className="text-xs font-mono text-muted-foreground">{r.time}</div>
                              <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-xs">
                                PASS
                              </Badge>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </GlassCard>

      {/* floating particle accents */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ 
              opacity: showResults ? [0.1, 1, 0.1] : [0.05, 0.8, 0.05], 
              y: showResults ? [20, -30, 20] : [20, -10, 20],
              scale: showResults ? [1, 1.5, 1] : 1
            }}
            transition={{ 
              duration: showResults ? 3 + i * 0.5 : 8 + i, 
              repeat: Infinity, 
              delay: i * 0.7 
            }}
            className={cn(
              "absolute w-1.5 h-1.5 rounded-full",
              showResults ? "bg-emerald-400/60" : "bg-primary/40"
            )}
            style={{ left: `${10 + i * 12}%`, top: `${60 + (i % 3) * 6}%` }}
          />
        ))}
        
        {/* Celebration particles when results show */}
        {showResults && [...Array(8)].map((_, i) => (
          <motion.div
            key={`celebration-${i}`}
            initial={{ opacity: 0, scale: 0, y: 0 }}
            animate={{ 
              opacity: [0, 1, 0], 
              scale: [0, 1.5, 0],
              y: [-50, -100, -150],
              x: [0, (i % 2 === 0 ? 20 : -20) * Math.random()]
            }}
            transition={{ 
              duration: 2,
              delay: i * 0.1,
              ease: 'easeOut'
            }}
            className="absolute w-2 h-2 rounded-full bg-emerald-400/80"
            style={{ 
              left: `${30 + i * 8}%`, 
              top: '50%'
            }}
          />
        ))}
      </div>
    </div>
  )
}

/* small placeholder icon element */
function SparklePlaceholder() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 2l1.8 3.8L18 7l-3.2 1.2L12 12 10.8 8.2 7.6 7 10.8 5.8 12 2z"
        fill="currentColor"
        style={{ color: 'rgb(16 185 129)' }}
      />
    </svg>
  )
}
