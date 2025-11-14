"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface SimilarityBarProps {
  similarity: number
  className?: string
  showLabel?: boolean
  animated?: boolean
  height?: "sm" | "md" | "lg"
}

export function SimilarityBar({
  similarity,
  className,
  showLabel = true,
  animated = true,
  height = "md",
}: SimilarityBarProps) {
  const percentage = Math.round(similarity * 100)
  
  const getColor = () => {
    if (similarity >= 0.9) return "bg-green-500"
    if (similarity >= 0.75) return "bg-blue-500"
    if (similarity >= 0.5) return "bg-yellow-500"
    return "bg-red-500"
  }

  const getHeight = () => {
    switch (height) {
      case "sm": return "h-1"
      case "md": return "h-2"
      case "lg": return "h-3"
      default: return "h-2"
    }
  }

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      {showLabel && (
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Similarity</span>
          <span className="font-medium text-foreground">{percentage}%</span>
        </div>
      )}
      <div className={cn("w-full bg-muted rounded-full overflow-hidden", getHeight())}>
        {animated ? (
          <motion.div
            className={cn("h-full rounded-full", getColor())}
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{
              duration: 0.6,
              ease: [0.4, 0, 0.2, 1],
            }}
          />
        ) : (
          <div
            className={cn("h-full rounded-full", getColor())}
            style={{ width: `${percentage}%` }}
          />
        )}
      </div>
    </div>
  )
}
