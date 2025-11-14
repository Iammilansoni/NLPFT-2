'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, Loader2, Database, Server } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'

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

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const checkHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health', {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      })

      if (response.ok) {
        const data = await response.json()
        setHealth({
          backend: data.status === 'healthy' ? 'healthy' : 'unhealthy',
          database: data.database === 'connected' ? 'healthy' : 'unhealthy',
          redis: data.redis === 'connected' ? 'healthy' : 'unhealthy',
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
    }
  }

  const allHealthy = health.backend === 'healthy' && health.database === 'healthy' && health.redis === 'healthy'
  const anyChecking = health.backend === 'checking' || health.database === 'checking' || health.redis === 'checking'

  return (
    <div className="relative w-full">
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={cn(
          'w-full flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all text-left',
          allHealthy
            ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/20'
            : anyChecking
            ? 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/20'
            : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20'
        )}
      >
        {anyChecking ? (
          <Loader2 className="h-4 w-4 text-blue-500 animate-spin flex-shrink-0" />
        ) : allHealthy ? (
          <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
        ) : (
          <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
        )}
        <span className="text-xs font-medium truncate">
          {anyChecking ? 'Checking...' : allHealthy ? 'Systems OK' : 'Issues Detected'}
        </span>
      </motion.button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute right-0 top-full mt-2 w-64 rounded-lg border-2 bg-card shadow-lg z-50"
          >
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between text-sm font-medium border-b pb-2">
                <span>System Health</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    checkHealth()
                  }}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Refresh
                </button>
              </div>

              <HealthItem
                label="Backend API"
                status={health.backend}
                icon={<Server className="h-4 w-4" />}
              />
              <HealthItem
                label="PostgreSQL"
                status={health.database}
                icon={<Database className="h-4 w-4" />}
              />
              <HealthItem
                label="Redis Cache"
                status={health.redis}
                icon={<Database className="h-4 w-4" />}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function HealthItem({
  label,
  status,
  icon,
}: {
  label: string
  status: 'healthy' | 'unhealthy' | 'checking'
  icon: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div
          className={cn(
            'h-8 w-8 rounded-lg flex items-center justify-center',
            status === 'healthy'
              ? 'bg-emerald-100 dark:bg-emerald-950/30 text-emerald-600'
              : status === 'checking'
              ? 'bg-blue-100 dark:bg-blue-950/30 text-blue-600'
              : 'bg-red-100 dark:bg-red-950/30 text-red-600'
          )}
        >
          {icon}
        </div>
        <span className="text-sm font-medium">{label}</span>
      </div>
      <Badge
        variant={status === 'healthy' ? 'default' : status === 'checking' ? 'secondary' : 'destructive'}
        className="text-xs"
      >
        {status === 'healthy' ? (
          <CheckCircle className="h-3 w-3 mr-1" />
        ) : status === 'checking' ? (
          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
        ) : (
          <XCircle className="h-3 w-3 mr-1" />
        )}
        {status === 'healthy' ? 'Online' : status === 'checking' ? 'Checking' : 'Offline'}
      </Badge>
    </div>
  )
}
