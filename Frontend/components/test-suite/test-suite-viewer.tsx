'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, FileCode } from 'lucide-react'

interface TestSuiteViewerProps {
  suite: any
  onExecute?: () => void
  onExecuteTest?: (testId: string) => void
}

export function TestSuiteViewer({ suite, onExecute, onExecuteTest }: TestSuiteViewerProps) {
  if (!suite) {
    return (
      <div className="text-sm text-muted-foreground">
        No test suite available
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white">
              <FileCode className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>Test Suite</CardTitle>
              <CardDescription>
                {suite.tests?.length || 0} tests generated
              </CardDescription>
            </div>
          </div>
          {onExecute && (
            <Button onClick={onExecute} size="sm">
              <Play className="h-4 w-4 mr-2" />
              Run All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {suite.tests?.map((test: any, index: number) => (
            <div
              key={index}
              className="p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{test.method || 'GET'}</Badge>
                    <span className="font-mono text-sm">{test.endpoint || '/api/test'}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {test.description || 'Test case'}
                  </p>
                </div>
                {onExecuteTest && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onExecuteTest(test.id || index.toString())}
                  >
                    <Play className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
