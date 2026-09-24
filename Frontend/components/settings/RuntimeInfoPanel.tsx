'use client'

import { useQuery } from '@tanstack/react-query'
import { Cpu, Database, Layers, Loader2, ShieldCheck, ShieldAlert, Sparkles } from 'lucide-react'
import { getApiBase } from '@/lib/runtime-config'

interface RuntimeInfo {
  execution_mode: string
  embedder: { model: string; dimension: number }
  generation: string
  extraction_model?: string
  reranker_enabled?: boolean
  stage1_top_k?: number
  vector_backend: string
  rls_enforced: boolean | null
}

async function fetchRuntime(): Promise<RuntimeInfo> {
  const res = await fetch(`${getApiBase()}/api/v1/health`, { credentials: 'include' })
  if (!res.ok) throw new Error(`health ${res.status}`)
  const body = await res.json()
  return body.runtime as RuntimeInfo
}

function Row({ icon, label, value, hint }: {
  icon: React.ReactNode
  label: string
  value: React.ReactNode
  hint?: string
}) {
  return (
    <div className="flex items-start gap-4 py-4 border-b border-border/40 last:border-0">
      <div className="p-2 rounded-lg bg-primary/10 text-primary shrink-0">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="font-medium text-foreground break-words">{value}</p>
        {hint && <p className="text-xs text-muted-foreground mt-1">{hint}</p>}
      </div>
    </div>
  )
}

/**
 * Read-only view of how this deployment routes queries.
 *
 * The embedding model is a deployment setting (EXECUTION_MODE), not a per-user
 * preference: every indexed vector and every query must come from the same
 * model, so it is shown here rather than offered as a choice.
 */
export function RuntimeInfoPanel() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['runtime-info'],
    queryFn: fetchRuntime,
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground p-6">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading runtime configuration...
      </div>
    )
  }
  if (error || !data) {
    return <p className="p-6 text-sm text-destructive">Could not reach the API health endpoint.</p>
  }

  return (
    <div className="rounded-2xl border border-border/40 bg-card p-6">
      <h3 className="text-lg font-semibold">Routing pipeline</h3>
      <p className="text-sm text-muted-foreground mt-1">
        Configured per deployment. Changing the embedding model requires re-embedding every dataset.
      </p>
      <div className="mt-4">
        <Row
          icon={<Cpu className="h-4 w-4" />}
          label="Execution mode"
          value={data.execution_mode === 'local' ? 'Local (Ollama, fully offline)' : 'Cloud (in-process ONNX)'}
        />
        <Row
          icon={<Layers className="h-4 w-4" />}
          label="Stage 1 · Embedding model"
          value={`${data.embedder.model} · ${data.embedder.dimension}-dim`}
          hint={`Top-${data.stage1_top_k ?? 25} utterance recall from ${data.vector_backend} (HNSW)`}
        />
        <Row
          icon={<Sparkles className="h-4 w-4" />}
          label="Stage 2 · Ranking"
          value={data.reranker_enabled ? 'Cross-encoder rerank + max-pool' : 'Max-pool by template (cross-encoder off)'}
          hint="The cross-encoder is off by default: it measured worse on the routing benchmark."
        />
        <Row
          icon={<Sparkles className="h-4 w-4" />}
          label="Stage 3 · Extraction model"
          value={data.extraction_model ?? data.generation}
          hint="Schema-constrained decoding, Pydantic validation, one repair retry."
        />
        <Row
          icon={data.rls_enforced ? <ShieldCheck className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
          label="Database row-level security"
          value={data.rls_enforced ? 'Enforced for the application role' : 'Bypassed by the database role'}
          hint={
            data.rls_enforced
              ? undefined
              : 'The DB role is a superuser; tenant isolation comes from the explicit tenant filter in every vector query.'
          }
        />
        <Row
          icon={<Database className="h-4 w-4" />}
          label="Vector store"
          value={data.vector_backend}
        />
      </div>
    </div>
  )
}
