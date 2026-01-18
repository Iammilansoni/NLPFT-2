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
        title: isApproved ? "Template Approved" : "Template Drafted",
        description: isApproved
          ? "Template is approved and available for dataset generation."
          : "Template is in draft state.",
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
      default: return 'bg-muted text-muted-foreground'
    }
  }

  return (
    <div className="min-h-screen bg-background font-sans">
      {/* Header Section */}
      <header className="px-6 py-8 md:py-10 max-w-7xl mx-auto border-b border-border/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div className="space-y-1.5">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Templates</h1>
            <div className="flex items-center gap-2 text-muted-foreground">
              <p className="text-sm">Manage standard API patterns</p>
              <span>•</span>
              <Badge variant="secondary" className="px-2 py-0.5 h-auto text-[10px] font-medium rounded-full bg-muted/50">
                {isLoading ? "..." : (filteredTemplates.length === templates?.length ? `${templates?.length || 0} Total` : `${filteredTemplates.length} Filtered`)}
              </Badge>
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
                    className="h-9 gap-2 text-muted-foreground hover:text-foreground border-dashed"
                  >
                    <RefreshCw className={cn("h-4 w-4", reloadMutation.isPending && "animate-spin")} />
                    Reload
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Reload Templates from Disk</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <DataExportButton
              data={filteredTemplates}
              filename="nlpforge_templates"
              disabled={!filteredTemplates || filteredTemplates.length === 0}
              label="Export"
            />

            <div className="h-6 w-px bg-border/60 mx-1" />

            <Button onClick={() => router.push("/templates/new")} className="shadow-sm" data-tour="create-template">
              <Plus className="h-4 w-4 mr-2" />
              New Template
            </Button>
          </div>
        </div>

        {/* Search & Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="w-full sm:max-w-md relative">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search by name, endpoint, or keywords..."
              className="w-full h-11 bg-muted/30 border-transparent focus:bg-background transition-all"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "h-9 border-dashed font-medium text-xs uppercase tracking-wide px-3",
                showFilters && "bg-muted border-solid"
              )}
            >
              <Filter className="h-3.5 w-3.5 mr-2" />
              Filters
            </Button>

            {(filters.status && filters.status.length > 0) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ ...filters, status: [] })}
                className="h-8 px-2 text-muted-foreground hover:text-foreground"
              >
                Reset
                <XCircle className="h-3 w-3 ml-2" />
              </Button>
            )}
          </div>
        </div>

        {/* Collapsible Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-border/40 animate-in slide-in-from-top-2 duration-200">
            <div className="flex items-center gap-4">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status:</span>
              <div className="flex flex-wrap gap-2">
                {(["draft", "active", "deprecated"] as const).map((status) => {
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
                        "px-3 py-1.5 rounded-full text-xs font-medium border transition-all",
                        isActive
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background text-muted-foreground border-border hover:border-foreground/30"
                      )}
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="px-6 py-8 max-w-7xl mx-auto">
        {isLoading && (
          <div className="space-y-4">
            <div className="h-12 w-full bg-muted/10 rounded-lg animate-pulse" />
            <TemplateListSkeleton count={4} />
          </div>
        )}

        {error && (
          <div className="p-6 border border-destructive/20 rounded-xl bg-destructive/5 text-destructive flex flex-col items-center justify-center text-center space-y-2">
            <AlertCircle className="h-8 w-8 mb-2" />
            <p className="font-semibold">Error loading templates</p>
            <p className="text-sm opacity-90 max-w-md">
              {error instanceof Error ? error.message : "An unexpected error occurred while fetching templates."}
            </p>
          </div>
        )}

        {!isLoading && !error && templates && templates.length === 0 && (
          <div className="mt-12">
            <EmptyState
              icon={<FileCode className="h-12 w-12 text-muted-foreground/50" />}
              title="No templates yet"
              description="Create your first API template to get started with semantic generation."
              action={{
                label: "Create First Template",
                onClick: () => router.push("/templates/new"),
              }}
            />
          </div>
        )}

        {!isLoading && !error && filteredTemplates.length === 0 && templates && templates.length > 0 && (
          <div className="mt-12">
            <EmptyState
              icon={<Search className="h-12 w-12 text-muted-foreground/50" />}
              title="No matches found"
              description="Adjust your search or filters to find what you're looking for."
              action={{
                label: "Clear Filters",
                onClick: () => {
                  setSearchQuery("")
                  setFilters({ status: [], intent: [] })
                }
              }}
            />
          </div>
        )}

        {/* Template List - Modern Grid/Table */}
        {filteredTemplates.length > 0 && (
          <div className="rounded-xl border border-border/40 bg-card overflow-hidden shadow-sm" data-tour="template-list">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-border/40 bg-muted/40">
                    <th className="px-6 py-4 font-medium text-xs text-muted-foreground uppercase tracking-wider w-[30%]">Template Name</th>
                    <th className="px-6 py-4 font-medium text-xs text-muted-foreground uppercase tracking-wider w-[10%]">Method</th>
                    <th className="px-6 py-4 font-medium text-xs text-muted-foreground uppercase tracking-wider w-[15%]">Status</th>
                    <th className="px-6 py-4 font-medium text-xs text-muted-foreground uppercase tracking-wider w-[25%] hidden md:table-cell">Base URL</th>
                    <th className="px-6 py-4 font-medium text-xs text-muted-foreground uppercase tracking-wider w-[10%] hidden lg:table-cell">Updated</th>
                    <th className="px-4 py-4 font-medium text-xs text-muted-foreground uppercase tracking-wider w-[10%] text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {filteredTemplates.map((template) => (
                    <tr
                      key={template.api_name}
                      className="group hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => router.push(`/templates/${template.template_id || template.api_name}/edit`)}
                    >
                      {/* Name Col */}
                      <td className="px-6 py-4 align-top">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-foreground text-base leading-tight">
                              {toTitleCase(template.api_name)}
                            </p>
                            {template.confidence !== undefined && template.confidence > 0 && (
                              <ConfidenceBadge confidence={template.confidence} showLabel={false} className="scale-90 origin-left" />
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed max-w-sm">
                            {template.description || "No description provided."}
                          </p>
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {template.intent_keywords.slice(0, 3).map((keyword) => (
                              <span key={keyword} className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground">
                                {keyword}
                              </span>
                            ))}
                            {template.intent_keywords.length > 3 && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-muted text-muted-foreground">
                                +{template.intent_keywords.length - 3}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Method Col */}
                      <td className="px-6 py-4 align-top">
                        <span className={cn(
                          "inline-flex px-2.5 py-1 rounded-md text-xs font-bold ring-1 ring-inset",
                          getMethodBadgeVariant(template.method)
                        )}>
                          {template.method}
                        </span>
                      </td>

                      {/* Status Col */}
                      <td className="px-6 py-4 align-top" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2 min-w-[90px]">
                            <span
                              className={cn(
                                "flex h-2.5 w-2.5 rounded-full",
                                template.status === "approved" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" : "bg-neutral-400"
                              )}
                            />
                            <span className={cn(
                              "text-sm font-medium",
                              template.status === "approved" ? "text-foreground" : "text-muted-foreground"
                            )}>
                              {template.status === "approved" ? "Active" : "Draft"}
                            </span>
                          </div>
                          <Switch
                            checked={template.status === "approved"}
                            onCheckedChange={() => toggleVisibilityMutation.mutate(template.template_id || template.api_name)}
                            disabled={togglingTemplateId === (template.template_id || template.api_name)}
                            className="scale-75 data-[state=checked]:bg-green-600"
                          />
                        </div>
                      </td>

                      {/* Base URL Col */}
                      <td className="px-6 py-4 align-top hidden md:table-cell">
                        <code className="text-xs font-mono text-muted-foreground bg-muted/50 px-2 py-1.5 rounded-md break-all block">
                          {template.base_url || template.endpoint || "No URL defined"}
                        </code>
                      </td>

                      {/* Updated Col */}
                      <td className="px-6 py-4 align-top hidden lg:table-cell">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {template.updated_at ? formatDate(template.updated_at) : "Never"}
                        </div>
                      </td>

                      {/* Actions Col */}
                      <td className="px-4 py-4 align-middle text-right" onClick={(e) => e.stopPropagation()}>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-[160px]">
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
      {/* Onboarding Tour for templates */}
      <OnboardingTour tourId="templates" />
    </div>
  )
}
