'use client'

import { useState } from 'react'
import {
  X, Play, Pause, Trash2, Terminal, Server,
  ChevronDown, ChevronRight, Filter,
  CheckCircle2, AlertTriangle, XCircle, Info,
  Bot, Database, FileText, Layers, KeyRound, Settings2, Globe, Eye, EyeOff
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSidebar } from '@/contexts/sidebar-context'
import { useSystemLogs, LogEntry, LogCategory, ActivityType } from '@/hooks/use-system-logs'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'

// Activity type configuration with icons
const ACTIVITY_CONFIG: Record<ActivityType, { icon: typeof Bot; color: string; label: string }> = {
  llm: { icon: Bot, color: 'text-purple-500', label: 'LLM' },
  dataset: { icon: Database, color: 'text-blue-500', label: 'Dataset' },
  template: { icon: FileText, color: 'text-emerald-500', label: 'Template' },
  embedding: { icon: Layers, color: 'text-cyan-500', label: 'Embedding' },
  auth: { icon: KeyRound, color: 'text-amber-500', label: 'Auth' },
  system: { icon: Settings2, color: 'text-gray-500', label: 'System' },
  api: { icon: Globe, color: 'text-indigo-500', label: 'API' },
}

// Command Center Category configuration
const CATEGORY_CONFIG = {
  info: {
    label: 'I',
    fullLabel: 'Info',
    icon: Info,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20',
  },
  warning: {
    label: 'W',
    fullLabel: 'Warning',
    icon: AlertTriangle,
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
  },
  error: {
    label: 'E',
    fullLabel: 'Error',
    icon: XCircle,
    color: 'text-error',
    bgColor: 'bg-error/10',
    borderColor: 'border-error/20',
  },
  success: {
    label: 'S',
    fullLabel: 'Success',
    icon: CheckCircle2,
    color: 'text-success',
    bgColor: 'bg-success/10',
    borderColor: 'border-success/20',
  },
}

// Helper to format timestamp - monospaced precision
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// Helper to format relative time
function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const logTime = new Date(timestamp)
  const diffMs = now.getTime() - logTime.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)

  if (diffSec < 10) return 'now'
  if (diffSec < 60) return `${diffSec}s`
  if (diffMin < 60) return `${diffMin}m`
  if (diffHour < 24) return `${diffHour}h`
  return logTime.toLocaleDateString()
}

// Command Center Log Item
function LogItem({
  log,
  index,
  onToggle
}: {
  log: LogEntry
  index: number
  onToggle: (index: number) => void
}) {
  const category = log.category || 'info'
  const config = CATEGORY_CONFIG[category as keyof typeof CATEGORY_CONFIG] || CATEGORY_CONFIG.info
  const activityConfig = log.activityType ? ACTIVITY_CONFIG[log.activityType] : null
  const ActivityIcon = activityConfig?.icon
  const displayMessage = log.humanMessage || log.message
  const isCritical = log.severity === 'critical'

  return (
    <div
      className={cn(
        "rounded-sm border transition-colors cursor-pointer",
        config.borderColor,
        isCritical && "border-amber-500/50",
        "hover:bg-accent/50"
      )}
      onClick={() => onToggle(index)}
    >
      {/* Compact row */}
      <div className="flex items-start gap-1.5 p-2">
        {/* Activity type icon */}
        {ActivityIcon && (
          <ActivityIcon className={cn("h-3.5 w-3.5 flex-shrink-0 mt-0.5", activityConfig.color)} />
        )}
        
        {/* Severity indicator - single character */}
        <span className={cn(
          "font-mono text-[10px] font-bold w-4 text-center flex-shrink-0 mt-0.5",
          config.color
        )}>
          {config.label}
        </span>

        {/* Timestamp - monospaced */}
        <span className="font-mono text-[10px] text-muted-foreground tabular-nums w-16 flex-shrink-0 mt-0.5">
          {formatTimestamp(log.timestamp)}
        </span>

        {/* Message */}
        <div className="flex-1 min-w-0">
          <p className={cn(
            "text-sm leading-tight truncate",
            isCritical && "text-amber-500 font-medium"
          )}>
            {displayMessage}
          </p>
        </div>

        {/* Expand indicator */}
        <div className="flex-shrink-0 mt-0.5">
          {log.isExpanded ? (
            <ChevronDown className="h-3 w-3 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded details */}
      {log.isExpanded && (
        <div className="px-2 pb-2 pt-1 border-t border-border/50 ml-6 space-y-1.5">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
            <div>
              <span className="text-muted-foreground">Level:</span>{' '}
              <span className={cn(
                "font-mono font-medium",
                log.level === 'ERROR' && "text-error",
                log.level === 'WARNING' && "text-amber-500",
                log.level === 'INFO' && "text-blue-500"
              )}>
                {log.level}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Age:</span>{' '}
              <span className="font-mono">{formatRelativeTime(log.timestamp)}</span>
            </div>
            {log.logger && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Source:</span>{' '}
                <span className="font-mono text-[9px]">
                  {log.logger}:{log.line}
                </span>
              </div>
            )}
          </div>

          {/* Raw message if different */}
          {log.humanMessage && log.message !== log.humanMessage && (
            <div className="mt-1.5">
              <span className="text-[9px] text-muted-foreground">Raw:</span>
              <pre className="mt-0.5 p-1.5 bg-muted/50 rounded-sm text-[9px] font-mono overflow-x-auto whitespace-pre-wrap break-all max-h-20">
                {log.message}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Command Center Activity & Audit Sidebar
 * High-density log display with monospaced timestamps and severity indicators
 */
export function SystemLogsSidebar() {
  const { isSystemLogsOpen, setIsSystemLogsOpen } = useSidebar()
  const {
    filteredLogs,
    logs,
    isConnected,
    isPaused,
    filter,
    setFilter,
    showNoise,
    setShowNoise,
    clearLogs,
    togglePause,
    toggleExpanded
  } = useSystemLogs()
  const [isScrolled, setIsScrolled] = useState(false)

  // Count logs by category (from filtered logs which excludes noise by default)
  const counts = {
    all: filteredLogs.length,
    info: filteredLogs.filter(l => l.category === 'info').length,
    warning: filteredLogs.filter(l => l.category === 'warning').length,
    error: filteredLogs.filter(l => l.category === 'error').length,
    success: filteredLogs.filter(l => l.category === 'success').length,
  }
  // Count hidden noise logs
  const hiddenNoise = logs.filter(l => l.isNoise).length

  return (
    <>
      {/* Mobile Overlay */}
      {isSystemLogsOpen && (
        <div
          onClick={() => setIsSystemLogsOpen(false)}
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Toggle Button (Visible when closed) - Enhanced visibility */}
      {!isSystemLogsOpen && (
        <button
          onClick={() => setIsSystemLogsOpen(true)}
          className={cn(
            "fixed right-0 z-40 flex items-center gap-2 rounded-l-xl",
            "bg-card/95 backdrop-blur-md border border-r-0 border-border/60 shadow-xl",
            "px-3 py-4 md:py-3 hover:bg-accent hover:border-primary/30 transition-all duration-200",
            "active:scale-95",
            // Position: different on mobile vs desktop, with safe area support
            "top-20 md:top-1/3 lg:top-1/2 lg:-translate-y-1/2",
            "mr-safe-right"
          )}
          aria-label="Open Activity Panel"
        >
          <div className="flex flex-col items-center gap-2">
            <Terminal className="h-5 w-5 text-primary" />
            <span className="text-xs font-semibold tracking-wide uppercase hidden md:block">Activity</span>
            {isConnected && (
              <span className="h-2 w-2 rounded-full bg-success animate-cc-pulse" />
            )}
            {counts.error > 0 && (
              <span className="h-6 min-w-6 px-1.5 rounded-lg bg-error text-[10px] text-white flex items-center justify-center font-mono font-bold shadow-sm">
                {counts.error > 99 ? '99+' : counts.error}
              </span>
            )}
          </div>
        </button>
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 right-0 z-50 flex flex-col',
          'bg-card/95 backdrop-blur-md lg:bg-card lg:backdrop-blur-none',
          'border-l border-border transition-all duration-300 ease-out shadow-2xl',
          // Responsive width: full on mobile, 360px on sm, 380px on md, 400px on lg+
          isSystemLogsOpen 
            ? 'w-full sm:w-[360px] md:w-[380px] lg:w-[400px]' 
            : 'w-0 overflow-hidden pointer-events-none',
          // Safe area support for notched devices
          'pt-safe-top pb-safe-bottom pr-safe-right'
        )}
      >
        {/* Header */}
        <div className={cn(
          "flex items-center justify-between px-4 md:px-3 py-3 md:py-2 border-b border-border h-14 md:h-12",
          isScrolled && "bg-card/80 backdrop-blur-sm"
        )}>
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-muted-foreground" />
            <h2 className="font-semibold text-sm">Activity</h2>
            <span className={cn(
              "font-mono text-[10px] px-1.5 py-0.5 rounded-sm",
              isConnected
                ? "bg-success/10 text-success"
                : "bg-error/10 text-error"
            )}>
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-0.5">
            {/* Filter dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Filter className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={() => setFilter('all')}>
                  <span className={filter === 'all' ? 'font-bold' : ''}>All ({counts.all})</span>
                </DropdownMenuItem>
                {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => (
                  <DropdownMenuItem key={key} onClick={() => setFilter(key as LogCategory)}>
                    <span className={cn("mr-2 font-mono text-[10px]", cfg.color)}>{cfg.label}</span>
                    <span className={filter === key ? 'font-bold' : ''}>
                      {cfg.fullLabel} ({counts[key as keyof typeof counts]})
                    </span>
                  </DropdownMenuItem>
                ))}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setShowNoise(!showNoise)}>
                  {showNoise ? (
                    <EyeOff className="h-3 w-3 mr-2 text-muted-foreground" />
                  ) : (
                    <Eye className="h-3 w-3 mr-2 text-muted-foreground" />
                  )}
                  <span className={showNoise ? 'font-medium' : ''}>
                    {showNoise ? 'Hide noise' : `Show noise (${hiddenNoise})`}
                  </span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 md:h-6 md:w-6"
              onClick={togglePause}
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? <Play className="h-4 w-4 md:h-3 md:w-3" /> : <Pause className="h-4 w-4 md:h-3 md:w-3" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 md:h-6 md:w-6"
              onClick={clearLogs}
              title="Clear Logs"
            >
              <Trash2 className="h-4 w-4 md:h-3 md:w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 md:h-6 md:w-6"
              onClick={() => setIsSystemLogsOpen(false)}
            >
              <X className="h-4 w-4 md:h-3 md:w-3" />
            </Button>
          </div>
        </div>

        {/* Filter indicator */}
        {filter !== 'all' && (
          <div className="px-3 py-1.5 bg-muted/30 border-b border-border flex items-center justify-between">
            <span className="text-[10px] text-muted-foreground">
              Filter: <span className="font-medium text-foreground">{CATEGORY_CONFIG[filter]?.fullLabel}</span>
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="h-5 text-[10px] px-1.5"
              onClick={() => setFilter('all')}
            >
              Clear
            </Button>
          </div>
        )}

        {/* Logs Area */}
        <ScrollArea
          className="flex-1 px-2 py-2"
          onScrollCapture={(e) => {
            const target = e.target as HTMLElement
            setIsScrolled(target.scrollTop > 0)
          }}
        >
          <div className="space-y-1">
            {filteredLogs.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <Terminal className="h-6 w-6 mx-auto mb-2 opacity-50" />
                <p className="text-xs font-medium">No activity</p>
                <p className="text-[10px] mt-0.5">Logs will appear here</p>
              </div>
            )}
            {filteredLogs.map((log, i) => (
              <LogItem
                key={`${log.timestamp}-${i}`}
                log={log}
                index={i}
                onToggle={toggleExpanded}
              />
            ))}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="border-t border-border px-3 py-2 bg-muted/20">
          <div className="flex items-center justify-between text-[9px] font-mono text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className={cn(
                "h-1.5 w-1.5 rounded-full",
                isConnected ? "bg-success" : "bg-error"
              )} />
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            <span>{isPaused ? 'PAUSED' : 'LIVE'}</span>
            <span>{filteredLogs.length} logs</span>
          </div>

          {/* Quick stats */}
          {(counts.error > 0 || counts.warning > 0) && (
            <div className="flex items-center justify-center gap-4 mt-1.5 pt-1.5 border-t border-border/50">
              {counts.error > 0 && (
                <span className="flex items-center gap-1 text-[9px] text-error font-mono">
                  <span className="font-bold">E</span>
                  {counts.error}
                </span>
              )}
              {counts.warning > 0 && (
                <span className="flex items-center gap-1 text-[9px] text-amber-500 font-mono">
                  <span className="font-bold">W</span>
                  {counts.warning}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
