'use client'

import { useState } from 'react'
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  ChevronDown,
  Cpu,
  Database,
  FileJson,
  Layers,
  ListOrdered,
  Maximize2,
  Sparkles,
  XCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useQueryStats } from '@/hooks/useQuery'
import { useTemplateStats } from '@/hooks/useTemplates'
import { apiClient } from '@/lib/api'
import type { EmbeddingGroup, MismatchOption, SemanticRetrieveResponse } from '@/lib/api-types'
import { ModelMismatchPanel } from '@/components/embeddings/ModelMismatchPanel'
import { useToast } from '@/hooks/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { JsonDisplay } from '@/components/ui/JsonDisplay'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { SearchSection } from '@/components/dashboard/SearchSection'
import { MetricCard } from '@/components/dashboard/MetricCard'
import { MetricGridSkeleton } from '@/components/ui/skeleton'
import { OnboardingTour } from '@/components/onboarding/OnboardingTour'
import { cn } from '@/lib/utils'

// Requests against the seeded demo catalogue (Backend/app/demo_catalogue.py).
const EXAMPLES = [
  'Refund 25 dollars on order 8820 because it arrived broken',
  'I forgot my password, send me a reset link for sam@acme.io',
  'Log me in as priya@corp.dev with password hunter22',
  'Change my password from oldpass1 to NewPass#9',
]

const METHOD_STYLES: Record<string, string> = {
  GET: 'bg-info/10 text-info',
  POST: 'bg-success/10 text-success',
  PUT: 'bg-warning/10 text-warning',
  PATCH: 'bg-warning/10 text-warning',
  DELETE: 'bg-destructive/10 text-destructive',
}

function MethodBadge({ method }: { method?: string }) {
  const m = (method || 'POST').toUpperCase()
  return (
    <span className={cn('px-2 py-0.5 rounded text-xs font-bold font-mono', METHOD_STYLES[m] || 'bg-muted')}>
      {m}
    </span>
  )
}

function ms(value?: number) {
  if (value === undefined || value === null) return '—'
  return value >= 1000 ? `${(value / 1000).toFixed(1)} s` : `${Math.round(value)} ms`
}

function StageCard({ step, title, icon, status, lines }: {
  step: number
  title: string
  icon: React.ReactNode
  status: 'ok' | 'warn' | 'fail'
  lines: React.ReactNode[]
}) {
  const ring = { ok: 'border-success/30', warn: 'border-warning/40', fail: 'border-destructive/40' }[status]
  return (
    <div className={cn('rounded-xl border bg-card p-4 space-y-2', ring)}>
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-muted-foreground">STAGE {step}</span>
        <span className="ml-auto">
          {status === 'ok' && <CheckCircle2 className="w-4 h-4 text-success" />}
          {status === 'warn' && <AlertTriangle className="w-4 h-4 text-warning" />}
          {status === 'fail' && <XCircle className="w-4 h-4 text-destructive" />}
        </span>
      </div>
      <div className="flex items-center gap-2 font-semibold">
        {icon}
        {title}
      </div>
      <div className="space-y-0.5 text-sm text-muted-foreground">
        {lines.map((l, i) => <div key={i}>{l}</div>)}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { toast } = useToast()
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<SemanticRetrieveResponse | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  // Datasets embedded with another model than the one this user searches with.
  const [mismatch, setMismatch] = useState<{
    message: string
    options: MismatchOption[]
    excluded?: EmbeddingGroup[]
    blocking: boolean
  } | null>(null)
  const [showStage1, setShowStage1] = useState(false)

  const { data: stats, isLoading, error } = useQueryStats()
  const { data: templateStats, isLoading: templatesLoading } = useTemplateStats()

  async function runSearch(override?: string) {
    const q = (override ?? query).trim()
    if (!q) return
    setIsSearching(true)
    setSearchError(null)
    setMismatch(null)
    setShowStage1(false)
    try {
      const res = await apiClient.semanticRetrieve(q, 25, undefined, true, true)
      if (!res.success) {
        setResult(null)
        if (res.error === 'MODEL_MISMATCH' && res.options?.length) {
          setMismatch({ message: res.message ?? '', options: res.options, excluded: res.metadata?.excluded_datasets, blocking: true })
        } else {
          setSearchError(res.message || res.error || 'No route found for this request.')
        }
        return
      }
      setResult(res)
      const excluded = res.metadata?.excluded_datasets ?? []
      if (excluded.length && res.options?.length) {
        const count = excluded.reduce((n, g) => n + g.datasets.length, 0)
        setMismatch({
          message: `${count} dataset(s) were not searched because they were embedded with a different model than yours (${res.metadata.embedding?.label}).`,
          options: res.options,
          excluded,
          blocking: false,
        })
      }
    } catch (err: any) {
      const message = err?.detail?.message || err?.detail || err?.message || 'Request failed'
      setResult(null)
      setSearchError(typeof message === 'string' ? message : 'Request failed')
      toast({ title: 'Routing failed', description: String(message), variant: 'destructive' })
    } finally {
      setIsSearching(false)
    }
  }

  const out = result?.final_output
  const extraction = result?.extraction
  const ranking = result?.ranking
  const timings = result?.metadata?.timings_ms
  const body = extraction?.values ?? result?.extracted_request_body ?? {}
  const extractionStatus: 'ok' | 'warn' | 'fail' = !extraction
    ? 'warn'
    : extraction.ok
      ? 'ok'
      : extraction.degraded ? 'fail' : 'warn'

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      <div className="max-w-6xl mx-auto p-6 md:p-8 space-y-8">
        <DashboardHeader systemStatus={!error && stats ? 'healthy' : 'degraded'} />

        <section className="py-4" data-tour="search">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-semibold tracking-tight mb-2">Route a request</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Describe an API call in plain English. NLPForge picks the endpoint from your template
              catalogue and extracts a request body that validates against its JSON Schema.
            </p>
          </div>
          <SearchSection
            query={query}
            setQuery={setQuery}
            onSearch={runSearch}
            isSearching={isSearching}
            examples={result || isSearching ? [] : EXAMPLES}
          />
        </section>

        {isSearching && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-pulse" aria-live="polite">
            {['Embedding & vector recall', 'Ranking templates', 'Extracting request body'].map((t) => (
              <div key={t} className="rounded-xl border border-border/60 bg-muted/20 p-4 h-28">
                <div className="h-3 w-20 bg-muted rounded mb-3" />
                <div className="text-sm text-muted-foreground">{t}…</div>
              </div>
            ))}
          </div>
        )}

        {mismatch && !isSearching && (
          <ModelMismatchPanel
            message={mismatch.message}
            options={mismatch.options}
            excluded={mismatch.excluded}
            variant={mismatch.blocking ? 'error' : 'notice'}
            onResolved={(how) => {
              setMismatch(null)
              if (how === 'switched') runSearch()
            }}
          />
        )}

        {searchError && !isSearching && (
          <div className="p-4 bg-warning/5 border border-warning/30 rounded-xl flex items-start gap-3 text-warning dark:text-warning">
            <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0" />
            <p className="text-sm font-medium">{searchError}</p>
          </div>
        )}

        {result && out && !isSearching && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            {/* Resolved call */}
            <div className="rounded-2xl border border-success/25 bg-gradient-to-br from-success/5 to-transparent p-6">
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <span className="px-3 py-1 rounded-full bg-success/10 text-success border border-success/20 text-xs font-semibold uppercase tracking-wider">
                  Routed to
                </span>
                <span className="text-sm text-muted-foreground">
                  match score {(out.confidence_score * 100).toFixed(1)}%
                </span>
                {result.degraded && (
                  <span className="px-2 py-0.5 rounded-full bg-warning/10 text-warning text-xs font-medium">
                    degraded
                  </span>
                )}
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="ml-auto">
                      <Maximize2 className="w-4 h-4 mr-2" /> Full response
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-5xl max-h-[85vh] overflow-hidden flex flex-col">
                    <DialogHeader>
                      <DialogTitle>POST /api/v1/query/semantic-search</DialogTitle>
                    </DialogHeader>
                    <div className="flex-1 overflow-hidden">
                      <JsonDisplay data={result} maxHeight="calc(85vh - 120px)" showCopyButton showLineNumbers />
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              <h3 className="text-2xl font-bold tracking-tight">{out.api_name}</h3>
              <div className="mt-3 p-3 rounded-lg bg-muted/40 border border-border/50 font-mono text-sm break-all flex items-center gap-3">
                <MethodBadge method={out.method} />
                <span>
                  <span className="text-muted-foreground">{out.effective_base_url || out.base_url}</span>
                  {out.endpoint}
                </span>
              </div>
            </div>

            {/* Pipeline */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StageCard
                step={1}
                title="Vector recall"
                icon={<Brain className="w-4 h-4 text-primary" />}
                status="ok"
                lines={[
                  `${result.stage1_vector_search.length} utterances · pgvector HNSW`,
                  result.metadata.embedding?.label ?? `${result.metadata.embedding_model} (${result.metadata.embedding_dimension}-dim)`,
                  `embed ${ms(timings?.embed)} · search ${ms(timings?.vector_search)}`,
                ]}
              />
              <StageCard
                step={2}
                title="Template ranking"
                icon={<ListOrdered className="w-4 h-4 text-primary" />}
                status={ranking?.degraded ? 'warn' : 'ok'}
                lines={[
                  ranking?.strategy === 'cross_encoder' ? 'Cross-encoder + max-pool' : 'Max-pool per template',
                  `${result.stage2_reranking.length} candidate templates`,
                  ranking?.degraded ? `fallback: ${ranking.degraded_reason}` : `rank ${ms(timings?.ranking)}`,
                ]}
              />
              <StageCard
                step={3}
                title="Structured extraction"
                icon={<Sparkles className="w-4 h-4 text-primary" />}
                status={extractionStatus}
                lines={[
                  extraction?.ok
                    ? `${Object.keys(body).length} fields · schema-valid`
                    : extraction?.missing_required?.length
                      ? `missing required: ${extraction.missing_required.join(', ')}`
                      : extraction?.reason || 'not run',
                  `${extraction?.model ?? '—'} · ${extraction?.attempts ?? 0} attempt(s)`,
                  `extract ${ms(extraction?.latency_ms)}`,
                ]}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Extracted body */}
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <FileJson className="w-4 h-4 text-primary" /> Extracted request body
                </h4>
                <JsonDisplay data={body} maxHeight="18rem" showCopyButton />
                {extraction && !extraction.ok && (
                  <p className="text-xs text-muted-foreground">
                    {extraction.degraded
                      ? 'The extraction model was unavailable; the route above is still valid.'
                      : 'Values the request did not contain are reported, never invented.'}
                  </p>
                )}
              </div>

              {/* Candidates */}
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <ListOrdered className="w-4 h-4 text-primary" /> Candidate templates
                </h4>
                <div className="rounded-xl border border-border/60 overflow-hidden">
                  {result.stage2_reranking.map((c, i) => (
                    <div key={c.t_id} className={cn('px-4 py-3 border-b border-border/40 last:border-0', i === 0 && 'bg-primary/5')}>
                      <div className="flex items-center gap-3">
                        <span className={cn('w-6 h-6 rounded-full text-xs flex items-center justify-center font-bold shrink-0',
                          i === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}>
                          {c.rank}
                        </span>
                        <span className="font-medium truncate">{c.api_name}</span>
                        <span className="ml-auto font-mono text-sm tabular-nums">{c.ce_score.toFixed(3)}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 pl-9 truncate">
                        best match: “{c.best_utterance}”
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Stage 1 rows */}
            <div>
              <button
                onClick={() => setShowStage1(!showStage1)}
                className="w-full flex items-center justify-between p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 transition-colors"
              >
                <span className="flex items-center gap-2 font-semibold">
                  <Layers className="w-4 h-4 text-primary" /> Retrieved utterances (Stage 1)
                </span>
                <ChevronDown className={cn('w-5 h-5 text-muted-foreground transition-transform', showStage1 && 'rotate-180')} />
              </button>
              {showStage1 && (
                <div className="mt-2 rounded-xl border border-border/60 overflow-hidden">
                  {result.stage1_vector_search.map((r, i) => (
                    <div key={i} className="px-4 py-2.5 border-b border-border/40 last:border-0 flex items-center gap-3 text-sm">
                      <span className="flex-1">{r.query}</span>
                      <span className="text-xs text-muted-foreground hidden sm:inline">{r.api_name}</span>
                      <span className="font-mono text-primary tabular-nums">{r.similarity_score.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metrics */}
        {isLoading || templatesLoading ? (
          <MetricGridSkeleton count={4} />
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-4" data-tour="metrics">
            <MetricCard
              label="Indexed utterances"
              value={stats?.total_embeddings?.toLocaleString() ?? '0'}
              subtitle="Routable vectors in pgvector"
              icon={<Database className="w-5 h-5 text-white" />}
              gradient="from-primary to-brand-2"
            />
            <MetricCard
              label="API templates"
              value={templateStats?.total_templates ?? 0}
              subtitle="In your catalogue"
              icon={<CheckCircle2 className="w-5 h-5 text-white" />}
              gradient="from-success to-success"
            />
            <MetricCard
              label="APIs in datasets"
              value={stats?.unique_apis ?? 0}
              subtitle="From generated / uploaded data"
              icon={<Layers className="w-5 h-5 text-white" />}
              gradient="from-warning to-warning"
            />
            <MetricCard
              label="Embedding model"
              value={stats?.embedding?.model_id ?? stats?.model ?? '—'}
              subtitle={
                stats?.embedding
                  ? `${stats.embedding.provider_label} · ${stats.embedding.dimension}-dim${stats.embedding.is_default ? ' · default' : ''}`
                  : 'Change it in Settings'
              }
              icon={<Cpu className="w-5 h-5 text-white" />}
              gradient="from-brand-2 to-destructive"
            />
          </div>
        )}
      </div>

      <OnboardingTour tourId="dashboard" />
    </div>
  )
}
