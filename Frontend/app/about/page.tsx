'use client';

import Link from 'next/link';
import { Github } from 'lucide-react';
import { LandingNav } from '@/components/landing/LandingNav';
import { LandingFooter } from '@/components/landing/LandingFooter';
import { REPO_URL } from '@/lib/constants';

const ARCHITECTURE = `Next.js 16 (App Router)
   │  same-origin /api/*  →  proxied to FastAPI
   ▼
FastAPI  ── JWT (HttpOnly cookies), rate limits, structured errors
   │
   ├─ Stage 1  embed query ──► Ollama nomic-embed-text   (local mode)
   │                          fastembed ONNX bge-small   (cloud mode)
   │          KNN ──► PostgreSQL + pgvector HNSW, tenant-scoped
   ├─ Stage 2  max-pool utterance scores → template  (cross-encoder optional)
   └─ Stage 3  JSON-Schema-constrained LLM decode → Pydantic → repair retry
                                             (Ollama llama3.2:3b, circuit breaker)

Celery + Redis ── LLM-generated utterance datasets, background jobs
Redis ── rate limits, JWT denylist, circuit-breaker state, Celery broker`;

const STACK: [string, string[]][] = [
  ['Frontend', ['Next.js 16', 'React 18', 'TypeScript', 'Tailwind CSS', 'TanStack Query']],
  ['Backend', ['FastAPI', 'Python 3.11', 'SQLAlchemy 2 (async)', 'Pydantic v2', 'Celery']],
  ['Data', ['PostgreSQL 16', 'pgvector (HNSW)', 'Row-level security', 'Redis', 'Alembic']],
  ['AI / ML', ['Ollama', 'nomic-embed-text', 'bge-small (ONNX)', 'llama3.2:3b', 'FlashRank']],
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNav />
      <main className="max-w-4xl mx-auto px-6 py-16 space-y-14">
        <section className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">About NLPForge</h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            NLPForge is a routing layer for API catalogues. It resolves one natural-language request
            to one endpoint and returns a request body that validates against that endpoint&apos;s
            schema. It is deliberately not an agent: it has no planning loop or multi-step execution,
            which is what lets routing be treated as a measurable retrieval problem.
          </p>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Architecture</h2>
          <pre className="rounded-xl border border-border/60 bg-muted/30 p-5 text-xs md:text-sm font-mono leading-relaxed overflow-x-auto">
            {ARCHITECTURE}
          </pre>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Technology</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {STACK.map(([group, items]) => (
              <div key={group} className="rounded-xl border border-border/60 bg-card p-5">
                <h3 className="font-semibold mb-3">{group}</h3>
                <div className="flex flex-wrap gap-2">
                  {items.map((i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-muted text-muted-foreground">{i}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-2xl font-semibold">Project history</h2>
          <p className="text-muted-foreground leading-relaxed">
            v1 was built by a team (Milan Soni, Avadhi Singhal, Abhilash Joshi) during an internship. It
            was a FastAPI, Redis-vector and Celery prototype. v2 is an individual rewrite by Milan Soni. It
            moved vectors to pgvector, replaced an unmeasured reranking heuristic with a benchmark-driven
            pipeline, and added schema-constrained extraction and a cloud runtime.
          </p>
          <div className="flex gap-4 text-sm">
            <a href={REPO_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-primary hover:underline">
              <Github className="w-4 h-4" /> Source code
            </a>
            <Link href="/docs" className="text-primary hover:underline">Documentation</Link>
          </div>
        </section>
      </main>
      <LandingFooter />
    </div>
  );
}
