'use client'

import { motion } from 'framer-motion'
import { XCircle, CheckCircle2, Code2, Clock, Wrench, Zap, Package, Search } from 'lucide-react'

const BEFORE = [
  { icon: Clock, text: 'Hours per endpoint writing test scripts by hand' },
  { icon: Wrench, text: 'Brittle scripts that break with every API change' },
  { icon: Code2, text: 'Limited coverage — only happy paths, no edge cases' },
  { icon: XCircle, text: 'No semantic search — grep-based test discovery' },
]

const AFTER = [
  { icon: Zap, text: 'Describe once, generate 1,000+ test cases in seconds' },
  { icon: Package, text: 'Auto-versioned templates that adapt when APIs change' },
  { icon: CheckCircle2, text: 'Full coverage — valid, edge, and extreme cases by default' },
  { icon: Search, text: 'Natural language search returns structured test JSON in <50ms' },
]

const cardVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.45, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] },
  }),
}

const cardVariantsRight = {
  hidden: { opacity: 0, x: 20 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.45, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] },
  }),
}

export function ProblemSolution() {
  return (
    <section className="py-20 md:py-28 border-t bg-muted/20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-14 space-y-3"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            The old way is broken
          </h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">
            Manual API testing doesn&apos;t scale. NLPForge changes that.
          </p>
        </motion.div>

        {/* Side by side */}
        <div className="grid gap-8 lg:grid-cols-2 max-w-5xl mx-auto">
          {/* BEFORE */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="rounded-2xl border border-destructive/20 bg-destructive/5 p-7"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-destructive/10">
                <XCircle className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <div className="text-xs font-semibold text-destructive/70 uppercase tracking-wider mb-0.5">Before NLPForge</div>
                <h3 className="font-semibold text-foreground">Manual testing</h3>
              </div>
            </div>

            <div className="space-y-3">
              {BEFORE.map((item, i) => (
                <motion.div
                  key={item.text}
                  variants={cardVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  custom={i}
                  className="flex items-start gap-3 p-3.5 rounded-xl bg-background/60 border border-destructive/10"
                >
                  <div className="flex-shrink-0 mt-0.5 w-7 h-7 rounded-lg bg-destructive/10 flex items-center justify-center">
                    <item.icon className="h-3.5 w-3.5 text-destructive/70" />
                  </div>
                  <p className="text-sm text-muted-foreground leading-snug">{item.text}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* AFTER */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-7"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-500/10">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <div className="text-xs font-semibold text-emerald-600/70 uppercase tracking-wider mb-0.5">With NLPForge</div>
                <h3 className="font-semibold text-foreground">AI-powered testing</h3>
              </div>
            </div>

            <div className="space-y-3">
              {AFTER.map((item, i) => (
                <motion.div
                  key={item.text}
                  variants={cardVariantsRight}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  custom={i}
                  className="flex items-start gap-3 p-3.5 rounded-xl bg-background/60 border border-emerald-500/10"
                >
                  <div className="flex-shrink-0 mt-0.5 w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <item.icon className="h-3.5 w-3.5 text-emerald-600" />
                  </div>
                  <p className="text-sm text-foreground leading-snug font-medium">{item.text}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

export default ProblemSolution
