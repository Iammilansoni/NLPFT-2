'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Download,
  RefreshCw,
  Database,
  FileJson,
  FileText,
  Sparkles,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Play,
  Settings,
  TrendingUp,
  Upload,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
// import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

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
  created_at?: string
  completed_at?: string
  statistics?: DatasetStatistics
  files?: {
    json: string
    jsonl: string
    csv: string
    summary: string
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

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

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
  const [numExamples, setNumExamples] = useState(100)
  const [userPrompt, setUserPrompt] = useState('')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
      const response = await fetch(
        `${API_BASE}/api/v1/datasets/preview/${taskId}?limit=${limit}&offset=${offset}`
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
      setAllTasks(data.datasets || [])
    } catch (err) {
      // Backend not available - this is expected in development
      console.log('Backend API not available')
    } finally {
      setIsLoading(false)
    }
  }, [API_BASE])

  const fetchTaskStatus = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/datasets/status/${taskId}`)
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
          num_examples: numExamples,
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
      const response = await fetch(`${API_BASE}/api/v1/datasets/download/${taskId}/${format}`)
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

      const response = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
        method: 'POST',
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-emerald-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-5 h-5 text-gray-500" />
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">Loading datasets...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="p-6 lg:p-8 space-y-8 max-w-[1600px] mx-auto">
        {/* Header */}
        <motion.div initial="hidden" animate="show" variants={fadeUp}>
          <div className="flex items-center gap-4 mb-6">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
              <Database className="h-7 w-7" />
            </div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight">Dataset Generator</h1>
              <p className="text-muted-foreground mt-1">
                Generate structured datasets with NLP augmentation and embeddings
              </p>
            </div>
          </div>
        </motion.div>

        <Tabs defaultValue="generate" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="generate">Generate New Dataset</TabsTrigger>
            <TabsTrigger value="upload">Upload for Embedding</TabsTrigger>
          </TabsList>

          <TabsContent value="generate">
            {/* Configuration Card */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
              <Card className="border-2">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white shadow-md">
                      <Settings className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>Configuration</CardTitle>
                      <CardDescription>Set up your dataset generation parameters</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Template Selector */}
                  <div className="space-y-2">
                    <Label htmlFor="template-select" className="text-sm font-medium">
                      Select Template <span className="text-red-500">*</span>
                    </Label>
                    <select
                      id="template-select"
                      value={templateId}
                      onChange={(e) => setTemplateId(e.target.value)}
                      disabled={isGenerating}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <option value="">Select an approved template...</option>
                      {Array.isArray(templates) && templates.length > 0 ? (
                        templates.map((template) => (
                          <option key={template.template_id || template.t_id} value={template.template_id || template.t_id}>
                            ✓ {template.api_name}
                          </option>
                        ))
                      ) : (
                        <option value="" disabled>No approved templates available</option>
                      )}
                    </select>
                    <div className="flex items-center gap-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-md">
                      <span className="text-amber-600 dark:text-amber-400 text-xs">
                        💡 Only approved templates can be used for dataset generation. 
                        {templates.length === 0 && ' Go to Templates page to create and approve templates.'}
                      </span>
                    </div>
                  </div>

                  {/* User Prompt */}
                  <div className="space-y-2">
                    <Label htmlFor="user-prompt" className="text-sm font-medium">
                      User Prompt <span className="text-red-500">*</span>
                    </Label>
                    <textarea
                      id="user-prompt"
                      value={userPrompt}
                      onChange={(e) => setUserPrompt(e.target.value)}
                      placeholder="Describe the specific scenarios, edge cases, or variations you want to generate.&#10;&#10;Examples:&#10;• &quot;Focus on validation errors for invalid email formats&quot;&#10;• &quot;Generate high-risk security scenarios like SQL injection&quot;&#10;• &quot;Include mixed English and Spanish queries&quot;&#10;• &quot;Simulate slow network timeouts and partial data&quot;"
                      rows={4}
                      disabled={isGenerating}
                      className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                    />
                    <p className="text-xs text-muted-foreground">
                      💡 Provide additional context to customize generated test cases (required for better quality)
                    </p>
                  </div>

                  {/* Parameters Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="num-examples">Number of Examples</Label>
                      <Input
                        id="num-examples"
                        type="number"
                        min={1}
                        max={1000}
                        value={numExamples}
                        onChange={(e) => setNumExamples(parseInt(e.target.value) || 100)}
                        disabled={isGenerating}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="llm-model">LLM Model</Label>
                      <Input
                        id="llm-model"
                        type="text"
                        value="Llama 3.2 Instruct (Ollama)"
                        disabled
                        className="bg-muted"
                      />
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-purple-500" />
                        Local CPU inference with quantized models
                      </p>
                    </div>
                  </div>

                  {/* Generate Button */}
                  <Button
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    size="lg"
                    className="w-full gap-2 shadow-lg"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Generating Dataset...
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5" />
                        Generate Dataset
                      </>
                    )}
                  </Button>

                  {error && (
                    <div className="p-4 rounded-lg border-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20">
                      <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          <TabsContent value="upload">
            {/* Upload CSV Card */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <Card className="border-2">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-500 flex items-center justify-center text-white shadow-md">
                      <Upload className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>Upload CSV for Embedding</CardTitle>
                      <CardDescription>Upload an existing CSV file to generate embeddings</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <Label
                        htmlFor="csv-upload"
                        className="flex items-center justify-center h-32 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                      >
                        <div className="text-center">
                          {uploadedFile ? (
                            <div className="flex flex-col items-center gap-2">
                              <FileText className="h-8 w-8 text-emerald-500" />
                              <p className="text-sm font-medium">{uploadedFile.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {(uploadedFile.size / 1024).toFixed(2)} KB
                              </p>
                            </div>
                          ) : (
                            <div className="flex flex-col items-center gap-2">
                              <Upload className="h-8 w-8 text-muted-foreground" />
                              <p className="text-sm font-medium">Click to upload CSV</p>
                              <p className="text-xs text-muted-foreground">or drag and drop</p>
                            </div>
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
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={handleFileUpload}
                      disabled={!uploadedFile || isUploading}
                      className="flex-1 gap-2"
                    >
                      {isUploading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Upload & Process
                        </>
                      )}
                    </Button>
                    {uploadedFile && (
                      <Button
                        variant="outline"
                        onClick={() => setUploadedFile(null)}
                        disabled={isUploading}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>
        </Tabs>

        {/* Task Status */}
        {currentTask && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(currentTask.status)}
                    <div>
                      <CardTitle>Task Status</CardTitle>
                      <CardDescription>Task ID: {currentTask.task_id}</CardDescription>
                    </div>
                  </div>
                  <Badge
                    variant={
                      currentTask.status === 'completed'
                        ? 'default'
                        : currentTask.status === 'failed'
                        ? 'destructive'
                        : 'secondary'
                    }
                    className="capitalize"
                  >
                    {currentTask.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">{currentTask.message}</p>

                {currentTask.statistics && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <StatCard
                      label="Total APIs"
                      value={currentTask.statistics.total_apis}
                      gradient="from-blue-500 to-cyan-500"
                    />
                    <StatCard
                      label="NL Variations"
                      value={currentTask.statistics.total_nl_variations}
                      gradient="from-purple-500 to-pink-500"
                    />
                    <StatCard
                      label="Avg per API"
                      value={currentTask.statistics.avg_variations_per_api.toFixed(1)}
                      gradient="from-emerald-500 to-green-500"
                    />
                  </div>
                )}

                {currentTask.status === 'completed' && (
                  <div className="flex flex-wrap gap-3 pt-4 border-t">
                    <Button onClick={() => handleDownload(currentTask.task_id, 'json')} variant="outline" className="gap-2">
                      <FileJson className="w-4 h-4" />
                      Download JSON
                    </Button>
                    <Button onClick={() => handleDownload(currentTask.task_id, 'csv')} variant="outline" className="gap-2">
                      <FileText className="w-4 h-4" />
                      Download CSV
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Preview Data */}
        {previewData && previewData.records && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Dataset Preview</CardTitle>
                  <Badge variant="secondary">
                    {previewData.showing || 0} of {previewData.total_records || 0} records
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b">
                      <tr className="text-left">
                        <th className="pb-3 font-medium">API</th>
                        <th className="pb-3 font-medium">Natural Language Input</th>
                        <th className="pb-3 font-medium">Definition</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {(previewData.records || []).map((record, index) => (
                        <tr key={index} className="hover:bg-muted/50">
                          <td className="py-3 font-mono text-xs">{record.api || ''}</td>
                          <td className="py-3">{record.nl_input || ''}</td>
                          <td className="py-3 text-xs text-muted-foreground">
                            {(record.definition_of_api || '').substring(0, 100)}...
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between pt-4 border-t mt-4">
                  <div className="text-sm text-muted-foreground">
                    Showing {previewData.offset + 1} - {previewData.offset + previewData.showing} of{' '}
                    {previewData.total_records || 0}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => fetchPreview(currentTask!.task_id, pageSize, 0)}
                      disabled={(previewData.offset || 0) === 0}
                    >
                      <ChevronsLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() =>
                        fetchPreview(currentTask!.task_id, pageSize, Math.max(0, (previewData.offset || 0) - pageSize))
                      }
                      disabled={(previewData.offset || 0) === 0}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-sm px-4">
                      Page {currentPage + 1} of {Math.ceil((previewData.total_records || 1) / pageSize)}
                    </span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => fetchPreview(currentTask!.task_id, pageSize, (previewData.offset || 0) + pageSize)}
                      disabled={!previewData.has_more}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() =>
                        fetchPreview(
                          currentTask!.task_id,
                          pageSize,
                          Math.floor(((previewData.total_records || 1) - 1) / pageSize) * pageSize
                        )
                      }
                      disabled={!previewData.has_more}
                    >
                      <ChevronsRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Previous Generations */}
        {allTasks.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Previous Generations</CardTitle>
                  <Button variant="ghost" size="sm" onClick={fetchAllTasks} className="gap-2">
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {allTasks.slice(0, 5).map((task) => (
                  <div
                    key={task.task_id}
                    className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {getStatusIcon(task.status)}
                      <div>
                        <p className="font-medium">Dataset {task.dataset_id || task.task_id}</p>
                        <p className="text-sm text-muted-foreground">
                          {task.created_at ? new Date(task.created_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>
                    </div>
                    {task.status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setCurrentTask(task)
                          fetchPreview(task.task_id)
                        }}
                      >
                        View
                      </Button>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, gradient }: { label: string; value: string | number; gradient: string }) {
  return (
    <div className="p-4 rounded-xl border bg-card">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-muted-foreground">{label}</p>
        <div className={cn('h-8 w-8 rounded-lg bg-gradient-to-br flex items-center justify-center', gradient)}>
          <TrendingUp className="h-4 w-4 text-white" />
        </div>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}
