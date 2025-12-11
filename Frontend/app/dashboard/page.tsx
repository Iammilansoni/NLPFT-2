'use client'

import { useMemo, useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { motion } from 'framer-motion'
import {
  CheckCircle2,
  FileCode,
  Activity,
  Brain,
  Zap,
  ArrowRight,
  Search,
  Command,
  Terminal,
  Cpu,
  Target,
  Plus,
  X,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { useQueryStats } from '@/hooks/useQuery'
import { useTemplateStats } from '@/hooks/useTemplates'
import { apiClient } from '@/lib/api'
import { EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL, getEmbeddingModelInfo } from '@/lib/constants/embedding-models'
import { GlassCard } from '@/components/ui/GlassCard'
import { MagneticButton } from '@/components/ui/MagneticButton'
import { ModelMismatchDialog } from '@/components/ui/model-mismatch-dialog'
import { toast } from '@/hooks/use-toast'

const TrendChart = dynamic(
  () => import('@/components/dashboard/trend-chart').then((m) => m.TrendChart),
  {
    ssr: false,
    loading: () => (
      <div className="h-64 w-full bg-muted/10 animate-pulse rounded-2xl border border-dashed border-muted" />
    ),
  }
)

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { 
    opacity: 1, 
    y: 0,
    transition: { 
      type: "spring",
      stiffness: 50,
      damping: 20
    }
  },
}

export default function DashboardPage() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<{
    query: string;
    ranked_results: Array<{ rank: number; score: number; text: string }>;
    stage1_results?: any[];
  } | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [embeddingModel, setEmbeddingModel] = useState(DEFAULT_EMBEDDING_MODEL)
  const [showStage1, setShowStage1] = useState(false)
  
  // Model mismatch dialog state
  const [showMismatchDialog, setShowMismatchDialog] = useState(false)
  const [mismatchInfo, setMismatchInfo] = useState<{
    datasetModel: string
    settingsModel: string
    datasetId: string
    datasetName?: string
  } | null>(null)
  const [isReEmbedding, setIsReEmbedding] = useState(false)

  // Use our custom hooks for backend data
  const { data: stats, isLoading, error } = useQueryStats()
  const { data: templateStats, isLoading: templatesLoading, error: templatesError } = useTemplateStats()

  // Calculate detailed health status with safe defaults
  const backendHealthy = !error && !!stats
  const databaseHealthy = !!stats && typeof stats?.total_embeddings === 'number' && stats.total_embeddings >= 0
  const templatesHealthy = !templatesError && !!templateStats

  const allHealthy = backendHealthy && databaseHealthy && templatesHealthy
  const isLoading_ = isLoading || templatesLoading

  const quickActions = [
    { label: 'Test Login', icon: <Terminal className="w-4 h-4" />, query: 'Test login with credentials' },
    { label: 'Create User', icon: <Plus className="w-4 h-4" />, query: 'Create new user account' },
    { label: 'Update Profile', icon: <FileCode className="w-4 h-4" />, query: 'Update user profile' },
    { label: 'Delete User', icon: <X className="w-4 h-4" />, query: 'Delete user by ID' },
  ]

  // Handle model mismatch dialog actions
  const handleUseCurrentModel = useCallback(() => {
    setShowMismatchDialog(false)
    // Proceed with search using current settings model (may fail or produce inaccurate results)
    toast({
      title: "⚠️ Searching with different model",
      description: "Results may be inaccurate due to dimension mismatch",
    })
  }, [])

  const handleReEmbed = useCallback(async () => {
    if (!mismatchInfo?.datasetId) return
    
    setIsReEmbedding(true)
    try {
      const result = await apiClient.reembedDataset(mismatchInfo.datasetId, {
        model: embeddingModel,
        force: true,
      })
      
      toast({
        title: "🔄 Re-embedding started",
        description: `Converting to ${getEmbeddingModelInfo(embeddingModel)?.label || embeddingModel}. This may take a few minutes.`,
      })
      
      setShowMismatchDialog(false)
      
      // Optionally poll for status
      if (result.celery_task_id) {
        // Could implement polling here
        console.log('Re-embed task started:', result.celery_task_id)
      }
    } catch (err: any) {
      toast({
        title: "Re-embedding failed",
        description: err?.message || "Failed to start re-embedding",
        variant: "destructive",
      })
    } finally {
      setIsReEmbedding(false)
    }
  }, [mismatchInfo, embeddingModel])

  async function handleSearch() {
    if (!query.trim()) return
    
    setIsSearching(true)
    setSearchError(null)
    setSearchResults(null)
    
    try {
      // Use 2-stage ranking API: Stage 1 (KNN Vector Search) + Stage 2 (FlashRank Reranking)
      const results = await apiClient.rankQueryDetailed(
        query.trim(),
        10 // top_k for Stage 1 retrieval
      )
      
      // Check for MODEL_MISMATCH error in response
      if (results?.error === 'MODEL_MISMATCH') {
        setMismatchInfo({
          datasetModel: results.embedded_with_model,
          settingsModel: results.current_model,
          datasetId: results.dataset_id,
          datasetName: results.dataset_name,
        })
        setShowMismatchDialog(true)
        setSearchError('Embedding model mismatch detected')
        return
      }
      
      setSearchResults(results)
      
      toast({
        title: "Search Complete",
        description: `Found ${results.ranked_results?.length || 0} results using 2-stage ranking`,
      })
    } catch (err: any) {
      console.error('Search failed:', err)
      
      // Check if error response contains MODEL_MISMATCH
      if (err?.error === 'MODEL_MISMATCH' || err?.detail?.error === 'MODEL_MISMATCH') {
        const errorData = err.detail || err
        setMismatchInfo({
          datasetModel: errorData.embedded_with_model || errorData.dataset_model,
          settingsModel: errorData.current_model || errorData.search_model,
          datasetId: errorData.dataset_id,
          datasetName: errorData.dataset_name,
        })
        setShowMismatchDialog(true)
        setSearchError('Embedding model mismatch detected')
        return
      }
      
      // Check for dimension mismatch errors
      if (err?.message?.includes('dimension') || err?.detail?.includes('dimension')) {
        setSearchError('Vector dimension mismatch. The embedding model may have changed. Please re-embed your dataset.')
        toast({
          title: "Dimension Mismatch",
          description: "The search failed due to vector dimension mismatch. Re-embedding may be required.",
          variant: "destructive",
        })
        return
      }
      
      setSearchError(err.detail?.message || err.detail || err.message || 'Failed to perform search')
      
      toast({
        title: "Search Failed",
        description: err.detail?.message || err.detail || err.message || 'Failed to perform search',
        variant: "destructive",
      })
    } finally {
      setIsSearching(false)
    }
  }

  const topIntents = useMemo(() => {
    if (!stats?.intents) return []
    return Object.entries(stats.intents)
      .sort((a, b) => (b[1] as number) - (a[1] as number))
      .slice(0, 5)
  }, [stats])

  if (isLoading_) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="relative w-16 h-16 mx-auto">
            <div className="absolute inset-0 border-t-2 border-primary animate-spin rounded-full" />
            <div className="absolute inset-2 border-b-2 border-muted animate-spin rounded-full reverse" />
          </div>
          <p className="text-sm font-medium tracking-wide text-muted-foreground">Initializing System...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-6 lg:p-12 relative overflow-hidden">
      {/* Background Ambient Effects */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-purple-500/5 blur-[120px]" />
      </div>

      <div className="max-w-[1600px] mx-auto space-y-10 relative z-10">
        
        {/* Header Section */}
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2"
        >
          <div className="space-y-2">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70 pb-1">
              Dashboard
            </h1>
            <p className="text-lg text-muted-foreground font-light max-w-2xl">
              Welcome back to <span className="font-medium text-primary">NLPForge</span>. 
              System status is <span className={cn("font-medium", allHealthy ? "text-emerald-500" : "text-red-500")}>{allHealthy ? "Nominal" : "Degraded"}</span>.
            </p>
          </div>

          <div className="flex items-center gap-4">
             <div className={cn(
              "flex items-center gap-2.5 px-4 py-2 rounded-full text-sm font-medium border backdrop-blur-sm transition-all shadow-sm",
              allHealthy 
                ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10" 
                : "border-red-500/20 bg-red-500/5 text-red-600 dark:text-red-400 hover:bg-red-500/10"
            )}>
              <div className="relative flex h-2.5 w-2.5">
                <span className={cn(
                  "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                  allHealthy ? "bg-emerald-500" : "bg-red-500"
                )}></span>
                <span className={cn(
                  "relative inline-flex rounded-full h-2.5 w-2.5",
                  allHealthy ? "bg-emerald-500" : "bg-red-500"
                )}></span>
              </div>
              {allHealthy ? "System Online" : "System Alert"}
            </div>
          </div>
        </motion.header>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="space-y-8"
        >
          {/* Search / Command Center */}
          <motion.div variants={itemVariants} className="relative z-20">
            <div className="relative group">
              {/* Animated gradient border */}
              <div className="absolute -inset-[1px] bg-gradient-to-r from-primary via-purple-500 to-primary rounded-2xl opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 blur-sm transition-all duration-500 animate-gradient-x" />
              <div className="absolute -inset-[1px] bg-gradient-to-r from-primary via-purple-500 to-primary rounded-2xl opacity-0 group-hover:opacity-50 group-focus-within:opacity-70 transition-all duration-500" />
              
              <GlassCard className="relative p-1.5 shadow-2xl shadow-primary/10 border-primary/10 group-hover:border-transparent group-focus-within:border-transparent transition-all duration-300">
                <div className="flex items-center gap-3 p-2 bg-gradient-to-r from-background/80 to-background/60 rounded-xl backdrop-blur-sm">
                  {/* Search Icon with pulse animation */}
                  <div className="relative flex items-center justify-center w-12 h-12">
                    <div className="absolute inset-0 bg-primary/20 rounded-xl blur-lg opacity-0 group-focus-within:opacity-100 transition-opacity duration-300" />
                    <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/30">
                      <Search className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  
                  {/* Enhanced Input */}
                  <div className="flex-1 relative">
                    <Input
                      type="text"
                      placeholder="Ask anything or search test cases..."
                      className="border-none bg-transparent h-14 text-lg font-medium placeholder:text-muted-foreground/40 focus-visible:ring-0 focus-visible:ring-offset-0 pr-4"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    {/* Typing indicator line */}
                    <div className="absolute bottom-2 left-0 right-4 h-0.5 bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity duration-300" />
                  </div>
                  
                  {/* Model Selector - Enhanced */}
                  <div className="hidden md:flex items-center gap-2 px-4 py-2.5 bg-muted/40 hover:bg-muted/60 rounded-xl border border-white/5 transition-all duration-200 cursor-pointer">
                    <Brain className="w-4 h-4 text-primary" />
                    <select
                      value={embeddingModel}
                      onChange={(e) => setEmbeddingModel(e.target.value)}
                      className="bg-transparent border-none text-sm font-medium text-foreground focus:outline-none cursor-pointer"
                    >
                      {EMBEDDING_MODELS.map((model) => (
                        <option key={model.value} value={model.value} className="bg-background">
                          {model.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Keyboard shortcut hint */}
                  <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 bg-muted/30 rounded-lg border border-white/5">
                    <Command className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-xs font-medium text-muted-foreground">K</span>
                  </div>

                  {/* Submit Button - Enhanced */}
                  <Button 
                    size="lg" 
                    onClick={handleSearch}
                    disabled={isSearching || !query.trim()}
                    className="relative rounded-xl px-6 h-12 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 shadow-lg shadow-primary/30 hover:shadow-xl hover:shadow-primary/40 transition-all duration-300 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
                  >
                    {isSearching ? (
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span className="hidden sm:inline">Searching...</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Zap className="h-5 w-5" />
                        <span className="hidden sm:inline font-semibold">Search</span>
                      </div>
                    )}
                  </Button>
                </div>
              </GlassCard>
            </div>
            
            {/* Search suggestions/quick prompts */}
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex items-center gap-2 mt-4 px-2 overflow-x-auto pb-2 scrollbar-hide"
            >
              <span className="text-xs text-muted-foreground whitespace-nowrap">Try:</span>
              {['Test user login', 'Create new account', 'Validate API response', 'Update profile'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setQuery(suggestion)}
                  className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-primary bg-muted/30 hover:bg-primary/10 rounded-full border border-transparent hover:border-primary/20 transition-all duration-200 whitespace-nowrap"
                >
                  {suggestion}
                </button>
              ))}
            </motion.div>
          </motion.div>

          {/* Search Results Section */}
          {searchResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Search className="w-5 h-5 text-primary" />
                      Search Results
                      <span className="text-sm font-normal text-muted-foreground ml-2">
                        (2-Stage: KNN + FlashRank Reranking)
                      </span>
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Query: "{searchResults.query}"
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowStage1(!showStage1)}
                      className="text-xs"
                    >
                      {showStage1 ? 'Hide Stage 1' : 'Show Stage 1'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSearchResults(null)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Stage 1 Results (KNN Vector Search) */}
                {showStage1 && searchResults.stage1_results && (
                  <div className="mb-6 p-4 bg-muted/30 rounded-lg border border-dashed">
                    <h4 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
                      <Brain className="w-4 h-4" />
                      Stage 1: KNN Vector Search (Cosine Similarity)
                    </h4>
                    <div className="space-y-2">
                      {searchResults.stage1_results.slice(0, 5).map((result: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between text-sm p-2 bg-background/50 rounded">
                          <span className="truncate max-w-[60%]">{result.query || result.text}</span>
                          <span className="text-xs font-mono bg-blue-500/10 text-blue-600 px-2 py-0.5 rounded">
                            {((result.vector_score ?? result.cosine_similarity ?? 0) * 100).toFixed(1)}% similarity
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stage 2 Results (FlashRank Reranked) */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-primary flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Stage 2: FlashRank Reranked Results
                  </h4>
                  {searchResults.ranked_results?.length > 0 ? (
                    searchResults.ranked_results.map((result, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        className="p-4 bg-muted/20 hover:bg-muted/40 rounded-xl border border-transparent hover:border-primary/20 transition-all group"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center">
                                {result.rank}
                              </span>
                              {result.api && (
                                <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-600 text-xs font-medium rounded">
                                  {result.api}
                                </span>
                              )}
                              {result.endpoint && (
                                <span className="text-xs text-muted-foreground font-mono truncate max-w-[200px]">
                                  {result.endpoint}
                                </span>
                              )}
                            </div>
                            <p className="text-sm font-medium mb-1 line-clamp-2">
                              {result.text}
                            </p>
                            {result.original_similarity !== undefined && (
                              <p className="text-xs text-muted-foreground">
                                Original similarity: {(result.original_similarity * 100).toFixed(1)}%
                              </p>
                            )}
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="text-lg font-bold text-primary">
                              {(result.score * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-muted-foreground">
                              FlashRank Score
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No results found for your query
                    </div>
                  )}
                </div>
              </GlassCard>
            </motion.div>
          )}

          {/* Search Error */}
          {searchError && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg"
            >
              <div className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-medium">{searchError}</span>
              </div>
            </motion.div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              label="Total Embeddings"
              value={stats?.total_embeddings?.toLocaleString() || 0}
              subtitle="Vectors in Redis"
              icon={<Brain className="w-5 h-5 text-blue-500" />}
              delay={0.1}
            />
            <MetricCard
              label="Approved Templates"
              value={templateStats?.by_status?.approved || 0}
              subtitle={`${templateStats?.total_templates || 0} total`}
              icon={<CheckCircle2 className="w-5 h-5 text-emerald-500" />}
              delay={0.2}
            />
            <MetricCard
              label="Total Intents"
              value={Object.keys(stats?.intents || {}).length}
              subtitle="Unique APIs"
              icon={<Target className="w-5 h-5 text-purple-500" />}
              delay={0.3}
            />
            <MetricCard
              label="Embedding Model"
              value={getEmbeddingModelInfo(stats?.model || embeddingModel)?.label?.split(' ')[0] || 'Nomic'}
              subtitle={`${getEmbeddingModelInfo(stats?.model || embeddingModel)?.dimensions || 768}D vectors`}
              icon={<Cpu className="w-5 h-5 text-amber-500" />}
              delay={0.4}
            />
          </div>

          {/* Main Content Area */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Column: Activity & Trends */}
            <div className="lg:col-span-2 space-y-8">
              <GlassCard className="p-6 h-[400px] flex flex-col">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    Performance Telemetry
                  </h3>
                </div>
                <div className="flex-1 w-full">
                  <TrendChart />
                </div>
              </GlassCard>
            </div>

            {/* Right Column: Actions & Stats */}
            <div className="space-y-8">
              {/* Quick Actions */}
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
                  <Cpu className="w-5 h-5 text-primary" />
                  Quick Actions
                </h3>
                <div className="grid gap-3">
                  {quickActions.map((action) => (
                    <MagneticButton key={action.label}>
                      <button
                        className="w-full flex items-center gap-4 p-3 rounded-xl bg-muted/30 hover:bg-primary/5 border border-transparent hover:border-primary/20 transition-all duration-300 group text-left relative overflow-hidden"
                        onClick={() => {
                          setQuery(action.query)
                          handleSearch()
                        }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        
                        <div className="relative z-10 w-10 h-10 rounded-lg bg-background flex items-center justify-center shadow-sm border border-white/5 group-hover:scale-110 group-hover:border-primary/20 transition-all duration-300 text-primary">
                          {action.icon}
                        </div>
                        <div className="relative z-10">
                          <div className="font-medium group-hover:text-primary transition-colors">
                            {action.label}
                          </div>
                          <div className="text-xs text-muted-foreground group-hover:text-muted-foreground/80">
                            Click to run
                          </div>
                        </div>
                        <ArrowRight className="relative z-10 w-4 h-4 ml-auto text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-1 transition-all duration-300" />
                      </button>
                    </MagneticButton>
                  ))}
                </div>
              </GlassCard>

              {/* Top Intents */}
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold flex items-center gap-2 mb-6">
                  <Target className="w-5 h-5 text-primary" />
                  Top Intents
                </h3>
                <div className="space-y-5">
                  {isLoading ? (
                    <div className="space-y-4">
                      {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} className="h-8 w-full rounded-lg" />
                      ))}
                    </div>
                  ) : topIntents.length > 0 ? (
                    topIntents.map(([intent, count], idx) => {
                      const max = topIntents[0][1] as number
                      const percent = Math.round(((count as number) / max) * 100)
                      return (
                        <div key={intent} className="space-y-2 group">
                          <div className="flex items-center justify-between text-sm font-medium">
                            <span className="group-hover:text-primary transition-colors truncate max-w-[200px]">{intent}</span>
                            <span className="text-muted-foreground font-mono text-xs bg-muted/50 px-2 py-0.5 rounded-full">{count}</span>
                          </div>
                          <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${percent}%` }}
                              transition={{ duration: 1, delay: idx * 0.1, ease: "circOut" }}
                              className="h-full bg-gradient-to-r from-primary to-purple-500 rounded-full relative"
                            >
                                <div className="absolute inset-0 bg-white/20 animate-[shimmer_2s_infinite]" />
                            </motion.div>
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                      No intent data available
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          </div>
        </motion.div>
      </div>
      
      {/* Model Mismatch Dialog */}
      {mismatchInfo && (
        <ModelMismatchDialog
          isOpen={showMismatchDialog}
          onClose={() => setShowMismatchDialog(false)}
          datasetModel={mismatchInfo.datasetModel}
          settingsModel={mismatchInfo.settingsModel}
          datasetName={mismatchInfo.datasetName}
          onUseCurrentModel={handleUseCurrentModel}
          onReEmbed={handleReEmbed}
          isReEmbedding={isReEmbedding}
        />
      )}
    </div>
  )
}

function MetricCard({
  label,
  value,
  subtitle,
  icon,
  delay = 0
}: {
  label: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  delay?: number
}) {
  return (
    <motion.div 
      variants={itemVariants}
      whileHover={{ y: -5, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <GlassCard className="relative p-6 h-full flex flex-col justify-between group overflow-hidden border-primary/10 hover:border-primary/30 transition-colors">
        {/* Gradient Background on Hover */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        
        <div className="relative z-10 flex items-start justify-between mb-4">
          <div className="font-medium text-sm text-muted-foreground group-hover:text-primary transition-colors">
            {label}
          </div>
          <div className="p-2.5 rounded-xl bg-background/50 shadow-sm border border-white/5 group-hover:scale-110 group-hover:bg-primary/10 transition-all duration-300">
            {icon}
          </div>
        </div>
        <div className="relative z-10 flex items-end justify-between">
          <div className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
            {value}
          </div>
          {subtitle && (
            <div className="text-xs font-medium text-muted-foreground px-2.5 py-1 rounded-full bg-background/50 border border-white/5">
              {subtitle}
            </div>
          )}
        </div>
      </GlassCard>
    </motion.div>
  )
}
