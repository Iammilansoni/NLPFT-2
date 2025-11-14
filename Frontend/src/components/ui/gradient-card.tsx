'use client'

import { ReactNode, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface GradientCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  withHover?: boolean
}

export function GradientCard({ 
  children, 
  className,
  withHover = true,
  ...props 
}: GradientCardProps) {
  return (
    <div
      {...props}
      className={cn(
        'card-gradient rounded-2xl p-5 edge-glow transition-all duration-200',
        withHover && 'hover:-translate-y-1 hover:shadow-glow cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  )
}
