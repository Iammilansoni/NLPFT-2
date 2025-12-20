"use client"

import * as React from "react"
import { FileQuestion, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-4 text-center",
        className
      )}
    >
      <div className="mb-4 text-muted-foreground">
        {icon || <FileQuestion className="h-12 w-12" />}
      </div>

      <h3 className="text-lg font-semibold mb-2">
        {title}
      </h3>

      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-6">
          {description}
        </p>
      )}

      {action && (
        <Button onClick={action.onClick} size="sm">
          <Plus className="h-4 w-4 mr-2" />
          {action.label}
        </Button>
      )}
    </div>
  )
}
