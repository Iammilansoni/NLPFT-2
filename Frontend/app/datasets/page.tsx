'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { getApiBase } from '@/lib/runtime-config'
import {
  Download,
  RefreshCw,
  Database,
  FileText,
  FileSpreadsheet,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Play,
  Settings,
  Upload,
  X,
  Sparkles,
  AlertTriangle,
  Search,
  MoreHorizontal,
  Trash2,
  Eye,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { toast } from '@/hooks/use-toast'
import { OnboardingTour } from '@/components/onboarding/OnboardingTour'
import { ActiveTasksPanel } from '@/components/datasets/ActiveTasksPanel'

interface DatasetRecord {
  api: string
  endpoint: string
  nl_input: string
  definition_of_api: string
  paraphrase_type: string
  embedding_model: string
}

interface DatasetStatistics {
  total_apis: number
  total_nl_variations: number
  avg_variations_per_api: number
  redis_stored_count?: number
  redis_status?: string
}

interface GenerationTask {
  task_id: string
  dataset_id?: string
  status: string
  message: string
  progress?: number
  current_step?: string
  steps?: Array<{ name: string; status: string; timestamp: string }>
  error?: string
  created_at?: string
  completed_at?: string
  statistics?: DatasetStatistics
  result?: {
    total_generated?: number
    csv_path?: string
  }
  files?: {
    jsonl?: string
    csv?: string
    summary?: string
  }
}

interface DatasetPreview {
  task_id: string
  dataset_id?: string
  total_records: number
  showing: number
  offset: number
  limit: number
  has_more: boolean
  records: DatasetRecord[]
}

// New interface for persistent datasets from PostgreSQL
interface PersistentDataset {
  dataset_id: string
  name: string
  template_id?: string
  template_name?: string
  total_rows: number
  embedded_rows: number
  embedding_status: string
  embedding_model?: string
  source_type: 'AI_GENERATED' | 'CSV_UPLOAD'
  created_at: string
  updated_at?: string
}

// Animation variants removed for cleaner enterprise styling

export default function DatasetGeneratorPage() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentTask, setCurrentTask] = useState<GenerationTask | null>(null)
  const [previewData, setPreviewData] = useState<DatasetPreview | null>(null)
  const [allTasks, setAllTasks] = useState<GenerationTask[]>([])
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [pageSize] = useState(100)

  const [templateId, setTemplateId] = useState('')
  const [templates, setTemplates] = useState<any[]>([])
  const [numExamples, setNumExamples] = useState('100')
  const [userPrompt, setUserPrompt] = useState('')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // New state for persistent datasets
  const [persistentDatasets, setPersistentDatasets] = useState<PersistentDataset[]>([])
  const [viewingDataset, setViewingDataset] = useState<PersistentDataset | null>(null)
  const [viewingRows, setViewingRows] = useState<any[]>([])
  const [viewTotal, setViewTotal] = useState(0)
  const [viewPage, setViewPage] = useState(0)
  const [isViewLoading, setIsViewLoading] = useState(false)
  const [renamingDataset, setRenamingDataset] = useState<PersistentDataset | null>(null)
  const [newDatasetName, setNewDatasetName] = useState('')
  const [embeddingDatasetId, setEmbeddingDatasetId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const RAW_API_BASE = getApiBase()
  const API_BASE = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : ''

  // Format date in unambiguous format with local timezone: "Dec 10, 2025, 7:28 PM"
  const formatDateTime = (dateString: string | undefined): string => {
    if (!dateString) return 'N/A'
    try {
      // Parse ISO date string (handles both with and without Z suffix)
      const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z')

      // Check if date is valid
      if (isNaN(date.getTime())) return dateString

      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZoneName: 'short'
      })
    } catch {
      return dateString
    }
  }

  const formatError = (err: unknown): string => {
    if (typeof err === 'string') return err
    if (err && typeof err === 'object') {
      const errorObj = err as Record<string, unknown>
      if (errorObj.detail) {
        if (Array.isArray(errorObj.detail)) {
          return errorObj.detail
            .map((e: Record<string, unknown>) => (e.msg as string) || JSON.stringify(e))
            .join(', ')
        }
        return typeof errorObj.detail === 'string' ? errorObj.detail : JSON.stringify(errorObj.detail)
      }
      return JSON.stringify(err)
    }
    return 'An unexpected error occurred'
  }

  const fetchPreview = useCallback(async (taskId: string, limit: number = 100, offset: number = 0) => {
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(
        `${API_BASE}/api/v1/datasets/preview/task/${taskId}?limit=${limit}&offset=${offset}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      const data = await response.json()
      setPreviewData(data)
      setCurrentPage(Math.floor(offset / pageSize))
    } catch (err) {
      console.error('Error fetching preview:', err)
      setError(formatError(err))
    }
  }, [API_BASE, pageSize])

  const fetchAllTasks = useCallback(async () => {
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      // Now datasets come from PostgreSQL (persistent)
      setPersistentDatasets(data.datasets || [])
    } catch (err) {
      // Backend not available - this is expected in development
      console.log('Backend API not available')
    } finally {
      setIsLoading(false)
    }
  }, [API_BASE])

  const fetchTaskStatus = useCallback(async (taskId: string) => {
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets/status/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      const data = await response.json()
      setCurrentTask(data)

      if (data.status === 'completed') {
        setIsGenerating(false)
        fetchPreview(taskId)
        fetchAllTasks()
      } else if (data.status === 'failed') {
        setIsGenerating(false)
        setError(formatError(data.message || data))
      }
    } catch (err) {
      console.error('Error fetching task status:', err)
      setError(formatError(err))
    }
  }, [API_BASE, fetchPreview, fetchAllTasks])

  useEffect(() => {
    // Only fetch on client side
    if (typeof window !== 'undefined') {
      fetchAllTasks().catch((err) => {
        // Silently fail if backend is not available
        console.log('Backend not available:', err)
      })
      // Fetch only APPROVED templates for dataset generation
      const token = localStorage.getItem('nlpforge_access_token')
      fetch(`${API_BASE}/api/v1/templates?status_filter=approved`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
        .then(async (res) => {
          if (!res.ok) throw new Error('Failed to fetch templates')
          return res.json()
        })
        .then((data) => {
          if (Array.isArray(data)) {
            // Filter only approved templates (double-check client-side)
            const approvedTemplates = data.filter((t: any) => t.status === 'approved')
            setTemplates(approvedTemplates)
          } else {
            console.error('Templates data is not an array:', data)
            setTemplates([])
          }
        })
        .catch((err) => {
          console.log('Templates not available:', err)
          setTemplates([])
        })
    }
  }, [fetchAllTasks, API_BASE])

  useEffect(() => {
    if (currentTask && currentTask.status === 'running') {
      const interval = setInterval(() => {
        fetchTaskStatus(currentTask.task_id)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [currentTask, fetchTaskStatus])

  // Poll for embedding status updates when any dataset is in_progress
  useEffect(() => {
    const hasEmbeddingInProgress = persistentDatasets.some(
      d => d.embedding_status === 'in_progress'
    )

    if (hasEmbeddingInProgress) {
      const interval = setInterval(() => {
        fetchAllTasks()
      }, 3000) // Poll every 3 seconds
      return () => clearInterval(interval)
    }
  }, [persistentDatasets, fetchAllTasks])

  const handleGenerate = async () => {
    if (!templateId) {
      setError('Please select a template')
      return
    }

    if (!userPrompt.trim()) {
      setError('Please provide a user prompt to guide the generation')
      return
    }

    setIsGenerating(true)
    setError(null)
    setCurrentTask(null)
    setPreviewData(null)

    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          template_id: templateId,
          num_examples: parseInt(numExamples) || 100,
          user_prompt: userPrompt,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setCurrentTask(data)
        fetchTaskStatus(data.task_id)
      } else {
        setError(formatError(data))
        setIsGenerating(false)
      }
    } catch (err) {
      setError(formatError(err))
      setIsGenerating(false)
    }
  }

  const handleDownload = async (taskId: string, format: string) => {
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets/download/${taskId}/${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `api_dataset_${taskId}.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        setError('Failed to download file')
      }
    } catch (err) {
      console.error('Error downloading file:', err)
      setError(formatError(err))
    }
  }

  const handleFileUpload = async () => {
    if (!uploadedFile) return

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)

      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        setCurrentTask(data)
        fetchTaskStatus(data.task_id)
        setUploadedFile(null)
      } else {
        setError(formatError(data))
      }
    } catch (err) {
      setError(formatError(err))
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setUploadedFile(file)
        setError(null)
      } else {
        setError('Please upload a CSV file')
        e.target.value = ''
      }
    }
  }

  // Handler: View dataset rows
  const handleViewDataset = async (dataset: PersistentDataset) => {
    setViewingDataset(dataset)
    setViewPage(0)
    setIsViewLoading(true)
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(
        `${API_BASE}/api/v1/datasets/db/${dataset.dataset_id}/rows?skip=0&limit=50`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      const data = await response.json()
      setViewingRows(data.rows || [])
      setViewTotal(data.total || 0)
    } catch (err) {
      setError(formatError(err))
    } finally {
      setIsViewLoading(false)
    }
  }

  // Handler for pagination in view modal
  const handleViewPageChange = async (newPage: number) => {
    if (!viewingDataset) return
    setIsViewLoading(true)
    setViewPage(newPage)
    const newSkip = newPage * 50
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(
        `${API_BASE}/api/v1/datasets/db/${viewingDataset.dataset_id}/rows?skip=${newSkip}&limit=50`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      const data = await response.json()
      setViewingRows(data.rows || [])
    } catch (err) {
      setError(formatError(err))
    } finally {
      setIsViewLoading(false)
    }
  }

  // Handler: Embed dataset to Redis
  const handleEmbedDataset = async (datasetId: string, forceReembed: boolean = false) => {
    setEmbeddingDatasetId(datasetId)

    // Show start notification
    toast({
      title: forceReembed ? "Re-embedding Started" : "Embedding Started",
      description: "Processing vectors with your current embedding model...",
    })

    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const url = `${API_BASE}/api/v1/datasets/db/${datasetId}/embed${forceReembed ? '?force_reembed=true' : ''}`
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || 'Failed to embed dataset')
      }

      const result = await response.json()

      // Show success notification
      toast({
        title: "✓ Embedding Completed",
        description: `Successfully embedded ${result.embedded_count || 'all'} rows with ${result.model || 'current model'}`,
      })

      // Refresh datasets to show updated status
      await fetchAllTasks()
    } catch (err: any) {
      toast({
        title: "Embedding Failed",
        description: err.message || formatError(err),
        variant: "destructive",
      })
      setError(formatError(err))
    } finally {
      setEmbeddingDatasetId(null)
    }
  }

  // Handler: Rename dataset
  const handleRenameDataset = async () => {
    if (!renamingDataset || !newDatasetName.trim()) return
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(
        `${API_BASE}/api/v1/datasets/db/${renamingDataset.dataset_id}/rename`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: newDatasetName.trim() })
        }
      )
      if (!response.ok) throw new Error('Failed to rename')
      setRenamingDataset(null)
      setNewDatasetName('')
      await fetchAllTasks()
    } catch (err) {
      setError(formatError(err))
    }
  }

  // Handler: Delete dataset
  const handleDeleteDataset = async (datasetId: string) => {
    if (!confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) return
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets/db/${datasetId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('Failed to delete')
      await fetchAllTasks()
    } catch (err) {
      setError(formatError(err))
    }
  }

  // Handler: Download dataset as CSV
  const handleDownloadDatasetById = async (dataset: PersistentDataset) => {
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      // Use the dataset rows endpoint to get all rows
      const response = await fetch(
        `${API_BASE}/api/v1/datasets/db/${dataset.dataset_id}/rows?skip=0&limit=${dataset.total_rows}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      const data = await response.json()

      // Convert to CSV
      if (data.rows && data.rows.length > 0) {
        const headers = ['query', 'api_name', 'endpoint', 'scenario_type']
        const csvContent = [
          headers.join(','),
          ...data.rows.map((row: any) =>
            headers.map(h => `"${(row[h] || '').toString().replace(/"/g, '""')}"`).join(',')
          )
        ].join('\n')

        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${dataset.name || 'dataset'}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (err) {
      setError(formatError(err))
    }
  }


  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading datasets...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20">
      <OnboardingTour tourId="datasets" />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border/40">
        {/* Background Decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute top-20 -left-20 w-60 h-60 bg-blue-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        <div className="relative w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-14">
          {/* Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10">
                  <Database className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h1 className="text-3xl lg:text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                    Datasets
                  </h1>
                  <p className="text-muted-foreground mt-1">
                    Manage your evaluation datasets and embeddings
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Stats Pills */}
              <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-background/60 border border-border/50 backdrop-blur-sm">
                <span className="text-2xl font-bold tabular-nums text-foreground">{persistentDatasets.length}</span>
                <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Total</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 backdrop-blur-sm">
                <span className="text-2xl font-bold tabular-nums text-emerald-600 dark:text-emerald-400">
                  {persistentDatasets.filter(d => d.embedding_status === 'completed').length}
                </span>
                <span className="text-xs text-emerald-600/80 dark:text-emerald-400/80 font-medium uppercase tracking-wider">Embedded</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Active Tasks Panel - Shows running/recent generation tasks */}
        <ActiveTasksPanel 
          onTaskComplete={fetchAllTasks}
          className="animate-in fade-in slide-in-from-top-2 duration-300 mb-8"
        />

        <Tabs defaultValue="generate" className="w-full space-y-6" data-tour="dataset-tabs">
          <TabsList className="grid w-full sm:w-[400px] grid-cols-2 p-1 bg-muted/50 rounded-xl" data-tour="generate-dataset">
            <TabsTrigger
              value="generate"
              className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm rounded-xl transition-all duration-200"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Generate
            </TabsTrigger>
            <TabsTrigger
              value="upload"
              className="gap-2 data-[state=active]:bg-background data-[state=active]:shadow-sm rounded-xl transition-all duration-200"
            >
              <Upload className="w-4 h-4" />
              Upload
            </TabsTrigger>
          </TabsList>

          <TabsContent value="generate" className="outline-none animate-in fade-in-50 slide-in-from-bottom-2 duration-300">
            {/* Active Generation Progress Card */}
            {currentTask && (currentTask.status === 'running' || currentTask.status === 'pending') && (
              <Card className="mb-6 border-blue-200 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 dark:border-blue-900 dark:from-blue-900/20 dark:to-indigo-900/20 shadow-sm animate-in fade-in slide-in-from-top-2">
                <CardContent className="p-5 space-y-4">
                  {/* Header Row */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <Loader2 className="w-8 h-8 animate-spin text-blue-600 dark:text-blue-400" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-3 h-3 rounded-full bg-blue-500/30" />
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                          Generating Dataset
                        </p>
                        <p className="text-xs text-blue-600 dark:text-blue-400 font-mono">
                          ID: {currentTask.task_id.slice(0, 8)}...
                        </p>
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "text-xs font-medium px-2.5 py-1",
                        currentTask.status === 'running' 
                          ? "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:border-blue-700"
                          : "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/50 dark:text-amber-300 dark:border-amber-700"
                      )}
                    >
                      {currentTask.status === 'running' ? 'Processing' : 'Queued'}
                    </Badge>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-blue-700 dark:text-blue-300 font-medium">
                        {currentTask.current_step || currentTask.message || 'Initializing...'}
                      </span>
                      <span className="text-blue-900 dark:text-blue-100 font-bold tabular-nums">
                        {currentTask.progress !== undefined ? `${Math.round(currentTask.progress)}%` : '—'}
                      </span>
                    </div>
                    <div className="h-2.5 bg-blue-200/50 dark:bg-blue-900/50 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${currentTask.progress || 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Step Details */}
                  {currentTask.steps && currentTask.steps.length > 0 && (
                    <div className="pt-2 border-t border-blue-200/50 dark:border-blue-800/50">
                      <div className="flex flex-wrap gap-2">
                        {currentTask.steps.map((step, idx) => (
                          <div 
                            key={idx}
                            className={cn(
                              "flex items-center gap-1.5 text-xs px-2 py-1 rounded-full",
                              step.status === 'completed' && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
                              step.status === 'running' && "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 animate-pulse",
                              step.status === 'pending' && "bg-gray-100 text-gray-500 dark:bg-gray-800/30 dark:text-gray-500"
                            )}
                          >
                            {step.status === 'completed' && <CheckCircle className="w-3 h-3" />}
                            {step.status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
                            {step.status === 'pending' && <Clock className="w-3 h-3" />}
                            <span>{step.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Time Estimate */}
                  {currentTask.created_at && (
                    <p className="text-[10px] text-blue-600/70 dark:text-blue-400/70 text-center">
                      Started {formatDateTime(currentTask.created_at)} • Generation typically takes 30-60 seconds
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            <Card className="border-border shadow-sm bg-card overflow-hidden" data-tour="generate-dataset">
              <CardHeader className="bg-muted/30 border-b pb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center ring-1 ring-primary/20">
                    <Sparkles className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg font-semibold">AI Dataset Generation</CardTitle>
                    <CardDescription>Create synthetic evaluation data using approved templates</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6 grid gap-8 md:grid-cols-2">
                {/* Left Column: Inputs */}
                <div className="space-y-6">
                  <div className="space-y-3">
                    <Label htmlFor="template-select" className="text-sm font-medium flex items-center gap-1">
                      Template <span className="text-red-500">*</span>
                    </Label>
                    <select
                      id="template-select"
                      value={templateId}
                      onChange={(e) => setTemplateId(e.target.value)}
                      disabled={isGenerating}
                      className="flex h-11 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50 transition-all"
                    >
                      <option value="">Select an approved template...</option>
                      {Array.isArray(templates) && templates.length > 0 ? (
                        templates.map((template) => (
                          <option key={template.template_id || template.t_id} value={template.template_id || template.t_id}>
                            {template.api_name}
                          </option>
                        ))
                      ) : (
                        <option value="" disabled>No approved templates available</option>
                      )}
                    </select>
                    {templates.length === 0 && (
                      <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1.5 mt-2">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        No approved templates found. Approve a template to continue.
                      </p>
                    )}
                  </div>

                  <div className="space-y-3">
                    <Label htmlFor="num-examples" className="text-sm font-medium">Count</Label>
                    <Input
                      id="num-examples"
                      type="number"
                      min={1}
                      max={1000}
                      value={numExamples}
                      onChange={(e) => setNumExamples(e.target.value)}
                      onBlur={(e) => {
                        // On blur, validate and set default if empty
                        const val = parseInt(e.target.value)
                        if (isNaN(val) || val < 1) {
                          setNumExamples('100')
                        } else if (val > 1000) {
                          setNumExamples('1000')
                        }
                      }}
                      disabled={isGenerating}
                      className="h-11"
                    />
                  </div>
                </div>

                {/* Right Column: Prompt */}
                <div className="space-y-6 flex flex-col">
                  <div className="space-y-3 flex-1 flex flex-col">
                    <Label htmlFor="user-prompt" className="text-sm font-medium flex items-center gap-1">
                      Generation Prompt <span className="text-red-500">*</span>
                    </Label>
                    <textarea
                      id="user-prompt"
                      value={userPrompt}
                      onChange={(e) => setUserPrompt(e.target.value)}
                      placeholder="Describe the scenarios to generate...&#10;e.g., 'Focus on edge cases for invalid dates' or 'Generate SQL injection attempts'"
                      className="flex min-h-[160px] w-full rounded-lg border border-input bg-background px-4 py-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50 resize-none flex-1 font-mono text-xs leading-relaxed"
                      disabled={isGenerating}
                    />
                  </div>

                  <Button
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    size="lg"
                    className="w-full gap-2 shadow-sm font-semibold h-11"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-current" />
                        Start Generation
                      </>
                    )}
                  </Button>

                  {error && (
                    <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                      <AlertCircle className="w-4 h-4" />
                      {error}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="upload" className="outline-none animate-in fade-in-50 slide-in-from-bottom-2 duration-300">
            <Card className="border-border shadow-sm bg-card" data-tour="upload-dataset">
              <CardHeader className="bg-muted/30 border-b pb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-muted flex items-center justify-center ring-1 ring-border">
                    <Upload className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <CardTitle className="text-lg font-semibold">CSV Upload</CardTitle>
                    <CardDescription>Import existing datasets for embedding</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-8">
                <div className="max-w-xl mx-auto space-y-6">
                  <Label
                    htmlFor="csv-upload"
                    className={cn(
                      "relative flex flex-col items-center justify-center w-full h-48 rounded-xl border-2 border-dashed transition-all cursor-pointer",
                      uploadedFile
                        ? "border-emerald-500/50 bg-emerald-50/10"
                        : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/20"
                    )}
                  >
                    <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center">
                      {uploadedFile ? (
                        <>
                          <div className="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-3">
                            <FileSpreadsheet className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                          </div>
                          <p className="text-sm font-semibold text-foreground mb-1">
                            {uploadedFile.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {(uploadedFile.size / 1024).toFixed(2)} KB
                          </p>
                        </>
                      ) : (
                        <>
                          <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3">
                            <Upload className="h-6 w-6 text-muted-foreground" />
                          </div>
                          <p className="text-sm font-medium text-foreground mb-1">
                            Click to upload or drag and drop
                          </p>
                          <p className="text-xs text-muted-foreground">
                            CSV files only (max 10MB)
                          </p>
                        </>
                      )}
                    </div>
                    <input
                      id="csv-upload"
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                      className="hidden"
                      disabled={isUploading}
                    />
                  </Label>

                  {uploadedFile && (
                    <div className="flex gap-3 animate-in fade-in slide-in-from-top-2">
                      <Button
                        onClick={handleFileUpload}
                        disabled={isUploading}
                        className="flex-1"
                        size="lg"
                      >
                        {isUploading ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Confirm Upload
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setUploadedFile(null)}
                        disabled={isUploading}
                        size="lg"
                        className="px-3"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* ============= DATASET TABLE SECTION ============= */}
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden" data-tour="dataset-list">
          {/* Toolbar */}
          <div className="p-4 border-b flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative w-full sm:max-w-xs group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <Input
                placeholder="Filter datasets..."
                className="pl-9 h-9 bg-muted/40 border-transparent focus:bg-background focus:border-input transition-all"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              className="h-9 gap-2 text-muted-foreground hover:text-foreground hidden sm:flex"
              onClick={fetchAllTasks}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
          </div>

          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-muted/30 border-b text-xs font-medium text-muted-foreground uppercase tracking-wider">
            <div className="col-span-4">Dataset Name</div>
            <div className="col-span-2">Source</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-1 text-right">Rows</div>
            <div className="col-span-2">Date</div>
            <div className="col-span-1 text-right">Actions</div>
          </div>

          {/* Table Body */}
          <div className="divide-y divide-border">
            {persistentDatasets.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="h-16 w-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                  <Database className="h-8 w-8 text-muted-foreground/50" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">No datasets yet</h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                  Generate a dataset from a template or upload a CSV to get started.
                </p>
              </div>
            ) : (
              persistentDatasets
                .filter(d => d.name.toLowerCase().includes(searchQuery.toLowerCase()))
                .map((dataset) => (
                  <div
                    key={dataset.dataset_id}
                    className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-muted/30 transition-colors group"
                  >
                    {/* Name */}
                    <div className="col-span-4 min-w-0">
                      <div className="font-medium text-sm text-foreground truncate" title={dataset.name}>
                        {dataset.name}
                      </div>
                      {dataset.template_name && (
                        <div className="text-xs text-muted-foreground truncate flex items-center gap-1.5 mt-0.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary/40" />
                          {dataset.template_name}
                        </div>
                      )}
                    </div>

                    {/* Source */}
                    <div className="col-span-2">
                      <Badge variant="outline" className={cn(
                        "font-medium text-[10px] uppercase tracking-wide border-0 px-2 py-0.5",
                        dataset.source_type === 'AI_GENERATED' ? "bg-blue-100 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400" : "bg-sky-100 text-sky-700 dark:bg-sky-500/10 dark:text-sky-400"
                      )}>
                        {dataset.source_type === 'AI_GENERATED' ? 'AI Generated' : 'Uploaded'}
                      </Badge>
                    </div>

                    {/* Status */}
                    <div className="col-span-2">
                      {embeddingDatasetId === dataset.dataset_id ? (
                        <div className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 font-medium">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Processing
                        </div>
                      ) : dataset.embedding_status === 'completed' ? (
                        <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Embedded
                        </div>
                      ) : dataset.embedding_status === 'in_progress' ? (
                        <div className="flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400 font-medium">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Processing
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <span className="w-2 h-2 rounded-full bg-muted-foreground/30" />
                          Pending
                        </div>
                      )}
                    </div>

                    {/* Rows */}
                    <div className="col-span-1 text-right text-sm tabular-nums text-muted-foreground font-mono">
                      {dataset.total_rows.toLocaleString()}
                    </div>

                    {/* Date */}
                    <div className="col-span-2 text-xs text-muted-foreground truncate">
                      {formatDateTime(dataset.created_at)}
                    </div>

                    {/* Actions */}
                    <div className="col-span-1 flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-muted-foreground hover:text-primary"
                              onClick={() => handleViewDataset(dataset)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>View Data</TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      {dataset.embedding_status !== 'completed' && dataset.embedding_status !== 'in_progress' && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-muted-foreground hover:text-blue-600"
                                onClick={() => handleEmbedDataset(dataset.dataset_id)}
                                disabled={embeddingDatasetId === dataset.dataset_id}
                              >
                                {embeddingDatasetId === dataset.dataset_id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Zap className="w-4 h-4" />
                                )}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Generate Embeddings</TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-[180px]">
                          {dataset.embedding_status === 'completed' && (
                            <>
                              <DropdownMenuItem
                                onClick={() => handleEmbedDataset(dataset.dataset_id, true)}
                                className="text-blue-600 focus:text-blue-600"
                              >
                                <Zap className="w-4 h-4 mr-2" /> Re-embed
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                            </>
                          )}
                          <DropdownMenuItem onClick={() => handleDownloadDatasetById(dataset)}>
                            <Download className="w-4 h-4 mr-2" /> Download CSV
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive focus:text-destructive"
                            onClick={() => handleDeleteDataset(dataset.dataset_id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>

        {/* ============= PREVIEW MODAL ============= */}
        {viewingDataset && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div
              className="bg-card w-full max-w-5xl max-h-[85vh] rounded-xl shadow-2xl border flex flex-col overflow-hidden animate-in zoom-in-95 duration-300 ring-1 ring-border"
              role="dialog"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-5 border-b bg-muted/20">
                <div className="space-y-1">
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    {viewingDataset.name}
                    <Badge variant="outline" className="font-normal text-xs">{viewingDataset.source_type}</Badge>
                  </h3>
                  <p className="text-sm text-muted-foreground font-mono">
                    {viewTotal.toLocaleString()} rows • {viewingDataset.embedding_status === 'completed' ? 'Embedded' : 'Not Embedded'}
                  </p>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setViewingDataset(null)} className="h-9 w-9 rounded-full">
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 overflow-auto bg-card">
                {isViewLoading ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] space-y-4">
                    <Loader2 className="w-10 h-10 animate-spin text-primary/50" />
                    <p className="text-sm text-muted-foreground font-medium">Fetching records...</p>
                  </div>
                ) : (
                  <table className="w-full text-sm text-left">
                    <thead className="bg-muted/40 sticky top-0 z-10 text-xs uppercase tracking-wider font-medium text-muted-foreground">
                      <tr>
                        <th className="px-6 py-3 w-1/2">Query</th>
                        <th className="px-6 py-3">API Endpoint</th>
                        <th className="px-6 py-3">Type</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {viewingRows.map((row, i) => (
                        <tr key={i} className="hover:bg-muted/30 transition-colors">
                          <td className="px-6 py-3 font-mono text-xs text-foreground/80 leading-relaxed max-w-lg truncate" title={row.query}>
                            {row.query}
                          </td>
                          <td className="px-6 py-3">
                            <code className="text-[10px] bg-muted px-1.5 py-0.5 rounded border text-muted-foreground font-mono">
                              {row.endpoint || row.api_name || '-'}
                            </code>
                          </td>
                          <td className="px-6 py-3 text-muted-foreground">
                            {row.scenario_type || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Modal Footer with Pagination */}
              <div className="p-4 border-t bg-muted/20 flex justify-between items-center">
                <div className="text-xs text-muted-foreground">
                  Page {viewPage + 1} of {Math.ceil(viewTotal / 50)}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleViewPageChange(Math.max(0, viewPage - 1))}
                    disabled={viewPage === 0 || isViewLoading}
                    className="h-8 w-8"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleViewPageChange(viewPage + 1)}
                    disabled={(viewPage + 1) * 50 >= viewTotal || isViewLoading}
                    className="h-8 w-8"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                  <div className="ml-4 pl-4 border-l">
                    <Button variant="ghost" onClick={() => setViewingDataset(null)}>Close</Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Rename Dataset Modal */}
        {renamingDataset && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-card w-full max-w-md bg-card border rounded-lg shadow-xl p-6 space-y-4">
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Rename Dataset</h3>
                <p className="text-sm text-muted-foreground">Enter a new name for this dataset.</p>
              </div>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="dataset-name">Name</Label>
                  <Input
                    id="dataset-name"
                    value={newDatasetName}
                    onChange={(e) => setNewDatasetName(e.target.value)}
                    placeholder="Enter dataset name"
                    autoFocus
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setRenamingDataset(null)}>Cancel</Button>
                  <Button onClick={handleRenameDataset}>Save Changes</Button>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
