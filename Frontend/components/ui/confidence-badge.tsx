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
    if (percentage >= 90) return "bg-success dark:bg-success text-white"
    if (percentage >= 75) return "bg-info dark:bg-info text-white"
    if (percentage >= 50) return "bg-warning dark:bg-warning text-white"
    return "bg-destructive dark:bg-destructive text-white"
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
