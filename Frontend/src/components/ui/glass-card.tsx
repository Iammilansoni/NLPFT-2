'use client'

import { ReactNode, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  withSpotlight?: boolean
  withDivider?: boolean
}

export function GlassCard({ 
  children, 
  className, 
  withSpotlight = true,
  withDivider = false,
  ...props 
}: GlassCardProps) {
  return (
    <div
      {...props}
      className={cn(
        'glass-card rounded-2xl p-6 edge-glow transition-all duration-200',
        withSpotlight && 'hover-spotlight hover:-translate-y-1 hover:shadow-glow',
        className
      )}
      onMouseMove={withSpotlight ? (e) => {
        const rect = e.currentTarget.getBoundingClientRect()
        const x = ((e.clientX - rect.left) / rect.width) * 100
        const y = ((e.clientY - rect.top) / rect.height) * 100
        e.currentTarget.style.setProperty('--mx', `${x}%`)
        e.currentTarget.style.setProperty('--my', `${y}%`)
      } : undefined}
      onMouseLeave={withSpotlight ? (e) => {
        e.currentTarget.style.removeProperty('--mx')
        e.currentTarget.style.removeProperty('--my')
      } : undefined}
    >
      {withDivider && <div className="divider-shimmer w-full mb-4 opacity-60" />}
      {children}
    </div>
  )
}
