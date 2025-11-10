'use client'

import { motion } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, Play, FileText, Copy, CheckCircle, ExternalLink, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { toast } from '@/hooks/use-toast'

interface MeaningJSON {
  intent: string
  template: string
  slots: Record<string, any>
  confidence: number
  evidence: {
    similar_cases: Array<{ id: string, similarity: number, text?: string }>
  }
}

interface MeaningJSONCardProps {
  meaning: MeaningJSON
  onRunSelenium?: () => void
  onViewTemplate?: () => void
  onViewDataset?: () => void
  isLoading?: boolean
}

export function MeaningJSONCard({ 
  meaning, 
  onRunSelenium,
  onViewTemplate,
  onViewDataset,
  isLoading = false
}: MeaningJSONCardProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(meaning, null, 2))
    setCopied(true)
    toast({
      title: 'Success',
      description: 'JSON copied to clipboard',
    })
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(meaning, null, 2)], { 
      type: 'application/json' 
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `meaning-${meaning.intent}-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast({
      title: 'Success',
      description: 'JSON downloaded',
    })
  }

  const handleDownloadCSV = () => {
    // Convert slots to CSV format
    const headers = Object.keys(meaning.slots).join(',')
    const values = Object.values(meaning.slots).join(',')
    const csv = `${headers}\n${values}`
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `slots-${meaning.intent}-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast({
      title: 'Success',
      description: 'CSV downloaded',
    })
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
    if (confidence >= 0.7) return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20'
    return 'text-red-500 bg-red-500/10 border-red-500/20'
  }

  if (isLoading) {
    return (
      <Card className="p-6 space-y-6 animate-pulse">
        <div className="h-8 bg-muted rounded w-1/3" />
        <div className="h-64 bg-muted rounded" />
        <div className="flex gap-3">
          <div className="h-12 bg-muted rounded flex-1" />
          <div className="h-12 bg-muted rounded w-32" />
          <div className="h-12 bg-muted rounded w-32" />
        </div>
      </Card>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="p-6 space-y-6 border-2 hover:border-primary/40 transition-all duration-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <h3 className="text-2xl font-bold">Meaning JSON</h3>
            </div>
            <p className="text-muted-foreground">
              Extracted intent and slots from your natural language query
            </p>
          </div>
          
          {/* Confidence Badge */}
          <Badge 
            className={`text-lg px-5 py-2.5 font-bold border-2 ${getConfidenceColor(meaning.confidence)}`}
          >
            {(meaning.confidence * 100).toFixed(1)}%
          </Badge>
        </div>

        {/* Intent & Template Info */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-card/50 border border-border/50">
            <div className="text-sm text-muted-foreground mb-1">Intent</div>
            <div className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {meaning.intent}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-card/50 border border-border/50">
            <div className="text-sm text-muted-foreground mb-1">Template</div>
            <div className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {meaning.template}
            </div>
          </div>
        </div>

        {/* JSON Display */}
        <div className="relative group">
          <pre className="bg-black/95 text-emerald-400 p-6 rounded-xl overflow-x-auto font-mono text-sm border-2 border-primary/20 shadow-lg">
            <code>{JSON.stringify(meaning, null, 2)}</code>
          </pre>
          
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="absolute top-4 right-4 p-2 rounded-lg bg-black/80 border border-primary/30 hover:border-primary/60 transition-all backdrop-blur-sm"
            onClick={handleCopy}
          >
            {copied ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : (
              <Copy className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
            )}
          </motion.button>
        </div>

        {/* Slots Breakdown */}
        <div className="space-y-3">
          <h4 className="font-semibold text-lg flex items-center gap-2">
            <span className="h-1 w-1 rounded-full bg-primary" />
            Extracted Slots
          </h4>
          <div className="grid gap-3">
            {Object.entries(meaning.slots).map(([key, value], i) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center justify-between p-3 rounded-lg bg-card/50 border border-border/50 hover:border-primary/30 transition-all"
              >
                <span className="font-mono text-sm text-muted-foreground">{key}</span>
                <span className="font-semibold">{String(value)}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 pt-4 border-t">
          {onRunSelenium && (
            <Button
              onClick={onRunSelenium}
              className="flex-1 min-w-[200px] h-12 text-base font-bold shadow-[0_4px_20px_rgba(6,182,212,0.3)] hover:shadow-[0_4px_30px_rgba(6,182,212,0.5)]"
              size="lg"
            >
              <Play className="mr-2 h-5 w-5" />
              Run with Selenium
            </Button>
          )}
          
          {onViewTemplate && (
            <Button
              variant="outline"
              onClick={onViewTemplate}
              className="h-12"
            >
              <FileText className="mr-2 h-4 w-4" />
              View Template
            </Button>
          )}
          
          {onViewDataset && (
            <Button
              variant="outline"
              onClick={onViewDataset}
              className="h-12"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              View Dataset
            </Button>
          )}
          
          <Button
            variant="outline"
            onClick={handleDownloadJSON}
            className="h-12"
          >
            <Download className="mr-2 h-4 w-4" />
            JSON
          </Button>
          
          <Button
            variant="outline"
            onClick={handleDownloadCSV}
            className="h-12"
          >
            <Download className="mr-2 h-4 w-4" />
            CSV
          </Button>
        </div>

        {/* Similar Cases */}
        {meaning.evidence.similar_cases.length > 0 && (
          <div className="space-y-3 pt-4 border-t">
            <h4 className="font-semibold flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-primary" />
              Top Similar Cases
              <Badge variant="secondary" className="ml-2">
                {meaning.evidence.similar_cases.length}
              </Badge>
            </h4>
            <div className="space-y-3">
              {meaning.evidence.similar_cases.slice(0, 5).map((case_, i) => (
                <motion.div
                  key={case_.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="space-y-2 p-3 rounded-lg bg-card/50 border border-border/50 hover:border-primary/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono text-muted-foreground">
                      {case_.id}
                    </span>
                    <span className="text-sm font-bold">
                      {(case_.similarity * 100).toFixed(1)}% match
                    </span>
                  </div>
                  
                  {case_.text && (
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {case_.text}
                    </p>
                  )}
                  
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${case_.similarity * 100}%` }}
                      transition={{ duration: 0.6, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
                      className="h-full bg-gradient-to-r from-primary via-[#14b8a6] to-accent shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  )
}
