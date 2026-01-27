"use client"

import * as React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  FileCode,
  Plus,
  Edit,
  Trash2,
  Copy,
  Eye,
  RefreshCw,
  Search,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  MoreHorizontal,
  ArrowUpDown,
  Calendar,
  Layers,
  Sparkles,
  TrendingUp,
  FileJson,
  Zap,
  ArrowRight,
  Grid3X3,
  List,
  ChevronRight,
  Activity,
  Shield,
  Code2,
  Box,
  LayoutGrid,
  Workflow,
} from "lucide-react"
import { apiClient } from "@/lib/api"
import type { TemplateModel, TemplateFilters } from "@/lib/api-types"
import { cn, formatDate, toTitleCase } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { ConfidenceBadge } from "@/components/ui/confidence-badge"
import { EmptyState } from "@/components/ui/empty-state"
import { TemplateListSkeleton } from "@/components/ui/skeleton"
import { SearchInput } from "@/components/ui/search-input"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { DataExportButton } from "@/components/data-export/DataExportButton"
import { OnboardingTour } from "@/components/onboarding/OnboardingTour"

// =============================================================================
// STAT CARD COMPONENT
// =============================================================================

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  gradient: string
  trend?: { value: number; label: string }
}

const StatCard = ({ title, value, subtitle, icon: Icon, gradient, trend }: StatCardProps) => (
  <div className={cn(
    "relative overflow-hidden rounded-2xl p-6",
    "bg-gradient-to-br border border-white/10",
    "shadow-lg shadow-black/5",
    "transition-all duration-300 hover:scale-[1.02] hover:shadow-xl",
    gradient
  )}>
    {/* Background Pattern */}
    <div className="absolute inset-0 opacity-10">
      <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/20" />
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/10" />
    </div>
    
    <div className="relative">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
          <Icon className="h-5 w-5 text-white" />
        </div>
        {trend && (
          <div className="flex items-center gap-1 text-xs font-medium text-white/80">
            <TrendingUp className="h-3 w-3" />
            {trend.value > 0 ? '+' : ''}{trend.value}% {trend.label}
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm font-medium text-white/80">{title}</div>
      {subtitle && <div className="text-xs text-white/60 mt-1">{subtitle}</div>}
    </div>
  </div>
)

// =============================================================================
// TEMPLATE CARD COMPONENT
// =============================================================================

interface TemplateCardProps {
  template: TemplateModel
  onView: () => void
  onEdit: () => void
  onDelete: () => void
  onToggleStatus: () => void
  isToggling: boolean
  getMethodBadgeVariant: (method: string) => string
}

const TemplateCard = ({ 
  template, 
  onView, 
  onEdit, 
  onDelete, 
  onToggleStatus,
  isToggling,
  getMethodBadgeVariant 
}: TemplateCardProps) => {
  const isApproved = template.status === "approved"
  
  return (
    <div className={cn(
      "group relative rounded-2xl border bg-card p-6",
      "transition-all duration-300",
      "hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1",
      isApproved 
        ? "border-emerald-500/20 bg-gradient-to-br from-emerald-500/[0.03] to-transparent" 
        : "border-border/50 hover:border-border"
    )}>
      {/* Status Indicator */}
      <div className="absolute top-4 right-4">
        <div className={cn(
          "flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium",
          isApproved 
            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" 
            : "bg-muted text-muted-foreground"
        )}>
          <span className={cn(
            "h-1.5 w-1.5 rounded-full",
            isApproved ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"
          )} />
          {isApproved ? "Active" : "Draft"}
        </div>
      </div>

      {/* Method Badge */}
      <div className="mb-4">
        <span className={cn(
          "inline-flex px-2.5 py-1 rounded-lg text-xs font-bold ring-1 ring-inset",
          getMethodBadgeVariant(template.method)
        )}>
          {template.method}
        </span>
      </div>

      {/* Title & Description */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground mb-1.5 group-hover:text-primary transition-colors">
          {toTitleCase(template.api_name)}
        </h3>
        <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
          {template.description || "No description provided."}
        </p>
      </div>

      {/* Base URL */}
      <div className="mb-4">
        <code className="text-xs font-mono text-muted-foreground bg-muted/50 px-2.5 py-1.5 rounded-lg block truncate">
          {template.base_url || template.endpoint || "No URL defined"}
        </code>
      </div>

      {/* Keywords */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        {template.intent_keywords.slice(0, 4).map((keyword) => (
          <span 
            key={keyword} 
            className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-primary/5 text-primary border border-primary/10"
          >
            {keyword}
          </span>
        ))}
        {template.intent_keywords.length > 4 && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-muted text-muted-foreground">
            +{template.intent_keywords.length - 4} more
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-border/50">
        <div className="flex items-center gap-2">
          <Switch
            checked={isApproved}
            onCheckedChange={onToggleStatus}
            disabled={isToggling}
            className="scale-90 data-[state=checked]:bg-emerald-600"
          />
          <span className="text-xs text-muted-foreground">
            {template.updated_at ? formatDate(template.updated_at) : "Not updated"}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  onClick={(e) => { e.stopPropagation(); onView() }}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>View Details</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 text-muted-foreground hover:text-primary"
                  onClick={(e) => { e.stopPropagation(); onEdit() }}
                >
                  <Edit className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Edit Template</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={(e) => { 
                    e.stopPropagation()
                    if (confirm(`Delete template "${template.api_name}"?`)) {
                      onDelete()
                    }
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Delete Template</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Confidence Indicator */}
      {template.confidence !== undefined && template.confidence > 0 && (
        <div className="absolute bottom-16 left-6">
          <ConfidenceBadge confidence={template.confidence} showLabel={false} className="scale-90" />
        </div>
      )}
    </div>
  )
}

// =============================================================================
// MAIN PAGE COMPONENT
// =============================================================================

export default function TemplatesPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [searchQuery, setSearchQuery] = React.useState("")
  const [filters, setFilters] = React.useState<TemplateFilters>({
    status: [],
    intent: [],
  })
  const [showFilters, setShowFilters] = React.useState(false)
  const [togglingTemplateId, setTogglingTemplateId] = React.useState<string | null>(null)
  const [viewMode, setViewMode] = React.useState<'grid' | 'list'>('grid')

  // Fetch templates
  const { data: templates, isLoading, error } = useQuery({
    queryKey: ["templates"],
    queryFn: () => apiClient.listTemplates(),
  })

  // Hot reload mutation
  const reloadMutation = useMutation({
    mutationFn: () => apiClient.reloadTemplates(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] })
      toast({
        title: "Templates Reloaded",
        description: "All templates have been refreshed from disk.",
      })
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (templateId: string) => apiClient.deleteTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] })
      queryClient.refetchQueries({ queryKey: ["templates"] })
      toast({
        title: "Template Deleted",
        description: "The template has been successfully deleted.",
        variant: "default",
      })
    },
    onError: (error: any) => {
      toast({
        title: "Delete Failed",
        description: error?.message || "Failed to delete template. Only draft templates can be deleted.",
        variant: "destructive",
      })
    },
  })

  // Filter templates
  const filteredTemplates = React.useMemo(() => {
    if (!templates) return []

    return templates.filter((template) => {
      // Search filter
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase()
        const matchesSearch =
          template.api_name.toLowerCase().includes(searchLower) ||
          template.description.toLowerCase().includes(searchLower) ||
          template.intent_keywords.some((k) => k.toLowerCase().includes(searchLower))

        if (!matchesSearch) return false
      }

      // Status filter
      if (filters.status && filters.status.length > 0) {
        if (!filters.status.includes(template.status || "active")) return false
      }

      // Intent filter
      if (filters.intent && filters.intent.length > 0) {
        const hasMatchingIntent = template.intent_keywords.some((keyword) =>
          filters.intent!.some((filterIntent) =>
            keyword.toLowerCase().includes(filterIntent.toLowerCase())
          )
        )
        if (!hasMatchingIntent) return false
      }

      return true
    })
  }, [templates, searchQuery, filters])

  // Toggle template visibility mutation
  const toggleVisibilityMutation = useMutation({
    mutationFn: (templateId: string) => {
      setTogglingTemplateId(templateId)
      return apiClient.toggleTemplateVisibility(templateId)
    },
    onMutate: async (templateId: string) => {
      await queryClient.cancelQueries({ queryKey: ["templates"] })
      const previousTemplates = queryClient.getQueryData(["templates"])

      queryClient.setQueryData(["templates"], (old: any) => {
        if (!old) return old
        return old.map((t: any) => {
          const id = t.template_id || t.api_name
          if (id === templateId) {
            const newStatus = t.status === "approved" ? "draft" : "approved"
            return { ...t, status: newStatus }
          }
          return t
        })
      })

      return { previousTemplates }
    },
    onSuccess: (data, templateId) => {
      setTogglingTemplateId(null)

      queryClient.setQueryData(["templates"], (old: any) => {
        if (!old) return old
        return old.map((t: any) => {
          const id = t.template_id || t.api_name
          if (id === templateId) {
            return { ...t, status: data.status }
          }
          return t
        })
      })

      const isApproved = data.status === "approved"
      toast({
        title: isApproved ? "Template Activated" : "Template Deactivated",
        description: isApproved
          ? "Template is now active and available for dataset generation."
          : "Template has been moved to draft state.",
      })
    },
    onError: (error: any, templateId, context) => {
      setTogglingTemplateId(null)

      if (context?.previousTemplates) {
        queryClient.setQueryData(["templates"], context.previousTemplates)
      }

      toast({
        title: "Toggle Failed",
        description: error?.detail || error?.message || "Failed to toggle status",
        variant: "destructive",
      })
    },
  })

  // UI Helpers
  const getMethodBadgeVariant = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 hover:bg-blue-500/20 border-blue-200 dark:border-blue-900'
      case 'POST': return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-500/20 border-emerald-200 dark:border-emerald-900'
      case 'PUT': return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 hover:bg-amber-500/20 border-amber-200 dark:border-amber-900'
      case 'DELETE': return 'bg-red-500/10 text-red-700 dark:text-red-400 hover:bg-red-500/20 border-red-200 dark:border-red-900'
      case 'PATCH': return 'bg-purple-500/10 text-purple-700 dark:text-purple-400 hover:bg-purple-500/20 border-purple-200 dark:border-purple-900'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  // Calculate stats
  const stats = React.useMemo(() => {
    if (!templates) return { total: 0, active: 0, draft: 0, methods: {} }
    
    const active = templates.filter(t => t.status === "approved").length
    const draft = templates.filter(t => t.status !== "approved").length
    const methods: Record<string, number> = {}
    
    templates.forEach(t => {
      methods[t.method] = (methods[t.method] || 0) + 1
    })
    
    return { total: templates.length, active, draft, methods }
  }, [templates])

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border/40">
        {/* Background Decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
          <div className="absolute top-20 -left-20 w-60 h-60 bg-blue-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-12 lg:py-16">
          {/* Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-10">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10">
                  <Layers className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h1 className="text-3xl lg:text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                    API Templates
                  </h1>
                  <p className="text-muted-foreground mt-1">
                    Design, manage, and deploy your semantic API patterns
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => reloadMutation.mutate()}
                      disabled={reloadMutation.isPending}
                      className="h-10 gap-2 rounded-xl border-dashed"
                    >
                      <RefreshCw className={cn("h-4 w-4", reloadMutation.isPending && "animate-spin")} />
                      Sync
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Reload templates from disk</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <DataExportButton
                data={filteredTemplates}
                filename="nlpforge_templates"
                disabled={!filteredTemplates || filteredTemplates.length === 0}
                label="Export"
              />

              <div className="h-8 w-px bg-border/60" />

              <Button 
                onClick={() => router.push("/templates/new")} 
                className="h-10 gap-2 rounded-xl shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all"
                data-tour="create-template"
              >
                <Plus className="h-4 w-4" />
                New Template
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={Box}
              title="Total Templates"
              value={stats.total}
              subtitle="Across all categories"
              gradient="from-violet-600 to-indigo-600"
            />
            <StatCard
              icon={CheckCircle}
              title="Active Templates"
              value={stats.active}
              subtitle="Ready for generation"
              gradient="from-emerald-600 to-teal-600"
            />
            <StatCard
              icon={FileCode}
              title="Draft Templates"
              value={stats.draft}
              subtitle="Pending approval"
              gradient="from-amber-600 to-orange-600"
            />
            <StatCard
              icon={Activity}
              title="HTTP Methods"
              value={Object.keys(stats.methods).length}
              subtitle={Object.keys(stats.methods).join(", ") || "None"}
              gradient="from-pink-600 to-rose-600"
            />
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Toolbar */}
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between mb-8">
          {/* Search */}
          <div className="w-full lg:max-w-md">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates by name, endpoint, or keywords..."
                className={cn(
                  "w-full h-12 pl-11 pr-4 rounded-xl",
                  "bg-muted/30 border border-border/50",
                  "text-sm placeholder:text-muted-foreground",
                  "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/30",
                  "transition-all duration-200"
                )}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-muted"
                >
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                </button>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 w-full lg:w-auto">
            {/* Filter Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "h-10 rounded-xl gap-2",
                showFilters && "bg-muted border-primary/30"
              )}
            >
              <Filter className="h-4 w-4" />
              Filters
              {(filters.status?.length ?? 0) > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-[10px]">
                  {filters.status?.length}
                </Badge>
              )}
            </Button>

            {/* View Toggle */}
            <div className="flex items-center rounded-xl border border-border/50 p-1 bg-muted/30" role="group" aria-label="View options">
              <button
                onClick={() => setViewMode('grid')}
                aria-label="Grid view"
                aria-pressed={viewMode === 'grid'}
                title="Grid view"
                className={cn(
                  "p-2 rounded-lg transition-all",
                  viewMode === 'grid' ? "bg-background shadow-sm" : "hover:bg-background/50"
                )}
              >
                <Grid3X3 className="h-4 w-4" aria-hidden="true" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                aria-label="List view"
                aria-pressed={viewMode === 'list'}
                title="List view"
                className={cn(
                  "p-2 rounded-lg transition-all",
                  viewMode === 'list' ? "bg-background shadow-sm" : "hover:bg-background/50"
                )}
              >
                <List className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>

            {/* Results Count */}
            <Badge variant="outline" className="h-10 px-4 rounded-xl text-sm font-normal">
              {filteredTemplates.length} {filteredTemplates.length === 1 ? 'template' : 'templates'}
            </Badge>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mb-6 p-5 rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm animate-in slide-in-from-top-2 duration-200">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <span className="text-sm font-medium text-muted-foreground">Status:</span>
              <div className="flex flex-wrap gap-2">
                {(["approved", "draft", "deprecated"] as const).map((status) => {
                  const statusLabels: Record<string, string> = {
                    approved: "Active",
                    draft: "Draft", 
                    deprecated: "Deprecated"
                  }
                  const isActive = filters.status?.includes(status)
                  return (
                    <button
                      key={status}
                      onClick={() => {
                        const newStatus = isActive
                          ? filters.status?.filter((s) => s !== status)
                          : [...(filters.status || []), status]
                        setFilters({ ...filters, status: newStatus })
                      }}
                      className={cn(
                        "px-4 py-2 rounded-xl text-sm font-medium border transition-all",
                        isActive
                          ? "bg-primary text-primary-foreground border-primary shadow-sm"
                          : "bg-background text-muted-foreground border-border/50 hover:border-primary/30 hover:text-foreground"
                      )}
                    >
                      {statusLabels[status]}
                    </button>
                  )
                })}
              </div>

              {(filters.status?.length ?? 0) > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFilters({ ...filters, status: [] })}
                  className="ml-auto text-muted-foreground hover:text-foreground"
                >
                  Clear filters
                  <XCircle className="h-3.5 w-3.5 ml-2" />
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-72 rounded-2xl bg-muted/20 animate-pulse" />
              ))}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-8 rounded-2xl border border-destructive/20 bg-destructive/5 text-center">
            <div className="inline-flex items-center justify-center p-3 rounded-xl bg-destructive/10 mb-4">
              <AlertCircle className="h-6 w-6 text-destructive" />
            </div>
            <p className="font-semibold text-destructive mb-1">Error loading templates</p>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              {error instanceof Error ? error.message : "An unexpected error occurred while fetching templates."}
            </p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-4"
              onClick={() => queryClient.refetchQueries({ queryKey: ["templates"] })}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        )}

        {/* Empty State - No Templates */}
        {!isLoading && !error && templates && templates.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/10 mb-6">
              <Layers className="h-12 w-12 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No templates yet</h3>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              Create your first API template to get started with semantic generation and intelligent API routing.
            </p>
            <Button onClick={() => router.push("/templates/new")} className="gap-2 rounded-xl">
              <Plus className="h-4 w-4" />
              Create Your First Template
            </Button>
          </div>
        )}

        {/* Empty State - No Search Results */}
        {!isLoading && !error && filteredTemplates.length === 0 && templates && templates.length > 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="p-4 rounded-2xl bg-muted/50 mb-6">
              <Search className="h-12 w-12 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No matches found</h3>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              Adjust your search or filters to find what you're looking for.
            </p>
            <Button 
              variant="outline"
              onClick={() => {
                setSearchQuery("")
                setFilters({ status: [], intent: [] })
              }}
              className="gap-2 rounded-xl"
            >
              Clear All Filters
            </Button>
          </div>
        )}

        {/* Templates Grid */}
        {filteredTemplates.length > 0 && viewMode === 'grid' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-tour="template-list">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.template_id || template.api_name}
                template={template}
                onView={() => router.push(`/templates/${template.template_id || template.api_name}`)}
                onEdit={() => router.push(`/templates/${template.template_id || template.api_name}/edit`)}
                onDelete={() => deleteMutation.mutate(template.template_id || template.api_name)}
                onToggleStatus={() => toggleVisibilityMutation.mutate(template.template_id || template.api_name)}
                isToggling={togglingTemplateId === (template.template_id || template.api_name)}
                getMethodBadgeVariant={getMethodBadgeVariant}
              />
            ))}
          </div>
        )}

        {/* Templates List View */}
        {filteredTemplates.length > 0 && viewMode === 'list' && (
          <div className="rounded-2xl border border-border/50 bg-card overflow-hidden" data-tour="template-list">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/40 bg-muted/30">
                    <th className="px-6 py-4 text-left font-medium text-xs text-muted-foreground uppercase tracking-wider">Template</th>
                    <th className="px-4 py-4 text-left font-medium text-xs text-muted-foreground uppercase tracking-wider">Method</th>
                    <th className="px-4 py-4 text-left font-medium text-xs text-muted-foreground uppercase tracking-wider">Status</th>
                    <th className="px-4 py-4 text-left font-medium text-xs text-muted-foreground uppercase tracking-wider hidden lg:table-cell">Endpoint</th>
                    <th className="px-4 py-4 text-left font-medium text-xs text-muted-foreground uppercase tracking-wider hidden md:table-cell">Updated</th>
                    <th className="px-4 py-4 text-right font-medium text-xs text-muted-foreground uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {filteredTemplates.map((template) => (
                    <tr
                      key={template.template_id || template.api_name}
                      className="group hover:bg-muted/20 transition-colors cursor-pointer"
                      onClick={() => router.push(`/templates/${template.template_id || template.api_name}/edit`)}
                    >
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <p className="font-semibold text-foreground group-hover:text-primary transition-colors">
                            {toTitleCase(template.api_name)}
                          </p>
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {template.description || "No description"}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className={cn(
                          "inline-flex px-2.5 py-1 rounded-lg text-xs font-bold ring-1 ring-inset",
                          getMethodBadgeVariant(template.method)
                        )}>
                          {template.method}
                        </span>
                      </td>
                      <td className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "flex h-2 w-2 rounded-full",
                            template.status === "approved" ? "bg-emerald-500" : "bg-muted-foreground"
                          )} />
                          <span className="text-sm">
                            {template.status === "approved" ? "Active" : "Draft"}
                          </span>
                          <Switch
                            checked={template.status === "approved"}
                            onCheckedChange={() => toggleVisibilityMutation.mutate(template.template_id || template.api_name)}
                            disabled={togglingTemplateId === (template.template_id || template.api_name)}
                            className="scale-75 data-[state=checked]:bg-emerald-600"
                          />
                        </div>
                      </td>
                      <td className="px-4 py-4 hidden lg:table-cell">
                        <code className="text-xs font-mono text-muted-foreground">
                          {template.base_url || template.endpoint || "—"}
                        </code>
                      </td>
                      <td className="px-4 py-4 hidden md:table-cell">
                        <span className="text-xs text-muted-foreground">
                          {template.updated_at ? formatDate(template.updated_at) : "—"}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-40 rounded-xl">
                            <DropdownMenuItem onClick={() => router.push(`/templates/${template.template_id || template.api_name}`)}>
                              <Eye className="mr-2 h-4 w-4" />
                              View
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => router.push(`/templates/${template.template_id || template.api_name}/edit`)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => {
                                if (confirm(`Delete template "${template.api_name}"?`)) {
                                  deleteMutation.mutate(template.template_id || template.api_name)
                                }
                              }}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Onboarding Tour */}
      <OnboardingTour tourId="templates" />
    </div>
  )
}

