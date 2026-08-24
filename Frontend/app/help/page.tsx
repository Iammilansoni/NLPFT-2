'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, BookOpen, Zap, Database, FileCode, Settings,
  ChevronDown, MessageCircle, Mail, Github, ExternalLink,
  ArrowRight, CheckCircle2, AlertCircle, LifeBuoy
} from 'lucide-react'
import Link from 'next/link'

const QUICK_LINKS = [
  { icon: Zap, label: 'Getting Started', href: '/docs#getting-started', desc: 'Set up your first template in 5 minutes' },
  { icon: FileCode, label: 'Templates Guide', href: '/docs#templates', desc: 'Define and manage API templates' },
  { icon: Database, label: 'Datasets', href: '/docs#datasets', desc: 'Generate and embed NLP datasets' },
  { icon: Settings, label: 'Configuration', href: '/settings', desc: 'LLM providers & embedding models' },
]

const FAQS = [
  {
    q: 'How do I create my first API template?',
    a: 'Navigate to Templates → New Template. Fill in the API name, HTTP method, base URL and endpoint path. Add intent keywords that describe what this API does. Save as Draft, then toggle to Active when ready.',
  },
  {
    q: 'Why is the semantic search returning no results?',
    a: 'You need at least one embedded dataset. Go to Datasets > select a dataset > click "Embed to Redis". Make sure the embedding model in Settings matches the model used at search time.',
  },
  {
    q: 'What LLM providers are supported for dataset generation?',
    a: 'NLPForge supports Gemini (Google AI), OpenAI GPT-4/3.5, Anthropic Claude, Mistral, and local Ollama models. Configure API keys in Settings → AI Providers.',
  },
  {
    q: 'How many test cases can I generate per dataset?',
    a: 'You can generate 10 to 5,000 rows per dataset run. The recommended amount is 100–500 for balanced coverage. Generation time scales with row count and provider latency.',
  },
  {
    q: 'What is the difference between "Approved" and "Draft" templates?',
    a: 'Only Approved templates appear in dataset generation and semantic search. Draft templates are hidden from active workflows — use them to prepare templates before activating.',
  },
  {
    q: 'Can I upload my own CSV dataset instead of generating one?',
    a: 'Yes. Go to Datasets → Upload tab. Your CSV must have at minimum a "query" column. After upload you can embed it to Redis for semantic search.',
  },
  {
    q: 'What embedding models are available?',
    a: 'NLPForge uses Ollama for local embedding. Supported models include nomic-embed-text (768D), mxbai-embed-large (1024D), and others. Download models from Settings → Embeddings.',
  },
  {
    q: "Why does the model mismatch warning appear?",
    a: "Your search model dimensions don't match your embedded dataset's model dimensions. Switch to the settings-default model in the search dropdown or re-embed the dataset with the current model.",
  },
]

function FAQItem({ faq, index }: { faq: typeof FAQS[0]; index: number }) {
  const [open, setOpen] = useState(false)
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
      className="border border-border/60 rounded-xl overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left bg-card hover:bg-muted/40 transition-colors gap-4"
      >
        <span className="font-medium text-foreground text-sm leading-snug">{faq.q}</span>
        <ChevronDown className={`h-4 w-4 text-muted-foreground flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 py-4 bg-muted/20 border-t border-border/40">
              <p className="text-sm text-muted-foreground leading-relaxed">{faq.a}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function HelpPage() {
  const [search, setSearch] = useState('')
  const filtered = FAQS.filter(f =>
    f.q.toLowerCase().includes(search.toLowerCase()) ||
    f.a.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border/40">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-40 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute top-10 left-1/4 w-64 h-64 bg-violet-500/5 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto px-6 py-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 text-sm text-muted-foreground mb-5">
            <LifeBuoy className="h-3.5 w-3.5 text-primary" />
            Help Center
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-4">
            How can we help?
          </h1>
          <p className="text-muted-foreground text-lg mb-8 max-w-xl mx-auto">
            Find answers, guides, and resources for NLPForge.
          </p>

          {/* Search */}
          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search help articles..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full h-12 pl-11 pr-4 rounded-xl border border-border bg-card text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 transition-all"
            />
          </div>
        </div>
      </section>

      <main className="max-w-5xl mx-auto px-6 py-12 space-y-14">
        {/* Quick Links */}
        {!search && (
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-5">Browse by Topic</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {QUICK_LINKS.map((link) => (
                <Link key={link.label} href={link.href}
                  className="group flex flex-col gap-3 p-5 rounded-xl border border-border/60 bg-card hover:border-primary/30 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200"
                >
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                    <link.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">{link.label}</div>
                    <div className="text-xs text-muted-foreground mt-0.5 leading-snug">{link.desc}</div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all mt-auto" />
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* FAQ */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-foreground">
              {search ? `Results for "${search}"` : 'Frequently Asked Questions'}
            </h2>
            {search && (
              <span className="text-sm text-muted-foreground">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
            )}
          </div>

          {filtered.length === 0 ? (
            <div className="text-center py-16 rounded-xl border border-border/40 bg-muted/20">
              <AlertCircle className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-foreground font-medium">No results found</p>
              <p className="text-sm text-muted-foreground mt-1">Try a different search term</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {filtered.map((faq, i) => <FAQItem key={i} faq={faq} index={i} />)}
            </div>
          )}
        </section>

        {/* Contact */}
        <section className="rounded-2xl border border-border/60 bg-gradient-to-br from-primary/5 via-card to-card p-8 md:p-10 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-4">
            <MessageCircle className="h-6 w-6 text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Still need help?</h2>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto text-sm">
            Can&apos;t find what you&apos;re looking for? Reach out via GitHub or check the full documentation.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/docs"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors"
            >
              <BookOpen className="h-4 w-4" />
              Read the Docs
            </Link>
            <a href={process.env.NEXT_PUBLIC_ISSUES_URL || 'https://github.com/affina-group/nlpforge/issues'} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-border bg-card text-foreground text-sm font-medium hover:bg-muted/60 transition-colors"
            >
              <Github className="h-4 w-4" />
              Open an Issue
              <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
            </a>
          </div>
        </section>
      </main>
    </div>
  )
}
