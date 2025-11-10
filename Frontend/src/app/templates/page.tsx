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
} from "lucide-react"
import { apiClient } from "@/lib/api"
import type { TemplateModel, TemplateFilters } from "@/lib/api-types"
import { cn, formatDate, toTitleCase } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ConfidenceBadge } from "@/components/ui/confidence-badge"
import { EmptyState } from "@/components/ui/empty-state"
import { CardGridSkeleton } from "@/components/ui/skeleton"
import { SearchInput } from "@/components/ui/search-input"

export default function TemplatesPage() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = React.useState("")
  const [filters, setFilters] = React.useState<TemplateFilters>({
    status: [],
    intent: [],
  })
  const [showFilters, setShowFilters] = React.useState(false)

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
    mutationFn: (intent: string) => apiClient.deleteTemplate(intent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] })
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

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Active
          </Badge>
        )
      case "draft":
        return (
          <Badge variant="warning" className="gap-1">
            <Clock className="h-3 w-3" />
            Draft
          </Badge>
        )
      case "deprecated":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Deprecated
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Active
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
              <Button>
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

                  <div className="text-sm text-muted-foreground">
                    Filter options coming soon...
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
                    {template.confidence !== undefined && (
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
                  <div className="flex gap-2 pt-4 border-t opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button size="sm" variant="outline" className="flex-1">
                      <Edit className="h-3 w-3 mr-1" />
                      Edit
                    </Button>
                    <Button size="sm" variant="outline">
                      <Copy className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-destructive hover:bg-destructive/10"
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm(`Delete template "${template.api_name}"?`)) {
                          deleteMutation.mutate(template.api_name)
                        }
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
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
