'use client';

import Link from 'next/link';
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Database,
  FileJson,
  Gauge,
  Github,
  ListOrdered,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { LandingNav } from '@/components/landing/LandingNav';
import { LandingFooter } from '@/components/landing/LandingFooter';
import { Button } from '@/components/ui/button';
import { DEMO_MODE, REPO_URL } from '@/lib/constants';

/**
 * Landing page. Every claim here is backed by code or by a number reproducible
 * with `python evals/run_eval.py` (see the repository README).
 */

const STACK = ['FastAPI', 'PostgreSQL · pgvector', 'Ollama', 'Pydantic v2', 'Celery · Redis', 'Next.js 16'];

const STAGES = [
  {
    icon: Brain,
    title: 'Recall',
    body: 'The request is embedded and matched against example utterances for every API template, using pgvector HNSW search scoped to your tenant.',
    meta: 'nomic-embed-text · top-25',
  },
  {
    icon: ListOrdered,
    title: 'Rank',
    body: 'Utterance scores are max-pooled per template, so one exact match beats many near-misses. The cross-encoder stays off because measurement said so.',
    meta: 'max-pool · 5 candidates',
  },
  {
    icon: FileJson,
    title: 'Extract',
    body: 'A JSON-Schema-constrained LLM fills the request body. Pydantic validates it, one repair retry runs on failure, and missing fields are reported, never invented.',
    meta: 'llama3.2:3b · Pydantic',
  },
];

const RESULTS = [
  { label: 'Dense retrieval + max-pool', value: 0.822, note: 'shipped default · bge-small', best: true },
  { label: 'Dense + BM25 hybrid (RRF)', value: 0.806, note: 'best on hard negatives only' },
  { label: 'Live API · local mode', value: 0.8, note: 'nomic-embed-text through pgvector' },
  { label: 'Dense + ms-marco cross-encoder', value: 0.739, note: 'off-distribution, disabled' },
  { label: 'v1 weighted heuristic', value: 0.589, note: 'what the first version shipped' },
];

const HIGHLIGHTS = [
  {
    icon: Gauge,
    title: 'Measured routing',
    body: 'A 180-query held-out benchmark across four difficulty tiers runs in CI and gates merges on Hit@1.',
  },
  {
    icon: ShieldCheck,
    title: 'Tenant isolation',
    body: 'Every vector query carries an explicit tenant predicate, and PostgreSQL row-level security enforces it again for non-superuser roles.',
  },
  {
    icon: Sparkles,
    title: 'Honest failure',
    body: 'Responses carry `degraded` and a reason, so "no values in the request" is distinguishable from "the LLM was unreachable".',
  },
  {
    icon: Database,
    title: 'Two runtimes',
    body: 'Local mode runs fully offline on Ollama. Cloud mode embeds in-process with ONNX, so the stack reduces to FastAPI and Postgres.',
  },
];

/* A syntax-coloured JSON response, as the API returns it. */
function ResultJson() {
  const k = 'text-[hsl(245_90%_78%)]';
  const str = 'text-[hsl(156_60%_62%)]';
  const num = 'text-[hsl(34_95%_66%)]';
  const kw = 'text-[hsl(205_90%_70%)]';
  return (
    <pre className="font-mono text-[12.5px] leading-[1.7] text-white/80 overflow-x-auto">
      {'{\n'}
      {'  '}<span className={k}>&quot;api_name&quot;</span>: <span className={str}>&quot;Refund_Order&quot;</span>,{'\n'}
      {'  '}<span className={k}>&quot;method&quot;</span>: <span className={str}>&quot;POST&quot;</span>,{'\n'}
      {'  '}<span className={k}>&quot;endpoint&quot;</span>: <span className={str}>&quot;/orders/{'{order_id}'}/refund&quot;</span>,{'\n'}
      {'  '}<span className={k}>&quot;extracted_request_body&quot;</span>: {'{\n'}
      {'    '}<span className={k}>&quot;order_id&quot;</span>: <span className={str}>&quot;8820&quot;</span>,{'\n'}
      {'    '}<span className={k}>&quot;amount&quot;</span>: <span className={num}>25.0</span>{'\n'}
      {'  },\n'}
      {'  '}<span className={k}>&quot;extraction&quot;</span>: {'{ '}<span className={k}>&quot;ok&quot;</span>: <span className={kw}>true</span>, <span className={k}>&quot;missing_required&quot;</span>: []{' },\n'}
      {'  '}<span className={k}>&quot;degraded&quot;</span>: <span className={kw}>false</span>{'\n'}
      {'}'}
    </pre>
  );
}

function ProductWindow() {
  const stages = [
    { n: '01', label: 'Vector recall', detail: '25 utterances · 30 ms' },
    { n: '02', label: 'Template ranking', detail: 'Refund_Order · 0.693' },
    { n: '03', label: 'Structured extraction', detail: '2 fields · schema-valid' },
  ];
  return (
    <div className="relative mx-auto max-w-5xl">
      <div className="absolute -inset-x-10 -inset-y-8 -z-10 rounded-[2.5rem] bg-brand-gradient opacity-25 blur-3xl" />
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-[hsl(236_28%_9%)] shadow-2xl ring-1 ring-black/5">
        <div className="flex items-center gap-2 border-b border-white/10 px-5 py-3.5">
          <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <span className="h-3 w-3 rounded-full bg-[#28c840]" />
          <span className="ml-4 rounded-md bg-white/5 px-3 py-1 font-mono text-[11px] text-white/50">
            POST /api/v1/query/semantic-search
          </span>
        </div>
        <div className="grid gap-0 md:grid-cols-[1fr_1.15fr]">
          <div className="space-y-5 border-b border-white/10 p-6 md:border-b-0 md:border-r">
            <div>
              <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-white/40">Request</p>
              <div className="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 text-[15px] text-white/90">
                Refund 25 dollars on order 8820 because it arrived broken
              </div>
            </div>
            <div className="space-y-2.5">
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-white/40">Pipeline</p>
              {stages.map((s) => (
                <div key={s.n} className="flex items-center gap-3 rounded-lg border border-white/[0.07] bg-white/[0.03] px-3.5 py-2.5">
                  <span className="font-mono text-[11px] text-white/35">{s.n}</span>
                  <span className="text-sm text-white/85">{s.label}</span>
                  <span className="ml-auto text-xs text-white/45">{s.detail}</span>
                  <CheckCircle2 className="h-4 w-4 text-[hsl(156_60%_55%)]" />
                </div>
              ))}
            </div>
          </div>
          <div className="p-6">
            <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-white/40">Response</p>
            <ResultJson />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const demoHref = DEMO_MODE ? '/auth/login?demo=1' : '/auth/login';

  return (
    <div className="min-h-screen overflow-x-hidden bg-background">
      <LandingNav />
      <main>
        {/* ── Hero ───────────────────────────────────────────── */}
        <section className="relative isolate pt-36 pb-24">
          <div
            className="absolute inset-0 -z-10 opacity-[0.55] dark:opacity-30"
            style={{
              backgroundImage:
                'linear-gradient(hsl(var(--border)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--border)) 1px, transparent 1px)',
              backgroundSize: '56px 56px',
              maskImage: 'radial-gradient(ellipse 70% 55% at 50% 0%, black 30%, transparent 75%)',
              WebkitMaskImage: 'radial-gradient(ellipse 70% 55% at 50% 0%, black 30%, transparent 75%)',
            }}
          />
          <div className="absolute left-1/2 top-0 -z-10 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-primary/20 blur-[140px]" />

          <div className="mx-auto max-w-4xl px-6 text-center">
            <Link
              href="#results"
              className="group inline-flex items-center gap-2 rounded-full border border-border/70 bg-card/70 px-3.5 py-1.5 text-xs font-medium text-muted-foreground shadow-xs backdrop-blur transition-colors hover:text-foreground"
            >
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-primary">Hit@1 0.822</span>
              Measured on a 180-query held-out benchmark
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>

            <h1 className="mt-8 font-display text-5xl font-bold leading-[1.04] tracking-[-0.035em] text-foreground sm:text-6xl md:text-7xl">
              Turn a sentence into a
              <br />
              <span className="bg-brand-gradient bg-clip-text text-transparent">validated API call</span>
            </h1>

            <p className="mx-auto mt-7 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
              NLPForge picks the right endpoint from your API catalogue with vector retrieval, then
              extracts a request body that validates against that endpoint&apos;s JSON Schema.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg" className="h-12 gap-2 rounded-full px-7 text-[15px] shadow-glow">
                <Link href={demoHref}>
                  Try the live demo <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="h-12 gap-2 rounded-full bg-card/60 px-7 text-[15px] backdrop-blur">
                <a href={REPO_URL} target="_blank" rel="noreferrer">
                  <Github className="h-4 w-4" /> View source
                </a>
              </Button>
            </div>
          </div>

          <div className="mt-20 px-6">
            <ProductWindow />
          </div>

          <div className="mx-auto mt-16 flex max-w-4xl flex-wrap items-center justify-center gap-x-8 gap-y-3 px-6 text-sm text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground/70">Built with</span>
            {STACK.map((t) => (
              <span key={t} className="font-medium">{t}</span>
            ))}
          </div>
        </section>

        {/* ── How it works ───────────────────────────────────── */}
        <section id="how" className="border-t border-border/60 bg-surface-1/60 py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold text-primary">How it works</p>
              <h2 className="mt-3 font-display text-4xl font-bold tracking-tight">Three stages, one request, one endpoint</h2>
              <p className="mt-4 text-lg text-muted-foreground">
                There is no planning loop and no tool chain, just a routing problem precise enough to measure.
              </p>
            </div>
            <div className="relative mt-14 grid gap-6 md:grid-cols-3">
              <div className="absolute left-0 right-0 top-[38px] hidden h-px bg-gradient-to-r from-transparent via-border to-transparent md:block" />
              {STAGES.map((s, i) => (
                <div key={s.title} className="relative rounded-2xl border border-border/70 bg-card p-7 shadow-xs transition-shadow hover:shadow-md">
                  <div className="flex items-center justify-between">
                    <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-gradient text-white shadow-glow">
                      <s.icon className="h-5 w-5" />
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">0{i + 1}</span>
                  </div>
                  <h3 className="mt-6 text-xl font-semibold">{s.title}</h3>
                  <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">{s.body}</p>
                  <p className="mt-5 inline-flex rounded-md bg-muted px-2.5 py-1 font-mono text-xs text-muted-foreground">{s.meta}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Benchmark ──────────────────────────────────────── */}
        <section id="results" className="py-28">
          <div className="mx-auto grid max-w-6xl gap-14 px-6 lg:grid-cols-[1fr_1.2fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold text-primary">Measured, not asserted</p>
              <h2 className="mt-3 font-display text-4xl font-bold tracking-tight">Every design choice is a benchmark result</h2>
              <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
                180 held-out queries against 20 API templates, with sibling endpoints included as hard
                negatives. The correct template is in the top-25 for every query, so all remaining error
                is ranking. That&apos;s why the reranker that measured worse ships disabled.
              </p>
              <div className="mt-8 grid grid-cols-3 gap-4">
                {[
                  ['1.000', 'Recall@25'],
                  ['0.822', 'Hit@1'],
                  ['0.983', 'Hit@3'],
                ].map(([v, l]) => (
                  <div key={l} className="rounded-xl border border-border/70 bg-card p-4 shadow-xs">
                    <p className="font-display text-2xl font-semibold tabular-nums">{v}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{l}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-border/70 bg-card p-7 shadow-md">
              <div className="mb-6 flex items-baseline justify-between">
                <h3 className="font-semibold">Hit@1 by ranking strategy</h3>
                <span className="text-xs text-muted-foreground">n = 180</span>
              </div>
              <div className="space-y-5">
                {RESULTS.map((r) => (
                  <div key={r.label}>
                    <div className="mb-1.5 flex items-baseline justify-between gap-4 text-sm">
                      <span className={r.best ? 'font-semibold text-foreground' : 'text-foreground/85'}>{r.label}</span>
                      <span className="font-mono tabular-nums">{r.value.toFixed(3)}</span>
                    </div>
                    <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                      <div
                        className={r.best ? 'h-full rounded-full bg-brand-gradient' : 'h-full rounded-full bg-foreground/20'}
                        style={{ width: `${r.value * 100}%` }}
                      />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{r.note}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Engineering ────────────────────────────────────── */}
        <section className="border-t border-border/60 bg-surface-1/60 py-28">
          <div className="mx-auto max-w-6xl px-6">
            <p className="text-sm font-semibold text-primary">Engineering</p>
            <h2 className="mt-3 max-w-2xl font-display text-4xl font-bold tracking-tight">Built like a production service</h2>
            <div className="mt-12 grid gap-5 sm:grid-cols-2">
              {HIGHLIGHTS.map((h) => (
                <div key={h.title} className="group flex gap-5 rounded-2xl border border-border/70 bg-card p-7 shadow-xs transition-all hover:-translate-y-0.5 hover:shadow-md">
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <h.icon className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="text-lg font-semibold">{h.title}</h3>
                    <p className="mt-1.5 text-[15px] leading-relaxed text-muted-foreground">{h.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Closing CTA ────────────────────────────────────── */}
        <section className="px-6 py-24">
          <div className="relative mx-auto max-w-5xl overflow-hidden rounded-3xl bg-[hsl(236_30%_9%)] px-8 py-16 text-center shadow-xl md:px-16">
            <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-primary/40 blur-[100px]" />
            <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-brand-2/40 blur-[100px]" />
            <h2 className="relative font-display text-4xl font-bold tracking-tight text-white">See it route a request</h2>
            <p className="relative mx-auto mt-4 max-w-xl text-lg text-white/65">
              The demo tenant ships with 20 API templates already indexed. Sign in with one click and try your own phrasing.
            </p>
            <div className="relative mt-9 flex flex-wrap justify-center gap-3">
              <Button asChild size="lg" className="h-12 gap-2 rounded-full bg-white px-7 text-[15px] text-[hsl(236_30%_12%)] hover:bg-white/90">
                <Link href={demoHref}>
                  Open the demo <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="h-12 rounded-full border-white/20 bg-transparent px-7 text-[15px] text-white hover:bg-white/10 hover:text-white">
                <Link href="/docs">Read the docs</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
      <LandingFooter />
    </div>
  );
}
