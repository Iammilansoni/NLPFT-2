"use client"

import { motion } from "framer-motion"
import { LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface KpiCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: {
    value: number
    label: string
    isPositive?: boolean
  }
  gradient?: string
  onClick?: () => void
  isLoading?: boolean
  className?: string
}

export function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  gradient = "from-primary/10 to-primary/5",
  onClick,
  isLoading,
  className
}: KpiCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.16 }}
      className={cn("group", className)}
    >
      <Card
        className={cn(
          "border-2 hover:border-primary/50 transition-all duration-200 cursor-pointer h-full",
          onClick && "hover:shadow-lg"
        )}
        onClick={onClick}
      >
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <p className="text-sm font-medium text-muted-foreground mb-1">
                {title}
              </p>
              {isLoading ? (
                <div className="h-9 w-24 bg-muted animate-pulse rounded" />
              ) : (
                <h3 className="text-3xl font-bold font-heading text-foreground">
                  {value}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
              )}
            </div>

            <div className={cn(
              "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br transition-transform group-hover:scale-110",
              gradient
            )}>
              <Icon className="h-6 w-6 text-primary" />
            </div>
          </div>

          {trend && (
            <div className="flex items-center gap-2 text-sm">
              <span className={cn(
                "font-semibold",
                trend.isPositive ? "text-green-500" : "text-red-500"
              )}>
                {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
              </span>
              <span className="text-muted-foreground">{trend.label}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
