"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  X,
  Check,
  Loader2,
  AlertCircle,
  Network,
  FileJson,
  Database,
  Gauge,
  Play,
  BarChart3,
  ChevronDown,
  ChevronUp
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

export interface RunStep {
  id: string
  label: string
  description: string
  status: "pending" | "running" | "completed" | "failed"
  icon: React.ElementType
  progress?: number
  logs?: string[]
  error?: string
}

interface ProgressDrawerProps {
  isOpen: boolean
  onClose: () => void
  onCancel?: () => void
  steps: RunStep[]
  currentStepIndex: number
  runId?: string
  canCancel?: boolean
}

const stepIcons = {
  intent: Network,
  json: FileJson,
  dataset: Database,
  embed: Gauge,
  execute: Play,
  results: BarChart3
}

export function ProgressDrawer({
  isOpen,
  onClose,
  onCancel,
  steps,
  currentStepIndex,
  runId,
  canCancel = true
}: ProgressDrawerProps) {
  const [expandedSteps, setExpandedSteps] = React.useState<string[]>([])
  const [showLogs, setShowLogs] = React.useState(true)
  const scrollRef = React.useRef<HTMLDivElement>(null)

  const currentStep = steps[currentStepIndex]
  const completedSteps = steps.filter(s => s.status === "completed").length
  const overallProgress = (completedSteps / steps.length) * 100

  // Auto-scroll logs to bottom
  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [currentStep?.logs])

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev =>
      prev.includes(stepId) ? prev.filter(id => id !== stepId) : [...prev, stepId]
    )
  }

  const getStatusIcon = (status: RunStep["status"]) => {
    switch (status) {
      case "completed":
        return <Check className="h-5 w-5 text-green-500" />
      case "running":
        return <Loader2 className="h-5 w-5 text-primary animate-spin" />
      case "failed":
        return <AlertCircle className="h-5 w-5 text-destructive" />
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-muted" />
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-background border-l shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b px-6 py-4">
              <div className="flex-1">
                <h2 className="text-2xl font-bold font-heading">Test Run in Progress</h2>
                {runId && (
                  <p className="text-sm text-muted-foreground mt-1">
                    Run ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{runId}</code>
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2">
                {canCancel && currentStep?.status === "running" && (
                  <Button variant="outline" size="sm" onClick={onCancel}>
                    Cancel Run
                  </Button>
                )}
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            {/* Overall Progress */}
            <div className="border-b px-6 py-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">
                  Step {currentStepIndex + 1} of {steps.length}
                </span>
                <span className="text-sm text-muted-foreground">
                  {Math.round(overallProgress)}% complete
                </span>
              </div>
              <Progress value={overallProgress} className="h-2" />
            </div>

            {/* Steps List */}
            <ScrollArea className="flex-1 px-6 py-4">
              <div className="space-y-4">
                {steps.map((step, index) => {
                  const Icon = step.icon
                  const isExpanded = expandedSteps.includes(step.id)
                  const isCurrent = index === currentStepIndex

                  return (
                    <motion.div
                      key={step.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        "rounded-lg border-2 transition-all",
                        isCurrent && step.status === "running" && "border-primary bg-primary/5",
                        step.status === "completed" && "border-green-500/30 bg-green-500/5",
                        step.status === "failed" && "border-destructive/30 bg-destructive/5",
                        step.status === "pending" && "border-border bg-muted/20"
                      )}
                    >
                      <button
                        onClick={() => toggleStep(step.id)}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-accent/50 rounded-lg transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          {/* Status Icon */}
                          <div className="flex-shrink-0">
                            {getStatusIcon(step.status)}
                          </div>

                          {/* Step Icon */}
                          <div className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-lg",
                            step.status === "running" && "bg-primary/10 text-primary",
                            step.status === "completed" && "bg-green-500/10 text-green-500",
                            step.status === "failed" && "bg-destructive/10 text-destructive",
                            step.status === "pending" && "bg-muted text-muted-foreground"
                          )}>
                            <Icon className="h-5 w-5" />
                          </div>

                          {/* Step Info */}
                          <div className="flex-1 text-left">
                            <div className="font-semibold">{step.label}</div>
                            <div className="text-sm text-muted-foreground">{step.description}</div>

                            {/* Step Progress */}
                            {step.status === "running" && step.progress !== undefined && (
                              <div className="mt-2">
                                <Progress value={step.progress} className="h-1" />
                                <span className="text-xs text-muted-foreground mt-1 inline-block">
                                  {step.progress}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Expand Icon */}
                        {(step.logs?.length || step.error) && (
                          <div className="flex-shrink-0">
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            )}
                          </div>
                        )}
                      </button>

                      {/* Expanded Content (Logs/Error) */}
                      <AnimatePresence>
                        {isExpanded && (step.logs?.length || step.error) && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="px-4 pb-3 pt-0">
                              {step.error ? (
                                <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
                                  <div className="flex items-start gap-2">
                                    <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                                    <div className="text-sm text-destructive">{step.error}</div>
                                  </div>
                                </div>
                              ) : step.logs && step.logs.length > 0 && (
                                <div className="bg-muted/50 rounded-md p-3 font-mono text-xs space-y-1 max-h-40 overflow-y-auto">
                                  {step.logs.map((log, logIndex) => (
                                    <div key={logIndex} className="text-muted-foreground">
                                      <span className="text-primary mr-2">→</span>
                                      {log}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )
                })}
              </div>
            </ScrollArea>

            {/* Live Logs Section (Current Step) */}
            {showLogs && currentStep?.logs && currentStep.logs.length > 0 && (
              <div className="border-t px-6 py-4 bg-muted/30">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold">Live Logs</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowLogs(!showLogs)}
                  >
                    {showLogs ? "Hide" : "Show"}
                  </Button>
                </div>
                <div
                  ref={scrollRef}
                  className="bg-background rounded-md p-3 font-mono text-xs max-h-32 overflow-y-auto space-y-1"
                >
                  {currentStep.logs.map((log, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="text-muted-foreground"
                    >
                      <span className="text-primary mr-2">→</span>
                      {log}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Footer Actions */}
            <div className="border-t px-6 py-4 flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {currentStep?.status === "running" && "Processing..."}
                {currentStep?.status === "completed" && "✓ All steps completed"}
                {currentStep?.status === "failed" && "✗ Run failed"}
              </div>
              <div className="flex gap-2">
                {currentStep?.status === "completed" && (
                  <Button onClick={onClose}>
                    View Results
                    <BarChart3 className="ml-2 h-4 w-4" />
                  </Button>
                )}
                {currentStep?.status === "failed" && (
                  <Button variant="outline" onClick={onClose}>
                    Close
                  </Button>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
