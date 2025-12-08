"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  X,
  Settings,
  RefreshCw,
  Loader2,
  ArrowRight,
  Zap,
  Rocket,
  Target,
  Info,
  Brain,
  Database,
  Clock,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getEmbeddingModelInfo, type EmbeddingModelOption } from '@/lib/constants/embedding-models'

interface ModelMismatchDialogProps {
  isOpen: boolean
  onClose: () => void
  datasetModel: string
  settingsModel: string
  datasetName?: string
  onUseCurrentModel: () => void
  onReEmbed: () => void
  isReEmbedding?: boolean
}

const ModelIcon = ({ modelId, className }: { modelId: string; className?: string }) => {
  const iconMap: Record<string, React.ReactNode> = {
    'all-minilm': <Zap className={className} />,
    'nomic-embed-text': <Rocket className={className} />,
    'mxbai-embed-large': <Target className={className} />,
  }
  return iconMap[modelId] || <Brain className={className} />
}

const ModelBadge = ({ model, label }: { model: EmbeddingModelOption | undefined; label: string }) => {
  if (!model) return null
  
  const colorMap: Record<string, string> = {
    'all-minilm': 'from-blue-500 to-cyan-500',
    'nomic-embed-text': 'from-green-500 to-emerald-500',
    'mxbai-embed-large': 'from-red-500 to-orange-500',
  }
  
  return (
    <div className="flex flex-col items-center gap-2 p-4 rounded-xl bg-muted/50 border">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
      <div className={cn(
        "w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center",
        colorMap[model.value] || 'from-gray-500 to-gray-600'
      )}>
        <ModelIcon modelId={model.value} className="w-6 h-6 text-white" />
      </div>
      <div className="text-center">
        <p className="font-semibold">{model.label}</p>
        <Badge variant="secondary" className="font-mono text-xs mt-1">
          {model.dimension}D
        </Badge>
      </div>
    </div>
  )
}

export function ModelMismatchDialog({
  isOpen,
  onClose,
  datasetModel,
  settingsModel,
  datasetName,
  onUseCurrentModel,
  onReEmbed,
  isReEmbedding = false,
}: ModelMismatchDialogProps) {
  const datasetModelInfo = getEmbeddingModelInfo(datasetModel)
  const settingsModelInfo = getEmbeddingModelInfo(settingsModel)

  if (!isOpen) return null

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

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", duration: 0.5 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg"
          >
            <div className="relative bg-card rounded-2xl border shadow-2xl overflow-hidden">
              {/* Warning Banner */}
              <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-4">
                <div className="flex items-center gap-3 text-white">
                  <div className="p-2 rounded-lg bg-white/20">
                    <AlertTriangle className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="font-bold text-lg">Embedding Model Mismatch</h2>
                    <p className="text-sm opacity-90">
                      Incompatible vector dimensions detected
                    </p>
                  </div>
                </div>
                {/* Close Button */}
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-1 rounded-lg hover:bg-white/20 transition-colors text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                {/* Model Comparison */}
                <div className="flex items-center justify-center gap-4">
                  <ModelBadge model={datasetModelInfo} label="Dataset Model" />
                  <div className="flex flex-col items-center gap-1">
                    <ArrowRight className="w-6 h-6 text-muted-foreground" />
                    <span className="text-xs text-destructive font-semibold">≠</span>
                  </div>
                  <ModelBadge model={settingsModelInfo} label="Settings Model" />
                </div>

                {/* Explanation */}
                <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                    <div className="space-y-2 text-sm text-amber-800 dark:text-amber-200">
                      <p>
                        <strong>Why does this matter?</strong>
                      </p>
                      <p>
                        {datasetName ? `The dataset "${datasetName}"` : 'This dataset'} was embedded using 
                        <strong> {datasetModelInfo?.label || datasetModel}</strong> ({datasetModelInfo?.dimension || '?'}D vectors), 
                        but your current settings use <strong>{settingsModelInfo?.label || settingsModel}</strong> ({settingsModelInfo?.dimension || '?'}D vectors).
                      </p>
                      <p>
                        Vectors from different embedding models are <strong>incompatible</strong> and will produce 
                        <strong> incorrect similarity scores</strong>.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Options */}
                <div className="space-y-3">
                  <p className="text-sm font-medium text-muted-foreground">
                    Choose how to proceed:
                  </p>

                  {/* Option 1: Use Current Settings Model (Search with different model) */}
                  <button
                    onClick={onUseCurrentModel}
                    disabled={isReEmbedding}
                    className="w-full text-left p-4 rounded-xl border-2 hover:border-primary/50 hover:bg-primary/5 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                        <Settings className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold group-hover:text-primary transition-colors">
                          Use Current Settings Model
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Search will use <strong>{settingsModelInfo?.label || settingsModel}</strong>. 
                          Results may be less accurate or fail if dimensions mismatch in Redis.
                        </p>
                        <Badge variant="outline" className="mt-2">
                          <Clock className="w-3 h-3 mr-1" />
                          Instant
                        </Badge>
                      </div>
                    </div>
                  </button>

                  {/* Option 2: Re-Embed Dataset */}
                  <button
                    onClick={onReEmbed}
                    disabled={isReEmbedding}
                    className="w-full text-left p-4 rounded-xl border-2 border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30 hover:border-green-500 hover:bg-green-100 dark:hover:bg-green-950/50 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2 rounded-lg bg-green-500/20 text-green-600 dark:text-green-400 group-hover:bg-green-500 group-hover:text-white transition-colors">
                        {isReEmbedding ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <RefreshCw className="w-5 h-5" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-green-700 dark:text-green-300 group-hover:text-green-800 dark:group-hover:text-green-200 transition-colors">
                          Re-Embed Dataset
                        </p>
                        <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                          {isReEmbedding ? (
                            "Re-embedding in progress... This may take a few minutes."
                          ) : (
                            <>
                              Convert all vectors to <strong>{settingsModelInfo?.label || settingsModel}</strong> ({settingsModelInfo?.dimension || '?'}D). 
                              Ensures accurate similarity search.
                            </>
                          )}
                        </p>
                        <Badge variant="outline" className="mt-2 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300">
                          <Database className="w-3 h-3 mr-1" />
                          Recommended
                        </Badge>
                      </div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t bg-muted/30">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    You can change your default model in Settings → AI Models
                  </p>
                  <Button variant="ghost" size="sm" onClick={onClose}>
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default ModelMismatchDialog
