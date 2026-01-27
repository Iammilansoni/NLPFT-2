"use client"

/**
 * Embedding Model Picker Component - Unified Workflow
 * 
 * Simple flow:
 * 1. Shows current active model prominently at top
 * 2. Downloaded models → Click "Set as Default" to use
 * 3. Available models → Click "Download & Activate" to get AND set as default
 * 
 * One model is active at a time - used for all embedding operations.
 */

import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Loader2,
  Check,
  AlertTriangle,
  Download,
  RefreshCw,
  Server,
  HardDrive,
  Cloud,
  CheckCircle2,
  Info,
  Zap,
  Brain,
  Rocket,
  Target,
  Clock,
  Ruler,
  Cpu,
  Star,
  FileText,
  ChevronDown,
  ChevronUp,
  Play,
  Crown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { toast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

// =============================================================================
// TYPES
// =============================================================================

interface EmbeddingModel {
  name: string
  display_name: string
  size: string
  is_local: boolean
  is_registered: boolean
  dimension: number | null
  family: string | null
}

interface ModelStats {
  parameters: string
  context_length: string
  speed: 'fast' | 'moderate' | 'slow'
  accuracy: 'good' | 'excellent' | 'superior'
  best_for: string[]
  description?: string
}

// Known model stats database - Updated from https://ollama.com/search?c=embedding
const MODEL_STATS_DB: Record<string, ModelStats> = {
  // === BGE Models (BAAI - Beijing Academy of AI) ===
  'bge-base': {
    parameters: '~109M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['Balanced performance', 'General retrieval', 'Cost-effective'],
    description: 'BAAI\'s balanced embedding model offering good tradeoff between speed and accuracy for general retrieval tasks.',
  },
  'bge-large': {
    parameters: '~335M',
    context_length: '512 tokens',
    speed: 'moderate',
    accuracy: 'superior',
    best_for: ['High accuracy English', 'Question answering', 'Semantic search'],
    description: 'BAAI\'s high-accuracy English embedding model. Excellent for question answering and semantic search applications.',
  },
  'bge-m3': {
    parameters: '~567M',
    context_length: '8192 tokens',
    speed: 'moderate',
    accuracy: 'superior',
    best_for: ['Multilingual (100+ languages)', 'Multi-granularity', 'Dense & sparse retrieval'],
    description: 'BAAI\'s multi-functional, multi-lingual, multi-granularity model supporting 100+ languages with hybrid dense/sparse retrieval.',
  },

  // === Nomic Models ===
  'nomic-embed-text': {
    parameters: '~137M',
    context_length: '8192 tokens',
    speed: 'fast',
    accuracy: 'excellent',
    best_for: ['Long documents', 'RAG pipelines', 'Production workloads'],
    description: 'High-performing open embedding model with an 8192 token context window. Ideal for RAG and production use.',
  },
  'nomic-embed-text-v2-moe': {
    parameters: '~300M (MoE)',
    context_length: '8192 tokens',
    speed: 'moderate',
    accuracy: 'superior',
    best_for: ['Multilingual retrieval', 'High performance', 'Mixed-language content'],
    description: 'Mixture-of-Experts embedding model excelling at multilingual retrieval with state-of-the-art performance.',
  },

  // === MiniLM Models (Sentence Transformers) ===
  'all-minilm': {
    parameters: '22M-33M',
    context_length: '256 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['Fast prototyping', 'Low resources', 'Edge devices'],
    description: 'Ultra-lightweight sentence-transformers model. Perfect for prototyping and resource-constrained environments.',
  },
  'all-minilm:22m': {
    parameters: '~22M',
    context_length: '256 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['Ultrafast inference', 'Memory-constrained', 'Real-time apps'],
    description: 'Smallest MiniLM variant. Blazing fast inference for real-time applications.',
  },
  'all-minilm:33m': {
    parameters: '~33M',
    context_length: '256 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['Fast inference', 'Sentence similarity', 'Clustering'],
    description: 'Slightly larger MiniLM with improved accuracy while maintaining fast inference speeds.',
  },

  // === MixedBread Models ===
  'mxbai-embed-large': {
    parameters: '~335M',
    context_length: '512 tokens',
    speed: 'moderate',
    accuracy: 'superior',
    best_for: ['State-of-the-art accuracy', 'Enterprise search', 'RAG systems'],
    description: 'State-of-the-art large embedding model from mixedbread.ai. Top-tier accuracy for enterprise search.',
  },

  // === Snowflake Models ===
  'snowflake-arctic-embed': {
    parameters: '22M-335M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'excellent',
    best_for: ['Enterprise retrieval', 'Scalable search', 'Production'],
    description: 'Snowflake\'s suite of enterprise-optimized embedding models available in multiple sizes.',
  },
  'snowflake-arctic-embed:22m': {
    parameters: '~22M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['Lightweight embedding', 'Quick search', 'Low latency'],
    description: 'Smallest Arctic Embed variant for low-latency applications.',
  },
  'snowflake-arctic-embed:33m': {
    parameters: '~33M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['Balanced size/speed', 'General retrieval'],
    description: 'Compact Arctic Embed with good balance of size and performance.',
  },
  'snowflake-arctic-embed:110m': {
    parameters: '~110M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'excellent',
    best_for: ['Good accuracy', 'Production ready'],
    description: 'Mid-size Arctic Embed offering excellent accuracy for production workloads.',
  },
  'snowflake-arctic-embed:137m': {
    parameters: '~137M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'excellent',
    best_for: ['Strong performance', 'Enterprise search'],
    description: 'Larger Arctic Embed variant with enhanced performance for enterprise use.',
  },
  'snowflake-arctic-embed:335m': {
    parameters: '~335M',
    context_length: '512 tokens',
    speed: 'moderate',
    accuracy: 'superior',
    best_for: ['Best accuracy', 'Critical applications'],
    description: 'Largest Arctic Embed model with the highest accuracy for mission-critical retrieval.',
  },
  'snowflake-arctic-embed2': {
    parameters: '~568M',
    context_length: '8192 tokens',
    speed: 'moderate',
    accuracy: 'superior',
    best_for: ['Multilingual support', 'Long context', 'Frontier performance'],
    description: 'Snowflake\'s frontier embedding model with multilingual support and 8K context without sacrificing English performance.',
  },

  // === Google Models ===
  'embeddinggemma': {
    parameters: '~300M',
    context_length: '2048 tokens',
    speed: 'moderate',
    accuracy: 'excellent',
    best_for: ['Google ecosystem', 'Versatile tasks', 'General purpose'],
    description: 'Google\'s 300M parameter embedding model. Versatile for general-purpose text embedding tasks.',
  },

  // === Qwen Models (Alibaba) ===
  'qwen3-embedding': {
    parameters: '0.6B-8B',
    context_length: '8192 tokens',
    speed: 'slow',
    accuracy: 'superior',
    best_for: ['Advanced retrieval', 'Research', 'Maximum quality'],
    description: 'Alibaba\'s comprehensive Qwen3 embedding series. Multiple sizes from 0.6B to 8B parameters.',
  },
  'qwen3-embedding:0.6b': {
    parameters: '~600M',
    context_length: '8192 tokens',
    speed: 'moderate',
    accuracy: 'excellent',
    best_for: ['Balanced Qwen', 'Good performance'],
    description: 'Smallest Qwen3 embedding variant. Good balance of quality and resource usage.',
  },
  'qwen3-embedding:4b': {
    parameters: '~4B',
    context_length: '8192 tokens',
    speed: 'slow',
    accuracy: 'superior',
    best_for: ['High quality', 'Complex retrieval'],
    description: 'Mid-size Qwen3 model offering superior quality for complex retrieval tasks.',
  },
  'qwen3-embedding:8b': {
    parameters: '~8B',
    context_length: '8192 tokens',
    speed: 'slow',
    accuracy: 'superior',
    best_for: ['Maximum quality', 'Research tasks'],
    description: 'Largest Qwen3 embedding model. Maximum quality for research and critical applications.',
  },

  // === IBM Granite Models ===
  'granite-embedding': {
    parameters: '30M-278M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'excellent',
    best_for: ['Enterprise', 'IBM ecosystem', 'Multilingual'],
    description: 'IBM\'s Granite embedding models. 30M English-only or 278M multilingual for enterprise use.',
  },
  'granite-embedding:30m': {
    parameters: '~30M',
    context_length: '512 tokens',
    speed: 'fast',
    accuracy: 'good',
    best_for: ['English only', 'Fast inference', 'Low resources'],
    description: 'Lightweight Granite model for English-only fast inference applications.',
  },
  'granite-embedding:278m': {
    parameters: '~278M',
    context_length: '512 tokens',
    speed: 'moderate',
    accuracy: 'excellent',
    best_for: ['Multilingual', 'Enterprise search', 'Production'],
    description: 'Full Granite model with multilingual support for enterprise production use.',
  },

  // === Paraphrase Models (Sentence Transformers) ===
  'paraphrase-multilingual': {
    parameters: '~278M',
    context_length: '512 tokens',
    speed: 'moderate',
    accuracy: 'excellent',
    best_for: ['50+ languages', 'Semantic similarity', 'Clustering'],
    description: 'Sentence-transformers model supporting 50+ languages. Excellent for clustering and semantic similarity.',
  },
}

const getModelStats = (name: string): ModelStats => {
  const baseName = name.split(':')[0]
  return MODEL_STATS_DB[baseName] || {
    parameters: 'Unknown',
    context_length: 'Standard',
    speed: 'moderate',
    accuracy: 'good',
    best_for: ['Embeddings'],
  }
}

const getSpeedColor = (speed: string) => {
  if (speed === 'fast') return 'text-emerald-600 bg-emerald-500/10 border-emerald-500/20'
  if (speed === 'moderate') return 'text-amber-600 bg-amber-500/10 border-amber-500/20'
  return 'text-red-600 bg-red-500/10 border-red-500/20'
}

const getAccuracyColor = (accuracy: string) => {
  if (accuracy === 'superior') return 'text-purple-600 bg-purple-500/10 border-purple-500/20'
  if (accuracy === 'excellent') return 'text-blue-600 bg-blue-500/10 border-blue-500/20'
  return 'text-slate-600 bg-slate-500/10 border-slate-500/20'
}

// =============================================================================
// PROGRESS DIALOG - Shows during long operations
// =============================================================================

const ProgressDialog = ({ 
  isOpen, 
  title, 
  message,
}: { 
  isOpen: boolean
  title: string
  message: string
}) => (
  <Dialog open={isOpen}>
    <DialogContent 
      className="sm:max-w-md [&>button]:hidden" 
      onPointerDownOutside={(e) => e.preventDefault()}
      onEscapeKeyDown={(e) => e.preventDefault()}
      onInteractOutside={(e) => e.preventDefault()}
    >
      <DialogHeader>
        <DialogTitle className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 text-primary animate-spin" />
          {title}
        </DialogTitle>
        <DialogDescription>{message}</DialogDescription>
      </DialogHeader>
      <div className="py-4">
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary animate-pulse w-full" />
        </div>
        <p className="text-xs text-center text-muted-foreground mt-4">
          Please wait. This may take a few moments...
        </p>
      </div>
    </DialogContent>
  </Dialog>
)

// =============================================================================
// ACTIVE MODEL STATUS - Shows current active model prominently
// =============================================================================

interface ActiveModelStatusProps {
  activeModel: string | null
  activeModelInfo: EmbeddingModel | null
  dimension: number | null
}

const ActiveModelStatus = ({ activeModel, activeModelInfo, dimension }: ActiveModelStatusProps) => {
  const stats = activeModel ? getModelStats(activeModel) : null
  
  if (!activeModel) {
    return (
      <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 via-card to-card p-6">
        <div className="flex items-center gap-4">
          <div className="p-4 rounded-xl bg-amber-500/20 ring-4 ring-amber-500/10">
            <AlertTriangle className="h-6 w-6 text-amber-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-amber-600 uppercase tracking-wider">No Active Model</p>
            <p className="text-lg font-bold text-foreground mt-1">
              Select a model below to get started
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Choose a model and click "Download & Activate" to enable embedding operations
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 via-card to-card p-6">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-60 h-60 bg-gradient-to-bl from-primary/30 via-primary/10 to-transparent rounded-full blur-3xl" />
      
      <div className="relative flex items-center gap-5">
        <div className="p-4 rounded-xl bg-primary/20 ring-4 ring-primary/10 shadow-lg shadow-primary/20">
          <Crown className="h-7 w-7 text-primary" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active Default Model</p>
            <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full">
              <div className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </div>
              Ready
            </span>
          </div>
          <h3 className="text-2xl font-bold text-foreground mt-1">
            {activeModelInfo?.display_name || activeModel}
          </h3>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            {dimension && (
              <span className="text-sm px-3 py-1 rounded-lg bg-muted/50 text-muted-foreground font-mono border border-border/40">
                {dimension}D vectors
              </span>
            )}
            {stats && (
              <>
                <span className={cn("text-xs px-2 py-1 rounded border", getSpeedColor(stats.speed))}>
                  {stats.speed}
                </span>
                <span className={cn("text-xs px-2 py-1 rounded border", getAccuracyColor(stats.accuracy))}>
                  {stats.accuracy}
                </span>
              </>
            )}
          </div>
        </div>
        <CheckCircle2 className="h-8 w-8 text-emerald-500 shrink-0" />
      </div>
      
      <p className="relative text-xs text-muted-foreground mt-4 pt-4 border-t border-border/30">
        <Info className="h-3.5 w-3.5 inline mr-1.5" />
        This model is used for all embedding operations: dataset embeddings, semantic search, and similarity matching.
      </p>
    </div>
  )
}

// =============================================================================
// MODEL ROW - Simple inline display with action buttons
// =============================================================================

interface ModelRowProps {
  model: EmbeddingModel
  onAction: () => void
  isLoading: boolean
  actionLabel: string
  actionIcon: React.ReactNode
  isActive?: boolean
  actionVariant?: 'default' | 'secondary'
}

const ModelRow = ({ model, onAction, isLoading, actionLabel, actionIcon, isActive, actionVariant = 'default' }: ModelRowProps) => {
  const stats = getModelStats(model.name)
  const [showDetails, setShowDetails] = useState(false)

  const handleAction = () => {
    console.log('[ModelRow] handleAction called for:', model.name)
    onAction()
  }

  return (
    <div className={cn(
      "border rounded-xl overflow-hidden transition-all",
      isActive 
        ? "border-primary/40 bg-primary/5 ring-2 ring-primary/20" 
        : model.is_local 
          ? "border-border/40 bg-card/50 hover:border-border/60"
          : "border-border/30 bg-muted/30 hover:border-border/50"
    )}>
      {/* Main Row */}
      <div className="flex items-center gap-3 p-3">
        {/* Icon */}
        <div className={cn(
          "p-2 rounded-lg shrink-0",
          isActive 
            ? "bg-primary/20" 
            : model.is_local 
              ? "bg-muted/50"
              : "bg-muted/30"
        )}>
          {isActive ? (
            <Crown className="h-4 w-4 text-primary" />
          ) : model.is_local ? (
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          ) : (
            <Cloud className="h-4 w-4 text-muted-foreground/60" />
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm">{model.display_name || model.name}</span>
            {model.dimension && (
              <span className="text-xs font-mono text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded">
                {model.dimension}D
              </span>
            )}
            {isActive && (
              <span className="text-xs text-primary font-semibold bg-primary/10 px-2 py-0.5 rounded-full">
                ★ Active
              </span>
            )}
            {!isActive && model.is_local && (
              <span className="text-xs text-muted-foreground">Downloaded</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
            <span className={cn("px-1.5 py-0.5 rounded border", getSpeedColor(stats.speed))}>
              {stats.speed}
            </span>
            <span className={cn("px-1.5 py-0.5 rounded border", getAccuracyColor(stats.accuracy))}>
              {stats.accuracy}
            </span>
            {model.size && <span>{model.size}</span>}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDetails(!showDetails)}
            className="h-8 px-2"
          >
            <Info className="h-3.5 w-3.5" />
          </Button>
          
          {isActive ? (
            <span className="text-xs text-primary font-medium px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20">
              Current Default
            </span>
          ) : (
            <Button
              size="sm"
              variant={actionVariant}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                handleAction()
              }}
              disabled={isLoading}
              className="h-8 gap-1.5"
              type="button"
            >
              {isLoading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                actionIcon
              )}
              {isLoading ? 'Working...' : actionLabel}
            </Button>
          )}
        </div>
      </div>

      {/* Details Panel */}
      {showDetails && (
        <div className="px-3 pb-3 pt-0 border-t border-border/30 bg-muted/30">
          {stats.description && (
            <p className="text-xs text-muted-foreground pt-3 pb-2 italic">
              {stats.description}
            </p>
          )}
          <div className="grid grid-cols-3 gap-3 pt-2 text-xs">
            <div>
              <span className="text-muted-foreground">Parameters</span>
              <p className="font-medium">{stats.parameters}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Context</span>
              <p className="font-medium">{stats.context_length}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Best for</span>
              <p className="font-medium">{stats.best_for.join(', ')}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface EmbeddingModelPickerProps {
  onModelActivated?: (modelName: string, dimension: number) => void;
}

export const EmbeddingModelPicker = ({ onModelActivated }: EmbeddingModelPickerProps = {}) => {
  const queryClient = useQueryClient()
  const [isExpanded, setIsExpanded] = useState(true) // Start expanded by default
  const [showAllAvailable, setShowAllAvailable] = useState(false)
  const [processingModel, setProcessingModel] = useState<string | null>(null)
  const [progressTitle, setProgressTitle] = useState('')
  const [progressMessage, setProgressMessage] = useState('')

  // Fetch available models
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['embedding-models-available'],
    queryFn: () => apiClient.listEmbeddingModels(),
    staleTime: 60000,
  })

  // Fetch user settings to get current active model
  const { data: userSettings } = useQuery({
    queryKey: ['userSettings'],
    queryFn: () => apiClient.getUserSettings(),
    staleTime: 30000,
  })

  const activeModel = userSettings?.default_embedding_model || null
  const activeDimension = userSettings?.embedding_dimension || null

  // Download & Activate mutation (for remote models)
  // This downloads the model AND sets it as the active default
  const downloadAndActivateMutation = useMutation({
    mutationFn: async (modelName: string) => {
      // Check if model is already available locally to avoid re-pulling on retries
      const availableModels = await apiClient.listEmbeddingModels()
      const existingModel = availableModels.models.find(
        m => m.name === modelName && m.is_local
      )
      
      let pullResult: { model_id: string; dimension: number; display_name: string; status: string }
      
      if (existingModel && existingModel.dimension) {
        // Model already exists locally, use existing info
        pullResult = {
          model_id: modelName,
          dimension: existingModel.dimension,
          display_name: existingModel.display_name,
          status: 'already_available'
        }
      } else {
        // Step 1: Pull the model (this also registers it)
        pullResult = await apiClient.pullEmbeddingModel(modelName)
      }
      
      // Step 2: Set as active default - wrap in try/catch for partial failure handling
      const dimension = pullResult.dimension
      try {
        await apiClient.updateUserSettings({
          default_embedding_model: modelName,
          embedding_dimension: dimension
        })
      } catch (settingsError: any) {
        // Model downloaded but failed to set as default
        throw {
          detail: `Model "${modelName}" downloaded successfully (${dimension}D) but failed to set as default: ${settingsError?.detail || settingsError?.message || 'Unknown error'}`,
          modelName,
          dimension,
          partialSuccess: true
        }
      }
      
      return { ...pullResult, dimension }
    },
    onMutate: (modelName) => {
      setProcessingModel(modelName)
      setProgressTitle('Downloading & Activating')
      setProgressMessage(`Downloading ${modelName} and setting as your default model. This may take several minutes...`)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['embedding-models-available'] })
      queryClient.invalidateQueries({ queryKey: ['userSettings'] })
      toast({
        title: '✓ Model Downloaded & Activated',
        description: `${result.display_name || result.model_id} is now your default (${result.dimension}D)`,
      })
      if (onModelActivated) {
        onModelActivated(result.model_id, result.dimension)
      }
    },
    onError: (err: any) => {
      toast({
        title: 'Download Failed',
        description: err?.detail || err?.message || 'Could not download model',
        variant: 'destructive',
      })
    },
    onSettled: () => {
      setProcessingModel(null)
    },
  })

  // Set as Default mutation (for already downloaded models)
  const setAsDefaultMutation = useMutation({
    mutationFn: async (modelName: string) => {
      // First ensure model is registered
      const registerResult = await apiClient.registerEmbeddingModel(modelName, false)
      
      // Then set as default
      await apiClient.updateUserSettings({
        default_embedding_model: modelName,
        embedding_dimension: registerResult.dimension
      })
      
      return registerResult
    },
    onMutate: (modelName) => {
      setProcessingModel(modelName)
      setProgressTitle('Setting as Default')
      setProgressMessage(`Activating ${modelName} as your default embedding model...`)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['embedding-models-available'] })
      queryClient.invalidateQueries({ queryKey: ['userSettings'] })
      toast({
        title: '✓ Default Model Updated',
        description: `${result.display_name || result.model_id} is now your default (${result.dimension}D)`,
      })
      if (onModelActivated) {
        onModelActivated(result.model_id, result.dimension)
      }
    },
    onError: (err: any) => {
      toast({
        title: 'Activation Failed',
        description: err?.detail || err?.message || 'Could not set model as default',
        variant: 'destructive',
      })
    },
    onSettled: () => {
      setProcessingModel(null)
    },
  })

  const models = data?.models || []
  
  // Find the active model info
  const activeModelInfo = models.find(m => m.name === activeModel) || null
  
  // Separate models: Downloaded (local) vs Available (not local)
  // Exclude the active model from the downloaded list since it's shown separately
  const downloadedModels = models.filter(m => m.is_local && m.name !== activeModel)
  const availableToDownload = models.filter(m => !m.is_local)
  
  const visibleAvailable = showAllAvailable ? availableToDownload : availableToDownload.slice(0, 5)

  return (
    <>
      {/* Progress Dialog */}
      <ProgressDialog 
        isOpen={!!processingModel}
        title={progressTitle}
        message={progressMessage}
      />

      <div className="space-y-4">
        {/* Active Model Status - Always visible */}
        <ActiveModelStatus 
          activeModel={activeModel}
          activeModelInfo={activeModelInfo}
          dimension={activeDimension}
        />

        {/* Model Management Panel */}
        <div className="rounded-2xl border border-border/40 bg-card/80 backdrop-blur-xl overflow-hidden">
          {/* Header */}
          <button
            className="w-full flex items-center justify-between p-5 hover:bg-muted/20 transition-colors"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg">
                <Server className="h-5 w-5 text-white" />
              </div>
              <div className="text-left">
                <h3 className="font-bold text-foreground">Manage Embedding Models</h3>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {downloadedModels.length} downloaded • {availableToDownload.length} available
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={(e) => {
                  e.stopPropagation()
                  refetch()
                }}
                disabled={isLoading}
              >
                <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
              </Button>
              <ChevronDown className={cn(
                "h-4 w-4 text-muted-foreground transition-transform",
                isExpanded && "rotate-180"
              )} />
            </div>
          </button>

          {/* Content */}
          {isExpanded && (
            <div className="border-t border-border/40 p-5 space-y-6">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  <span className="ml-2 text-muted-foreground">Loading models...</span>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Failed to load. Is Ollama running?</p>
                  <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
                    Retry
                  </Button>
                </div>
              ) : (
                <>
                  {/* Section 1: Downloaded models - Set as Default */}
                  {downloadedModels.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                        <h4 className="font-semibold text-sm">Downloaded Models</h4>
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          {downloadedModels.length}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground -mt-1">
                        These models are on your system. Click <strong>Set as Default</strong> to use one.
                      </p>
                      <div className="space-y-2">
                        {downloadedModels.map((model) => (
                          <ModelRow
                            key={model.name}
                            model={model}
                            isActive={false}
                            onAction={() => {
                              console.log('[EmbeddingModelPicker] Set as Default clicked for:', model.name)
                              setAsDefaultMutation.mutate(model.name)
                            }}
                            isLoading={processingModel === model.name}
                            actionLabel="Set as Default"
                            actionIcon={<Crown className="h-3.5 w-3.5" />}
                            actionVariant="secondary"
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Section 2: Available to download */}
                  {availableToDownload.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Cloud className="h-4 w-4 text-muted-foreground" />
                        <h4 className="font-semibold text-sm">Available to Download</h4>
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          {availableToDownload.length}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground -mt-1">
                        Click <strong>Download & Activate</strong> to download and set as your default model.
                      </p>
                      <div className="space-y-2">
                        {visibleAvailable.map((model) => (
                          <ModelRow
                            key={model.name}
                            model={model}
                            isActive={false}
                            onAction={() => {
                              console.log('[EmbeddingModelPicker] Download & Activate clicked for:', model.name)
                              downloadAndActivateMutation.mutate(model.name)
                            }}
                            isLoading={processingModel === model.name}
                            actionLabel="Download & Activate"
                            actionIcon={<Download className="h-3.5 w-3.5" />}
                          />
                        ))}
                      </div>
                      
                      {availableToDownload.length > 5 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowAllAvailable(!showAllAvailable)}
                          className="w-full text-muted-foreground"
                        >
                          {showAllAvailable ? (
                            <>Show Less <ChevronUp className="h-4 w-4 ml-1" /></>
                          ) : (
                            <>Show {availableToDownload.length - 5} More <ChevronDown className="h-4 w-4 ml-1" /></>
                          )}
                        </Button>
                      )}
                    </div>
                  )}

                  {/* Empty state */}
                  {downloadedModels.length === 0 && availableToDownload.length === 0 && (
                    <div className="text-center py-8">
                      <Server className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
                      <p className="text-sm text-muted-foreground">No embedding models found.</p>
                      <p className="text-xs text-muted-foreground mt-1">Make sure Ollama is running.</p>
                    </div>
                  )}

                  {/* Help text */}
                  <div className="rounded-lg bg-blue-500/5 border border-blue-500/20 p-3 text-xs text-muted-foreground">
                    <Info className="h-4 w-4 text-blue-500 inline mr-2" />
                    <strong>Unified workflow:</strong> Click "Download & Activate" to download a model and immediately set it as your default for all embedding operations.
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default EmbeddingModelPicker
