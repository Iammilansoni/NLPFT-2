"use client"

import * as React from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  FileCode,
  Plus,
  Edit,
  Trash2,
  Copy,
  RefreshCw,
  Upload,
  Download,
  Search,
  Filter,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  ToggleLeft,
  ToggleRight,
} from "lucide-react"
import { apiClient } from "@/lib/api"
import type { TemplateModel, TemplateFilters } from "@/lib/api-types"
import { cn, formatDate, toTitleCase } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { ConfidenceBadge } from "@/components/ui/confidence-badge"
import { EmptyState } from "@/components/ui/empty-state"
import { CardGridSkeleton } from "@/components/ui/skeleton"
import { SearchInput } from "@/components/ui/search-input"
import { useToast } from "@/hooks/use-toast"

import { useRouter } from "next/navigation"

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

  // Sync from JSON mutation
  const syncMutation = useMutation({
    mutationFn: () => apiClient.syncTemplates(),
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
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["templates"] })
      
      // Snapshot the previous value
      const previousTemplates = queryClient.getQueryData(["templates"])
      
      // Optimistically update - toggle the status immediately
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
      
      // Update cache with actual server response
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
      
      // Rollback to previous state on error
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

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "approved":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Approved
          </Badge>
        )
      case "review":
        return (
          <Badge variant="warning" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            In Review
          </Badge>
        )
      case "draft":
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            Draft
          </Badge>
        )
      case "rejected":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Rejected
          </Badge>
        )
      default:
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            Draft
          </Badge>
        )
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-40"
      >
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <FileCode className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-3xl font-bold">Templates</h1>
                <p className="text-sm text-muted-foreground">
                  Manage API templates without code changes
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending}
              >
                <Upload className="h-4 w-4 mr-2" />
                Sync from JSON
              </Button>
              <Button
                variant="outline"
                onClick={() => reloadMutation.mutate()}
                disabled={reloadMutation.isPending}
              >
                <RefreshCw
                  className={cn(
                    "h-4 w-4 mr-2",
                    reloadMutation.isPending && "animate-spin"
                  )}
                />
                Hot Reload
              </Button>
              <Button onClick={() => router.push("/templates/new")}>
                <Plus className="h-4 w-4 mr-2" />
                New Template
              </Button>
            </div>
          </div>

          {/* Search & Filters */}
          <div className="flex gap-3">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search templates by name, description, or keywords..."
              className="flex-1"
            />
            <Button
              variant="outline"
              size="lg"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(showFilters && "bg-accent")}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
          </div>

          {/* Filters Panel */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-4 p-4 border rounded-lg bg-muted/30 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Filters</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setFilters({ status: [], intent: [] })}
                    >
                      Clear all
                    </Button>
                  </div>

                  {/* Status Filter */}
                  <div>
                    <h4 className="text-sm font-medium mb-2">Status</h4>
                    <div className="flex flex-wrap gap-2">
                      {(["draft", "active", "deprecated"] as const).map((status) => (
                        <Button
                          key={status}
                          variant={filters.status?.includes(status) ? "default" : "outline"}
                          size="sm"
                          onClick={() => {
                            const newStatus = filters.status?.includes(status)
                              ? filters.status.filter((s) => s !== status)
                              : [...(filters.status || []), status]
                            setFilters({ ...filters, status: newStatus })
                          }}
                        >
                          {status === "draft" && <Clock className="h-3 w-3 mr-1" />}
                          {status === "active" && <CheckCircle className="h-3 w-3 mr-1" />}
                          {status === "deprecated" && <XCircle className="h-3 w-3 mr-1" />}
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {isLoading && <CardGridSkeleton count={6} />}

        {error && (
          <div className="p-4 border border-destructive rounded-lg bg-destructive/10 text-destructive">
            <p className="font-medium">Error loading templates</p>
            <p className="text-sm mt-1">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        )}

        {!isLoading && !error && templates && templates.length === 0 && (
          <EmptyState
            icon={<FileCode className="h-16 w-16" />}
            title="No templates yet"
            description="Create your first API template to get started"
            action={{
              label: "Create Template",
              onClick: () => {},
            }}
          />
        )}

        {!isLoading && !error && filteredTemplates.length === 0 && templates && templates.length > 0 && (
          <EmptyState
            icon={<Search className="h-16 w-16" />}
            title="No templates found"
            description="No templates match your search criteria. Try adjusting your filters."
          />
        )}

        {filteredTemplates.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            <div className="text-sm text-muted-foreground mb-4">
              Showing {filteredTemplates.length} of {templates?.length || 0} templates
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map((template, index) => (
                <motion.div
                  key={template.api_name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.2 }}
                  whileHover={{ scale: 1.02, y: -4 }}
                  className="group border rounded-lg p-6 bg-card cursor-pointer transition-shadow hover:shadow-lg"
                  onClick={() => {
                    // Go to edit page
                    router.push(`/templates/${template.template_id || template.api_name}/edit`)
                  }}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-lg mb-1 truncate">
                        {toTitleCase(template.api_name)}
                      </h3>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {template.description}
                      </p>
                    </div>
                    {template.confidence !== undefined && template.confidence !== null && template.confidence > 0 && (
                      <ConfidenceBadge
                        confidence={template.confidence}
                        showLabel={false}
                        animated={false}
                      />
                    )}
                  </div>

                  {/* Info */}
                  <div className="space-y-3 mb-4">
                    <div className="flex items-center gap-2 text-xs">
                      <Badge variant="outline">{template.method}</Badge>
                      {getStatusBadge(template.status)}
                    </div>

                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Endpoint</p>
                      <p className="text-xs font-mono bg-muted px-2 py-1 rounded truncate">
                        {template.endpoint}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Intent Keywords</p>
                      <div className="flex flex-wrap gap-1">
                        {template.intent_keywords.slice(0, 3).map((keyword) => (
                          <Badge key={keyword} variant="secondary" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                        {template.intent_keywords.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{template.intent_keywords.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {template.updated_at && (
                      <p className="text-xs text-muted-foreground">
                        Updated {formatDate(template.updated_at)}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 pt-4 border-t">
                    {/* Continue Editing - For draft or rejected templates */}
                    {(template.status === "draft" || template.status === "rejected") && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        className="w-full border-primary text-primary hover:bg-primary/10"
                        onClick={(e) => {
                          e.stopPropagation()
                          router.push(`/templates/${template.template_id || template.api_name}/edit`)
                        }}
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Continue Editing
                      </Button>
                    )}

                    {/* Draft/Approved Toggle */}
                    <div 
                      className={cn(
                        "flex items-center justify-between p-2 rounded-lg border",
                        template.status === "approved" 
                          ? "bg-green-50 border-green-200" 
                          : "bg-muted/50 border-gray-200"
                      )}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="flex items-center gap-2">
                        {template.status === "approved" ? (
                          <>
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <span className="text-sm font-medium text-green-700">Approved</span>
                          </>
                        ) : (
                          <>
                            <Clock className="h-4 w-4 text-gray-400" />
                            <span className="text-sm font-medium text-gray-500">Draft</span>
                          </>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={template.status === "approved"}
                          onCheckedChange={(checked) => {
                            toggleVisibilityMutation.mutate(template.template_id || template.api_name)
                          }}
                          disabled={togglingTemplateId === (template.template_id || template.api_name)}
                          className="data-[state=checked]:bg-green-600"
                        />
                      </div>
                    </div>

                    {/* Standard Actions - Show on hover */}
                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {/* Only show Edit for non-draft/rejected templates since they have Continue Editing */}
                      {template.status !== "draft" && template.status !== "rejected" && (
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="flex-1"
                          onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/templates/${template.template_id || template.api_name}/edit`)
                          }}
                        >
                          <Edit className="h-3 w-3 mr-1" />
                          Edit
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="outline" 
                        title="Copy template"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-destructive hover:bg-destructive/10"
                        title="Delete template"
                        onClick={(e) => {
                          e.stopPropagation()
                          if (confirm(`Delete template "${template.api_name}"?`)) {
                            deleteMutation.mutate(template.template_id || template.api_name)
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </main>
    </div>
  )
}
