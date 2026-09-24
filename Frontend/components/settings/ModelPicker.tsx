"use client"

/**
 * Searchable picker over live catalogue models.
 *
 * Providers list anywhere from 2 (a local Ollama) to ~500 (OpenRouter) models,
 * so this is a filterable listbox, not a <select>. Each row carries what a user
 * needs to choose: where it runs, whether it is free, context size, and whether
 * the provider is phasing it out.
 */

import { useMemo, useState } from 'react'
import { AlertTriangle, Loader2, RefreshCw, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { CatalogModel } from '@/lib/api-types'

const RENDER_LIMIT = 150

export function formatContext(tokens?: number | null): string | null {
  if (!tokens) return null
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(tokens % 1_000_000 ? 1 : 0)}M context`
  if (tokens >= 1000) return `${Math.round(tokens / 1000)}K context`
  return `${tokens} context`
}

export function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export function ModelStatusBadges({ model }: { model: CatalogModel }) {
  return (
    <>
      {model.is_local && <Badge variant="info">Local</Badge>}
      {model.is_free && !model.is_local && <Badge variant="success">Free</Badge>}
      {model.is_new && <Badge variant="default">New</Badge>}
      {model.kind === 'embedding' && (
        <Badge variant="outline">{model.dimension ? `${model.dimension}-dim` : 'dimension unknown'}</Badge>
      )}
      {model.status === 'deprecated' && (
        <Badge variant="warning" title={model.status_reason ?? undefined}>Deprecated</Badge>
      )}
      {model.status === 'retired' && (
        <Badge variant="destructive" title={model.status_reason ?? undefined}>Retired</Badge>
      )}
      {model.shutdown_date && model.status !== 'retired' && (
        <Badge variant="warning">Shuts down {formatShortDate(model.shutdown_date)}</Badge>
      )}
    </>
  )
}

interface ModelPickerProps {
  models: CatalogModel[]
  value: string
  onChange: (modelId: string) => void
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  /** Shown instead of the list when the provider cannot be listed yet (e.g. no key typed). */
  placeholder?: string
}

export function ModelPicker({ models, value, onChange, loading, error, onRetry, placeholder }: ModelPickerProps) {
  const [search, setSearch] = useState('')
  const [freeOnly, setFreeOnly] = useState(false)
  const [manual, setManual] = useState(false)

  const hasFree = models.some(m => m.is_free && !m.is_local)
  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return models
      .filter(m => !freeOnly || m.is_free)
      .filter(m => !needle || m.model_id.toLowerCase().includes(needle) || m.display_name.toLowerCase().includes(needle))
      // Active first, then new, then alphabetical.
      .sort((a, b) =>
        Number(a.status !== 'active') - Number(b.status !== 'active') ||
        Number(!!b.is_new) - Number(!!a.is_new) ||
        a.display_name.localeCompare(b.display_name)
      )
  }, [models, search, freeOnly])

  const selectedIsListed = models.some(m => m.model_id === value)

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-border/60 p-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Asking the provider which models it serves…
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm" role="alert">
        <p className="flex items-start gap-2 text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
        </p>
        <div className="flex gap-2">
          {onRetry && (
            <Button type="button" variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="mr-2 h-3.5 w-3.5" /> Try again
            </Button>
          )}
          <Button type="button" variant="ghost" size="sm" onClick={() => setManual(true)}>
            Enter a model id instead
          </Button>
        </div>
        {manual && <ManualEntry value={value} onChange={onChange} />}
      </div>
    )
  }

  if (!models.length) {
    return (
      <div className="space-y-3 rounded-xl border border-dashed border-border/60 p-4 text-sm text-muted-foreground">
        <p>{placeholder ?? 'This provider listed no chat models.'}</p>
        <ManualEntry value={value} onChange={onChange} />
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${models.length} model${models.length === 1 ? '' : 's'}`}
            className="h-10 rounded-xl pl-9"
            aria-label="Search models"
          />
        </div>
        {hasFree && (
          <Button
            type="button"
            variant={freeOnly ? 'default' : 'outline'}
            size="sm"
            className="h-10 rounded-xl"
            aria-pressed={freeOnly}
            onClick={() => setFreeOnly(!freeOnly)}
          >
            Free only
          </Button>
        )}
      </div>

      <div role="listbox" aria-label="Models" className="max-h-72 overflow-y-auto rounded-xl border border-border/60">
        {filtered.slice(0, RENDER_LIMIT).map((model) => {
          const selected = model.model_id === value
          const context = formatContext(model.context_tokens)
          return (
            <button
              key={model.model_id}
              type="button"
              role="option"
              aria-selected={selected}
              onClick={() => onChange(model.model_id)}
              className={cn(
                'flex w-full flex-col items-start gap-1 border-b border-border/40 px-3 py-2.5 text-left last:border-b-0',
                'transition-colors hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:outline-none',
                selected && 'bg-primary/10 hover:bg-primary/10'
              )}
            >
              <div className="flex w-full flex-wrap items-center gap-1.5">
                <span className="font-medium">{model.display_name}</span>
                <ModelStatusBadges model={model} />
              </div>
              <div className="flex w-full flex-wrap items-center gap-x-3 text-xs text-muted-foreground">
                <span className="font-mono">{model.model_id}</span>
                {context && <span>{context}</span>}
              </div>
              {model.status !== 'active' && model.status_reason && (
                <span className="text-xs text-warning">{model.status_reason}</span>
              )}
            </button>
          )
        })}
        {filtered.length === 0 && (
          <p className="p-4 text-sm text-muted-foreground">No models match “{search}”.</p>
        )}
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
        <span>
          {filtered.length > RENDER_LIMIT
            ? `Showing ${RENDER_LIMIT} of ${filtered.length}. Search to narrow the list.`
            : `${filtered.length} model${filtered.length === 1 ? '' : 's'}`}
        </span>
        <button type="button" className="text-primary hover:underline" onClick={() => setManual(!manual)}>
          {manual ? 'Hide manual entry' : 'Model not listed?'}
        </button>
      </div>
      {(manual || (value && !selectedIsListed)) && <ManualEntry value={value} onChange={onChange} />}
    </div>
  )
}

function ManualEntry({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-1">
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Exact model id, e.g. llama3.2:3b"
        className="h-10 rounded-xl font-mono text-sm"
        aria-label="Model id"
      />
      <p className="text-xs text-muted-foreground">Use the id exactly as the provider spells it.</p>
    </div>
  )
}
