'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ArrowLeft, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api-client'

interface TestRun {
  id: number
  query: string
  intent: string
  status: 'passed' | 'failed' | 'running'
  confidence: number
  tests_count: number
  processing_time_ms: number
  best_match_api: string | null
  best_match_score: number | null
  search_results_count: number
  dataset_generated: boolean
  error_message: string | null
  created_at: string
  updated_at: string
  time_ago: string
}

export default function RunDetailPage() {
  const params = useParams()
  const runId = params.id as string

  const { data: run, isLoading, error } = useQuery<TestRun>({
    queryKey: ['run', runId],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/runs/${runId}`)
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-muted rounded w-1/4"></div>
            <div className="h-64 bg-muted rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !run) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                <h2 className="text-xl font-semibold mb-2">Run Not Found</h2>
                <p className="text-muted-foreground mb-4">
                  The test run you're looking for doesn't exist.
                </p>
                <Button asChild>
                  <Link href="/runs">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Runs
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const statusIcon = {
    passed: <CheckCircle2 className="h-5 w-5 text-green-500" />,
    failed: <XCircle className="h-5 w-5 text-destructive" />,
    running: <Clock className="h-5 w-5 text-blue-500 animate-spin" />,
  }[run.status]

  const statusColor = {
    passed: 'bg-green-500/10 text-green-500 border-green-500/20',
    failed: 'bg-destructive/10 text-destructive border-destructive/20',
    running: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  }[run.status]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <Button variant="ghost" asChild className="mb-4">
            <Link href="/runs">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Runs
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">Test Run #{run.id}</h1>
          <p className="text-muted-foreground mt-1">{run.time_ago}</p>
        </motion.div>

        {/* Status Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {statusIcon}
                Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className={statusColor}>{run.status.toUpperCase()}</Badge>
            </CardContent>
          </Card>
        </motion.div>

        {/* Query Details */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Query Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Query</label>
                <p className="mt-1 text-lg">{run.query}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Intent</label>
                  <p className="mt-1">
                    <Badge variant="outline">{run.intent}</Badge>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Confidence</label>
                  <p className="mt-1">{(run.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Results */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Results</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Processing Time</label>
                  <p className="mt-1">{run.processing_time_ms.toFixed(0)}ms</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Tests Count</label>
                  <p className="mt-1">{run.tests_count}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Search Results</label>
                  <p className="mt-1">{run.search_results_count}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Dataset Generated</label>
                  <p className="mt-1">{run.dataset_generated ? 'Yes' : 'No'}</p>
                </div>
              </div>
              {run.best_match_api && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Best Match</label>
                  <p className="mt-1">
                    <Badge variant="outline">{run.best_match_api}</Badge>
                    {run.best_match_score && (
                      <span className="ml-2 text-sm text-muted-foreground">
                        ({(run.best_match_score * 100).toFixed(1)}% match)
                      </span>
                    )}
                  </p>
                </div>
              )}
              {run.error_message && (
                <div>
                  <label className="text-sm font-medium text-destructive">Error</label>
                  <p className="mt-1 text-sm text-destructive">{run.error_message}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Timestamps */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Timestamps</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Created</label>
                <p className="mt-1 text-sm">{new Date(run.created_at).toLocaleString()}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Updated</label>
                <p className="mt-1 text-sm">{new Date(run.updated_at).toLocaleString()}</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
