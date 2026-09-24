"use client"

/**
 * LLM Provider Settings Component
 * 
 * Allows users to configure LLM providers (OpenAI, Google, Grok, Ollama, etc.)
 * with API key management, model selection, and connection testing.
 * 
 * Redesigned with modern SaaS aesthetics.
 */

import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Loader2,
  Check,
  AlertTriangle,
  Trash2,
  Settings2,
  Zap,
  Star,
  ExternalLink,
  Eye,
  EyeOff,
  TestTube,
  Sparkles,
  Info,
  CheckCircle2,
  Clock,
  Shield,
  ArrowRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ProviderIcon } from '@/components/ui/provider-icons'
import { describeAccess, useProviders } from '@/hooks/useProviders'
import type { ProviderInfo } from '@/lib/api-types'
import { ModelPicker, formatShortDate } from '@/components/settings/ModelPicker'
import type { CatalogModel } from '@/lib/api-types'

// =============================================================================
// TYPES
// =============================================================================

interface LLMConfig {
  config_id: string
  name: string
  provider: string
  model_name: string
  base_url?: string
  model_type: string
  config_params: Record<string, any>
  is_default: boolean
  is_active: boolean
  has_api_key: boolean
  api_key_masked?: string
  last_tested_at?: string
  last_test_success?: boolean
  last_test_message?: string
  last_test_latency_ms?: number
  created_at: string
  updated_at?: string
}

// =============================================================================
// PROVIDER CARD
// =============================================================================

interface ProviderCardProps {
  config: LLMConfig
  providerInfo: ProviderInfo
  /** Catalogue entry for the configured model; undefined when the catalogue hasn't listed it. */
  catalogModel?: CatalogModel
  onEdit: () => void
  onDelete: () => void
  onTest: () => void
  onSetDefault: () => void
  isTestingThis: boolean
}

const ProviderCard = ({
  config,
  providerInfo,
  catalogModel,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
  isTestingThis,
}: ProviderCardProps) => {
  return (
    <div
      className={cn(
        "group relative rounded-2xl border p-6",
        "bg-card/60 backdrop-blur-sm",
        "transition-all duration-300",
        "hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1",
        config.is_default 
          ? "border-primary/50 ring-2 ring-primary/20 bg-gradient-to-br from-primary/5 via-card to-card" 
          : "border-border/40 hover:border-border/60"
      )}
    >
      {/* Background decoration for default */}
      {config.is_default && (
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-primary/20 via-transparent to-transparent rounded-2xl" />
      )}
      
      {/* Header */}
      <div className="relative flex items-start justify-between gap-4 mb-5">
        <div className="flex items-center gap-4">
          <div className={cn(
            "p-3 rounded-xl transition-transform duration-300 group-hover:scale-105",
            config.is_default 
              ? "bg-primary/10 ring-4 ring-primary/5" 
              : "bg-muted/50"
          )}>
            <ProviderIcon provider={providerInfo.id} label={providerInfo.label} size={28} className="text-foreground" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-lg">{config.name}</h3>
              {config.is_default && (
                <span className="text-xs font-bold text-primary bg-primary/10 px-3 py-1 rounded-full flex items-center gap-1.5 border border-primary/20">
                  <Star className="w-3 h-3 fill-current" />
                  Default
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {providerInfo.label} • <span className="font-mono text-xs">{config.model_name}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 rounded-xl hover:bg-primary/10"
            onClick={onTest}
            disabled={isTestingThis}
            title="Test Connection"
          >
            {isTestingThis ? (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            ) : (
              <TestTube className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 rounded-xl hover:bg-info/10"
            onClick={onEdit}
            title="Edit Configuration"
          >
            <Settings2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 rounded-xl text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={onDelete}
            title="Delete Configuration"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        {/* API Key Status */}
        <div className={cn(
          "p-3 rounded-xl border transition-colors",
          config.has_api_key || !providerInfo.requires_key
            ? "bg-success/5 border-success/20"
            : "bg-warning/5 border-warning/20"
        )}>
          <div className="flex items-center gap-2">
            {config.has_api_key ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span className="text-sm font-medium text-success dark:text-success">API Key Set</span>
              </>
            ) : !providerInfo.requires_key ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-success" />
                <span className="text-sm font-medium text-success dark:text-success">No key needed</span>
              </>
            ) : (
              <>
                <AlertTriangle className="h-4 w-4 text-warning" />
                <span className="text-sm font-medium text-warning dark:text-warning">No API Key</span>
              </>
            )}
          </div>
        </div>

        {/* Connection Status */}
        <div className={cn(
          "p-3 rounded-xl border transition-colors",
          config.last_tested_at
            ? config.last_test_success
              ? "bg-success/5 border-success/20"
              : "bg-destructive/5 border-destructive/20"
            : "bg-muted/30 border-border/40"
        )}>
          <div className="flex items-center gap-2">
            {config.last_tested_at ? (
              config.last_test_success ? (
                <>
                  <Zap className="h-4 w-4 text-success" />
                  <span className="text-sm font-medium text-success dark:text-success">
                    {typeof config.last_test_latency_ms === 'number' ? `${config.last_test_latency_ms}ms latency` : 'Connected'}
                  </span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-4 w-4 text-destructive" />
                  <span className="text-sm font-medium text-destructive dark:text-destructive truncate">
                    Connection Failed
                  </span>
                </>
              )
            ) : (
              <>
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Not Tested</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Model lifecycle: the provider is phasing this model out */}
      {catalogModel && catalogModel.status !== 'active' && (
        <div
          role="status"
          className={cn(
            "mb-5 flex items-start gap-2 rounded-xl border p-3 text-sm",
            catalogModel.status === 'retired'
              ? "border-destructive/30 bg-destructive/5 text-destructive"
              : "border-warning/30 bg-warning/5 text-warning"
          )}
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            <strong className="font-semibold">
              {catalogModel.status === 'retired' ? 'Model retired.' : 'Model deprecated.'}
            </strong>{' '}
            {catalogModel.status_reason} Edit this connection to pick another model.
          </span>
        </div>
      )}
      {catalogModel?.status === 'active' && catalogModel.shutdown_date && (
        <div role="status" className="mb-5 flex items-start gap-2 rounded-xl border border-warning/30 bg-warning/5 p-3 text-sm text-warning">
          <Clock className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{providerInfo.label} will shut this model down on {formatShortDate(catalogModel.shutdown_date)}.</span>
        </div>
      )}

      {/* Actions */}
      {!config.is_default && (
        <div className="pt-4 border-t border-border/30">
          <Button
            variant="outline"
            size="sm"
            onClick={onSetDefault}
            className="text-xs rounded-xl hover:bg-primary/5 hover:border-primary/30 hover:text-primary transition-colors"
          >
            <Star className="h-3.5 w-3.5 mr-2" />
            Set as Default Provider
          </Button>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// ADD/EDIT DIALOG
// =============================================================================

interface ProviderFormData {
  name: string
  provider: string
  model_name: string
  api_key: string
  base_url: string
}

interface ProviderDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editConfig?: LLMConfig | null
  onSubmit: (data: ProviderFormData) => Promise<void>
  isSubmitting: boolean
}

const EMPTY_FORM: ProviderFormData = { name: '', provider: 'ollama', model_name: '', api_key: '', base_url: '' }

/** The value after it has stopped changing for `ms`: list models once the user finishes typing a key. */
function useSettled<T>(value: T, ms: number): T {
  const [settled, setSettled] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms)
    return () => clearTimeout(timer)
  }, [value, ms])
  return settled
}

const isValidUrl = (url: string): boolean => {
  if (!url) return true
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

const ProviderDialog = ({
  open,
  onOpenChange,
  editConfig,
  onSubmit,
  isSubmitting,
}: ProviderDialogProps) => {
  const [formData, setFormData] = useState<ProviderFormData>(EMPTY_FORM)
  const [nameTouched, setNameTouched] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)

  const { providers, getProvider } = useProviders()
  // Only providers that need a saved connection; built-in models need none.
  const connectable = providers.filter(p => p.chat || p.requires_key || p.custom_base_url)
  const providerInfo: ProviderInfo = getProvider(formData.provider) ?? {
    id: formData.provider, label: formData.provider, description: '', api: 'openai', base_url: '', key_url: '',
    requires_key: false, list_requires_key: false, chat: true, embeddings: false, local: false,
    free_tier: false, custom_base_url: false, embed_batch: 0, access: null,
  }
  // Providers without chat models (Jina) are connected for their embedding models.
  const modelKind = providerInfo.chat ? 'llm' : 'embedding'
  const settledKey = useSettled(formData.api_key.trim(), 600)
  const settledBaseUrl = useSettled(formData.base_url.trim(), 600)
  const baseUrlError = formData.base_url && !isValidUrl(formData.base_url)
    ? 'Enter a full URL starting with http:// or https://'
    : null

  useEffect(() => {
    if (!open) return
    if (editConfig) {
      setFormData({
        name: editConfig.name,
        provider: editConfig.provider,
        model_name: editConfig.model_name,
        api_key: '',
        base_url: editConfig.base_url || '',
      })
      setNameTouched(true)
    } else {
      setFormData({ ...EMPTY_FORM, name: 'Ollama' })
      setNameTouched(false)
    }
    setShowApiKey(false)
  }, [open, editConfig])

  // A new connection to a keyed provider can't be listed until a key is typed;
  // an existing one lists with its saved key.
  const canList = !providerInfo.list_requires_key || !!settledKey || !!editConfig
  const discovery = useQuery({
    queryKey: ['model-discovery', formData.provider, settledKey, settledBaseUrl, editConfig?.config_id ?? null],
    queryFn: () => apiClient.discoverModels({
      provider: formData.provider,
      apiKey: settledKey || undefined,
      baseUrl: isValidUrl(settledBaseUrl) ? settledBaseUrl || undefined : undefined,
      configId: editConfig?.config_id,
    }),
    enabled: open && canList,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
  const chatModels = useMemo(
    () => (discovery.data?.models ?? []).filter(m => m.kind === modelKind),
    [discovery.data, modelKind]
  )
  const discoveryError = discovery.error
    ? 'Could not reach the server to list models.'
    : discovery.data && !discovery.data.ok ? discovery.data.error ?? 'Listing models failed.' : null

  // Preselect when the choice is obvious (a local Ollama with a couple of
  // models); from hundreds, the user picks. Never override a choice.
  useEffect(() => {
    if (!formData.model_name && chatModels.length > 0 && chatModels.length <= 5) {
      const firstActive = chatModels.find(m => m.status === 'active') ?? chatModels[0]
      setFormData(f => (f.model_name ? f : { ...f, model_name: firstActive.model_id }))
    }
  }, [chatModels, formData.model_name])

  const handleProviderChange = (next: string) => {
    setFormData(f => ({
      ...f,
      provider: next,
      model_name: '',
      api_key: '',
      base_url: '',
      name: nameTouched ? f.name : getProvider(next)?.label ?? next,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (baseUrlError || !formData.model_name.trim()) return
    await onSubmit({ ...formData, model_name: formData.model_name.trim() })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto rounded-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-xl">
            <div className="p-2.5 rounded-xl bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            {editConfig ? 'Edit connection' : 'Connect an LLM'}
          </DialogTitle>
          <DialogDescription className="pt-2">
            Used to generate example requests for your templates and to extract request bodies.
            The model list comes live from the provider.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 py-2">
          {/* Provider */}
          <div className="space-y-2">
            <Label className="font-semibold">Provider</Label>
            <Select
              value={formData.provider}
              onValueChange={(v: string) => handleProviderChange(v)}
              disabled={!!editConfig}
            >
              <SelectTrigger className="h-12 rounded-xl">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                {connectable.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id} className="rounded-lg">
                    <div className="flex items-center gap-3 py-1">
                      <ProviderIcon provider={provider.id} label={provider.label} size={20} />
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {provider.label}
                          {provider.local && <span className="ml-2 text-xs text-info">local</span>}
                          {provider.free_tier && !provider.local && <span className="ml-2 text-xs text-success">free tier</span>}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {provider.description}
                          {provider.access && provider.access !== 'none-needed' && ` · ${describeAccess(provider)}`}
                        </span>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* API key */}
          {(providerInfo.requires_key || providerInfo.id === 'custom') && (
            <div className="space-y-2">
              <div className="flex items-baseline justify-between gap-2">
                <Label htmlFor="api_key" className="font-semibold">
                  API key{' '}
                  {editConfig && <span className="font-normal text-muted-foreground">(leave empty to keep the saved one)</span>}
                  {!providerInfo.requires_key && !editConfig && <span className="font-normal text-muted-foreground">(optional)</span>}
                </Label>
                {providerInfo.key_url && providerInfo.requires_key && (
                  <a
                    href={providerInfo.key_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                  >
                    Get a key <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
              <div className="relative">
                <Input
                  id="api_key"
                  type={showApiKey ? 'text' : 'password'}
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder={`Paste your ${providerInfo.label} API key`}
                  required={providerInfo.requires_key && !editConfig && providerInfo.access !== 'deployment'}
                  autoComplete="off"
                  className="pr-12 h-12 rounded-xl"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-10 w-10 rounded-lg hover:bg-muted"
                  onClick={() => setShowApiKey(!showApiKey)}
                  aria-label={showApiKey ? 'Hide API key' : 'Show API key'}
                >
                  {showApiKey ? <EyeOff className="h-4 w-4 text-muted-foreground" /> : <Eye className="h-4 w-4 text-muted-foreground" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <Shield className="h-3 w-3" />
                Encrypted before it is stored. It is only sent to {providerInfo.label}.
                {providerInfo.access === 'deployment' && !editConfig && ' Leave empty to use the key this deployment already has.'}
              </p>
            </div>
          )}

          {/* Server URL (self-hosted providers only) */}
          {providerInfo.custom_base_url && (
            <div className="space-y-2">
              <Label htmlFor="base_url" className="font-semibold">
                Server URL {providerInfo.id !== 'custom' && <span className="font-normal text-muted-foreground">(optional)</span>}
              </Label>
              <Input
                id="base_url"
                type="url"
                value={formData.base_url}
                onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                placeholder={providerInfo.id === 'ollama' ? 'Leave empty to use the bundled Ollama' : 'http://localhost:1234/v1'}
                required={providerInfo.id === 'custom'}
                className={cn('h-12 rounded-xl', baseUrlError && 'border-destructive focus-visible:ring-destructive')}
              />
              {baseUrlError && (
                <p className="text-xs text-destructive flex items-center gap-1.5">
                  <AlertTriangle className="h-3 w-3" />
                  {baseUrlError}
                </p>
              )}
            </div>
          )}

          {/* Model */}
          <div className="space-y-2">
            <Label className="font-semibold">Model</Label>
            {canList ? (
              <ModelPicker
                models={chatModels}
                value={formData.model_name}
                onChange={(model_name) => setFormData(f => ({ ...f, model_name }))}
                loading={discovery.isFetching && !discovery.data}
                error={discoveryError}
                onRetry={() => discovery.refetch()}
                placeholder={
                  providerInfo.id === 'ollama'
                    ? 'No chat models are pulled into Ollama yet. Run "ollama pull llama3.2:3b", or type a model id below.'
                    : undefined
                }
              />
            ) : (
              <p className="rounded-xl border border-dashed border-border/60 p-4 text-sm text-muted-foreground">
                Paste your API key above to see the models it can use.
              </p>
            )}
          </div>

          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="font-semibold">Connection name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => {
                setNameTouched(true)
                setFormData({ ...formData, name: e.target.value })
              }}
              placeholder="e.g. Gemini (free tier)"
              className="h-12 rounded-xl"
              required
            />
          </div>

          <DialogFooter className="gap-3 sm:gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="rounded-xl">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !formData.model_name.trim() || !!baseUrlError}
              className="rounded-xl min-w-[140px]"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : editConfig ? (
                <>
                  Save changes
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              ) : (
                <>
                  Add connection
                  <Plus className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export const LLMProviderSettings = () => {
  const queryClient = useQueryClient()
  const { getProvider } = useProviders()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editConfig, setEditConfig] = useState<LLMConfig | null>(null)
  const [testingConfigId, setTestingConfigId] = useState<string | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  // Fetch configs
  const { data, isLoading, error } = useQuery({
    queryKey: ['llm-configs'],
    queryFn: () => apiClient.listLLMConfigs(false),
  })

  // Lifecycle status of each configured model (retired included, to warn about them).
  const { data: catalog } = useQuery({
    queryKey: ['model-catalog', 'llm', 'with-retired'],
    queryFn: () => apiClient.getModelCatalog({ kind: 'llm', includeRetired: true }),
    staleTime: 60 * 1000,
  })
  const catalogIndex = useMemo(
    () => new Map((catalog?.models ?? []).map(m => [`${m.provider}/${m.model_id}`, m])),
    [catalog]
  )
  // Saving a connection queues a catalogue refresh on the worker; pick it up shortly after.
  const refreshCatalogSoon = () => {
    setTimeout(() => queryClient.invalidateQueries({ queryKey: ['model-catalog'] }), 4000)
  }

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: ProviderFormData) => apiClient.createLLMConfig({
      name: data.name,
      provider: data.provider,
      model_name: data.model_name,
      api_key: data.api_key || undefined,
      base_url: data.base_url || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] })
      refreshCatalogSoon()
      setDialogOpen(false)
      toast({ title: 'Provider added', description: 'LLM provider configuration created successfully.' })
    },
    onError: (err: any) => {
      toast({ title: 'Error', description: err.detail || 'Failed to add provider.', variant: 'destructive' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProviderFormData }) =>
      apiClient.updateLLMConfig(id, {
        name: data.name,
        model_name: data.model_name,
        api_key: data.api_key || undefined,
        base_url: data.base_url || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] })
      refreshCatalogSoon()
      setDialogOpen(false)
      setEditConfig(null)
      toast({ title: 'Provider updated', description: 'Configuration updated successfully.' })
    },
    onError: (err: any) => {
      toast({ title: 'Error', description: err.detail || 'Failed to update.', variant: 'destructive' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.deleteLLMConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] })
      refreshCatalogSoon()
      setDeleteConfirmId(null)
      toast({ title: 'Provider deleted', description: 'Configuration removed.' })
    },
    onError: (err: any) => {
      setDeleteConfirmId(null)
      toast({ title: 'Error', description: err.detail || 'Failed to delete.', variant: 'destructive' })
    },
  })

  const testMutation = useMutation({
    mutationFn: (id: string) => {
      setTestingConfigId(id)
      return apiClient.testLLMConfig(id)
    },
    onSuccess: (result) => {
      setTestingConfigId(null)
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] })
      if (result.success) {
        toast({
          title: 'Connection successful',
          description: `Connected in ${result.latency_ms}ms`,
        })
      } else {
        toast({
          title: 'Connection failed',
          description: result.message,
          variant: 'destructive',
        })
      }
    },
    onError: (err: any) => {
      setTestingConfigId(null)
      toast({ title: 'Test failed', description: err.detail || 'Connection test failed.', variant: 'destructive' })
    },
  })

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => apiClient.setDefaultLLMConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-configs'] })
      toast({ title: 'Default updated', description: 'Default LLM provider changed.' })
    },
    onError: (err: any) => {
      toast({ title: 'Error', description: err.detail || 'Failed to set default.', variant: 'destructive' })
    },
  })

  const handleSubmit = async (formData: ProviderFormData) => {
    if (editConfig) {
      await updateMutation.mutateAsync({ id: editConfig.config_id, data: formData })
    } else {
      await createMutation.mutateAsync(formData)
    }
  }

  const handleEdit = (config: LLMConfig) => {
    setEditConfig(config)
    setDialogOpen(true)
  }

  const handleAdd = () => {
    setEditConfig(null)
    setDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative">
          <Loader2 className="h-10 w-10 animate-spin text-primary/50" />
          <div className="absolute inset-0 h-10 w-10 animate-ping bg-primary/20 rounded-full" />
        </div>
        <p className="text-muted-foreground mt-4">Loading providers...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-destructive/10 flex items-center justify-center mb-4">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="font-semibold text-lg text-foreground mb-2">Failed to Load</h3>
        <p className="text-muted-foreground">Could not load LLM configurations. Please try again.</p>
      </div>
    )
  }

  const configs = data?.configs || []

  return (
    <div className="space-y-6">
      {/* Section Card Wrapper */}
      <div className="rounded-2xl border border-border/40 bg-card/80 backdrop-blur-xl overflow-hidden shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border/40 bg-gradient-to-r from-muted/30 to-transparent">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-primary to-brand-2 shadow-lg shadow-primary/20">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">LLM Providers</h2>
              <p className="text-sm text-muted-foreground">
                Configure AI providers for dataset generation and advanced features
              </p>
            </div>
          </div>
          <Button onClick={handleAdd} className="rounded-xl h-11 gap-2 shadow-lg shadow-primary/20">
            <Plus className="h-4 w-4" />
            Add Provider
          </Button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Config List */}
          {configs.length === 0 ? (
            <div className="border border-dashed border-border/60 rounded-2xl p-16 text-center bg-muted/10">
              <div className="relative mx-auto w-20 h-20 mb-6">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary/5 rounded-3xl blur-xl" />
                <div className="relative w-20 h-20 rounded-3xl bg-muted/50 flex items-center justify-center border border-border/40">
                  <Sparkles className="h-10 w-10 text-muted-foreground/40" />
                </div>
              </div>
              <h3 className="font-bold text-xl text-foreground mb-2">No LLM Providers Yet</h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
                Add your first LLM provider to enable AI-powered dataset generation and intelligent features.
              </p>
              <Button onClick={handleAdd} variant="outline" className="rounded-xl">
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Provider
              </Button>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {configs.map((config) => {
                const providerInfo = getProvider(config.provider)
                if (!providerInfo) return null
                return (
                  <ProviderCard
                    key={config.config_id}
                    config={config}
                    providerInfo={providerInfo}
                    catalogModel={catalogIndex.get(`${config.provider}/${config.model_name}`)}
                    onEdit={() => handleEdit(config)}
                    onDelete={() => setDeleteConfirmId(config.config_id)}
                    onTest={() => testMutation.mutate(config.config_id)}
                    onSetDefault={() => setDefaultMutation.mutate(config.config_id)}
                    isTestingThis={testingConfigId === config.config_id}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Dialog */}
      <ProviderDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editConfig={editConfig}
        onSubmit={handleSubmit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirmId} onOpenChange={(open) => !open && setDeleteConfirmId(null)}>
        <DialogContent className="sm:max-w-[420px] rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-xl">
              <div className="p-2.5 rounded-xl bg-destructive/10">
                <Trash2 className="h-5 w-5 text-destructive" />
              </div>
              Delete LLM Provider
            </DialogTitle>
            <DialogDescription className="pt-2">
              Are you sure you want to delete this provider configuration? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-3 sm:gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => setDeleteConfirmId(null)}
              className="rounded-xl"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmId && deleteMutation.mutate(deleteConfirmId)}
              disabled={deleteMutation.isPending}
              className="rounded-xl min-w-[100px]"
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default LLMProviderSettings
