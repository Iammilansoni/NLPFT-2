"use client"

/**
 * LLM Provider Settings Component
 * 
 * Allows users to configure LLM providers (OpenAI, Google, Grok, Ollama, etc.)
 * with API key management, model selection, and connection testing.
 * 
 * Redesigned with modern SaaS aesthetics.
 */

import { useState, useEffect } from 'react'
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
import {
  LLM_PROVIDERS,
  getImplementedProviders,
  getProviderById,
  type LLMProviderType,
  type LLMProviderInfo,
} from '@/lib/constants/llm-providers'

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
  providerInfo: LLMProviderInfo
  onEdit: () => void
  onDelete: () => void
  onTest: () => void
  onSetDefault: () => void
  isTestingThis: boolean
}

const ProviderCard = ({
  config,
  providerInfo,
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
            <ProviderIcon provider={providerInfo.icon} size={28} className="text-foreground" />
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
              {providerInfo.name} • <span className="font-mono text-xs">{config.model_name}</span>
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
            className="h-9 w-9 rounded-xl hover:bg-blue-500/10"
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
          config.has_api_key 
            ? "bg-emerald-500/5 border-emerald-500/20" 
            : "bg-amber-500/5 border-amber-500/20"
        )}>
          <div className="flex items-center gap-2">
            {config.has_api_key ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">API Key Set</span>
              </>
            ) : (
              <>
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium text-amber-600 dark:text-amber-400">No API Key</span>
              </>
            )}
          </div>
        </div>

        {/* Connection Status */}
        <div className={cn(
          "p-3 rounded-xl border transition-colors",
          config.last_tested_at
            ? config.last_test_success
              ? "bg-emerald-500/5 border-emerald-500/20"
              : "bg-red-500/5 border-red-500/20"
            : "bg-muted/30 border-border/40"
        )}>
          <div className="flex items-center gap-2">
            {config.last_tested_at ? (
              config.last_test_success ? (
                <>
                  <Zap className="h-4 w-4 text-emerald-500" />
                  <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                    {typeof config.last_test_latency_ms === 'number' ? `${config.last_test_latency_ms}ms latency` : 'Connected'}
                  </span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium text-red-600 dark:text-red-400 truncate">
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
  provider: LLMProviderType
  model_name: string
  custom_model_name: string  // For custom model input (HuggingFace, Custom, Ollama)
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

const ProviderDialog = ({
  open,
  onOpenChange,
  editConfig,
  onSubmit,
  isSubmitting,
}: ProviderDialogProps) => {
  const [formData, setFormData] = useState<ProviderFormData>({
    name: '',
    provider: 'openai',
    model_name: '',
    custom_model_name: '',
    api_key: '',
    base_url: '',
  })
  const [showApiKey, setShowApiKey] = useState(false)
  const [baseUrlError, setBaseUrlError] = useState<string | null>(null)

  // Validate URL format
  const validateBaseUrl = (url: string): boolean => {
    if (!url) return true // Empty is valid (optional field)
    try {
      const parsed = new URL(url)
      return parsed.protocol === 'http:' || parsed.protocol === 'https:'
    } catch {
      return false
    }
  }

  // Get current provider info
  const providerInfo = getProviderById(formData.provider)
  
  // Check if provider allows custom model input
  const allowsCustomModel = ['huggingface', 'custom', 'ollama'].includes(formData.provider)
  const isUsingCustomModel = formData.model_name === 'custom' || formData.model_name === 'custom-model'

  // Reset form when dialog opens or editConfig changes
  useEffect(() => {
    if (open && editConfig) {
      // Check if the model_name is not in the predefined list
      const providerModels = getProviderById(editConfig.provider as LLMProviderType).models
      const isPredefinedModel = providerModels.some(m => m.id === editConfig.model_name)
      
      setFormData({
        name: editConfig.name,
        provider: editConfig.provider as LLMProviderType,
        model_name: isPredefinedModel ? editConfig.model_name : 'custom',
        custom_model_name: isPredefinedModel ? '' : editConfig.model_name,
        api_key: '',
        base_url: editConfig.base_url || '',
      })
    } else if (open && !editConfig) {
      setFormData({
        name: '',
        provider: 'openai',
        model_name: LLM_PROVIDERS.openai.models[0]?.id || '',
        custom_model_name: '',
        api_key: '',
        base_url: '',
      })
    }
  }, [open, editConfig])

  // Handle dialog open/close state changes
  const handleOpenChange = (isOpen: boolean) => {
    onOpenChange(isOpen)
  }

  // Update model when provider changes
  const handleProviderChange = (newProvider: LLMProviderType) => {
    const newProviderInfo = getProviderById(newProvider)
    setFormData({
      ...formData,
      provider: newProvider,
      model_name: newProviderInfo.models[0]?.id || '',
      custom_model_name: '',
      base_url: newProviderInfo.baseUrlPlaceholder || '',
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate base_url before submission
    if (formData.base_url && !validateBaseUrl(formData.base_url)) {
      setBaseUrlError('Please enter a valid URL (http:// or https://)')
      return
    }
    
    // Determine the actual model name to submit
    const actualModelName = (formData.model_name === 'custom' || formData.model_name === 'custom-model')
      ? formData.custom_model_name
      : formData.model_name
    
    await onSubmit({
      ...formData,
      model_name: actualModelName,
    })
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[520px] rounded-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-xl">
            <div className="p-2.5 rounded-xl bg-primary/10">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            {editConfig ? 'Edit LLM Provider' : 'Add LLM Provider'}
          </DialogTitle>
          <DialogDescription className="pt-2">
            Configure an LLM provider for dataset generation and AI-powered features.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 py-2">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="font-semibold">Configuration Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="My OpenAI Config"
              className="h-12 rounded-xl"
              required
            />
          </div>

          {/* Provider Selection */}
          <div className="space-y-2">
            <Label className="font-semibold">Provider</Label>
            <Select
              value={formData.provider}
              onValueChange={(v: string) => handleProviderChange(v as LLMProviderType)}
              disabled={!!editConfig}
            >
              <SelectTrigger className="h-12 rounded-xl">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="rounded-xl">
                {getImplementedProviders().map((provider) => (
                  <SelectItem key={provider.id} value={provider.id} className="rounded-lg">
                    <div className="flex items-center gap-3 py-1">
                      <ProviderIcon provider={provider.icon} size={20} />
                      <div className="flex flex-col">
                        <span className="font-medium">{provider.name}</span>
                        {provider.id === 'custom' && (
                          <span className="text-xs text-muted-foreground">
                            Only if you run LM Studio, vLLM, or another OpenAI-compatible server separately
                          </span>
                        )}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {providerInfo.docsUrl && (
              <a
                href={providerInfo.docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary hover:underline flex items-center gap-1.5 mt-2 font-medium"
              >
                <Info className="h-3 w-3" />
                View documentation
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <Label className="font-semibold">Model</Label>
            <Select
              value={formData.model_name}
              onValueChange={(v: string) => setFormData({ ...formData, model_name: v, custom_model_name: '' })}
            >
              <SelectTrigger className="h-12 rounded-xl">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="max-h-[300px] rounded-xl">
                {providerInfo.models.map((model) => (
                  <SelectItem key={model.id} value={model.id} className="rounded-lg py-3">
                    <div className="flex flex-col items-start">
                      <span className="font-semibold">{model.name}</span>
                      <span className="text-xs text-muted-foreground mt-0.5">
                        {model.description}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {/* Custom Model Input - shown when "custom" is selected or for providers that support it */}
            {isUsingCustomModel && (
              <div className="mt-3 space-y-2">
                <Label htmlFor="custom_model" className="font-semibold">
                  Custom Model {formData.provider === 'huggingface' ? 'Path' : 'Name'}
                </Label>
                <Input
                  id="custom_model"
                  type="text"
                  value={formData.custom_model_name}
                  onChange={(e) => setFormData({ ...formData, custom_model_name: e.target.value })}
                  placeholder={
                    formData.provider === 'huggingface' 
                      ? 'e.g., google/gemma-3-27b-it, meta-llama/Llama-3.3-70B-Instruct'
                      : formData.provider === 'ollama'
                      ? 'e.g., llama3.2:3b, qwen2.5:14b, deepseek-r1:8b'
                      : 'e.g., my-local-model, gpt-4-custom'
                  }
                  required
                  className="h-12 rounded-xl"
                />
                <p className="text-xs text-muted-foreground">
                  {formData.provider === 'huggingface' ? (
                    <>Enter the full HuggingFace model path (e.g., <code className="bg-muted px-1 rounded">owner/model-name</code>)</>
                  ) : formData.provider === 'ollama' ? (
                    <>Enter the Ollama model name with tag (e.g., <code className="bg-muted px-1 rounded">llama3.2:3b</code>)</>
                  ) : (
                    <>Enter the model name served by your endpoint</>
                  )}
                </p>
              </div>
            )}
          </div>

          {/* API Key */}
          {providerInfo.requiresApiKey && (
            <div className="space-y-2">
              <Label htmlFor="api_key" className="font-semibold">
                API Key {editConfig && <span className="font-normal text-muted-foreground">(leave empty to keep current)</span>}
              </Label>
              <div className="relative">
                <Input
                  id="api_key"
                  type={showApiKey ? 'text' : 'password'}
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder={providerInfo.apiKeyPlaceholder}
                  required={!editConfig}
                  className="pr-12 h-12 rounded-xl"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-10 w-10 rounded-lg hover:bg-muted"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <Shield className="h-3 w-3" />
                Your API key is encrypted and stored securely
              </p>
            </div>
          )}

          {/* Base URL (if supported) */}
          {providerInfo.supportsCustomBaseUrl && (
            <div className="space-y-2">
              <Label htmlFor="base_url" className="font-semibold">Base URL <span className="font-normal text-muted-foreground">(optional)</span></Label>
              <Input
                id="base_url"
                type="url"
                value={formData.base_url}
                onChange={(e) => {
                  const url = e.target.value
                  setFormData({ ...formData, base_url: url })
                  if (url && !validateBaseUrl(url)) {
                    setBaseUrlError('Please enter a valid URL (http:// or https://)')
                  } else {
                    setBaseUrlError(null)
                  }
                }}
                placeholder={providerInfo.baseUrlPlaceholder}
                className={`h-12 rounded-xl ${baseUrlError ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              {baseUrlError && (
                <p className="text-xs text-red-500 flex items-center gap-1.5">
                  <AlertTriangle className="h-3 w-3" />
                  {baseUrlError}
                </p>
              )}
            </div>
          )}

          <DialogFooter className="gap-3 sm:gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="rounded-xl"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting} className="rounded-xl min-w-[140px]">
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : editConfig ? (
                <>
                  Update Provider
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              ) : (
                <>
                  Add Provider
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
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editConfig, setEditConfig] = useState<LLMConfig | null>(null)
  const [testingConfigId, setTestingConfigId] = useState<string | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  // Fetch configs
  const { data, isLoading, error } = useQuery({
    queryKey: ['llm-configs'],
    queryFn: () => apiClient.listLLMConfigs(false),
  })

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
        <div className="mx-auto w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-4">
          <AlertTriangle className="h-8 w-8 text-red-500" />
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
            <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 shadow-lg shadow-purple-500/20">
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
                const providerInfo = LLM_PROVIDERS[config.provider as LLMProviderType] || LLM_PROVIDERS.custom
                return (
                  <ProviderCard
                    key={config.config_id}
                    config={config}
                    providerInfo={providerInfo}
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
              <div className="p-2.5 rounded-xl bg-red-500/10">
                <Trash2 className="h-5 w-5 text-red-500" />
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
