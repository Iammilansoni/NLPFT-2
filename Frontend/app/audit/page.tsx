'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import {
  Shield,
  Filter,
  Search,
  Calendar,
  CheckCircle,
  XCircle,
  FileText,
  Database,
  Settings,
  User,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Activity,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [actionFilter, setActionFilter] = useState('')
  const [resourceTypeFilter, setResourceTypeFilter] = useState('')
  const [successFilter, setSuccessFilter] = useState<boolean | undefined>(undefined)
  const [searchTerm, setSearchTerm] = useState('')

  // Fetch audit logs
  const { data: logsData, isLoading, error } = useQuery({
    queryKey: ['auditLogs', page, pageSize, actionFilter, resourceTypeFilter, successFilter],
    queryFn: () => apiClient.getAuditLogs({
      page,
      page_size: pageSize,
      action: actionFilter || undefined,
      resource_type: resourceTypeFilter || undefined,
      success_only: successFilter,
    }),
  })

  // Fetch audit stats
  const { data: statsData } = useQuery({
    queryKey: ['auditStats'],
    queryFn: () => apiClient.getAuditStats(30),
  })

  const handleClearFilters = () => {
    setActionFilter('')
    setResourceTypeFilter('')
    setSuccessFilter(undefined)
    setSearchTerm('')
    setPage(1)
  }

  const getResourceIcon = (resourceType: string) => {
    switch (resourceType) {
      case 'template':
        return <FileText className="h-4 w-4" />
      case 'dataset':
        return <Database className="h-4 w-4" />
      case 'settings':
        return <Settings className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const formatAction = (action: string) => {
    return action.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
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

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white shadow-lg">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-4xl font-bold font-heading">Audit Logs</h1>
            <p className="text-muted-foreground">
              Track all activities and changes in your account
            </p>
          </div>
        </div>
      </motion.div>

      {/* Stats Cards */}
      {statsData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
        >
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Actions</p>
                  <p className="text-2xl font-bold">{statsData.total_actions}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Successful</p>
                  <p className="text-2xl font-bold text-green-600">{statsData.successful_actions}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Failed</p>
                  <p className="text-2xl font-bold text-red-600">{statsData.failed_actions}</p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                  <p className="text-2xl font-bold">
                    {statsData.total_actions > 0
                      ? Math.round((statsData.successful_actions / statsData.total_actions) * 100)
                      : 0}%
                  </p>
                </div>
                <Shield className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                <CardTitle>Filters</CardTitle>
              </div>
              <Button variant="outline" size="sm" onClick={handleClearFilters}>
                Clear All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label htmlFor="search">Search</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="search"
                    placeholder="Search logs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="action">Action</Label>
                <select
                  id="action"
                  value={actionFilter}
                  onChange={(e) => setActionFilter(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">All Actions</option>
                  <option value="create_template">Create Template</option>
                  <option value="update_template">Update Template</option>
                  <option value="delete_template">Delete Template</option>
                  <option value="approve_template">Approve Template</option>
                  <option value="reject_template">Reject Template</option>
                  <option value="generate_dataset">Generate Dataset</option>
                  <option value="update_settings">Update Settings</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="resource-type">Resource Type</Label>
                <select
                  id="resource-type"
                  value={resourceTypeFilter}
                  onChange={(e) => setResourceTypeFilter(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">All Resources</option>
                  <option value="template">Template</option>
                  <option value="dataset">Dataset</option>
                  <option value="settings">Settings</option>
                  <option value="user">User</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  value={successFilter === undefined ? '' : successFilter ? 'success' : 'failure'}
                  onChange={(e) => 
                    setSuccessFilter(e.target.value === '' ? undefined : e.target.value === 'success')
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">All Status</option>
                  <option value="success">Success</option>
                  <option value="failure">Failure</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Logs Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Activity Log</CardTitle>
            <CardDescription>
              {logsData ? `Showing ${filteredLogs?.length || 0} of ${logsData.total} logs` : 'Loading...'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <div className="text-center py-12 text-muted-foreground">
                Failed to load audit logs
              </div>
            ) : filteredLogs?.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No audit logs found
              </div>
            ) : (
              <div className="space-y-2">
                {filteredLogs?.map((log: AuditLog) => (
                  <div
                    key={log.log_id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className={cn(
                        "h-10 w-10 rounded-lg flex items-center justify-center",
                        log.success 
                          ? "bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400" 
                          : "bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400"
                      )}>
                        {log.success ? <CheckCircle className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium">{formatAction(log.action)}</p>
                          <Badge variant="outline" className="flex items-center gap-1">
                            {getResourceIcon(log.resource_type)}
                            {log.resource_type}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(log.created_at)}
                          </span>
                          {log.ip_address && (
                            <span>IP: {log.ip_address}</span>
                          )}
                          {log.endpoint && (
                            <span className="truncate max-w-[200px]">{log.endpoint}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {log.error_message && (
                      <Badge variant="destructive" className="ml-2">
                        Error
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {logsData && logsData.total > pageSize && (
              <div className="flex items-center justify-between mt-6 pt-6 border-t">
                <p className="text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(logsData.total / pageSize)}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page >= Math.ceil(logsData.total / pageSize)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
