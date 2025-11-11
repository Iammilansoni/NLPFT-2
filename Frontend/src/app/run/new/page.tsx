"use client"

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  FileJson,
  Copy,
  Check,
  Download,
  ChevronDown,
  ChevronUp,
  Code,
  Zap,
  ArrowRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { useProcessQuery } from '@/hooks/useQuery'
import { toast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

export default function NewRunPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialQuery = searchParams?.get('query') || ''

  const [query, setQuery] = useState(initialQuery)
  const [generatedJson, setGeneratedJson] = useState<any>(null)
  const [queryResult, setQueryResult] = useState<any>(null)
  const [copied, setCopied] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [numExamples, setNumExamples] = useState(50)
  const [topK, setTopK] = useState(5)

  const processQueryMutation = useProcessQuery()

  const handleGenerateJson = async () => {
    if (!query.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a query',
        variant: 'destructive',
      })
      return
    }

    try {
      const result = await processQueryMutation.mutateAsync({
        query: query.trim(),
        generate_dataset: true,
        num_examples: numExamples,
        top_k: topK,
      })

      // Store the full query result
      setQueryResult(result)

      // Extract the API structure from search results
      const apiStructure = result.search_results[0]
      
      // Build comprehensive test JSON
      const testJson = {
        test_id: `test_${Date.now()}`,
        intent: result.intent,
        confidence: result.confidence,
        query: result.query,
        api_endpoint: apiStructure?.endpoint || `/api/${result.intent}`,
        api_name: apiStructure?.api_name || result.intent,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${TOKEN}' // Placeholder
        },
        request_body: result.slots,
        expected_response: {
          status: 200,
          body: {
            success: true,
            data: apiStructure || {}
          }
        },
        metadata: {
          generated_at: new Date().toISOString(),
          model: 'NLPForge',
          best_matches: result.best_matches,
          dataset_generated: result.dataset_generated,
        },
        // Future Selenium configuration
        selenium_config: {
          browser: 'chrome',
          headless: false,
          timeout: 30000,
          screenshot_on_failure: true,
        }
      }
      
      setGeneratedJson(testJson)

      toast({
        title: 'JSON Generated!',
        description: `Test structure created with ${Math.round(result.confidence * 100)}% confidence`,
      })
    } catch (error: any) {
      toast({
        title: 'Generation Failed',
        description: error.message || 'Failed to generate JSON',
        variant: 'destructive',
      })
    }
  }

  const handleCopyJson = () => {
    if (generatedJson) {
      navigator.clipboard.writeText(JSON.stringify(generatedJson, null, 2))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast({
        title: 'Copied!',
        description: 'JSON copied to clipboard',
      })
    }
  }

  const handleRunTest = async () => {
    if (!generatedJson) {
      toast({
        title: 'No test to run',
        description: 'Generate JSON first',
        variant: 'destructive',
      })
      return
    }

    toast({
      title: 'Test Execution Started',
      description: 'Selenium API integration coming soon...',
    })

    // TODO: Integrate with Selenium API
    console.log('🚀 Running test with:', generatedJson)
    
    // Future: Call your Selenium test execution API
    // const response = await fetch('/api/selenium/execute', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(generatedJson)
    // })
    
    // Simulate test execution
    setTimeout(() => {
      toast({
        title: 'Test Completed',
        description: 'Check the console for execution details',
      })
    }, 2000)
  }

  const handleDownloadJson = () => {
    if (generatedJson) {
      const blob = new Blob([JSON.stringify(generatedJson, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `test-${generatedJson.intent}-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const exampleQueries = [
    'Login with email user@example.com and password SecureP@ss123',
    'Create a new user account with username john_doe and email john@example.com',
    'Update user profile with name John Smith and phone +1234567890',
    'Delete user with ID 12345',
    'Search for users by email domain @company.com',
    'Reset password for user email test@example.com',
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="p-6 lg:p-8 space-y-8 max-w-[1400px] mx-auto">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-violet-500/25">
                <Sparkles className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-4xl font-bold tracking-tight">Create Test Run</h1>
                <p className="text-muted-foreground mt-1">
                  Convert natural language to executable test JSON
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={() => router.push('/runs')}>
              View All Runs
            </Button>
          </div>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Input Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="space-y-6"
          >
            {/* Query Input Card */}
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white shadow-md">
                    <Code className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle>Natural Language Query</CardTitle>
                    <CardDescription>Describe your test in plain English</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., Login with username admin and password P@ssw0rd"
                    className="h-12 text-base"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleGenerateJson()
                      }
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Press Enter to generate, or click the button below
                  </p>
                </div>

                <Button
                  onClick={handleGenerateJson}
                  disabled={!query.trim() || processQueryMutation.isPending}
                  className="w-full h-12 gap-2"
                  size="lg"
                >
                  {processQueryMutation.isPending ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Generating JSON...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5" />
                      Generate Test JSON
                    </>
                  )}
                </Button>

                {/* Advanced Options */}
                <div className="border-t pt-4">
                  <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showAdvanced ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                    Advanced Options
                  </button>

                  <AnimatePresence>
                    {showAdvanced && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden space-y-4 mt-4"
                      >
                        <div className="space-y-2">
                          <label className="text-sm font-medium">
                            Dataset Examples: {numExamples}
                          </label>
                          <input
                            type="range"
                            min="10"
                            max="200"
                            value={numExamples}
                            onChange={(e) => setNumExamples(Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">
                            Top Matches: {topK}
                          </label>
                          <input
                            type="range"
                            min="1"
                            max="20"
                            value={topK}
                            onChange={(e) => setTopK(Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </CardContent>
            </Card>

            {/* Example Queries */}
            <Card className="border-2">
              <CardHeader>
                <CardTitle className="text-base">Example Queries</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {exampleQueries.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => setQuery(example)}
                    className="w-full text-left p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors text-sm"
                  >
                    {example}
                  </button>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* JSON Output Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-500 flex items-center justify-center text-white shadow-md">
                      <FileJson className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>Generated Test JSON</CardTitle>
                      <CardDescription>
                        API request structure for your test
                      </CardDescription>
                    </div>
                  </div>
                  {generatedJson && (
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCopyJson}
                        className="gap-2"
                      >
                        {copied ? (
                          <>
                            <Check className="h-4 w-4" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" />
                            Copy
                          </>
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleDownloadJson}
                        className="gap-2"
                      >
                        <Download className="h-4 w-4" />
                        Download
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {processQueryMutation.isPending ? (
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                ) : generatedJson ? (
                  <div className="space-y-4">
                    {/* Confidence Badge */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            generatedJson.confidence > 0.9
                              ? 'default'
                              : generatedJson.confidence > 0.7
                              ? 'secondary'
                              : 'outline'
                          }
                          className="gap-1"
                        >
                          <Zap className="h-3 w-3" />
                          {Math.round(generatedJson.confidence * 100)}% Confidence
                        </Badge>
                        <Badge variant="outline">{generatedJson.intent}</Badge>
                        {queryResult?.dataset_generated && (
                          <Badge variant="secondary" className="gap-1">
                            <FileJson className="h-3 w-3" />
                            Dataset Generated
                          </Badge>
                        )}
                      </div>
                      {queryResult?.dataset_download_url && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                            window.open(`${apiBase}${queryResult.dataset_download_url}`, '_blank')
                          }}
                          className="gap-2"
                        >
                          <Download className="h-4 w-4" />
                          Download CSV
                        </Button>
                      )}
                    </div>

                    {/* JSON Display */}
                    <div className="relative">
                      <pre className="p-4 rounded-lg bg-muted text-sm overflow-x-auto max-h-[500px] overflow-y-auto">
                        <code>{JSON.stringify(generatedJson, null, 2)}</code>
                      </pre>
                    </div>

                    {/* Run Test Button */}
                    <Button
                      onClick={handleRunTest}
                      className="w-full h-12 gap-2 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600"
                      size="lg"
                    >
                      <Play className="h-5 w-5" />
                      Run Test Case (Selenium)
                      <ArrowRight className="h-4 w-4 ml-auto" />
                    </Button>

                    {/* Info Card */}
                    <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                            Ready for Selenium Integration
                          </p>
                          <p className="text-blue-800 dark:text-blue-200 text-xs">
                            This JSON structure includes all request details, expected responses, and Selenium configuration. 
                            Click &quot;Run Test Case&quot; to execute (Selenium API integration coming soon).
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <FileJson className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      Enter a query and click Generate to see the JSON structure
                    </p>
                  </div>
                )}

                {processQueryMutation.isError && (
                  <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium text-red-900 dark:text-red-100 mb-1">
                          Generation Failed
                        </p>
                        <p className="text-red-800 dark:text-red-200 text-sm">
                          {(processQueryMutation.error as any)?.message ||
                            'Failed to generate test JSON'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
