 'use client'

import { useEffect, useState } from 'react'
import { getApiBase } from '@/lib/runtime-config'
import {
  Activity,
  Database,
  Server,
  Zap,
  RefreshCw,
  ChevronDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface HealthStatus {
  backend: 'healthy' | 'unhealthy' | 'checking'
  database: 'healthy' | 'unhealthy' | 'checking'
  redis: 'healthy' | 'unhealthy' | 'checking'
}

export function HealthIndicator() {
  const [health, setHealth] = useState<HealthStatus>({
    backend: 'checking',
    database: 'checking',
    redis: 'checking',
  })
  const [isExpanded, setIsExpanded] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const checkHealth = async () => {
    setIsRefreshing(true)
    try {
      const RAW_API_BASE = getApiBase();
      const apiUrl = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : '';
      const response = await fetch(`${apiUrl}/api/v1/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      })

      if (response.ok) {
        const data = await response.json()
        setHealth({
          backend: data.status === 'healthy' ? 'healthy' : 'unhealthy',
          database: data.checks?.database?.status === 'healthy' ? 'healthy' : 'unhealthy',
          redis: data.checks?.redis?.status === 'healthy' ? 'healthy' : 'unhealthy',
        })
      } else {
        setHealth({
          backend: 'unhealthy',
          database: 'unhealthy',
          redis: 'unhealthy',
        })
      }
    } catch (error) {
      setHealth({
        backend: 'unhealthy',
        database: 'unhealthy',
        redis: 'unhealthy',
      })
    } finally {
      setIsRefreshing(false)
    }
  }

  const healthyCount = [health.backend, health.database, health.redis].filter(s => s === 'healthy').length
  const anyChecking = health.backend === 'checking' || health.database === 'checking' || health.redis === 'checking'
  const allHealthy = healthyCount === 3

  const getOverallStatus = () => {
    if (anyChecking) return { label: 'Checking...', color: 'blue' }
    if (allHealthy) return { label: 'All Online', color: 'emerald' }
    if (healthyCount > 0) return { label: `${healthyCount}/3 Online`, color: 'amber' }
    return { label: 'Offline', color: 'red' }
  }

  const status = getOverallStatus()

  return (
    <div className="relative w-full">
      {/* Main Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors',
          'hover:bg-muted/50',
          status.color === 'emerald' && 'border-emerald-200 dark:border-emerald-800',
          status.color === 'blue' && 'border-blue-200 dark:border-blue-800',
          status.color === 'amber' && 'border-amber-200 dark:border-amber-800',
          status.color === 'red' && 'border-red-200 dark:border-red-800'
        )}
      >
        {/* Status Dot */}
        <span className={cn(
          'h-2 w-2 rounded-full flex-shrink-0',
          status.color === 'emerald' && 'bg-emerald-500',
          status.color === 'blue' && 'bg-blue-500',
          status.color === 'amber' && 'bg-amber-500',
          status.color === 'red' && 'bg-red-500'
        )} />

        <span className="text-xs font-medium text-foreground flex-1 text-left">
          {status.label}
        </span>

        <ChevronDown className={cn(
          'h-3.5 w-3.5 text-muted-foreground transition-transform',
          isExpanded && 'rotate-180'
        )} />
      </button>

      {/* Expanded Panel */}
      {isExpanded && (
        <div className="absolute left-0 right-0 top-full mt-2 z-50 rounded-lg border bg-background shadow-lg">
          {/* Header */}
          <div className="px-3 py-2 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">System Status</span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                checkHealth()
              }}
              className="p-1 rounded hover:bg-muted transition-colors"
              title="Refresh status"
            >
              <RefreshCw className={cn(
                'h-3.5 w-3.5 text-muted-foreground',
                isRefreshing && 'animate-spin'
              )} />
            </button>
          </div>

          {/* Services */}
          <div className="p-2 space-y-1">
            <ServiceItem
              label="Backend API"
              status={health.backend}
              icon={<Server className="h-4 w-4" />}
            />
            <ServiceItem
              label="PostgreSQL"
              status={health.database}
              icon={<Database className="h-4 w-4" />}
            />
            <ServiceItem
              label="Redis"
              status={health.redis}
              icon={<Zap className="h-4 w-4" />}
            />
          </div>

          {/* Footer */}
          <div className="px-3 py-2 border-t text-[10px] text-muted-foreground">
            Auto-refresh: 30s
          </div>
        </div>
      )}
    </div>
  )
}

function ServiceItem({
  label,
  status,
  icon,
}: {
  label: string
  status: 'healthy' | 'unhealthy' | 'checking'
  icon: React.ReactNode
}) {
  const isHealthy = status === 'healthy'
  const isChecking = status === 'checking'

  return (
    <div className="flex items-center gap-3 p-2 rounded-md hover:bg-muted/50 transition-colors">
      {/* Icon */}
      <div className={cn(
        'h-7 w-7 rounded-md flex items-center justify-center',
        isHealthy && 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
        isChecking && 'bg-muted text-muted-foreground',
        !isHealthy && !isChecking && 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'
      )}>
        {isChecking ? (
          <div className="h-3.5 w-3.5 border-2 border-muted-foreground/30 border-t-muted-foreground rounded-full animate-spin" />
        ) : (
          icon
        )}
      </div>

      {/* Label */}
      <span className="text-sm flex-1">{label}</span>

      {/* Status Badge */}
      <span className={cn(
        'text-xs font-medium px-1.5 py-0.5 rounded',
        isHealthy && 'text-emerald-600 dark:text-emerald-400',
        isChecking && 'text-blue-600 dark:text-blue-400',
        !isHealthy && !isChecking && 'text-red-600 dark:text-red-400'
      )}>
        {isHealthy ? 'Online' : isChecking ? 'Checking' : 'Offline'}
      </span>
    </div>
  )
}
