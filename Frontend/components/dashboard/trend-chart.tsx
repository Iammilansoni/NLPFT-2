'use client'

import { Card } from '@/components/ui/card'
import { TrendingUp } from 'lucide-react'

export function TrendChart() {
  // Placeholder trend chart component
  // In production, this would use recharts or similar
  return (
    <div className="h-full flex flex-col items-center justify-center rounded-lg bg-gradient-to-br from-primary/5 to-accent/5 p-4">
      <TrendingUp className="h-8 w-8 text-primary mb-2" />
      <p className="text-sm font-medium">Trend Chart</p>
      <p className="text-xs text-muted-foreground">Coming soon</p>
    </div>
  )
}
