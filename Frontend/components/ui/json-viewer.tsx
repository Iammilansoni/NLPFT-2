"use client"

import * as React from "react"
import { Eye, EyeOff, Copy, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"

interface JSONViewerProps {
  data: Record<string, any> | null | undefined
  className?: string
  maxHeight?: string
  maskSecrets?: boolean
  secretKeys?: string[]
}

const defaultSecretKeys = [
  'password',
  'token',
  'secret',
  'api_key',
  'apiKey',
  'accessToken',
  'refreshToken',
  'auth',
]

export function JSONViewer({
  data,
  className,
  maxHeight = "400px",
  maskSecrets = true,
  secretKeys = defaultSecretKeys,
}: JSONViewerProps) {
  const [isMasked, setIsMasked] = React.useState(maskSecrets)
  const [isCopied, setIsCopied] = React.useState(false)

  const maskValue = (key: string, value: any): any => {
    if (!isMasked) return value

    const lowerKey = key.toLowerCase()
    const shouldMask = secretKeys.some(secret => lowerKey.includes(secret.toLowerCase()))

    if (shouldMask && typeof value === 'string') {
      return '••••••••'
    }

    return value
  }

  const processData = (obj: any): any => {
    if (obj === null || obj === undefined) return obj
    if (typeof obj !== 'object') return obj

    if (Array.isArray(obj)) {
      return obj.map(item => processData(item))
    }

    const processed: Record<string, any> = {}
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'object' && value !== null) {
        processed[key] = processData(value)
      } else {
        processed[key] = maskValue(key, value)
      }
    }
    return processed
  }

  const displayData = React.useMemo(() => {
    if (!data) return null
    return processData(data)
  }, [data, isMasked])

  const handleCopy = async () => {
    if (!data) return
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (!data) {
    return (
      <div className={cn("p-4 rounded-md border border-dashed text-center text-sm text-muted-foreground", className)}>
        No data available
      </div>
    )
  }

  return (
    <div className={cn("relative", className)}>
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        {maskSecrets && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsMasked(!isMasked)}
            className="h-7 w-7 p-0"
            aria-label={isMasked ? "Show sensitive values" : "Hide sensitive values"}
          >
            {isMasked ? (
              <Eye className="h-3.5 w-3.5" />
            ) : (
              <EyeOff className="h-3.5 w-3.5" />
            )}
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          onClick={handleCopy}
          className="h-7 w-7 p-0"
          aria-label="Copy JSON"
        >
          {isCopied ? (
            <Check className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <Copy className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>

      <div className="rounded-md border bg-muted/30 overflow-hidden">
        <pre
          className="p-4 overflow-auto text-xs font-mono custom-scrollbar"
          style={{ maxHeight }}
        >
          <code>{JSON.stringify(displayData, null, 2)}</code>
        </pre>
      </div>
    </div>
  )
}
