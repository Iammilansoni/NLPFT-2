'use client'

import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Play, Pause, Trash2, Activity, Terminal, Server } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSidebar } from '@/contexts/sidebar-context'
import { useSystemLogs, LogEntry } from '@/hooks/use-system-logs'
import { Badge } from '@/components/ui/badge'

export function SystemLogsSidebar() {
  const { isSystemLogsOpen, setIsSystemLogsOpen } = useSidebar()
  const { logs, isConnected, isPaused, clearLogs, togglePause } = useSystemLogs()
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom (since newest are at top, we scroll to top)
  useEffect(() => {
    if (scrollRef.current && !isPaused) {
      const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = 0; // Scroll to top since newest logs are first
      }
    }
  }, [logs, isPaused])

  return (
    <>
      {/* Toggle Button (Visible when closed) */}
      <AnimatePresence>
        {!isSystemLogsOpen && (
          <motion.button
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            onClick={() => setIsSystemLogsOpen(true)}
            className="fixed right-0 top-24 z-40 flex items-center gap-2 rounded-l-xl bg-background/80 backdrop-blur-md border border-r-0 border-border p-2 pl-3 shadow-lg hover:bg-accent transition-colors"
          >
            <Terminal className="h-5 w-5 text-muted-foreground" />
            <span className="text-xs font-medium vertical-rl writing-mode-vertical">Logs</span>
            {isConnected && (
              <span className="absolute -top-1 -left-1 h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{
          width: isSystemLogsOpen ? 420 : 0,
          opacity: isSystemLogsOpen ? 1 : 0,
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={cn(
          'fixed inset-y-0 right-0 z-50 flex flex-col bg-background/95 backdrop-blur-xl border-l border-border shadow-2xl overflow-hidden',
          !isSystemLogsOpen && 'pointer-events-none'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-primary" />
            <h2 className="font-semibold">System Logs</h2>
            <Badge variant={isConnected ? "default" : "destructive"} className="h-5 text-[10px] px-1.5">
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </Badge>
            <span className="text-xs text-muted-foreground">({logs.length})</span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={togglePause}
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={clearLogs}
              title="Clear Logs"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setIsSystemLogsOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Logs Area */}
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="space-y-2 font-mono text-xs">
            {logs.length === 0 && (
              <div className="text-center text-muted-foreground py-10">
                <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No logs to display...</p>
                <p className="text-[10px] mt-1">Logs will appear as you interact with the system</p>
              </div>
            )}
            {logs.map((log, i) => (
              <div 
                key={`${log.timestamp}-${i}`} 
                className={cn(
                  "flex gap-2 items-start p-2 rounded transition-colors group",
                  log.is_system 
                    ? "bg-muted/30 hover:bg-muted/50 border-l-2 border-primary/30" 
                    : "hover:bg-muted/50"
                )}
              >
                <div className="flex flex-col items-center gap-1 shrink-0">
                  <span className="text-muted-foreground w-14 text-[10px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  {log.is_system && (
                    <Server className="h-3 w-3 text-primary/60" title="System log" />
                  )}
                </div>
                <div className="flex-1 break-all">
                  <span className={cn(
                    "font-bold mr-2 text-[10px]",
                    log.level === 'INFO' && "text-blue-500",
                    log.level === 'WARNING' && "text-yellow-500",
                    log.level === 'ERROR' && "text-red-500",
                    log.level === 'CRITICAL' && "text-purple-500",
                    log.level === 'DEBUG' && "text-gray-500",
                  )}>
                    [{log.level}]
                  </span>
                  <span className="text-foreground/90">{log.message}</span>
                  {log.logger && (
                    <span className="ml-2 text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                      {log.logger}:{log.line}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        
        {/* Footer with connection info */}
        <div className="border-t border-border/50 p-2 text-[10px] text-muted-foreground flex items-center justify-between">
          <span>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          <span>
            {isPaused ? '⏸️ Paused' : '▶️ Live'}
          </span>
        </div>
      </motion.div>
    </>
  )
}
