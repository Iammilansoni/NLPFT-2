"use client"

/**
 * Settings -> Model catalogue.
 *
 * Every model the user's providers serve, straight from the live catalogue:
 * sync health per provider, a manual "sync now", and a browsable list with the
 * lifecycle state (new / deprecated / retired / shutting down) of each model.
 */

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Boxes, CheckCircle2, Loader2, RefreshCw, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { CatalogModel, CatalogSource, ModelCatalogSyncResult } from '@/lib/api-types'
import { ModelStatusBadges, formatContext } from '@/components/settings/ModelPicker'

const RENDER_LIMIT = 200

function timeAgo(iso: string | null): string {
  if (!iso) return 'never'
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.round(seconds / 60)} min ago`
  if (seconds < 86400) return `${Math.round(seconds / 3600)} h ago`
  return `${Math.round(seconds / 86400)} d ago`
}

function describeInterval(minutes: number): string {
  return minutes % 60 === 0 ? `${minutes / 60} hour${minutes === 60 ? '' : 's'}` : `${minutes} minutes`
}

/** What the user can do about a failed sync. */
function fixFor(source: CatalogSource): string | null {
  switch (source.last_error_code) {
    case 'AUTH':
      return source.scope === 'yours'
        ? 'Update the key on this connection in AI Providers.'
        : 'The deployment key is set on the server (environment variable). Ask the admin to update it.'
    case 'UNREACHABLE':
      return 'Check that the server is running and the URL is right. The next sync will retry.'
    case 'RATE_LIMITED':
      return 'Nothing to do. The next sync will retry.'
    default:
      return null
  }
}

function summarize(results: ModelCatalogSyncResult[]): string {
  const failed = results.filter(r => !r.ok)
  const changes = results
    .filter(r => r.ok && (r.added || r.deprecated || r.retired || r.deleted))
    .map(r => {
      const parts = [
        r.added && `${r.added} new`,
        r.deprecated && `${r.deprecated} deprecated`,
        r.retired && `${r.retired} retired`,
        r.deleted && `${r.deleted} removed`,
      ].filter(Boolean)
      return `${r.provider_label}: ${parts.join(', ')}`
    })
  const parts = [changes.length ? changes.join('. ') : 'No changes since the last sync.']
  failed.forEach(r => parts.push(r.error ?? `${r.provider_label} could not be synced.`))
  return parts.join(' ')
}

export function ModelCatalogPanel() {
  const queryClient = useQueryClient()
  const [kind, setKind] = useState<'llm' | 'embedding'>('llm')
  const [provider, setProvider] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [showRetired, setShowRetired] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['model-catalog', 'all', showRetired],
    queryFn: () => apiClient.getModelCatalog({ includeRetired: showRetired }),
    staleTime: 30 * 1000,
  })

  const sync = useMutation({
    mutationFn: () => apiClient.syncModelCatalog(),
    onSuccess: ({ results }) => {
      queryClient.invalidateQueries({ queryKey: ['model-catalog'] })
      toast({
        title: results.every(r => r.ok) ? 'Catalogue up to date' : 'Synced with problems',
        description: summarize(results),
        variant: results.every(r => r.ok) ? undefined : 'destructive',
      })
    },
    onError: (err: any) => {
      toast({ title: 'Sync failed', description: err?.detail || 'Could not reach the server.', variant: 'destructive' })
    },
  })

  const models = useMemo(() => data?.models ?? [], [data])
  const providers = useMemo(
    () => Array.from(new Map(models.map(m => [m.provider, m.provider_label ?? m.provider])).entries()),
    [models]
  )
  const visible = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return models
      .filter(m => m.kind === kind)
      .filter(m => provider === 'all' || m.provider === provider)
      .filter(m => !needle || m.model_id.toLowerCase().includes(needle) || m.display_name.toLowerCase().includes(needle))
      .sort((a, b) =>
        Number(!!b.is_new) - Number(!!a.is_new) ||
        a.provider.localeCompare(b.provider) ||
        a.display_name.localeCompare(b.display_name)
      )
  }, [models, kind, provider, search])

  const stats = useMemo(() => ({
    llm: models.filter(m => m.kind === 'llm').length,
    embedding: models.filter(m => m.kind === 'embedding').length,
    free: models.filter(m => m.is_free).length,
    fresh: models.filter(m => m.is_new).length,
    phasingOut: models.filter(m => m.status !== 'active' || m.shutdown_date).length,
  }), [models])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-3 py-20 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading the model catalogue…
      </div>
    )
  }
  if (error || !data) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive" role="alert">
        Could not load the model catalogue. Check that the backend is running.
      </div>
    )
  }

  const { policy } = data

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-2xl border border-border/40 bg-card/80 shadow-sm backdrop-blur-xl">
        <header className="flex flex-col gap-4 border-b border-border/40 bg-gradient-to-r from-muted/30 to-transparent px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-gradient-to-br from-primary to-brand-2 p-3 shadow-lg shadow-primary/20">
              <Boxes className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Model catalogue</h2>
              <p className="text-sm text-muted-foreground">
                Listed live from each provider and re-checked every {describeInterval(policy.sync_interval_minutes)}.
              </p>
            </div>
          </div>
          <Button onClick={() => sync.mutate()} disabled={sync.isPending} className="h-11 gap-2 rounded-xl">
            {sync.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Sync now
          </Button>
        </header>

        <div className="grid grid-cols-2 gap-3 p-6 sm:grid-cols-5">
          {[
            ['Chat models', stats.llm],
            ['Embedding models', stats.embedding],
            ['Free to use', stats.free],
            [`New (last ${policy.new_badge_days} days)`, stats.fresh],
            ['Being phased out', stats.phasingOut],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl border border-border/40 bg-muted/20 p-4">
              <p className="text-2xl font-bold tabular-nums text-foreground">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
            </div>
          ))}
        </div>

        <div className="border-t border-border/40 px-6 py-5">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Providers</h3>
          {data.sources.length === 0 ? (
            <p className="text-sm text-muted-foreground">No provider has been synced yet. Press “Sync now”.</p>
          ) : (
            <ul className="divide-y divide-border/40 rounded-xl border border-border/40">
              {data.sources.map((source) => {
                const failing = !!source.last_error && (!source.last_success_at || (source.last_attempt_at ?? '') > source.last_success_at)
                const fix = failing ? fixFor(source) : null
                return (
                  <li key={`${source.scope}-${source.provider}`} className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex items-start gap-3">
                      {failing
                        ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" aria-label="Sync failing" />
                        : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-label="Sync healthy" />}
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {source.provider_label}
                          <span className="ml-2 text-xs font-normal text-muted-foreground">
                            {source.scope === 'yours' ? 'your key' : 'shared'}
                          </span>
                        </p>
                        {failing && (
                          <p className="text-xs text-destructive">
                            {source.last_error} {fix}
                          </p>
                        )}
                      </div>
                    </div>
                    <p className="pl-7 text-xs text-muted-foreground sm:pl-0 sm:text-right">
                      {source.model_count} models · synced {timeAgo(source.last_success_at)}
                    </p>
                  </li>
                )
              })}
            </ul>
          )}
          <p className="mt-3 text-xs text-muted-foreground">
            When a provider stops listing a model it is marked <strong>deprecated</strong>. After{' '}
            {policy.retire_grace_hours} hours it is <strong>retired</strong> and hidden from pickers, and{' '}
            {policy.retired_retention_days} days later it is removed, unless a connection or dataset still uses it.
            A provider that can&apos;t be reached changes nothing.
          </p>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-border/40 bg-card/80 shadow-sm backdrop-blur-xl">
        <div className="flex flex-col gap-3 border-b border-border/40 px-6 py-4 lg:flex-row lg:items-center">
          <div role="tablist" aria-label="Model type" className="flex rounded-xl bg-muted/40 p-1">
            {(['llm', 'embedding'] as const).map((k) => (
              <button
                key={k}
                role="tab"
                aria-selected={kind === k}
                onClick={() => setKind(k)}
                className={cn(
                  'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                  kind === k ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {k === 'llm' ? `Chat (${stats.llm})` : `Embedding (${stats.embedding})`}
              </button>
            ))}
          </div>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            aria-label="Filter by provider"
            className="h-10 rounded-xl border border-input bg-background px-3 text-sm"
          >
            <option value="all">All providers</option>
            {providers.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search models"
              className="h-10 rounded-xl pl-9"
              aria-label="Search models"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input type="checkbox" checked={showRetired} onChange={(e) => setShowRetired(e.target.checked)} className="h-4 w-4 rounded" />
            Show retired
          </label>
        </div>

        <ul className="max-h-[560px] divide-y divide-border/40 overflow-y-auto">
          {visible.slice(0, RENDER_LIMIT).map((model: CatalogModel) => (
            <li key={`${model.provider}/${model.model_id}`} className="px-6 py-3">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-medium text-foreground">{model.display_name}</span>
                <ModelStatusBadges model={model} />
              </div>
              <div className="mt-0.5 flex flex-wrap gap-x-3 text-xs text-muted-foreground">
                <span>{model.provider_label}</span>
                <span className="font-mono">{model.model_id}</span>
                {formatContext(model.context_tokens) && <span>{formatContext(model.context_tokens)}</span>}
                {!model.shared && <span>found with your key</span>}
              </div>
              {model.status !== 'active' && model.status_reason && (
                <p className="mt-1 text-xs text-warning">{model.status_reason}</p>
              )}
            </li>
          ))}
          {visible.length === 0 && (
            <li className="px-6 py-10 text-center text-sm text-muted-foreground">
              {kind === 'embedding' && !search
                ? 'No embedding models listed. Pull one into Ollama (e.g. nomic-embed-text) or connect a provider that offers them.'
                : 'No models match these filters.'}
            </li>
          )}
        </ul>
        {visible.length > RENDER_LIMIT && (
          <p className="border-t border-border/40 px-6 py-3 text-xs text-muted-foreground">
            Showing {RENDER_LIMIT} of {visible.length}. Search or filter to narrow the list.
          </p>
        )}
      </section>
    </div>
  )
}

export default ModelCatalogPanel
