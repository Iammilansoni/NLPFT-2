"use client"

/**
 * Shown wherever vectors from two embedding models meet: the search box, the
 * datasets page, the generate flow. Vectors from different models can't be
 * compared, so instead of silently skipping data it explains what happened and
 * offers the backend's two ways out: switch to the model the data was embedded
 * with, or re-embed the data with the current model.
 */

import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Loader2, RefreshCw, Shuffle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { toast } from '@/hooks/use-toast'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { EmbeddingGroup, MismatchOption } from '@/lib/api-types'

/** The backend's message from any thrown API error, in the shapes FastAPI produces. */
export function apiErrorMessage(err: any, fallback = 'Something went wrong.'): string {
  const detail = err?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') return detail.message
  return err?.message || fallback
}

export type MismatchResolution = 'switched' | 'reembedding'

interface ModelMismatchPanelProps {
  message: string
  options: MismatchOption[]
  /** Datasets left out because of their model, when the backend listed them. */
  excluded?: EmbeddingGroup[]
  onResolved?: (how: MismatchResolution) => void
  /** Softer styling when results were still found and this is only a notice. */
  variant?: 'error' | 'notice'
  className?: string
}

export function ModelMismatchPanel({ message, options, excluded, onResolved, variant = 'error', className }: ModelMismatchPanelProps) {
  const queryClient = useQueryClient()
  const [running, setRunning] = useState<number | null>(null)

  const run = async (option: MismatchOption, index: number) => {
    setRunning(index)
    try {
      if (option.action === 'switch_model' && option.provider && option.model_id) {
        const result = await apiClient.chooseEmbeddingModel(option.provider, option.model_id)
        toast({ title: 'Embedding model switched', description: result.message })
        onResolved?.('switched')
      } else if (option.action === 'reembed' && option.dataset_id) {
        const result = await apiClient.embedDataset(option.dataset_id, true)
        toast({ title: 'Re-embedding started', description: result.message })
        onResolved?.('reembedding')
      } else if (option.action === 'reembed_all') {
        const result = await apiClient.reembedDatasets(option.dataset_ids)
        toast({ title: 'Re-embedding started', description: `${result.message} Progress shows on the Datasets page.` })
        onResolved?.('reembedding')
      }
      queryClient.invalidateQueries({ queryKey: ['embedding-settings'] })
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    } catch (err) {
      toast({ title: 'That did not work', description: apiErrorMessage(err), variant: 'destructive' })
    } finally {
      setRunning(null)
    }
  }

  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={cn(
        'space-y-3 rounded-xl border p-4 text-sm',
        variant === 'error' ? 'border-warning/40 bg-warning/5' : 'border-border/60 bg-muted/30',
        className
      )}
    >
      <p className="flex items-start gap-2 text-foreground">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
        <span>{message}</span>
      </p>

      {excluded && excluded.length > 0 && (
        <ul className="space-y-1 pl-6 text-xs text-muted-foreground">
          {excluded.map(group => (
            <li key={`${group.provider}/${group.model_id}/${group.dimension}`}>
              <span className="font-medium text-foreground">{group.label}</span>
              {': '}
              {group.datasets.map(d => d.name).join(', ')}
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap gap-2 pl-6">
        {options.map((option, index) => (
          <Button
            key={`${option.action}-${index}`}
            type="button"
            size="sm"
            variant={option.action === 'switch_model' ? 'outline' : 'default'}
            disabled={running !== null}
            onClick={() => run(option, index)}
            title={option.description}
            className="rounded-lg"
          >
            {running === index ? (
              <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
            ) : option.action === 'switch_model' ? (
              <Shuffle className="mr-2 h-3.5 w-3.5" />
            ) : (
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
            )}
            {option.label}
          </Button>
        ))}
      </div>
      <p className="pl-6 text-xs text-muted-foreground">
        Vectors from different embedding models can&apos;t be compared, so this data is left out of search until one of these is done.
      </p>
    </div>
  )
}

export default ModelMismatchPanel
