"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface ConfidenceBadgeProps {
  confidence: number
  className?: string
  showLabel?: boolean
  animated?: boolean
}

export function ConfidenceBadge({
  confidence,
  className,
  showLabel = true,
  animated = true,
}: ConfidenceBadgeProps) {
  const percentage = Math.round(confidence * 100)
  
  const getColor = () => {
    if (percentage >= 90) return "bg-green-500 text-white"
    if (percentage >= 75) return "bg-blue-500 text-white"
    if (percentage >= 50) return "bg-yellow-500 text-white"
    return "bg-red-500 text-white"
  }

  const BadgeContent = (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold transition-colors",
        getColor(),
        className
      )}
    >
      {showLabel && <span>Confidence:</span>}
      <span>{percentage}%</span>
    </div>
  )

  if (!animated) return BadgeContent

  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      {BadgeContent}
    </motion.div>
  )
}
