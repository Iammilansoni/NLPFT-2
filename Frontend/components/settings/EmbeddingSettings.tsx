"use client"

/**
 * Settings -> Embedding model.
 *
 * Every provider that offers embeddings is listed, whether or not a key exists
 * for it yet: bring your own key and its models become usable. Choosing a model
 * makes one real call (verifying key and model, measuring the vector width),
 * then shows which datasets need re-embedding to stay searchable.
 */

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ExternalLink, KeyRound, Layers, Loader2, RefreshCw, RotateCcw, Shuffle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ProviderIcon } from '@/components/ui/provider-icons'
import { ModelPicker } from '@/components/settings/ModelPicker'
import { apiErrorMessage } from '@/components/embeddings/ModelMismatchPanel'
import { toast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { EmbeddingGroup, EmbeddingSettingsResponse } from '@/lib/api-types'

interface EmbeddingSettingsProps {
  /** Open Settings -> AI Providers, where keys are added. */
  onOpenProviders: () => void
}

function countDatasets(groups: EmbeddingGroup[]): number {
  return groups.reduce((n, g) => n + g.datasets.length, 0)
}

export function EmbeddingSettings({ onOpenProviders }: EmbeddingSettingsProps) {
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['embedding-settings'],
    queryFn: () => apiClient.getEmbeddingSettings(),
  })
  const [providerId, setProviderId] = useState<string | null>(null)
  const [modelId, setModelId] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

  const selectedProvider = providerId ?? data?.active.provider ?? null
  const provider = data?.providers.find(p => p.id === selectedProvider)
  const canList = !!provider && (provider.connected || !provider.list_requires_key)

  // Catalogue first; a live listing (with the user's key or a public listing) when the catalogue has none yet.
  const catalogueModels = useMemo(
    () => (data?.models ?? []).filter(m => m.provider === selectedProvider),
    [data, selectedProvider]
  )
  const live = useQuery({
    queryKey: ['model-discovery', selectedProvider, 'embedding'],
    queryFn: () => apiClient.discoverModels({ provider: selectedProvider! }),
    enabled: !!selectedProvider && canList && catalogueModels.length === 0,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const models = catalogueModels.length
    ? catalogueModels
    : (live.data?.models ?? []).filter(m => m.kind === 'embedding')

  const refresh = (result: EmbeddingSettingsResponse) => {
    queryClient.setQueryData(['embedding-settings'], result)
    queryClient.invalidateQueries({ queryKey: ['datasets'] })
  }

  const choose = useMutation({
    mutationFn: ({ reembed }: { reembed: boolean }) =>
      apiClient.chooseEmbeddingModel(selectedProvider!, modelId).then(async result => {
        if (reembed && result.needs_reembed.length) await apiClient.reembedDatasets()
        return { result, reembed }
      }),
    onSuccess: ({ result, reembed }) => {
      refresh(result)
      setConfirmOpen(false)
      setModelId('')
      toast({
        title: 'Embedding model changed',
        description: reembed && result.needs_reembed.length
          ? `${result.message} Re-embedding ${result.needs_reembed.length} dataset(s) in the background.`
          : result.message,
      })
    },
    onError: (err) => {
      setConfirmOpen(false)
      toast({ title: 'Could not use that model', description: apiErrorMessage(err), variant: 'destructive' })
    },
  })

  const reset = useMutation({
    mutationFn: () => apiClient.resetEmbeddingModel(),
    onSuccess: (result) => {
      refresh(result)
      toast({ title: 'Back to the default', description: result.message })
    },
    onError: (err) => toast({ title: 'Reset failed', description: apiErrorMessage(err), variant: 'destructive' }),
  })

  const reembed = useMutation({
    mutationFn: (ids?: string[]) => apiClient.reembedDatasets(ids),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['embedding-settings'] })
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      toast({ title: 'Re-embedding started', description: `${result.message} Progress shows on the Datasets page.` })
    },
    onError: (err) => toast({ title: 'Re-embed failed', description: apiErrorMessage(err), variant: 'destructive' }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-3 py-20 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading embedding settings…
      </div>
    )
  }
  if (error || !data) {
    return (
      <div role="alert" className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
        Could not load embedding settings. {apiErrorMessage(error, 'Check that the backend is running.')}
      </div>
    )
  }

  const { active } = data
  const onActiveModel = data.groups.filter(g => g.matches_active)
  const pendingSwitch = modelId && !(selectedProvider === active.provider && modelId === active.model_id)

  return (
    <div className="space-y-6">
      {/* Active model */}
      <section className="overflow-hidden rounded-2xl border border-border/40 bg-card/80 shadow-sm backdrop-blur-xl">
        <header className="flex flex-col gap-4 border-b border-border/40 bg-gradient-to-r from-muted/30 to-transparent px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-gradient-to-br from-primary to-brand-2 p-3 shadow-lg shadow-primary/20">
              <Layers className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Embedding model</h2>
              <p className="text-sm text-muted-foreground">
                Turns your example requests and every search into vectors. Search only compares vectors from the same model.
              </p>
            </div>
          </div>
        </header>
        <div className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <ProviderIcon provider={active.provider} label={active.provider_label} size={32} />
            <div>
              <p className="font-semibold text-foreground">{active.model_id}</p>
              <p className="text-sm text-muted-foreground">
                {active.provider_label} · {active.dimension}-dimensional vectors
              </p>
            </div>
            {active.is_default && <Badge variant="outline">Deployment default</Badge>}
          </div>
          {!active.is_default && (
            <Button variant="outline" size="sm" onClick={() => reset.mutate()} disabled={reset.isPending} className="rounded-xl">
              {reset.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RotateCcw className="mr-2 h-4 w-4" />}
              Use the default ({data.deployment_default.model_id})
            </Button>
          )}
        </div>
      </section>

      {/* Datasets grouped by model */}
      <section className="overflow-hidden rounded-2xl border border-border/40 bg-card/80 shadow-sm">
        <div className="flex flex-col gap-2 border-b border-border/40 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="font-semibold text-foreground">Your datasets by embedding model</h3>
          {data.needs_reembed.length > 0 && (
            <Button size="sm" onClick={() => reembed.mutate(undefined)} disabled={reembed.isPending} className="rounded-xl">
              {reembed.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Re-embed {data.needs_reembed.length} dataset(s) with {active.model_id}
            </Button>
          )}
        </div>
        {data.groups.length === 0 ? (
          <p className="px-6 py-6 text-sm text-muted-foreground">No embedded datasets yet. Embed one from the Datasets page.</p>
        ) : (
          <ul className="divide-y divide-border/40">
            {data.groups.map(group => (
              <li key={`${group.provider}/${group.model_id}/${group.dimension}`} className="flex flex-col gap-3 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <ProviderIcon provider={group.provider} label={group.provider_label} size={18} />
                    <span className="font-medium text-foreground">{group.label}</span>
                    {group.matches_active
                      ? <Badge variant="success">Searchable</Badge>
                      : <Badge variant="warning">Not searched with your current model</Badge>}
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-foreground">
                    {group.datasets.map(d => d.name).join(', ')}
                  </p>
                </div>
                {!group.matches_active && (
                  <div className="flex shrink-0 flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-lg"
                      disabled={choose.isPending}
                      onClick={() => {
                        setProviderId(group.provider)
                        apiClient.chooseEmbeddingModel(group.provider, group.model_id)
                          .then(result => {
                            refresh(result)
                            toast({ title: 'Embedding model switched', description: result.message })
                          })
                          .catch(err => toast({ title: 'Could not switch', description: apiErrorMessage(err), variant: 'destructive' }))
                      }}
                    >
                      <Shuffle className="mr-2 h-3.5 w-3.5" /> Search with {group.model_id}
                    </Button>
                    <Button
                      size="sm"
                      className="rounded-lg"
                      disabled={reembed.isPending}
                      onClick={() => reembed.mutate(group.datasets.map(d => d.dataset_id))}
                    >
                      <RefreshCw className="mr-2 h-3.5 w-3.5" /> Re-embed with {active.model_id}
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Choose a model */}
      <section className="overflow-hidden rounded-2xl border border-border/40 bg-card/80 shadow-sm">
        <div className="border-b border-border/40 px-6 py-4">
          <h3 className="font-semibold text-foreground">Choose a model</h3>
          <p className="text-sm text-muted-foreground">
            Any provider below can be used. Local ones need nothing; hosted ones use your own API key.
          </p>
        </div>
        <div className="grid gap-2 p-6 sm:grid-cols-2 xl:grid-cols-3" role="radiogroup" aria-label="Embedding provider">
          {data.providers.map(p => (
            <button
              key={p.id}
              type="button"
              role="radio"
              aria-checked={selectedProvider === p.id}
              onClick={() => { setProviderId(p.id); setModelId('') }}
              className={cn(
                'flex items-start gap-3 rounded-xl border p-3 text-left transition-colors',
                selectedProvider === p.id ? 'border-primary bg-primary/5' : 'border-border/60 hover:bg-muted/40'
              )}
            >
              <ProviderIcon provider={p.id} label={p.label} size={22} className="mt-0.5" />
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-foreground">
                  {p.label}
                  {p.local && <Badge variant="info">Local</Badge>}
                  {p.free_tier && !p.local && <Badge variant="success">Free tier</Badge>}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {p.connected
                    ? p.credential_source === 'deployment' ? 'Ready (deployment key)' : 'Ready'
                    : 'Needs your API key'}
                </p>
              </div>
            </button>
          ))}
        </div>

        {provider && (
          <div className="space-y-4 border-t border-border/40 px-6 py-5">
            {!provider.connected && provider.requires_key && (
              <div className="flex flex-col gap-3 rounded-xl border border-dashed border-border/60 p-4 text-sm sm:flex-row sm:items-center sm:justify-between">
                <p className="flex items-start gap-2 text-muted-foreground">
                  <KeyRound className="mt-0.5 h-4 w-4 shrink-0" />
                  To embed with {provider.label}, add your API key as a connection first.
                  {!provider.list_requires_key && ' You can browse its models below meanwhile.'}
                </p>
                <div className="flex shrink-0 gap-2">
                  {provider.key_url && (
                    <a href={provider.key_url} target="_blank" rel="noopener noreferrer">
                      <Button variant="ghost" size="sm" className="rounded-lg">
                        Get a key <ExternalLink className="ml-1.5 h-3.5 w-3.5" />
                      </Button>
                    </a>
                  )}
                  <Button size="sm" onClick={onOpenProviders} className="rounded-lg">Add {provider.label} key</Button>
                </div>
              </div>
            )}

            {canList && (
              <ModelPicker
                models={models}
                value={modelId}
                onChange={setModelId}
                loading={live.isFetching && !models.length}
                error={live.data && !live.data.ok ? live.data.error ?? 'Listing models failed.' : null}
                onRetry={() => live.refetch()}
                placeholder={
                  provider.id === 'ollama'
                    ? 'No embedding models are pulled into Ollama. Run "ollama pull nomic-embed-text", or type a model id below.'
                    : `${provider.label} listed no embedding models. Type a model id below if you know one.`
                }
              />
            )}

            {pendingSwitch && (
              <div className="flex justify-end">
                <Button
                  onClick={() => (countDatasets(onActiveModel) ? setConfirmOpen(true) : choose.mutate({ reembed: false }))}
                  disabled={choose.isPending || (!provider.connected && provider.requires_key)}
                  className="rounded-xl"
                >
                  {choose.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
                  Use {modelId}
                </Button>
              </div>
            )}
          </div>
        )}
      </section>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-[480px] rounded-2xl">
          <DialogHeader>
            <DialogTitle>Switch to {modelId}?</DialogTitle>
            <DialogDescription className="pt-2">
              {countDatasets(onActiveModel)} dataset(s) were embedded with {active.model_id}. Search won&apos;t use them
              with the new model until they are re-embedded. You can re-embed now, or later from this page.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-2">
            <Button variant="outline" onClick={() => setConfirmOpen(false)} className="rounded-xl">Cancel</Button>
            <Button variant="outline" onClick={() => choose.mutate({ reembed: false })} disabled={choose.isPending} className="rounded-xl">
              Switch only
            </Button>
            <Button onClick={() => choose.mutate({ reembed: true })} disabled={choose.isPending} className="rounded-xl">
              {choose.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Switch and re-embed
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default EmbeddingSettings
