'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { getApiBase } from '@/lib/runtime-config'
import { 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Clock,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ActiveTask {
  task_id: string
  status: string
  progress: number
  message: string
  current_step: string
  created_at: string
  completed_at?: string
  error?: string
  result?: {
    total_generated?: number
    csv_path?: string
    embedded_to_redis?: boolean
  }
}

interface ActiveTasksPanelProps {
  onTaskComplete?: () => void
  className?: string
}

export function ActiveTasksPanel({ onTaskComplete, className }: ActiveTasksPanelProps) {
  const [tasks, setTasks] = useState<ActiveTask[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isExpanded, setIsExpanded] = useState(true)
  const [dismissedTaskIds, setDismissedTaskIds] = useState<Set<string>>(new Set())
  
  // Use ref to track previous tasks to avoid stale closure issues
  const prevTasksRef = useRef<ActiveTask[]>([])
  
  const RAW_API_BASE = getApiBase()
  const API_BASE = RAW_API_BASE ? RAW_API_BASE.replace(/\/$/, '') : ''

  const fetchTasks = useCallback(async () => {
    try {
      const token = localStorage.getItem('nlpforge_access_token')
      const response = await fetch(`${API_BASE}/api/v1/datasets/tasks?max_age_hours=2`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        // Log the error details for debugging
        let errorDetails = ''
        try {
          const errorJson = await response.json()
          errorDetails = JSON.stringify(errorJson)
        } catch {
          // If JSON parsing fails, try reading as text
          try {
            errorDetails = await response.text()
          } catch {
            errorDetails = 'Unable to read error response body'
          }
        }
        console.error(
          `Failed to fetch tasks: status=${response.status} ${response.statusText}`,
          errorDetails
        )
        // Clear tasks on auth errors (401/403) to avoid stale state
        if (response.status === 401 || response.status === 403) {
          prevTasksRef.current = []
          setTasks([])
        }
        return
      }
      
      const data = await response.json()
      const newTasks = (data.tasks || []).filter(
        (t: ActiveTask) => !dismissedTaskIds.has(t.task_id)
      )
      
      // Check if any tasks just completed using the ref
      const prevRunningIds = new Set(
        prevTasksRef.current.filter(t => t.status === 'running').map(t => t.task_id)
      )
      const nowCompletedIds = newTasks
        .filter((t: ActiveTask) => t.status === 'completed' && prevRunningIds.has(t.task_id))
        .map((t: ActiveTask) => t.task_id)
      
      if (nowCompletedIds.length > 0 && onTaskComplete) {
        onTaskComplete()
      }
      
      // Update ref before setting state
      prevTasksRef.current = newTasks
      setTasks(newTasks)
    } catch (err) {
      console.error('Error fetching tasks:', err)
    } finally {
      setIsLoading(false)
    }
  }, [API_BASE, dismissedTaskIds, onTaskComplete])

  // Initial fetch
  useEffect(() => {
    fetchTasks()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Poll for updates when there are running tasks
  useEffect(() => {
    const hasRunningTasks = tasks.some(t => t.status === 'running' || t.status === 'pending')
    
    if (hasRunningTasks) {
      const interval = setInterval(fetchTasks, 3000) // Poll every 3 seconds
      return () => clearInterval(interval)
    } else {
      // Slower poll when no running tasks
      const interval = setInterval(fetchTasks, 30000) // Poll every 30 seconds
      return () => clearInterval(interval)
    }
  }, [tasks, fetchTasks])

  // Auto-dismiss completed tasks after 60 seconds
  useEffect(() => {
    const completedTasks = tasks.filter(
      t => (t.status === 'completed' || t.status === 'failed') && t.completed_at
    )
    
    const timers = completedTasks.map(task => {
      const completedAt = new Date(task.completed_at!).getTime()
      const now = Date.now()
      const timeUntilDismiss = Math.max(0, completedAt + 60000 - now) // 60 seconds after completion
      
      return setTimeout(() => {
        setDismissedTaskIds(prev => new Set([...prev, task.task_id]))
      }, timeUntilDismiss)
    })
    
    return () => timers.forEach(t => clearTimeout(t))
  }, [tasks])

  const handleDismiss = (taskId: string) => {
    setDismissedTaskIds(prev => new Set([...prev, taskId]))
  }

  const handleHeaderKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
      if (e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault()
      }
      setIsExpanded(!isExpanded)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      case 'pending':
        return <Clock className="w-4 h-4 text-amber-500" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-emerald-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30'
      case 'pending':
        return 'border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/30'
      case 'completed':
        return 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-950/30'
      case 'failed':
        return 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/30'
      default:
        return 'border-gray-200 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-950/30'
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  // Filter out dismissed and show only active/recent tasks
  const visibleTasks = tasks.filter(t => !dismissedTaskIds.has(t.task_id))
  const runningCount = visibleTasks.filter(t => t.status === 'running' || t.status === 'pending').length

  if (isLoading || visibleTasks.length === 0) {
    return null
  }

  return (
    <Card className={cn("border-border shadow-sm overflow-hidden", className)}>
      {/* Header */}
      <div 
        className="flex items-center justify-between px-4 py-3 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyDown={handleHeaderKeyDown}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3">
          {runningCount > 0 ? (
            <div className="relative">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
            </div>
          ) : (
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          )}
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              {runningCount > 0 
                ? `${runningCount} Generation${runningCount > 1 ? 's' : ''} in Progress`
                : 'Recent Generations'
              }
            </h3>
            <p className="text-xs text-muted-foreground">
              {visibleTasks.length} task{visibleTasks.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              fetchTasks()
            }}
            className="h-8 w-8 p-0"
            aria-label="Refresh tasks"
            title="Refresh tasks"
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-5 h-5 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Task List */}
      {isExpanded && (
        <CardContent className="p-3 space-y-2">
          {visibleTasks.map((task) => (
            <div 
              key={task.task_id}
              className={cn(
                "relative p-3 rounded-lg border transition-all",
                getStatusColor(task.status)
              )}
            >
              {/* Dismiss button */}
              {(task.status === 'completed' || task.status === 'failed') && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDismiss(task.task_id)}
                  className="absolute top-2 right-2 h-6 w-6 p-0 opacity-50 hover:opacity-100"
                  aria-label="Dismiss task"
                  title="Dismiss task"
                >
                  <X className="w-3 h-3" />
                </Button>
              )}

              {/* Task Header */}
              <div className="flex items-center gap-2 mb-2">
                {getStatusIcon(task.status)}
                <span className="text-sm font-medium text-foreground">
                  {task.result?.total_generated 
                    ? `Generated ${task.result.total_generated} rows`
                    : 'Dataset Generation'}
                </span>
                <Badge 
                  variant="outline" 
                  className={cn(
                    "text-[10px] px-1.5 py-0",
                    task.status === 'running' && "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/50 dark:text-blue-300",
                    task.status === 'pending' && "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/50 dark:text-amber-300",
                    task.status === 'completed' && "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-300",
                    task.status === 'failed' && "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/50 dark:text-red-300"
                  )}
                >
                  {task.status}
                </Badge>
                <span className="text-[10px] text-muted-foreground ml-auto">
                  {formatTimeAgo(task.created_at)}
                </span>
              </div>

              {/* Progress Bar (for running/pending) */}
              {(task.status === 'running' || task.status === 'pending') && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground truncate max-w-[80%]">
                      {task.current_step || task.message || 'Processing...'}
                    </span>
                    <span className="font-mono font-medium tabular-nums">
                      {task.progress}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full transition-all duration-500"
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Message for completed/failed */}
              {task.status === 'completed' && task.message && (
                <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                  {task.message}
                </p>
              )}
              {task.status === 'failed' && task.error && (
                <p className="text-xs text-red-700 dark:text-red-300 mt-1 line-clamp-2">
                  {task.error}
                </p>
              )}
            </div>
          ))}
        </CardContent>
      )}
    </Card>
  )
}
