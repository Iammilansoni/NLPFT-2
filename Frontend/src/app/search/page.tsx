"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Search as SearchIcon,
  Filter,
  Download,
  X,
  ExternalLink,
  Play,
  Copy,
  ChevronRight,
  FileText,
  FileJson,
  Check,
  AlertCircle,
} from "lucide-react"
import { apiClient } from "@/lib/api"
import type { SearchRequest, SearchResultItem, SearchFilters } from "@/lib/api-types"
import { cn } from "@/lib/utils"
import { SearchInput } from "@/components/ui/search-input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ConfidenceBadge } from "@/components/ui/confidence-badge"
import { SimilarityBar } from "@/components/ui/similarity-bar"
import { EmptyState } from "@/components/ui/empty-state"
import { JSONViewer } from "@/components/ui/json-viewer"
import { Skeleton } from "@/components/ui/skeleton"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Label } from "@/components/ui/label"
import { toast } from "@/hooks/use-toast"

const SAMPLE_QUERIES = [
  "Login with username and password",
  "Create a new user account",
  "Update user profile information",
  "Delete user account",
  "Get user profile data",
  "Reset user password",
]

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [debouncedQuery, setDebouncedQuery] = React.useState("")
  const [filters, setFilters] = React.useState<SearchFilters>({
    intent: [],
    min_similarity: 0,
  })
  const [showFilters, setShowFilters] = React.useState(false)
  const [selectedResult, setSelectedResult] = React.useState<SearchResultItem | null>(null)

  // Debounce search query
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Fetch search results
  const { data, isLoading, error } = useQuery({
    queryKey: ["search", debouncedQuery, filters],
    queryFn: async () => {
      if (!debouncedQuery) return null
      
      const request: SearchRequest = {
        query: debouncedQuery,
        top_k: 20,
        ...filters,
      }
      return apiClient.search(request)
    },
    enabled: !!debouncedQuery,
  })

  const handleExport = (format: "csv" | "json") => {
    if (!data?.results) return
    
    let content: string
    let filename: string
    let mimeType: string

    if (format === "csv") {
      const headers = ["Query", "API", "Endpoint", "Similarity", "Distance", "Intent", "Confidence"]
      const rows = data.results.map(r => [
        `"${r.query.replace(/"/g, '""')}"`,
        r.api,
        r.endpoint,
        r.cosine_similarity.toFixed(4),
        r.cosine_distance.toFixed(4),
        r.intent || "",
        r.confidence?.toFixed(4) || "",
      ])
      content = [headers, ...rows].map(row => row.join(",")).join("\n")
      filename = `search-results-${Date.now()}.csv`
      mimeType = "text/csv"
    } else {
      content = JSON.stringify(data.results, null, 2)
      filename = `search-results-${Date.now()}.json`
      mimeType = "application/json"
    }

    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)

    toast({
      title: "Export successful",
      description: `Downloaded ${data.results.length} results as ${format.toUpperCase()}`,
    })
  }

  const [copiedId, setCopiedId] = React.useState<string | null>(null)

  const handleCopyRequest = (result: SearchResultItem) => {
    navigator.clipboard.writeText(JSON.stringify(result.request, null, 2))
    setCopiedId(result.hash_id || "")
    setTimeout(() => setCopiedId(null), 2000)
    toast({
      title: "Request copied",
      description: "The request JSON has been copied to your clipboard",
    })
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
          <div className="flex items-center gap-3 mb-6">
            <SearchIcon className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold">Semantic Search</h1>
              <p className="text-sm text-muted-foreground">
                Query embeddings with similarity and intent filters
              </p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex gap-3">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search for API test cases..."
              suggestions={SAMPLE_QUERIES}
              onSuggestionClick={setSearchQuery}
              className="flex-1"
              autoFocus
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
                      onClick={() => setFilters({ intent: [], min_similarity: 0 })}
                    >
                      Clear all
                    </Button>
                  </div>

                  <div className="space-y-6">
                    {/* Intent Multi-Select */}
                    <div className="space-y-3">
                      <Label className="text-sm font-medium">Filter by Intent</Label>
                      <div className="flex flex-wrap gap-2">
                        {['login', 'signup', 'update', 'delete', 'get', 'reset', 'create'].map((intent) => (
                          <Button
                            key={intent}
                            variant={filters.intent?.includes(intent) ? "default" : "outline"}
                            size="sm"
                            onClick={() => {
                              const currentIntents = filters.intent || []
                              const newIntents = currentIntents.includes(intent)
                                ? currentIntents.filter(i => i !== intent)
                                : [...currentIntents, intent]
                              setFilters({ ...filters, intent: newIntents })
                            }}
                            className="capitalize"
                          >
                            {intent}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <Separator />

                    {/* Min Similarity Slider */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium">Minimum Similarity</Label>
                        <span className="text-sm font-mono text-muted-foreground">
                          {Math.round((filters.min_similarity || 0) * 100)}%
                        </span>
                      </div>
                      <Slider
                        value={[(filters.min_similarity || 0) * 100]}
                        onValueChange={([value]) => setFilters({ ...filters, min_similarity: value / 100 })}
                        min={0}
                        max={100}
                        step={5}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                      </div>
                    </div>

                    <Separator />

                    {/* Export Actions */}
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExport("csv")}
                        disabled={!data?.results?.length}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        Export CSV
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExport("json")}
                        disabled={!data?.results?.length}
                      >
                        <FileJson className="h-4 w-4 mr-2" />
                        Export JSON
                      </Button>
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Results List */}
          <div className="lg:col-span-2 space-y-4">
            {isLoading && (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="border rounded-lg p-6">
                    <Skeleton className="h-6 w-3/4 mb-3" />
                    <Skeleton className="h-4 w-1/2 mb-4" />
                    <Skeleton className="h-2 w-full" />
                  </div>
                ))}
              </div>
            )}

            {error && (
              <div className="p-4 border border-destructive rounded-lg bg-destructive/10 text-destructive">
                <p className="font-medium">Error loading results</p>
                <p className="text-sm mt-1">
                  {error instanceof Error ? error.message : "Unknown error"}
                </p>
              </div>
            )}

            {!isLoading && !error && !debouncedQuery && (
              <EmptyState
                icon={<SearchIcon className="h-16 w-16" />}
                title="Start searching"
                description="Enter a query to find semantically similar API test cases"
              />
            )}

            {!isLoading && !error && debouncedQuery && !data?.results?.length && (
              <EmptyState
                icon={<SearchIcon className="h-16 w-16" />}
                title="No results found"
                description={`No matches found for "${debouncedQuery}". Try adjusting your filters or query.`}
              />
            )}

            {data?.results && data.results.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-3"
              >
                <div className="text-sm text-muted-foreground mb-4">
                  Found {data.results.length} {data.results.length === 1 ? "result" : "results"} for &quot;{debouncedQuery}&quot;
                </div>

                {data.results.map((result, index) => (
                  <motion.div
                    key={`${result.hash_id || index}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.2 }}
                    onClick={() => setSelectedResult(result)}
                    className={cn(
                      "p-4 border rounded-lg cursor-pointer transition-all duration-200",
                      "hover:shadow-md hover:scale-[1.01]",
                      selectedResult?.hash_id === result.hash_id
                        ? "ring-2 ring-primary bg-accent"
                        : "hover:bg-accent/50"
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">{result.api}</Badge>
                          {result.intent && (
                            <Badge variant="secondary">{result.intent}</Badge>
                          )}
                        </div>
                        
                        <p className="text-sm font-medium mb-2 line-clamp-2">
                          {result.query}
                        </p>
                        
                        <p className="text-xs text-muted-foreground mb-3">
                          {result.endpoint}
                        </p>

                        <SimilarityBar
                          similarity={result.cosine_similarity}
                          height="sm"
                          animated={false}
                        />
                      </div>

                      <div className="flex flex-col items-end gap-2">
                        {result.confidence !== undefined && (
                          <ConfidenceBadge
                            confidence={result.confidence}
                            showLabel={false}
                            animated={false}
                          />
                        )}
                        <ChevronRight className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </div>

          {/* Detail Panel */}
          <div className="lg:col-span-1">
            <AnimatePresence mode="wait">
              {selectedResult ? (
                <motion.div
                  key={selectedResult.hash_id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                  className="sticky top-24 border rounded-lg p-6 bg-card space-y-4"
                >
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-lg">Details</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedResult(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <p className="text-sm font-medium mb-1">Query</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedResult.query}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-1">API</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedResult.api}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-1">Endpoint</p>
                      <p className="text-sm text-muted-foreground break-all">
                        {selectedResult.endpoint}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-2">Similarity</p>
                      <SimilarityBar
                        similarity={selectedResult.cosine_similarity}
                        height="md"
                      />
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-2">Request</p>
                      <JSONViewer
                        data={selectedResult.request}
                        maxHeight="200px"
                        maskSecrets
                      />
                    </div>

                    <div>
                      <p className="text-sm font-medium mb-2">Expected Response</p>
                      <JSONViewer
                        data={selectedResult.response}
                        maxHeight="200px"
                        maskSecrets
                      />
                    </div>

                    <div className="flex gap-2 pt-4 border-t">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={() => handleCopyRequest(selectedResult)}
                      >
                        {copiedId === selectedResult.hash_id ? (
                          <>
                            <Check className="h-4 w-4 mr-2" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4 mr-2" />
                            Copy Request
                          </>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Run Test
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="sticky top-24 border rounded-lg p-6 bg-muted/30 text-center"
                >
                  <ExternalLink className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Select a result to view details
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  )
}
