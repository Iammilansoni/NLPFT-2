'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Activity, 
  Database, 
  Server, 
  Zap,
  RefreshCw,
  ChevronDown,
  Wifi,
  WifiOff
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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
    if (anyChecking) return { label: 'Checking', color: 'blue' }
    if (allHealthy) return { label: 'All Systems Online', color: 'emerald' }
    if (healthyCount > 0) return { label: `${healthyCount}/3 Online`, color: 'amber' }
    return { label: 'Systems Offline', color: 'red' }
  }

  const status = getOverallStatus()

  return (
    <div className="relative w-full">
      {/* Main Button */}
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className={cn(
          'w-full group relative overflow-hidden rounded-xl transition-all duration-300',
          'bg-gradient-to-r p-[1px]',
          status.color === 'emerald' && 'from-emerald-500/50 via-emerald-400/30 to-emerald-500/50',
          status.color === 'blue' && 'from-blue-500/50 via-blue-400/30 to-blue-500/50',
          status.color === 'amber' && 'from-amber-500/50 via-amber-400/30 to-amber-500/50',
          status.color === 'red' && 'from-red-500/50 via-red-400/30 to-red-500/50'
        )}
      >
        <div className="relative flex items-center gap-3 px-3 py-2.5 rounded-[11px] bg-background/95 backdrop-blur-sm">
          {/* Animated Status Indicator */}
          <div className="relative flex-shrink-0">
            <div className={cn(
              'h-2.5 w-2.5 rounded-full',
              status.color === 'emerald' && 'bg-emerald-500',
              status.color === 'blue' && 'bg-blue-500',
              status.color === 'amber' && 'bg-amber-500',
              status.color === 'red' && 'bg-red-500'
            )} />
            {(allHealthy || anyChecking) && (
              <div className={cn(
                'absolute inset-0 rounded-full animate-ping',
                status.color === 'emerald' && 'bg-emerald-500/60',
                status.color === 'blue' && 'bg-blue-500/60'
              )} />
            )}
          </div>

          <span className="text-xs font-medium text-foreground/90 flex-1 text-left truncate">
            {status.label}
          </span>

          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </motion.div>
        </div>
      </motion.button>

      {/* Expanded Panel */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="absolute left-0 right-0 top-full mt-2 z-50"
          >
            <div className="rounded-xl border border-border/50 bg-background/95 backdrop-blur-xl shadow-2xl shadow-black/10 dark:shadow-black/30 overflow-hidden">
              {/* Header */}
              <div className="px-4 py-3 border-b border-border/50 bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold">System Status</span>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => {
                      e.stopPropagation()
                      checkHealth()
                    }}
                    className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors"
                    title="Refresh status"
                  >
                    <RefreshCw className={cn(
                      'h-3.5 w-3.5 text-muted-foreground',
                      isRefreshing && 'animate-spin'
                    )} />
                  </motion.button>
                </div>
              </div>

              {/* Services Grid */}
              <div className="p-3 space-y-2">
                <ServiceItem
                  label="Backend API"
                  description="FastAPI Server"
                  status={health.backend}
                  icon={<Server className="h-4 w-4" />}
                  gradient="from-violet-500 to-purple-600"
                />
                <ServiceItem
                  label="PostgreSQL"
                  description="Primary Database"
                  status={health.database}
                  icon={<Database className="h-4 w-4" />}
                  gradient="from-blue-500 to-cyan-600"
                />
                <ServiceItem
                  label="Redis"
                  description="Vector Store & Cache"
                  status={health.redis}
                  icon={<Zap className="h-4 w-4" />}
                  gradient="from-rose-500 to-orange-600"
                />
              </div>

              {/* Footer */}
              <div className="px-4 py-2.5 border-t border-border/50 bg-muted/20">
                <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                  <span>Auto-refresh: 30s</span>
                  <span className="flex items-center gap-1">
                    {allHealthy ? (
                      <Wifi className="h-3 w-3 text-emerald-500" />
                    ) : (
                      <WifiOff className="h-3 w-3 text-muted-foreground" />
                    )}
                    {allHealthy ? 'Connected' : 'Limited'}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ServiceItem({
  label,
  description,
  status,
  icon,
  gradient,
}: {
  label: string
  description: string
  status: 'healthy' | 'unhealthy' | 'checking'
  icon: React.ReactNode
  gradient: string
}) {
  const isHealthy = status === 'healthy'
  const isChecking = status === 'checking'

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        'relative flex items-center gap-3 p-3 rounded-lg transition-all duration-200',
        'bg-muted/30 hover:bg-muted/50',
        isHealthy && 'ring-1 ring-emerald-500/20',
        !isHealthy && !isChecking && 'ring-1 ring-red-500/20'
      )}
    >
      {/* Icon Container */}
      <div className={cn(
        'relative flex-shrink-0 h-9 w-9 rounded-lg flex items-center justify-center',
        isHealthy ? `bg-gradient-to-br ${gradient} text-white shadow-lg` : 
        isChecking ? 'bg-muted text-muted-foreground' :
        'bg-red-500/10 text-red-500'
      )}>
        {icon}
        {isChecking && (
          <div className="absolute inset-0 flex items-center justify-center bg-muted rounded-lg">
            <div className="h-4 w-4 border-2 border-muted-foreground/30 border-t-muted-foreground rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Text Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{label}</span>
        </div>
        <span className="text-[10px] text-muted-foreground truncate block">
          {description}
        </span>
      </div>

      {/* Status Badge */}
      <div className={cn(
        'flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-medium',
        isHealthy && 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
        isChecking && 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
        !isHealthy && !isChecking && 'bg-red-500/10 text-red-600 dark:text-red-400'
      )}>
        <span className={cn(
          'h-1.5 w-1.5 rounded-full',
          isHealthy && 'bg-emerald-500',
          isChecking && 'bg-blue-500 animate-pulse',
          !isHealthy && !isChecking && 'bg-red-500'
        )} />
        {isHealthy ? 'Online' : isChecking ? 'Checking' : 'Offline'}
      </div>
    </motion.div>
  )
}
