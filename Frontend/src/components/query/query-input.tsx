'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Sparkles, Play } from 'lucide-react'

interface QueryInputProps {
  onSubmit?: (query: string) => void
}

export function QueryInput({ onSubmit }: QueryInputProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && onSubmit) {
      onSubmit(query.trim())
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <CardTitle>Natural Language Query</CardTitle>
            <CardDescription>Describe your test in plain English</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Authenticate my credentials for Milan and MS3ESD"
            className="h-12"
          />
          <Button type="submit" className="w-full" disabled={!query.trim()}>
            <Play className="h-4 w-4 mr-2" />
            Generate Test
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
