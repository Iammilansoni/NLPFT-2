'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertCircle } from 'lucide-react'

interface QueryResultsProps {
  result: any
}

export function QueryResults({ result }: QueryResultsProps) {
  if (!result) {
    return (
      <div className="text-sm text-muted-foreground">
        No results to display
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Query Results</CardTitle>
          <Badge variant={result.success ? 'default' : 'destructive'}>
            {result.success ? (
              <>
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Success
              </>
            ) : (
              <>
                <AlertCircle className="h-3 w-3 mr-1" />
                Failed
              </>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <pre className="text-xs bg-muted p-4 rounded-lg overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      </CardContent>
    </Card>
  )
}
