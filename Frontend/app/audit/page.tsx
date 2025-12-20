'use client'

import React, { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Shield,
  Search,
  CheckCircle2,
  XCircle,
  FileText,
  Database,
  Settings,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Activity,
  RefreshCw,
  Clock,
  User,
  Globe,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface AuditLog {
  log_id: string
  user_id: string
  action: string
  resource_type: string
  resource_id?: string
  ip_address?: string
  user_agent?: string
  endpoint?: string
  changes?: Record<string, any>
  metadata?: Record<string, any>
  success: boolean
  error_message?: string
  created_at: string
}

export default function AuditLogsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize] = useState(25)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'failed'>('all')
  const [isLive, setIsLive] = useState(true)

  // Fetch audit logs with auto-refresh when LIVE
  const { data: logsData, isLoading, error, isFetching } = useQuery({
    queryKey: ['auditLogs', page, pageSize, statusFilter],
    queryFn: () => apiClient.getAuditLogs({
      page,
      page_size: pageSize,
      success_only: statusFilter === 'all' ? undefined : statusFilter === 'success',
    }),
    refetchInterval: isLive ? 5000 : false, // Auto-refresh every 5s when LIVE
  })

  // Fetch audit stats
  const { data: statsData } = useQuery({
    queryKey: ['auditStats'],
    queryFn: () => apiClient.getAuditStats(30),
    refetchInterval: isLive ? 10000 : false,
  })

  const getResourceIcon = (resourceType: string) => {
    switch (resourceType) {
      case 'template':
        return <FileText className="h-3.5 w-3.5" />
      case 'dataset':
        return <Database className="h-3.5 w-3.5" />
      case 'settings':
        return <Settings className="h-3.5 w-3.5" />
      case 'user':
        return <User className="h-3.5 w-3.5" />
      default:
        return <Activity className="h-3.5 w-3.5" />
    }
  }

  const formatAction = (action: string) => {
    return action.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Filter logs by search term (client-side)
  const filteredLogs = logsData?.logs?.filter((log: AuditLog) => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      log.action.toLowerCase().includes(search) ||
      log.resource_type.toLowerCase().includes(search) ||
      log.resource_id?.toLowerCase().includes(search) ||
      log.endpoint?.toLowerCase().includes(search)
    )
  })

  const successRate = statsData?.total_actions > 0
    ? Math.round((statsData.successful_actions / statsData.total_actions) * 100)
    : 0

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Shield className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Activity Logs</h1>
              <p className="text-sm text-muted-foreground">
                Track all changes in real-time
              </p>
            </div>
          </div>

          {/* LIVE Badge */}
          <button
            onClick={() => setIsLive(!isLive)}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border transition-all",
              isLive
                ? "border-green-500/50 bg-green-500/10 text-green-600 dark:text-green-400"
                : "border-border bg-muted text-muted-foreground"
            )}
          >
            <span className={cn(
              "w-2 h-2 rounded-full",
              isLive ? "bg-green-500 animate-pulse" : "bg-muted-foreground"
            )} />
            {isLive ? 'LIVE' : 'Paused'}
            {isFetching && isLive && (
              <RefreshCw className="h-3 w-3 animate-spin ml-1" />
            )}
          </button>
        </header>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-card border rounded-lg p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <Activity className="h-4 w-4" />
              Total Actions
            </div>
            <p className="text-2xl font-semibold">{statsData?.total_actions || 0}</p>
          </div>

          <div className="bg-card border rounded-lg p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Successful
            </div>
            <p className="text-2xl font-semibold text-green-600">{statsData?.successful_actions || 0}</p>
          </div>

          <div className="bg-card border rounded-lg p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <XCircle className="h-4 w-4 text-red-500" />
              Failed
            </div>
            <p className="text-2xl font-semibold text-red-600">{statsData?.failed_actions || 0}</p>
          </div>

          <div className="bg-card border rounded-lg p-4">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <Zap className="h-4 w-4 text-amber-500" />
              Success Rate
            </div>
            <p className="text-2xl font-semibold">{successRate}%</p>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="flex gap-2">
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('all')}
              className="min-w-[70px]"
            >
              All
            </Button>
            <Button
              variant={statusFilter === 'success' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('success')}
              className={cn(
                "min-w-[80px]",
                statusFilter === 'success' && "bg-green-600 hover:bg-green-700"
              )}
            >
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
              Success
            </Button>
            <Button
              variant={statusFilter === 'failed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('failed')}
              className={cn(
                "min-w-[70px]",
                statusFilter === 'failed' && "bg-red-600 hover:bg-red-700"
              )}
            >
              <XCircle className="h-3.5 w-3.5 mr-1" />
              Failed
            </Button>
          </div>
        </div>

        {/* Activity Timeline */}
        <div className="bg-card border rounded-lg">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <span className="text-sm font-medium">Recent Activity</span>
            <span className="text-xs text-muted-foreground">
              {logsData?.total || 0} total logs
            </span>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-16 text-muted-foreground">
              <XCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Failed to load activity logs</p>
            </div>
          ) : filteredLogs?.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No activity found</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredLogs?.map((log: AuditLog) => (
                <div
                  key={log.log_id}
                  className="flex items-start gap-3 px-4 py-3 hover:bg-muted/30 transition-colors"
                >
                  {/* Status Icon */}
                  <div className={cn(
                    "mt-0.5 h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0",
                    log.success
                      ? "bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400"
                      : "bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400"
                  )}>
                    {log.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm">{formatAction(log.action)}</span>
                      <Badge variant="secondary" className="text-xs px-1.5 py-0 h-5 gap-1">
                        {getResourceIcon(log.resource_type)}
                        {log.resource_type}
                      </Badge>
                      {log.error_message && (
                        <Badge variant="destructive" className="text-xs px-1.5 py-0 h-5">
                          Error
                        </Badge>
                      )}
                    </div>

                    {/* Details Row */}
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground flex-wrap">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {getTimeAgo(log.created_at)}
                      </span>
                      {log.endpoint && (
                        <span className="flex items-center gap-1 font-mono truncate max-w-[200px]">
                          <Globe className="h-3 w-3" />
                          {log.endpoint}
                        </span>
                      )}
                      {log.ip_address && (
                        <span className="hidden sm:inline">IP: {log.ip_address}</span>
                      )}
                    </div>

                    {/* Error Message */}
                    {log.error_message && (
                      <p className="mt-1 text-xs text-red-600 dark:text-red-400 truncate">
                        {log.error_message}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {logsData && logsData.total > pageSize && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <span className="text-xs text-muted-foreground">
                Page {page} of {Math.ceil(logsData.total / pageSize)}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="h-8 px-2"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(logsData.total / pageSize)}
                  className="h-8 px-2"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
