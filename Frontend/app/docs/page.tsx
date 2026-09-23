'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BookOpen, Zap, FileCode, Database, Search as SearchIcon,
  Settings, ArrowRight, Copy, Check, Terminal, ChevronRight,
  Layers, ExternalLink, Code2, Cpu
} from 'lucide-react'
import Link from 'next/link'
import { LandingNav } from '@/components/landing/LandingNav'

// Backend Swagger UI URL, derived from the public API base so it works in all environments.
const SWAGGER_URL = `${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:19000').replace(/\/$/, '')}/docs`

const SECTIONS = [
  { id: 'getting-started', label: 'Getting Started', icon: Zap },
  { id: 'templates', label: 'Templates', icon: FileCode },
  { id: 'datasets', label: 'Datasets', icon: Database },
  { id: 'search', label: 'Semantic Search', icon: SearchIcon },
  { id: 'llm-providers', label: 'LLM Providers', icon: Cpu },
  { id: 'api-reference', label: 'API Reference', icon: Code2 },
]

const API_ENDPOINTS = [
  { method: 'POST', path: '/api/v1/query/semantic-search', desc: 'Route a natural-language request: template + extracted body' },
  { method: 'GET', path: '/api/v1/query/health', desc: 'Routing readiness: embedder reachable, vectors indexed' },
  { method: 'GET', path: '/api/v1/templates/', desc: 'List your API templates' },
  { method: 'POST', path: '/api/v1/templates/', desc: 'Create a template' },
  { method: 'GET', path: '/api/v1/templates/{id}', desc: 'Get a template' },
  { method: 'DELETE', path: '/api/v1/templates/{id}', desc: 'Delete a template (and its vectors)' },
  { method: 'POST', path: '/api/v1/datasets/generate', desc: 'Generate an utterance dataset with an LLM (Celery)' },
  { method: 'POST', path: '/api/v1/datasets/upload', desc: 'Upload a CSV dataset (auto-embedded)' },
  { method: 'GET', path: '/api/v1/datasets/db/list', desc: 'List stored datasets' },
  { method: 'POST', path: '/api/v1/datasets/db/{id}/embed', desc: 'Embed a dataset into pgvector' },
  { method: 'GET', path: '/api/v1/health', desc: 'Service health + runtime (embedder, RLS status)' },
]

const METHOD_COLORS: Record<string, string> = {
  GET:    'bg-info/10 text-info dark:text-info',
  POST:   'bg-success/10 text-success dark:text-success',
  PATCH:  'bg-warning/10 text-warning dark:text-warning',
  DELETE: 'bg-destructive/10 text-destructive dark:text-destructive',
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }}
      className="p-1.5 rounded-md hover:bg-muted/60 transition-colors text-muted-foreground hover:text-foreground"
      aria-label="Copy"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  )
}

function CodeBlock({ code }: { code: string }) {
  return (
    <div className="relative group rounded-xl bg-muted/40 border border-border/60 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/40 bg-muted/30">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-destructive/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-warning/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-success/60" />
        </div>
        <CopyButton text={code} />
      </div>
      <pre className="p-4 text-xs font-mono text-foreground/90 overflow-x-auto leading-relaxed whitespace-pre">{code}</pre>
    </div>
  )
}

export default function DocsPage() {
  const [active, setActive] = useState('getting-started')

  return (
    <div className="min-h-screen bg-background pt-16">
      <LandingNav />
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border/40 bg-gradient-to-b from-muted/30 to-background">
        <div className="absolute -top-40 right-1/3 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative max-w-5xl mx-auto px-6 py-14">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <BookOpen className="h-4 w-4 text-primary" />
            <span>Documentation</span>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="text-foreground capitalize">{active.replace(/-/g, ' ')}</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-3">
            NLPForge Docs
          </h1>
          <p className="text-muted-foreground text-lg max-w-xl">
            How NLPForge routes natural language to API calls, and how to use it.
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-6 py-10 flex gap-10">
        {/* Sidebar Nav */}
        <aside className="hidden lg:block w-56 shrink-0 sticky top-6 self-start">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Contents</p>
          <nav className="space-y-1">
            {SECTIONS.map((s) => {
              const Icon = s.icon
              const isActive = active === s.id
              return (
                <button
                  key={s.id}
                  onClick={() => setActive(s.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all text-left ${
                    isActive
                      ? 'bg-primary/10 text-primary font-semibold'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                  }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {s.label}
                </button>
              )
            })}
          </nav>

          <div className="mt-8 pt-6 border-t border-border/40">
            <p className="text-xs text-muted-foreground mb-2">Also see</p>
            <Link href="/help" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ArrowRight className="h-3.5 w-3.5" /> Help Center
            </Link>
            <a href={SWAGGER_URL} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mt-1.5">
              <ExternalLink className="h-3.5 w-3.5" /> Swagger UI
            </a>
          </div>
        </aside>

        {/* Content */}
        <main className="flex-1 min-w-0 space-y-12">

          {/* Getting Started */}
          <motion.section key={active} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>

            {active === 'getting-started' && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Getting Started</h2>
                  <p className="text-muted-foreground">From zero to a routed, schema-valid API call. The demo tenant already has steps 2 to 4 done.</p>
                </div>

                {[
                  {
                    step: '1', title: 'Sign in', icon: Zap,
                    body: 'Use the one-click demo login, Google, or register with email (verification code by e-mail).',
                  },
                  {
                    step: '2', title: 'Describe your APIs as templates', icon: FileCode,
                    body: 'Templates → New Template: method, endpoint, description and a JSON Schema for the request body.',
                  },
                  {
                    step: '3', title: 'Generate example utterances', icon: Database,
                    body: 'Datasets → Generate: an LLM writes realistic requests for an approved template (or upload a CSV with a query column).',
                  },
                  {
                    step: '4', title: 'Embed them', icon: Cpu,
                    body: 'Embedding writes each utterance to pgvector with the deployment’s embedding model. Uploads are embedded automatically.',
                  },
                  {
                    step: '5', title: 'Route a request', icon: SearchIcon,
                    body: 'Dashboard: type a request in plain English and get the endpoint plus a schema-validated request body.',
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-5">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                      {item.step}
                    </div>
                    <div className="flex-1 pb-6 border-b border-border/40 last:border-0">
                      <div className="flex items-center gap-2 mb-1">
                        <item.icon className="h-4 w-4 text-primary" />
                        <h3 className="font-semibold text-foreground">{item.title}</h3>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">{item.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {active === 'templates' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Templates</h2>
                  <p className="text-muted-foreground">Templates are the core building block — they define an API endpoint that NLPForge generates test cases for.</p>
                </div>
                <div className="rounded-xl border border-border/60 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/40 border-b border-border/40">
                      <tr>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Field</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Required</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ['api_name', 'Yes', 'Unique identifier for this API template'],
                        ['method', 'Yes', 'HTTP method: GET, POST, PUT, DELETE, PATCH'],
                        ['base_url', 'Yes', 'Base URL of the API, e.g. https://api.example.com'],
                        ['endpoint', 'Yes', 'Path component, e.g. /auth/login'],
                        ['description', 'Yes', 'Human-readable description of what this API does'],
                        ['intent_keywords', 'Yes', 'Comma-separated list of intent keywords for search'],
                        ['parameters', 'No', 'JSON schema of expected request parameters'],
                        ['status', 'Auto', 'Draft by default. Toggle to Approved to activate'],
                      ].map(([field, req, desc]) => (
                        <tr key={field} className="border-b border-border/30 last:border-0 hover:bg-muted/20 transition-colors">
                          <td className="px-4 py-3 font-mono text-xs text-primary">{field}</td>
                          <td className="px-4 py-3">
                            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${req === 'Yes' ? 'bg-success/10 text-success dark:text-success' : 'bg-muted text-muted-foreground'}`}>{req}</span>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground text-xs">{desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {active === 'datasets' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Datasets</h2>
                  <p className="text-muted-foreground">Datasets are LLM-generated NLP training records for each API template. Once embedded, they power semantic search.</p>
                </div>
                <CodeBlock code={`POST /api/v1/datasets/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "template_id": "login_api",
  "num_examples": 300,
  "user_prompt": "Generate realistic login scenarios including wrong passwords, locked accounts, and expired tokens"
}`} />
                <p className="text-sm text-muted-foreground">After generation, embed with:</p>
                <CodeBlock code={`POST /api/v1/datasets/db/{dataset_id}/embed
Authorization: Bearer <token>`} />
                <p className="text-xs text-muted-foreground leading-relaxed">
                  <strong>Note:</strong> Browser clients authenticate via HttpOnly cookies set at login —
                  no <code>Authorization</code> header is needed. The <code>Bearer &lt;token&gt;</code> header
                  shown above is supported only as a legacy fallback for non-browser API clients.
                </p>
              </div>
            )}

            {active === 'search' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Semantic Search</h2>
                  <p className="text-muted-foreground">Three stages: pgvector recall over indexed utterances → max-pool ranking per template → schema-constrained extraction validated with Pydantic. Every response reports whether any stage degraded.</p>
                </div>
                <CodeBlock code={`POST /api/v1/query/semantic-search
Content-Type: application/json

{ "query": "refund 25 dollars on order 8820, it arrived broken" }

// Response (abridged)
{
  "success": true,
  "final_output": {
    "api_name": "Refund_Order",
    "method": "POST",
    "endpoint": "/orders/{order_id}/refund",
    "confidence_score": 0.6931
  },
  "extracted_request_body": { "order_id": "8820", "amount": 25.0 },
  "extraction": { "ok": true, "missing_required": [], "degraded": false },
  "ranking": { "strategy": "vector_maxpool", "degraded": false },
  "degraded": false,
  "stage1_vector_search": [...],
  "stage2_reranking": [...]
}`} />
              </div>
            )}

            {active === 'llm-providers' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">LLM Providers</h2>
                  <p className="text-muted-foreground">Configure API keys in Settings → AI Providers. Each provider is used during dataset generation.</p>
                </div>
                <div className="grid gap-4">
                  {[
                    { name: 'Gemini (Google AI)', key: 'GEMINI_API_KEY', models: 'gemini-2.0-flash, gemini-1.5-pro', status: 'Recommended' },
                    { name: 'OpenAI', key: 'OPENAI_API_KEY', models: 'gpt-4o, gpt-4-turbo, gpt-3.5-turbo', status: 'Supported' },
                    { name: 'Anthropic Claude', key: 'ANTHROPIC_API_KEY', models: 'claude-3-5-sonnet, claude-3-haiku', status: 'Supported' },
                    { name: 'Ollama (local)', key: 'None required', models: 'llama3, mistral, phi3', status: 'Local only' },
                  ].map(p => (
                    <div key={p.name} className="flex items-start gap-4 p-4 rounded-xl border border-border/60 bg-card">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-foreground text-sm">{p.name}</span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{p.status}</span>
                        </div>
                        <p className="text-xs text-muted-foreground">Models: {p.models}</p>
                        <code className="text-xs font-mono text-muted-foreground mt-1 block">Env: {p.key}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === 'api-reference' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">API Reference</h2>
                  <p className="text-muted-foreground">
                    Full interactive docs available at{' '}
                    <a href={SWAGGER_URL} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline inline-flex items-center gap-1">
                      {SWAGGER_URL.replace(/^https?:\/\//, '')} <ExternalLink className="h-3 w-3" />
                    </a>
                  </p>
                </div>
                <div className="rounded-xl border border-border/60 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/40 border-b border-border/40">
                      <tr>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider w-20">Method</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Endpoint</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {API_ENDPOINTS.map(({ method, path, desc }) => (
                        <tr key={path} className="border-b border-border/30 last:border-0 hover:bg-muted/20 transition-colors">
                          <td className="px-4 py-3">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded ${METHOD_COLORS[method]}`}>{method}</span>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-foreground/80">{path}</td>
                          <td className="px-4 py-3 text-xs text-muted-foreground">{desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

          </motion.section>
        </main>
      </div>
    </div>
  )
}
