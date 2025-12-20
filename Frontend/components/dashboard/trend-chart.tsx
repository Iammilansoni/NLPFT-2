'use client'

import { useEffect, useState } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface TelemetryData {
  time: string
  searchLatency: number
  embeddingLatency: number
  rerankerLatency: number
}

// Generate fallback sample data when API fails
function generateSampleData(): TelemetryData[] {
  const now = new Date()
  const data: TelemetryData[] = []

  for (let i = 11; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 5 * 60 * 1000)
    data.push({
      time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      searchLatency: Math.floor(50 + Math.random() * 100),
      embeddingLatency: Math.floor(20 + Math.random() * 50),
      rerankerLatency: Math.floor(30 + Math.random() * 60),
    })
  }

  return data
}

// Professional custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card/95 backdrop-blur-sm border border-border/60 rounded-xl shadow-xl p-4 min-w-[180px]">
        <p className="text-sm font-semibold text-foreground mb-3 pb-2 border-b border-border/40">
          {label}
        </p>
        <div className="space-y-2">
          {payload.map((entry: any, index: number) => {
            const labels: Record<string, string> = {
              searchLatency: 'Vector Search',
              embeddingLatency: 'Embedding',
              rerankerLatency: 'Re-ranker',
            }
            return (
              <div key={index} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm text-muted-foreground">
                    {labels[entry.dataKey] || entry.dataKey}
                  </span>
                </div>
                <span className="text-sm font-semibold font-mono tabular-nums">
                  {entry.value}ms
                </span>
              </div>
            )
          })}
        </div>
      </div>
    )
  }
  return null
}

// Professional custom legend component
const CustomLegend = ({ payload }: any) => {
  const labels: Record<string, string> = {
    searchLatency: 'Vector Search',
    embeddingLatency: 'Embedding',
    rerankerLatency: 'Re-ranker',
  }

  return (
    <div className="flex items-center justify-center gap-6 pt-4">
      {payload?.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2 cursor-default">
          <div
            className="w-3 h-3 rounded-full shadow-sm"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-sm font-medium text-muted-foreground">
            {labels[entry.value] || entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export function TrendChart() {
  const [data, setData] = useState<TelemetryData[]>([])
  const [loading, setLoading] = useState(true)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const fetchTelemetry = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/telemetry/metrics?limit=12`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('nlpforge_access_token')}`,
        },
      })

      if (response.ok) {
        const metrics = await response.json()
        if (metrics && metrics.length > 0) {
          setData(metrics)
        } else {
          setData(generateSampleData())
        }
      } else {
        setData(generateSampleData())
      }
    } catch (error) {
      console.debug('Failed to fetch telemetry, using sample data:', error)
      setData(generateSampleData())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Fetch initial data
    fetchTelemetry()

    // Refresh every 30 seconds
    const interval = setInterval(fetchTelemetry, 30000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted-foreground">Loading telemetry...</span>
        </div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={data}
        margin={{ top: 20, right: 30, left: 0, bottom: 10 }}
      >
        <defs>
          {/* Vector Search - Blue gradient */}
          <linearGradient id="colorSearch" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.4} />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
          </linearGradient>
          {/* Embedding - Emerald gradient */}
          <linearGradient id="colorEmbed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
            <stop offset="50%" stopColor="#10b981" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
          </linearGradient>
          {/* Reranker - Violet gradient */}
          <linearGradient id="colorRerank" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.4} />
            <stop offset="50%" stopColor="#8b5cf6" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.02} />
          </linearGradient>
          {/* Glow filters for hover effects */}
          <filter id="glowBlue" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feFlood floodColor="#3b82f6" floodOpacity="0.3" />
            <feComposite in2="blur" operator="in" />
            <feMerge>
              <feMergeNode />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <CartesianGrid
          strokeDasharray="3 3"
          stroke="currentColor"
          opacity={0.06}
          vertical={false}
        />

        <XAxis
          dataKey="time"
          tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
          tickLine={false}
          axisLine={false}
          dy={10}
          tickMargin={8}
        />

        <YAxis
          tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${value}`}
          dx={-5}
          width={45}
        />

        <Tooltip
          content={<CustomTooltip />}
          cursor={{
            stroke: 'hsl(var(--primary))',
            strokeWidth: 1,
            strokeDasharray: '4 4',
            strokeOpacity: 0.5
          }}
        />

        <Legend content={<CustomLegend />} />

        {/* Vector Search Area - Blue */}
        <Area
          type="monotone"
          dataKey="searchLatency"
          stroke="#3b82f6"
          strokeWidth={2.5}
          fill="url(#colorSearch)"
          dot={false}
          activeDot={{
            r: 6,
            fill: '#3b82f6',
            stroke: '#fff',
            strokeWidth: 2,
            className: 'drop-shadow-md'
          }}
        />

        {/* Embedding Area - Emerald */}
        <Area
          type="monotone"
          dataKey="embeddingLatency"
          stroke="#10b981"
          strokeWidth={2.5}
          fill="url(#colorEmbed)"
          dot={false}
          activeDot={{
            r: 6,
            fill: '#10b981',
            stroke: '#fff',
            strokeWidth: 2,
            className: 'drop-shadow-md'
          }}
        />

        {/* Reranker Area - Violet */}
        <Area
          type="monotone"
          dataKey="rerankerLatency"
          stroke="#8b5cf6"
          strokeWidth={2.5}
          fill="url(#colorRerank)"
          dot={false}
          activeDot={{
            r: 6,
            fill: '#8b5cf6',
            stroke: '#fff',
            strokeWidth: 2,
            className: 'drop-shadow-md'
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

