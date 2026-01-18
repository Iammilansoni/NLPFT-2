'use client'

import * as React from 'react'
import { Filter, X, ChevronDown, ChevronUp, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
export type TemplateStatus = 'draft' | 'approved' | 'deprecated'

export interface SearchFilters {
  methods: HttpMethod[]
  statuses: TemplateStatus[]
  dateRange?: {
    from?: Date
    to?: Date
  }
  tags?: string[]
}

interface AdvancedSearchFiltersProps {
  filters: SearchFilters
  onFiltersChange: (filters: SearchFilters) => void
  availableTags?: string[]
  className?: string
}

const HTTP_METHODS: HttpMethod[] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
const TEMPLATE_STATUSES: TemplateStatus[] = ['draft', 'approved', 'deprecated']

const METHOD_COLORS: Record<HttpMethod, string> = {
  GET: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800',
  POST: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
  PUT: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800',
  DELETE: 'bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800',
  PATCH: 'bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-200 dark:border-purple-800',
}

const STATUS_COLORS: Record<TemplateStatus, string> = {
  draft: 'bg-muted text-muted-foreground',
  approved: 'bg-green-500/10 text-green-700 dark:text-green-400',
  deprecated: 'bg-orange-500/10 text-orange-700 dark:text-orange-400',
}

export function AdvancedSearchFilters({
  filters,
  onFiltersChange,
  availableTags = [],
  className,
}: AdvancedSearchFiltersProps) {
  const [isExpanded, setIsExpanded] = React.useState(false)

  const activeFilterCount = React.useMemo(() => {
    let count = 0
    if (filters.methods.length > 0) count += filters.methods.length
    if (filters.statuses.length > 0) count += filters.statuses.length
    if (filters.tags && filters.tags.length > 0) count += filters.tags.length
    if (filters.dateRange?.from || filters.dateRange?.to) count += 1
    return count
  }, [filters])

  const toggleMethod = (method: HttpMethod) => {
    const newMethods = filters.methods.includes(method)
      ? filters.methods.filter((m) => m !== method)
      : [...filters.methods, method]
    onFiltersChange({ ...filters, methods: newMethods })
  }

  const toggleStatus = (status: TemplateStatus) => {
    const newStatuses = filters.statuses.includes(status)
      ? filters.statuses.filter((s) => s !== status)
      : [...filters.statuses, status]
    onFiltersChange({ ...filters, statuses: newStatuses })
  }

  const toggleTag = (tag: string) => {
    const currentTags = filters.tags || []
    const newTags = currentTags.includes(tag)
      ? currentTags.filter((t) => t !== tag)
      : [...currentTags, tag]
    onFiltersChange({ ...filters, tags: newTags })
  }

  const clearAll = () => {
    onFiltersChange({
      methods: [],
      statuses: [],
      tags: [],
      dateRange: undefined,
    })
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Toggle Button */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            'h-9 border-dashed gap-2',
            isExpanded && 'bg-muted border-solid',
            activeFilterCount > 0 && 'border-primary/50'
          )}
        >
          <Filter className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1 h-5 min-w-[20px] px-1.5 text-xs">
              {activeFilterCount}
            </Badge>
          )}
          {isExpanded ? (
            <ChevronUp className="h-3 w-3 ml-1" />
          ) : (
            <ChevronDown className="h-3 w-3 ml-1" />
          )}
        </Button>

        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAll}
            className="h-8 px-2 text-muted-foreground hover:text-foreground"
          >
            Clear all
            <X className="h-3 w-3 ml-1" />
          </Button>
        )}
      </div>

      {/* Filter Panel */}
      {isExpanded && (
        <div className="p-4 rounded-lg border border-border/60 bg-card/50 space-y-4 animate-in slide-in-from-top-2 duration-200">
          {/* HTTP Methods */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              HTTP Method
            </label>
            <div className="flex flex-wrap gap-2">
              {HTTP_METHODS.map((method) => {
                const isActive = filters.methods.includes(method)
                return (
                  <button
                    key={method}
                    onClick={() => toggleMethod(method)}
                    className={cn(
                      'px-3 py-1.5 rounded-md text-xs font-bold border transition-all',
                      isActive
                        ? METHOD_COLORS[method]
                        : 'bg-muted/50 text-muted-foreground border-transparent hover:bg-muted'
                    )}
                  >
                    {method}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Status
            </label>
            <div className="flex flex-wrap gap-2">
              {TEMPLATE_STATUSES.map((status) => {
                const isActive = filters.statuses.includes(status)
                return (
                  <button
                    key={status}
                    onClick={() => toggleStatus(status)}
                    className={cn(
                      'px-3 py-1.5 rounded-full text-xs font-medium border transition-all capitalize',
                      isActive
                        ? cn(STATUS_COLORS[status], 'border-current')
                        : 'bg-muted/50 text-muted-foreground border-transparent hover:bg-muted'
                    )}
                  >
                    {status}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Tags (if available) */}
          {availableTags.length > 0 && (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Tags
              </label>
              <div className="flex flex-wrap gap-2">
                {availableTags.map((tag) => {
                  const isActive = filters.tags?.includes(tag)
                  return (
                    <button
                      key={tag}
                      onClick={() => toggleTag(tag)}
                      className={cn(
                        'px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
                        isActive
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'bg-muted/50 text-muted-foreground border-transparent hover:bg-muted'
                      )}
                    >
                      {tag}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className="pt-3 border-t border-border/40">
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{activeFilterCount}</span> filter{activeFilterCount !== 1 ? 's' : ''} active
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AdvancedSearchFilters
