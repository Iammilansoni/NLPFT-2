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
  Sparkles,
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

const STEP_COLORS = [
  { gradient: 'from-blue-500 to-cyan-500', bg: 'bg-blue-500/20', border: 'border-blue-500/40', text: 'text-blue-400', glow: 'shadow-blue-500/20' },
  { gradient: 'from-purple-500 to-pink-500', bg: 'bg-purple-500/20', border: 'border-purple-500/40', text: 'text-purple-400', glow: 'shadow-purple-500/20' },
  { gradient: 'from-emerald-500 to-teal-500', bg: 'bg-emerald-500/20', border: 'border-emerald-500/40', text: 'text-emerald-400', glow: 'shadow-emerald-500/20' },
  { gradient: 'from-orange-500 to-amber-500', bg: 'bg-orange-500/20', border: 'border-orange-500/40', text: 'text-orange-400', glow: 'shadow-orange-500/20' },
  { gradient: 'from-violet-500 to-indigo-500', bg: 'bg-violet-500/20', border: 'border-violet-500/40', text: 'text-violet-400', glow: 'shadow-violet-500/20' },
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

  const STEP_DELAY = 1800 // Timing for each step

  // Typewriter effect
  useEffect(() => {
    if (typed.length < fullText.length) {
      const tId = window.setTimeout(
        () => setTyped(fullText.slice(0, typed.length + 1)),
        30
      )
      return () => clearTimeout(tId)
    } else if (typing) {
      setTyping(false)
      // Start first step after typing completes
      const tId = window.setTimeout(() => {
        setStepIndex(1)
      }, 600)
      return () => clearTimeout(tId)
    }
  }, [typed, typing, fullText])

  // Progress through steps automatically
  useEffect(() => {
    if (stepIndex === 0 || stepIndex > STEPS.length) return

    const timer = window.setTimeout(() => {
      if (stepIndex < STEPS.length) {
        setStepIndex(stepIndex + 1)
      } else if (stepIndex === STEPS.length) {
        // All steps complete, show results
        window.setTimeout(() => setShowResults(true), 400)
      }
    }, STEP_DELAY)

    return () => clearTimeout(timer)
  }, [stepIndex])

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
      {/* Enhanced outer glow */}
      <div
        className="absolute -inset-8 rounded-3xl blur-3xl opacity-40"
        style={{
          background:
            'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(168,85,247,0.12), rgba(16,185,129,0.1))',
        }}
      />

      <GlassCard className="relative overflow-hidden p-0 shadow-2xl">
        <div className="rounded-2xl overflow-hidden border-2 border-primary/20 bg-gradient-to-br from-background via-background/95 to-background/90">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-primary/5 via-purple-500/5 to-primary/5 border-b-2 border-primary/20 backdrop-blur-xl">
            <div className="flex items-center gap-3">
              <div className="flex gap-1.5">
                <motion.span 
                  className="w-3 h-3 rounded-full bg-red-500/90 shadow-sm"
                  animate={{ opacity: [1, 0.7, 1] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 0 }}
                />
                <motion.span 
                  className="w-3 h-3 rounded-full bg-yellow-500/90 shadow-sm"
                  animate={{ opacity: [1, 0.7, 1] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
                />
                <motion.span 
                  className="w-3 h-3 rounded-full bg-green-500/90 shadow-sm"
                  animate={{ opacity: [1, 0.7, 1] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}
                />
              </div>
              <motion.span 
                className="text-sm font-bold text-foreground tracking-wide"
                animate={{ opacity: [1, 0.9, 1] }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                Live Demo
              </motion.span>
            </div>
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                boxShadow: [
                  '0 0 0px rgba(16, 185, 129, 0)',
                  '0 0 10px rgba(16, 185, 129, 0.3)',
                  '0 0 0px rgba(16, 185, 129, 0)'
                ]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
            >
              <Badge className="bg-gradient-to-r from-emerald-500/15 to-emerald-400/10 text-emerald-400 border-2 border-emerald-500/30 px-4 py-1.5 font-semibold shadow-lg">
                <motion.span
                  className="inline-block w-2 h-2 rounded-full bg-emerald-400 mr-2"
                  animate={{
                    scale: [1, 1.3, 1],
                    opacity: [1, 0.7, 1]
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'easeInOut'
                  }}
                />
                AI Active
              </Badge>
            </motion.div>
          </div>

          {/* Content */}
          <div className="p-6 md:p-8 bg-gradient-to-br from-background/50 via-primary/5 to-purple-500/5 min-h-[460px] backdrop-blur-sm">
            {/* Terminal / input */}
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <Terminal className="w-4 h-4 text-primary" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  Input
                </span>
              </div>

              <div className="relative rounded-xl border-2 border-primary/30 bg-gradient-to-br from-card/90 via-primary/5 to-purple-500/5 p-5 font-mono text-sm shadow-2xl overflow-hidden backdrop-blur-sm">
                {/* Animated background gradient */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-primary/10 via-purple-500/10 to-primary/10"
                  animate={{
                    x: ['-100%', '100%']
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: 'linear'
                  }}
                />
                <div className="relative flex items-center gap-3">
                  <motion.span 
                    className="text-primary font-bold text-lg"
                    animate={{ opacity: [1, 0.7, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    $
                  </motion.span>
                  <span className="text-foreground font-semibold">{typed}</span>
                  {typing && (
                    <motion.span
                      aria-hidden
                      animate={{ 
                        opacity: [1, 0.3, 1],
                        scale: [1, 1.1, 1]
                      }}
                      transition={{ 
                        duration: 0.8, 
                        repeat: Infinity,
                        ease: 'easeInOut'
                      }}
                      className="inline-block w-2.5 h-5 bg-gradient-to-b from-primary via-purple-500 to-primary/60 ml-1 rounded-sm align-middle shadow-lg"
                    />
                  )}
                </div>
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
                const pending = i > Math.max(0, stepIndex - 1)
                const Icon = s.icon
                const colors = STEP_COLORS[i] || STEP_COLORS[0]
                
                return (
                  <motion.div
                    key={s.id}
                    variants={itemVariant}
                    className={cn(
                      'flex items-center gap-4 p-5 rounded-xl border-2 transition-all duration-500 relative overflow-hidden group',
                      done
                        ? `bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 ${colors.border} shadow-xl ${colors.glow}`
                        : running
                        ? `bg-gradient-to-br ${colors.bg} ${colors.border} shadow-2xl ${colors.glow}`
                        : 'bg-card/30 border-border/20 opacity-50'
                    )}
                    animate={{
                      scale: running ? 1.02 : done ? 1 : pending ? 0.98 : 1,
                      y: done ? -1 : running ? 0 : 0,
                      opacity: pending ? 0.5 : 1,
                    }}
                    transition={{
                      duration: 0.4,
                      ease: 'easeOut'
                    }}
                    whileHover={!running && !done ? { scale: 0.99, opacity: 0.7 } : {}}
                  >
                    {/* Animated background gradient for running state */}
                    {running && (
                      <>
                        <motion.div
                          className={cn("absolute inset-0 bg-gradient-to-r from-transparent via-primary/15 to-transparent")}
                          animate={{
                            x: ['-100%', '200%']
                          }}
                          transition={{
                            duration: 2.5,
                            repeat: Infinity,
                            ease: 'linear'
                          }}
                        />
                        {/* Pulsing glow effect */}
                        <motion.div
                          className={cn("absolute inset-0 rounded-xl", `bg-gradient-to-r ${colors.gradient}`)}
                          animate={{
                            opacity: [0.1, 0.2, 0.1]
                          }}
                          transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: 'easeInOut'
                          }}
                        />
                      </>
                    )}
                    
                    {/* Success overlay animation */}
                    {done && (
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-emerald-500/15 via-emerald-400/10 to-emerald-500/15"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ 
                          duration: 0.6,
                          ease: 'easeOut',
                          delay: 0.1
                        }}
                      />
                    )}
                    
                    {/* Progress bar for running state */}
                    {running && (
                      <motion.div
                        className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary to-transparent"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{
                          duration: STEP_DELAY / 1000,
                          ease: 'linear'
                        }}
                      />
                    )}
                    <motion.div
                      className={cn(
                        'flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center overflow-hidden relative',
                        done
                          ? `bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 ${colors.border} border-2`
                          : running
                          ? `bg-gradient-to-br ${colors.bg} ${colors.border} border-2`
                          : 'bg-muted/20 text-muted-foreground border-2 border-border/40'
                      )}
                      animate={{
                        boxShadow: done 
                          ? '0 0 25px rgba(16, 185, 129, 0.4), 0 0 50px rgba(16, 185, 129, 0.1)' 
                          : running 
                          ? `0 0 20px rgba(59, 130, 246, 0.3), 0 0 40px rgba(59, 130, 246, 0.1)`
                          : '0 0 0px rgba(0, 0, 0, 0)',
                        scale: running ? [1, 1.05, 1] : done ? 1 : 1,
                      }}
                      transition={{ 
                        duration: running ? 1.5 : 0.5,
                        repeat: running ? Infinity : 0,
                        ease: 'easeInOut'
                      }}
                    >
                      <motion.div
                        animate={{
                          scale: done ? [1, 1.2, 1] : running ? [1, 1.1, 1] : 1,
                          rotate: done ? [0, 10, -10, 0] : running ? [0, 360] : 0
                        }}
                        transition={{
                          duration: done ? 0.6 : running ? 2 : 0,
                          ease: done ? 'easeOut' : 'easeInOut',
                          delay: done ? 0.1 : 0,
                          repeat: running ? Infinity : 0
                        }}
                      >
                        {done ? (
                          <motion.div
                            initial={{ scale: 0, opacity: 0, rotate: -180 }}
                            animate={{ scale: 1, opacity: 1, rotate: 0 }}
                            transition={{ 
                              duration: 0.5, 
                              ease: 'backOut',
                              delay: 0.2 
                            }}
                            className="relative"
                          >
                            <CheckCircle2 className={cn("w-6 h-6", colors.text)} />
                            {/* Checkmark glow */}
                            <motion.div
                              className={cn("absolute inset-0 rounded-full", `bg-gradient-to-r ${colors.gradient}`)}
                              initial={{ scale: 0, opacity: 0.8 }}
                              animate={{ scale: 2, opacity: 0 }}
                              transition={{ 
                                duration: 0.8,
                                ease: 'easeOut',
                                delay: 0.3
                              }}
                            />
                          </motion.div>
                        ) : running ? (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ 
                              duration: 1.2, 
                              repeat: Infinity, 
                              ease: 'linear' 
                            }}
                            className="relative"
                          >
                            <Loader2 className={cn("w-6 h-6", colors.text)} />
                            {/* Spinning glow trail */}
                            <motion.div
                              className={cn("absolute inset-0 rounded-full border-2", colors.border)}
                              animate={{ 
                                rotate: 360,
                                scale: [1, 1.2, 1]
                              }}
                              transition={{ 
                                duration: 1.5, 
                                repeat: Infinity, 
                                ease: 'linear' 
                              }}
                            />
                          </motion.div>
                        ) : (
                          <Icon className="w-5 h-5 opacity-50" />
                        )}
                      </motion.div>
                      
                      {/* Success pulse effect */}
                      {done && (
                        <>
                          <motion.div
                            className={cn("absolute inset-0 rounded-xl", `bg-gradient-to-r ${colors.gradient}`)}
                            initial={{ scale: 1, opacity: 0.3 }}
                            animate={{ scale: 1.8, opacity: 0 }}
                            transition={{ 
                              duration: 0.8,
                              ease: 'easeOut',
                              delay: 0.2
                            }}
                          />
                          <motion.div
                            className={cn("absolute inset-0 rounded-xl", `bg-gradient-to-r ${colors.gradient}`)}
                            initial={{ scale: 1, opacity: 0.2 }}
                            animate={{ scale: 2.2, opacity: 0 }}
                            transition={{ 
                              duration: 1,
                              ease: 'easeOut',
                              delay: 0.4
                            }}
                          />
                        </>
                      )}
                    </motion.div>

                    <div className="flex-1 min-w-0">
                      <motion.div
                        className={cn(
                          'text-sm font-semibold',
                          done ? 'text-emerald-700 dark:text-emerald-400' : running ? `${colors.text} font-bold` : 'text-foreground/70'
                        )}
                        animate={{
                          opacity: running ? 1 : done ? 1 : 0.7,
                          scale: running ? [1, 1.02, 1] : 1
                        }}
                        transition={{
                          duration: running ? 1.5 : 0.3,
                          repeat: running ? Infinity : 0,
                          ease: 'easeInOut'
                        }}
                      >
                        {s.title}
                      </motion.div>
                      <motion.div
                        className="text-xs mt-1.5 flex items-center gap-2"
                        animate={{
                          opacity: running ? 1 : done ? 0.9 : 0.6,
                        }}
                        transition={{ duration: 0.3 }}
                      >
                        <motion.span
                          className={cn(
                            "inline-flex items-center gap-1.5 font-medium",
                            done ? 'text-emerald-600 dark:text-emerald-400' : running ? colors.text : 'text-muted-foreground'
                          )}
                          animate={{
                            scale: done ? [1, 1.15, 1] : running ? [1, 1.05, 1] : 1,
                            x: running ? [0, 2, 0] : 0
                          }}
                          transition={{
                            duration: done ? 0.5 : running ? 1.2 : 0,
                            ease: 'backOut',
                            delay: done ? 0.2 : 0,
                            repeat: running ? Infinity : 0
                          }}
                        >
                          {done ? (
                            <>
                              <motion.span
                                initial={{ scale: 0, rotate: -180 }}
                                animate={{ scale: 1, rotate: 0 }}
                                transition={{ duration: 0.4, ease: 'backOut', delay: 0.3 }}
                              >
                                ✓
                              </motion.span>
                              <span>complete</span>
                            </>
                          ) : running ? (
                            <>
                              <motion.span
                                animate={{ 
                                  opacity: [0.5, 1, 0.5],
                                  scale: [1, 1.2, 1]
                                }}
                                transition={{ 
                                  duration: 1, 
                                  repeat: Infinity,
                                  ease: 'easeInOut'
                                }}
                              >
                                ⚡
                              </motion.span>
                              <span>in progress</span>
                            </>
                          ) : (
                            <>
                              <span>⏳</span>
                              <span>waiting</span>
                            </>
                          )}
                        </motion.span>
                      </motion.div>
                    </div>

                    <motion.div
                      className="flex items-center justify-center min-w-[40px]"
                      animate={{
                        opacity: running ? 1 : done ? 1 : 0,
                      }}
                      transition={{
                        duration: 0.3
                      }}
                    >
                      {done ? (
                        <motion.div
                          initial={{ scale: 0, rotate: -180, opacity: 0 }}
                          animate={{ scale: 1, rotate: 0, opacity: 1 }}
                          transition={{ 
                            duration: 0.6, 
                            ease: 'backOut',
                            delay: 0.2 
                          }}
                          className={cn("relative", colors.text)}
                        >
                          <motion.div
                            className={cn("w-8 h-8 rounded-full flex items-center justify-center font-bold text-lg", `bg-gradient-to-br ${colors.gradient} text-white shadow-lg`)}
                            animate={{
                              scale: [1, 1.1, 1],
                              boxShadow: [
                                `0 0 0px ${colors.text}`,
                                `0 0 15px ${colors.text}`,
                                `0 0 0px ${colors.text}`
                              ]
                            }}
                            transition={{
                              duration: 2,
                              repeat: Infinity,
                              ease: 'easeInOut'
                            }}
                          >
                            ✓
                          </motion.div>
                        </motion.div>
                      ) : running ? (
                        <motion.div
                          className="flex items-center gap-1"
                          animate={{ 
                            opacity: [0.6, 1, 0.6],
                          }}
                          transition={{ 
                            duration: 1.5, 
                            repeat: Infinity,
                            ease: 'easeInOut'
                          }}
                        >
                          <motion.span
                            animate={{ opacity: [0.3, 1, 0.3] }}
                            transition={{ 
                              duration: 0.8, 
                              repeat: Infinity,
                              delay: 0,
                              ease: 'easeInOut'
                            }}
                            className={cn("text-2xl", colors.text)}
                          >
                            •
                          </motion.span>
                          <motion.span
                            animate={{ opacity: [0.3, 1, 0.3] }}
                            transition={{ 
                              duration: 0.8, 
                              repeat: Infinity,
                              delay: 0.2,
                              ease: 'easeInOut'
                            }}
                            className={cn("text-2xl", colors.text)}
                          >
                            •
                          </motion.span>
                          <motion.span
                            animate={{ opacity: [0.3, 1, 0.3] }}
                            transition={{ 
                              duration: 0.8, 
                              repeat: Infinity,
                              delay: 0.4,
                              ease: 'easeInOut'
                            }}
                            className={cn("text-2xl", colors.text)}
                          >
                            •
                          </motion.span>
                        </motion.div>
                      ) : null}
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
                        <motion.div 
                          className="h-12 w-12 rounded-lg bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 flex items-center justify-center border-2 border-emerald-500/30 shadow-lg"
                          animate={{
                            rotate: [0, 5, -5, 0],
                            scale: [1, 1.05, 1]
                          }}
                          transition={{
                            duration: 3,
                            repeat: Infinity,
                            ease: 'easeInOut'
                          }}
                        >
                          <Sparkles className="w-6 h-6 text-emerald-500" />
                        </motion.div>
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
