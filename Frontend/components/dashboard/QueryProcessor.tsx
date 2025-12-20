'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useProcessQuery } from '@/hooks/useQuery'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Loader2, Send, CheckCircle2, AlertCircle, Cpu } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { QueryResponse } from '@/lib/api/types'

export function QueryProcessor() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<QueryResponse | null>(null)
  const { mutate: processQuery, isPending, isError, error } = useProcessQuery()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) return

    processQuery(
      {
        query: query.trim(),
        generate_dataset: true,
        num_examples: 50,
        top_k: 5,
      },
      {
        onSuccess: (data) => {
          setResult(data)
        },
      }
    )
  }

  const handleClear = () => {
    setQuery('')
    setResult(null)
  }

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-primary" />
            Natural Language Query
          </CardTitle>
          <CardDescription>
            Describe your API test in plain English. We'll extract the intent, generate test cases, and run semantic matching.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="query">Your Query</Label>
              <Textarea
                id="query"
                placeholder="e.g., Test login with email: user@example.com and password: P@ssw0rd"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="resize-none"
                disabled={isPending}
              />
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={isPending || !query.trim()} className="flex-1">
                {isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Process Query
                  </>
                )}
              </Button>
              {result && (
                <Button type="button" variant="outline" onClick={handleClear}>
                  Clear
                </Button>
              )}
            </div>

            {isError && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                <p>{error?.message || 'An error occurred while processing your query'}</p>
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Results Section */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Intent Detection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  Detected Intent
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-muted-foreground">API Intent</div>
                    <div className="text-2xl font-bold text-primary">{result.intent}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">Confidence</div>
                    <div className="text-2xl font-bold text-emerald-500">
                      {Math.round(result.confidence * 100)}%
                    </div>
                  </div>
                </div>

                {Object.keys(result.slots).length > 0 && (
                  <div>
                    <div className="text-sm font-semibold mb-2">Extracted Parameters</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(result.slots).map(([key, value]) => (
                        <div
                          key={key}
                          className="flex items-center justify-between p-2 bg-muted rounded-md"
                        >
                          <span className="text-sm font-medium">{key}:</span>
                          <code className="text-sm text-primary">{String(value)}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {result.dataset_generated && (
                  <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                    ✓ Dataset Generated ({result.dataset_info?.num_examples || 0} examples)
                  </Badge>
                )}
              </CardContent>
            </Card>

            {/* Best Matches */}
            {result.best_matches.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Best API Matches</CardTitle>
                  <CardDescription>
                    Similar API intents found in the knowledge base
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.best_matches.map((match, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={cn(
                          'flex items-center justify-between p-3 rounded-lg border',
                          match.score > 0.9
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : 'bg-muted/50 border-border'
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={cn(
                              'flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm',
                              match.score > 0.9
                                ? 'bg-emerald-500 text-white'
                                : 'bg-primary/10 text-primary'
                            )}
                          >
                            {index + 1}
                          </div>
                          <div>
                            <div className="font-medium">{match.api}</div>
                            <div className="text-sm text-muted-foreground">
                              Similarity: {(match.score * 100).toFixed(1)}%
                            </div>
                          </div>
                        </div>
                        <Badge
                          variant={match.score > 0.9 ? 'default' : 'secondary'}
                          className={cn(
                            match.score > 0.9 &&
                            'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                          )}
                        >
                          {(match.confidence * 100).toFixed(0)}% confidence
                        </Badge>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Search Results */}
            {result.search_results.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Semantic Search Results</CardTitle>
                  <CardDescription>
                    Top matching queries from the vector database
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {result.search_results.map((searchResult, index) => (
                      <div
                        key={index}
                        className="p-3 bg-muted/30 rounded-lg border border-border/50"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="font-medium text-sm">{searchResult.intent}</div>
                          <Badge variant="outline" className="text-xs">
                            {(searchResult.similarity * 100).toFixed(1)}% match
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground italic">
                          "{searchResult.query}"
                        </div>
                        {searchResult.endpoint && (
                          <div className="mt-2 text-xs font-mono text-primary">
                            {searchResult.endpoint}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
