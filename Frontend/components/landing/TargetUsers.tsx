'use client'

import { motion } from 'framer-motion'
import { FlaskConical, BrainCircuit, Users } from 'lucide-react'

const PERSONAS = [
  {
    icon: FlaskConical,
    role: 'QA Engineers',
    tagline: 'Stop writing tests. Start describing them.',
    description:
      'Define your API once. Get 1,000+ test cases covering valid inputs, edge cases, and boundary conditions — in seconds. Focus on what matters: reviewing results, not writing fixtures.',
    highlights: ['Automated test case generation', 'Edge & extreme case coverage', 'CSV / JSON export for any test runner'],
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-500',
    borderHover: 'hover:border-blue-500/30',
    badge: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  },
  {
    icon: BrainCircuit,
    role: 'AI / ML Engineers',
    tagline: 'Production-grade NLP datasets, on demand.',
    description:
      'Generate structured NLP datasets from API templates. Choose from 8 LLM providers, control distribution ratios, and embed with 15+ models. Your training data, purpose-built.',
    highlights: ['8 LLM providers supported', '15+ embedding models', 'Semantic similarity search via Redis Vector'],
    iconBg: 'bg-violet-500/10',
    iconColor: 'text-violet-500',
    borderHover: 'hover:border-violet-500/30',
    badge: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  },
  {
    icon: Users,
    role: 'Engineering Teams',
    tagline: 'Ship faster with AI-powered API intelligence.',
    description:
      'Shared template library, role-based access, and a semantic search layer over your entire API surface. Every engineer on the team can find the right test case in plain English.',
    highlights: ['Shared versioned templates', 'Natural language API discovery', 'Confidence scoring & explainability'],
    iconBg: 'bg-emerald-500/10',
    iconColor: 'text-emerald-500',
    borderHover: 'hover:border-emerald-500/30',
    badge: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  },
]

const cardVariants = {
  hidden: { opacity: 0, y: 28 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] },
  }),
}

export function TargetUsers() {
  return (
    <section className="py-12 md:py-16 border-t">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-14 max-w-2xl mx-auto space-y-4"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground">
            <Users className="h-3.5 w-3.5" />
            Built for Teams Who Ship
          </div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
            The right tool for every role
          </h2>
          <p className="text-muted-foreground text-lg leading-relaxed">
            Whether you write tests, build models, or ship APIs — NLPForge accelerates your workflow.
          </p>
        </motion.div>

        {/* Cards */}
        <div className="grid gap-7 md:grid-cols-3">
          {PERSONAS.map((p, i) => (
            <motion.div
              key={p.role}
              variants={cardVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-60px' }}
              custom={i}
              className={`group relative rounded-2xl border border-border/50 bg-card p-7 transition-all duration-300 ${p.borderHover} hover:shadow-xl hover:-translate-y-1`}
            >
              {/* Icon */}
              <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-5 ${p.iconBg}`}>
                <p.icon className={`h-6 w-6 ${p.iconColor}`} />
              </div>

              {/* Role badge */}
              <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold mb-3 ${p.badge}`}>
                {p.role}
              </div>

              {/* Tagline */}
              <h3 className="text-lg font-semibold mb-3 leading-snug group-hover:text-primary transition-colors">
                {p.tagline}
              </h3>

              {/* Description */}
              <p className="text-sm text-muted-foreground leading-relaxed mb-5">
                {p.description}
              </p>

              {/* Highlights */}
              <ul className="space-y-2">
                {p.highlights.map((h) => (
                  <li key={h} className="flex items-center gap-2.5 text-sm">
                    <span className={`flex-shrink-0 w-1.5 h-1.5 rounded-full ${p.iconBg.replace('/10', '/60')}`} />
                    <span className="text-muted-foreground">{h}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default TargetUsers
