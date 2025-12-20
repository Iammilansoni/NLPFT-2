"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ConfidenceBadgeProps {
  confidence: number
  className?: string
  showLabel?: boolean
}

export function ConfidenceBadge({
  confidence,
  className,
  showLabel = true,
}: ConfidenceBadgeProps) {
  const percentage = Math.round(confidence * 100)

  const getColor = () => {
    if (percentage >= 90) return "bg-green-600 dark:bg-green-500 text-white"
    if (percentage >= 75) return "bg-blue-600 dark:bg-blue-500 text-white"
    if (percentage >= 50) return "bg-amber-600 dark:bg-amber-500 text-white"
    return "bg-red-600 dark:bg-red-500 text-white"
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium",
        getColor(),
        className
      )}
    >
      {showLabel && <span>Confidence:</span>}
      <span className="tabular-nums">{percentage}%</span>
    </div>
  )
}
