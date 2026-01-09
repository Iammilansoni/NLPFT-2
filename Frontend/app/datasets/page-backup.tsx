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
// import { Switch } from '@/components/ui/switch'
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
    const [numExamples, setNumExamples] = useState(100)
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
                `${API_BASE}/api/v1/datasets/preview/${taskId}?limit=${limit}&offset=${offset}`,
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

    // Handler: Embed dataset to Redis
    const handleEmbedDataset = async (datasetId: string) => {
        setEmbeddingDatasetId(datasetId)
        try {
            const token = localStorage.getItem('nlpforge_access_token')
            const response = await fetch(`${API_BASE}/api/v1/datasets/db/${datasetId}/embed`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (!response.ok) throw new Error('Failed to start embedding')
            // Refresh datasets to show updated status
            await fetchAllTasks()
        } catch (err) {
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
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
            <div className="p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Datasets</h1>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                            Generate, upload, and manage datasets with embeddings
                        </p>
                    </div>
                    <div className="hidden md:flex items-center gap-6 text-sm">
                        <div className="text-right">
                            <p className="text-xl font-semibold tabular-nums text-slate-900 dark:text-slate-100">{persistentDatasets.length}</p>
                            <p className="text-slate-500">Total</p>
                        </div>
                        <div className="h-8 w-px bg-slate-200 dark:bg-slate-800" />
                        <div className="text-right">
                            <p className="text-xl font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                                {persistentDatasets.filter(d => d.embedding_status === 'completed').length}
                            </p>
                            <p className="text-slate-500">Embedded</p>
                        </div>
                    </div>
                </div>

                <Tabs defaultValue="generate" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 mb-6 h-11">
                        <TabsTrigger value="generate" className="gap-2">
                            <FileSpreadsheet className="w-4 h-4" />
                            Generate New Dataset
                        </TabsTrigger>
                        <TabsTrigger value="upload" className="gap-2">
                            <Upload className="w-4 h-4" />
                            Upload for Embedding
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="generate">
                        {/* Configuration Card */}
                        <div>
                            <Card className="border shadow-sm">
                                <CardHeader className="border-b bg-muted/30">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                            <Settings className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">Generation Configuration</CardTitle>
                                            <CardDescription>Set up your AI-powered dataset generation</CardDescription>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-6 space-y-6">
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

                                    {/* Parameters */}
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
                        </div>
                    </TabsContent>

                    <TabsContent value="upload">
                        {/* Upload CSV Card */}
                        <div>
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center gap-3">
                                        <div className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center">
                                            <Upload className="h-4 w-4 text-muted-foreground" />
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
                        </div>
                    </TabsContent>
                </Tabs>

                {/* ============= MY DATASETS SECTION ============= */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                    {/* Toolbar */}
                    <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">My Datasets</h2>
                            <span className="text-xs text-slate-500">
                                {persistentDatasets.length} total
                            </span>
                        </div>

                        <div className="flex items-center gap-2">
                            <div className="relative">
                                <Input
                                    placeholder="Filter datasets..."
                                    className="h-8 w-[200px] pl-8 text-xs bg-slate-50 dark:bg-slate-900"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                                <Database className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                className="h-8 w-8 p-0"
                                onClick={fetchAllTasks}
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                            </Button>
                        </div>
                    </div>

                    {/* Dataset List */}
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                        {persistentDatasets.length === 0 ? (
                            <div className="p-8 text-center text-slate-500">
                                <Database className="w-8 h-8 mx-auto mb-2 opacity-20" />
                                <p>No datasets found. Generate or upload one to get started.</p>
                            </div>
                        ) : (
                            persistentDatasets
                                .filter(d => d.name.toLowerCase().includes(searchQuery.toLowerCase()))
                                .map((dataset) => (
                                    <div key={dataset.dataset_id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                {/* Icon */}
                                                <div className={cn(
                                                    "w-10 h-10 rounded-lg flex items-center justify-center border",
                                                    dataset.source_type === 'AI_GENERATED'
                                                        ? "bg-purple-50 border-purple-100 text-purple-600 dark:bg-purple-900/10 dark:border-purple-900/20"
                                                        : "bg-blue-50 border-blue-100 text-blue-600 dark:bg-blue-900/10 dark:border-blue-900/20"
                                                )}>
                                                    {dataset.source_type === 'AI_GENERATED' ? (
                                                        <Zap className="w-5 h-5" />
                                                    ) : (
                                                        <FileText className="w-5 h-5" />
                                                    )}
                                                </div>

                                                {/* Info */}
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="font-medium text-slate-900 dark:text-slate-100">
                                                            {dataset.name}
                                                        </h3>
                                                        {dataset.embedding_status === 'completed' && (
                                                            <div className="flex items-center text-[10px] text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400 px-1.5 py-0.5 rounded-full font-medium">
                                                                <CheckCircle className="w-3 h-3 mr-1" />
                                                                Embedded
                                                            </div>
                                                        )}
                                                        {dataset.embedding_status === 'in_progress' && (
                                                            <div className="flex items-center text-[10px] text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400 px-1.5 py-0.5 rounded-full font-medium">
                                                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                                                Processing
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                                                        <span className="flex items-center">
                                                            <Database className="w-3 h-3 mr-1" />
                                                            {dataset.total_rows} rows
                                                        </span>
                                                        <span>•</span>
                                                        <span>{formatDateTime(dataset.created_at)}</span>
                                                        {dataset.template_name && (
                                                            <>
                                                                <span>•</span>
                                                                <span className="max-w-[150px] truncate">
                                                                    Template: {dataset.template_name}
                                                                </span>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleViewDataset(dataset)}
                                                >
                                                    View
                                                </Button>

                                                {dataset.embedding_status !== 'completed' && dataset.embedding_status !== 'in_progress' && (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleEmbedDataset(dataset.dataset_id)}
                                                        disabled={embeddingDatasetId === dataset.dataset_id}
                                                    >
                                                        {embeddingDatasetId === dataset.dataset_id ? (
                                                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                                                        ) : (
                                                            <Database className="w-3 h-3 mr-1" />
                                                        )}
                                                        Embed
                                                    </Button>
                                                )}

                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8 text-slate-400 hover:text-slate-600"
                                                    onClick={() => handleDownloadDatasetById(dataset)}
                                                >
                                                    <Download className="w-4 h-4" />
                                                </Button>

                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10"
                                                    onClick={() => handleDeleteDataset(dataset.dataset_id)}
                                                >
                                                    <X className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                        )}
                    </div>
                </div>

                {/* ============= PREVIEW OVERLAY (Simple Modal) ============= */}
                {viewingDataset && (
                    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden border border-slate-200 dark:border-slate-800 animate-in fade-in zoom-in duration-200">
                            <div className="p-4 border-b flex items-center justify-between bg-slate-50 dark:bg-slate-950">
                                <div>
                                    <h3 className="font-semibold text-lg">{viewingDataset.name}</h3>
                                    <p className="text-sm text-slate-500">{viewingDataset.total_rows} rows • {viewingDataset.source_type}</p>
                                </div>
                                <Button variant="ghost" size="icon" onClick={() => setViewingDataset(null)}>
                                    <X className="w-5 h-5" />
                                </Button>
                            </div>

                            <div className="flex-1 overflow-auto p-0">
                                {isViewLoading ? (
                                    <div className="flex flex-col items-center justify-center h-64">
                                        <Loader2 className="w-8 h-8 animate-spin text-primary mb-2" />
                                        <p className="text-sm text-muted-foreground">Loading preview...</p>
                                    </div>
                                ) : (
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-slate-50 dark:bg-slate-800/50 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-3 font-medium text-slate-500">Query</th>
                                                <th className="px-4 py-3 font-medium text-slate-500">API Endpoint</th>
                                                <th className="px-4 py-3 font-medium text-slate-500">Type</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                            {viewingRows.map((row, i) => (
                                                <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                                                    <td className="px-4 py-2 font-mono text-xs max-w-md truncate" title={row.query}>{row.query}</td>
                                                    <td className="px-4 py-2 max-w-xs truncate" title={row.endpoint || row.api_name}>
                                                        <span className="font-mono text-xs bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                                                            {row.endpoint || row.api_name || '-'}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-2 text-slate-500">
                                                        {row.scenario_type || 'Standard'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    </div>
                )}

            </div>
        </div>
    )
}
