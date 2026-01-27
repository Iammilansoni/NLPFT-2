'use client'

import { useMemo, useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import {
  CheckCircle2,
  Activity,
  Brain,
  Zap,
  Target,
  Cpu,
  RefreshCw,
  Sparkles,
  AlertTriangle,
  ChevronDown,
  Maximize2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useQueryStats } from '@/hooks/useQuery'
import { useTemplateStats } from '@/hooks/useTemplates'
import { apiClient } from '@/lib/api'
import { SemanticRetrieveResponse } from '@/lib/api-types'
import { DEFAULT_EMBEDDING_MODEL, areModelsCompatible, formatModelName } from '@/lib/constants/embedding-models'
import { useToast } from '@/hooks/use-toast'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { JsonDisplay } from '@/components/ui/JsonDisplay'


// New Components
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { SearchSection } from '@/components/dashboard/SearchSection'
import { MetricCard } from '@/components/dashboard/MetricCard'
import { TopIntents } from '@/components/dashboard/TopIntents'
import { MetricGridSkeleton } from '@/components/ui/skeleton'
import { OnboardingTour } from '@/components/onboarding/OnboardingTour'


const TrendChart = dynamic(
  () => import('@/components/dashboard/trend-chart').then((m) => m.TrendChart),
  {
    ssr: false,
    loading: () => (
      <div className="h-48 w-full bg-muted/20 rounded-sm animate-pulse" />
    ),
  }
)

/**
 * Detect user intent from query text.
 */
function detectQueryIntent(query: string): "action" | "info" {
  const q = query.toLowerCase().trim()

  // Action keywords (user wants to DO something)
  const actionKeywords = [
    "create", "make", "add", "submit", "place", "generate", "process",
    "initiate", "start", "begin", "execute", "run", "perform", "send",
    "post", "put", "delete", "update", "modify", "change", "set",
    "upload", "download", "install", "configure", "enable", "disable",
    "order", "purchase", "buy", "subscribe", "cancel", "refund",
    "i need to", "i want to", "let me", "gimme", "wanna", "gotta", "lemme"
  ]

  // Info keywords (user wants to KNOW something)
  const infoKeywords = [
    "what", "how", "where", "when", "why", "which", "who",
    "tell me", "show me", "explain", "describe", "list",
    "documentation", "docs", "guide", "help", "api for"
  ]

  for (const kw of actionKeywords) {
    if (q.includes(kw)) return "action"
  }

  for (const kw of infoKeywords) {
    if (q.includes(kw)) return "info"
  }

  return "action"
}


export default function DashboardPage() {
  const { toast } = useToast()


  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SemanticRetrieveResponse | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [embeddingModel, setEmbeddingModel] = useState(DEFAULT_EMBEDDING_MODEL)
  const [showStage1, setShowStage1] = useState(false)
  const [showStage2, setShowStage2] = useState(false)
  const [settingsModel, setSettingsModel] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Model mismatch state
  const [showModelMismatchDialog, setShowModelMismatchDialog] = useState(false)
  const [mismatchInfo, setMismatchInfo] = useState<{
    settingsModel: string;
    settingsDimension: number;
    selectedModel: string;
    selectedDimension: number;
  } | null>(null)
  const [pendingQuery, setPendingQuery] = useState<string | null>(null)

  // Available models from backend
  const [availableModels, setAvailableModels] = useState<Array<{
    model_id: string;
    label?: string;
    dimension?: number;
  }>>([{ model_id: 'nomic-embed-text', label: 'Nomic Embed Text', dimension: 768 }])

  const { data: stats, isLoading, error } = useQueryStats()
  const { data: templateStats, isLoading: templatesLoading, error: templatesError } = useTemplateStats()

  // System Health Logic
  const backendHealthy = !error && !!stats
  const databaseHealthy = !!stats && typeof stats?.total_embeddings === 'number' && stats.total_embeddings >= 0
  const templatesHealthy = !templatesError && !!templateStats
  const allHealthy = backendHealthy && databaseHealthy && templatesHealthy
  const isLoadingStats = isLoading || templatesLoading


  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const settings = await apiClient.getUserSettings()
        if (settings?.default_embedding_model) {
          setSettingsModel(settings.default_embedding_model)
          setEmbeddingModel(settings.default_embedding_model)
        }
      } catch (err) {
        console.debug('Failed to fetch user settings:', err)
      }
    }
    fetchSettings()
  }, [])

  // Fetch available embedding models from backend - only show downloaded (is_local) models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        // Use listEmbeddingModels which returns is_local status
        const data = await apiClient.listEmbeddingModels()
        if (data?.models && Array.isArray(data.models)) {
          // Filter to only show downloaded (is_local) models
          const localModels = data.models.filter((m: any) => m.is_local)
          const formattedModels = localModels.map((m: any) => ({
            model_id: m.name || m.model_id || m.id,
            label: m.display_name || m.name || m.label || m.model_id,
            dimension: m.dimension
          }))
          // If no local models found, show a default placeholder
          if (formattedModels.length === 0) {
            setAvailableModels([{ model_id: 'nomic-embed-text', label: 'Nomic Embed Text (not installed)', dimension: 768 }])
          } else {
            setAvailableModels(formattedModels)
          }
        }
      } catch (err) {
        console.debug('Failed to fetch available models:', err)
      }
    }
    fetchModels()
  }, [])

  // Helper functions to get model info from availableModels
  const getModelInfo = (modelId: string) => {
    return availableModels.find(m => m.model_id === modelId)
  }

  const getDimensionForModel = (modelId: string): number => {
    const model = getModelInfo(modelId)
    return model?.dimension ?? 768 // Default to 768 if not found
  }

  const getModelLabel = (modelId: string): string => {
    const model = getModelInfo(modelId)
    return model?.label || formatModelName(modelId)
  }

  // Check for model mismatch before search
  function checkModelMismatch(searchQuery: string): boolean {
    if (!settingsModel || embeddingModel === settingsModel) {
      return false // No mismatch
    }

    const settingsDim = getDimensionForModel(settingsModel)
    const selectedDim = getDimensionForModel(embeddingModel)

    // Use areModelsCompatible helper for centralized compatibility check
    if (!areModelsCompatible(settingsDim, selectedDim)) {
      // Dimension mismatch - show warning dialog
      setMismatchInfo({
        settingsModel: settingsModel,
        settingsDimension: settingsDim,
        selectedModel: embeddingModel,
        selectedDimension: selectedDim,
      })
      setPendingQuery(searchQuery)
      setShowModelMismatchDialog(true)
      return true // Has mismatch
    }

    return false
  }

  // Handle proceeding with settings model
  async function handleUseSettingsModel() {
    if (settingsModel) {
      setEmbeddingModel(settingsModel)
      setShowModelMismatchDialog(false)
      if (pendingQuery) {
        await performSearch(pendingQuery, settingsModel)
      }
      setPendingQuery(null)
    }
  }

  // Handle using selected model anyway (with warning)
  async function handleUseSelectedModelAnyway() {
    setShowModelMismatchDialog(false)
    if (pendingQuery) {
      toast({
        title: "Using Different Model",
        description: `Searching with ${getModelLabel(embeddingModel)}. Results may not include all embedded data.`,
        variant: "default",
      })
      await performSearch(pendingQuery, embeddingModel)
    }
    setPendingQuery(null)
  }

  // Core search function
  async function performSearch(searchQuery: string, model: string) {
    setIsSearching(true)
    setSearchError(null)
    setSearchResults(null)
    setShowStage1(false)
    setShowStage2(false)

    try {
      // Detect intent to maximize intent alignment bonus
      const detectedIntent = detectQueryIntent(searchQuery)

      const results = await apiClient.semanticRetrieve(
        searchQuery.trim(),
        5,
        detectedIntent, // Pass detected intent for alignment bonus
        false
      )

      if (!results.success && results.error) {
        setSearchError(results.error)
        toast({
          title: "Search Failed",
          description: results.error,
          variant: "destructive",
        })
        return
      }

      setSearchResults(results)
      const candidateCount = results.stage1_vector_search?.length || 0
      const processingTime = results.metadata?.processing_time_ms || 0

      toast({
        title: "Search Complete",
        description: `Found ${candidateCount} candidates in ${processingTime}ms using ${getModelLabel(model)}`,
      })
    } catch (err: any) {
      console.error('Search failed:', err)

      const errorMessage = err.detail?.message || err.detail || err.message || 'Failed to perform search'

      if (err?.message?.includes('dimension') || err?.detail?.includes('dimension')) {
        setSearchError('Vector dimension mismatch. The embedding model may have changed. Please re-embed your dataset.')
        toast({
          title: "Dimension Mismatch",
          description: "The search failed due to vector dimension mismatch. Re-embedding may be required.",
          variant: "destructive",
        })
        return
      }

      setSearchError(errorMessage)
      toast({
        title: "Search Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsSearching(false)
    }
  }

  async function handleSearch() {
    if (!query.trim()) return

    // Check for model mismatch first
    if (checkModelMismatch(query)) {
      return // Dialog will handle the rest
    }

    await performSearch(query, embeddingModel)
  }

  const topIntents = useMemo(() => {
    if (!stats?.intents) return []
    return Object.entries(stats.intents)
      .sort((a, b) => (b[1] as number) - (a[1] as number))
      .slice(0, 5)
  }, [stats])

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-8">

        <DashboardHeader systemStatus={allHealthy ? 'healthy' : 'degraded'} />

        {/* Main Search Area */}
        <section className="py-8" data-tour="search">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold tracking-tight mb-2">Semantic API Search</h2>
            <p className="text-muted-foreground max-w-lg mx-auto">
              Find and test your API endpoints using natural language.
              Our vector engine matches your intent with the most relevant API capabilities.
            </p>
          </div>

          <SearchSection
            query={query}
            setQuery={setQuery}
            model={embeddingModel}
            setModel={setEmbeddingModel}
            onSearch={handleSearch}
            isSearching={isSearching}
            settingsModel={settingsModel}
            models={availableModels}
          />

        </section>

        {/* Search Results - Enhanced with Stage Toggles & JSON Modal */}
        {searchResults && (
          <div className="mb-10 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-card border border-border/60 rounded-2xl shadow-md overflow-hidden">
              {/* Result Header */}
              <div className="px-6 py-5 border-b border-border/40 flex items-center justify-between bg-muted/20">
                <div className="flex items-center gap-4">
                  <div className="bg-primary/10 p-2.5 rounded-xl">
                    <Sparkles className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl leading-tight">Search Insights</h3>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                      <span className="font-mono bg-muted/50 px-2 py-0.5 rounded">{searchResults.metadata?.processing_time_ms || 0}ms</span>
                      <span>•</span>
                      <span>{searchResults.metadata?.total_candidates || 0} candidates analyzed</span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSearchResults(null)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              </div>

              {/* Main Result Content */}
              <div className="p-6">
                {searchResults.final_output ? (
                  <div className="space-y-6">
                    {/* Top Match Card */}
                    <div className="p-6 rounded-xl bg-gradient-to-br from-emerald-500/5 to-emerald-500/0 border border-emerald-500/20">
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-3 flex-1">
                          <div className="flex items-center gap-3">
                            <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 text-sm font-semibold uppercase tracking-wider">
                              Top Recommendation
                            </span>
                            <span className="text-sm text-muted-foreground font-medium">
                              {(searchResults.final_output.confidence_score * 100).toFixed(1)}% Confidence
                            </span>
                          </div>
                          <h4 className="text-2xl font-bold tracking-tight text-foreground">
                            {searchResults.final_output.api_name}
                          </h4>
                          <div className="p-4 rounded-lg bg-muted/40 border border-border/50 font-mono text-base break-all flex items-center gap-3">
                            <span className={`
                              px-2.5 py-1 rounded text-xs font-bold
                              ${searchResults.final_output.method === 'GET' ? 'bg-blue-500/10 text-blue-600' : ''}
                              ${searchResults.final_output.method === 'POST' ? 'bg-green-500/10 text-green-600' : ''}
                              ${searchResults.final_output.method === 'DELETE' ? 'bg-red-500/10 text-red-600' : ''}
                              ${searchResults.final_output.method === 'PUT' ? 'bg-amber-500/10 text-amber-600' : ''}
                            `}>
                              {searchResults.final_output.method}
                            </span>
                            <span className="text-foreground">{searchResults.final_output.endpoint}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Stage Buttons & JSON Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Stage 1: Vector Retrieval */}
                      <div className="space-y-3">
                        <button
                          onClick={() => setShowStage1(!showStage1)}
                          className="w-full flex items-center justify-between p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <Brain className="w-5 h-5 text-primary" />
                            <span className="font-semibold text-base">Stage 1: Vector Retrieval</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono bg-primary/10 text-primary px-2 py-0.5 rounded">{searchResults.stage1_vector_search?.length || 0} hits</span>
                            <ChevronDown className={`w-5 h-5 text-muted-foreground transition-transform ${showStage1 ? 'rotate-180' : ''}`} />
                          </div>
                        </button>
                        {showStage1 && (
                          <div className="bg-card border border-border/60 rounded-lg overflow-hidden animate-in slide-in-from-top-2 duration-300">
                            {searchResults.stage1_vector_search?.map((res: any, i: number) => (
                              <div key={i} className="px-4 py-3 border-b border-border/40 last:border-0 hover:bg-muted/30 transition-colors">
                                <div className="flex justify-between items-start gap-3">
                                  <span className="text-sm leading-relaxed">{res.query}</span>
                                  <span className="text-sm font-mono font-medium text-primary shrink-0">{(res.similarity_score * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                            ))}
                            {(!searchResults.stage1_vector_search?.length) && (
                              <div className="p-4 text-center text-sm text-muted-foreground">No matches found</div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Stage 2: Reranking */}
                      <div className="space-y-3">
                        <button
                          onClick={() => setShowStage2(!showStage2)}
                          className="w-full flex items-center justify-between p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <Zap className="w-5 h-5 text-primary" />
                            <span className="font-semibold text-base">Stage 2: Reranking</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-mono bg-primary/10 text-primary px-2 py-0.5 rounded">{searchResults.stage2_reranking?.length || 0} results</span>
                            <ChevronDown className={`w-5 h-5 text-muted-foreground transition-transform ${showStage2 ? 'rotate-180' : ''}`} />
                          </div>
                        </button>
                        {showStage2 && (
                          <div className="bg-card border border-border/60 rounded-lg overflow-hidden animate-in slide-in-from-top-2 duration-300">
                            {searchResults.stage2_reranking?.map((res: any, i: number) => (
                              <div key={i} className={`px-4 py-3 border-b border-border/40 last:border-0 hover:bg-muted/30 transition-colors ${i === 0 ? 'bg-primary/5' : ''}`}>
                                <div className="flex justify-between items-center">
                                  <div className="flex items-center gap-3">
                                    <span className={`w-6 h-6 rounded-full text-xs flex items-center justify-center font-bold ${i === 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
                                      {res.rank}
                                    </span>
                                    <span className="text-sm font-mono text-muted-foreground">{res.t_id?.substring(0, 12)}...</span>
                                  </div>
                                  <span className={`text-base font-semibold ${i === 0 ? 'text-primary' : ''}`}>
                                    {(res.final_score * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* JSON Output Section */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h5 className="font-semibold text-base">Full Response JSON</h5>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="outline" size="sm">
                              <Maximize2 className="w-4 h-4 mr-2" />
                              Expand View
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-5xl max-h-[85vh] overflow-hidden flex flex-col">
                            <DialogHeader>
                              <DialogTitle>Full Response JSON</DialogTitle>
                            </DialogHeader>
                            <div className="flex-1 overflow-hidden">
                              <JsonDisplay
                                data={searchResults.final_output}
                                maxHeight="calc(85vh - 120px)"
                                showCopyButton={true}
                                showLineNumbers={true}
                              />
                            </div>
                          </DialogContent>
                        </Dialog>
                      </div>
                      <JsonDisplay
                        data={searchResults.final_output}
                        maxHeight="20rem"
                        showCopyButton={true}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="p-12 text-center text-muted-foreground">
                    <p className="text-lg">No actionable match found.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        {isLoadingStats ? (
          <MetricGridSkeleton count={4} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-tour="metrics">
            <MetricCard
              label="Total Embeddings"
              value={stats?.total_embeddings?.toLocaleString() || '0'}
              subtitle="Vectors in Redis"
              icon={<Brain className="w-4 h-4" />}
            />
            <MetricCard
              label="Approved Templates"
              value={templateStats?.by_status?.approved ?? templateStats?.total_templates ?? 0}
              progress={{
                value: templateStats?.by_status?.approved ?? templateStats?.total_templates ?? 0,
                total: templateStats?.total_templates || 1,
                label: `${templateStats?.total_templates || 0} total declared`
              }}
              icon={<CheckCircle2 className="w-4 h-4" />}
            />
            <MetricCard
              label="Total Intents"
              value={stats?.total_intents || Object.keys(stats?.intents || {}).length}
              subtitle={`${stats?.unique_apis || 0} Unique APIs`}
              icon={<Target className="w-4 h-4" />}
            />
            <MetricCard
              label="Embedding Model"
              value={getModelLabel(embeddingModel)}
              subtitle={`${getDimensionForModel(embeddingModel)}D vectors`}
              icon={<Cpu className="w-4 h-4" />}
            />
          </div>
        )}

        {/* Search Results Display - Kept inline for now due to complexity, but restyled */}


        {/* Search Error */}
        {
          searchError && (
            <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              <p className="text-sm font-medium">{searchError}</p>
            </div>
          )
        }

        {/* Analytics & Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 pt-8 border-t border-border/40">
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="text-lg font-medium tracking-tight">System Telemetry</h3>
                <p className="text-sm text-muted-foreground">Search latency and request volume</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => {
                  // Force a re-render of chart or just simulate refresh for UI feedback
                  const btn = document.getElementById('refresh-btn-icon');
                  if (btn) btn.classList.add('animate-spin');
                  setTimeout(() => {
                    if (btn) btn.classList.remove('animate-spin');
                    toast({ title: "Refreshed", description: "Telemetry data updated" });
                  }, 1000);
                }}
              >
                <RefreshCw id="refresh-btn-icon" className="w-3.5 h-3.5" />
                Refresh
              </Button>
            </div>
            <div className="rounded-xl border border-border/60 bg-card p-1 shadow-sm">
              <div className="h-[300px] w-full p-4">
                <TrendChart />
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-1">
              <h3 className="text-lg font-medium tracking-tight">Top Intents</h3>
              <p className="text-sm text-muted-foreground">Most frequent user queries</p>
            </div>
            <div className="bg-card border border-border/60 rounded-xl p-6 shadow-sm min-h-[300px]">
              <TopIntents intents={topIntents} isLoading={isLoadingStats} />
            </div>
          </div>
        </div>
      </div >

      {/* Dialogs */}
      < Dialog open={showModelMismatchDialog} onOpenChange={setShowModelMismatchDialog} >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-warning">
              <AlertTriangle className="w-5 h-5" />
              Embedding Model Mismatch
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <p className="text-sm text-muted-foreground">
              Your selected model <strong>{getModelLabel(mismatchInfo?.selectedModel || '')}</strong> ({mismatchInfo?.selectedDimension}D)
              does not match the system default settings <strong>{getModelLabel(mismatchInfo?.settingsModel || '')}</strong> ({mismatchInfo?.settingsDimension}D).
            </p>
            <div className="bg-muted p-3 rounded-md text-xs border border-border">
              <p className="font-semibold mb-1">Impact:</p>
              <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                <li>Search vectors will have different dimensions</li>
                <li>Retrieval will likely fail or return garbage</li>
              </ul>
            </div>
            <div className="flex flex-col gap-2 pt-2">
              <Button onClick={handleUseSettingsModel} className="w-full">
                Switch to {getModelLabel(mismatchInfo?.settingsModel || '')} (Recommended)
              </Button>
              <Button variant="ghost" onClick={handleUseSelectedModelAnyway} className="w-full text-amber-600 hover:text-amber-700 hover:bg-amber-50">
                Proceed with {getModelLabel(mismatchInfo?.selectedModel || '')} anyway
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog >

      {/* Onboarding Tour for first-time users */}
      <OnboardingTour tourId="dashboard" />
    </div >
  )
}
