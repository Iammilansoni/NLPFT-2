import * as React from 'react'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface SectionHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  subtitle?: string
  eyebrow?: string
  icon?: LucideIcon
  action?: React.ReactNode
  gradient?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizeStyles = {
  sm: {
    title: 'text-lg font-semibold',
    subtitle: 'text-sm',
    eyebrow: 'text-xs',
    spacing: 'space-y-1'
  },
  md: {
    title: 'text-2xl font-bold',
    subtitle: 'text-base',
    eyebrow: 'text-sm',
    spacing: 'space-y-2'
  },
  lg: {
    title: 'text-3xl md:text-4xl font-bold tracking-tight',
    subtitle: 'text-lg',
    eyebrow: 'text-sm',
    spacing: 'space-y-3'
  }
}

export function SectionHeader({
  title,
  subtitle,
  eyebrow,
  icon: Icon,
  action,
  gradient = false,
  size = 'md',
  className,
  ...props
}: SectionHeaderProps) {
  const styles = sizeStyles[size]

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4',
        className
      )}
      {...props}
    >
      <div className={styles.spacing}>
        {eyebrow && (
          <div className={cn(
            'font-medium text-muted-foreground uppercase tracking-wider',
            styles.eyebrow
          )}>
            {eyebrow}
          </div>
        )}
        
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="p-2 corporate-gradient rounded-lg">
              <Icon className="h-6 w-6 text-white" />
            </div>
          )}
          <h1 className={cn(
            styles.title,
            gradient && 'corporate-gradient-text'
          )}>
            {title}
          </h1>
        </div>
        
        {subtitle && (
          <p className={cn(
            'text-muted-foreground max-w-3xl',
            styles.subtitle
          )}>
            {subtitle}
          </p>
        )}
      </div>
      
      {action && (
        <div className="flex-shrink-0">
          {action}
        </div>
      )}
    </div>
  )
}


export function SectionDivider({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex justify-center my-8', className)} {...props}>
      <div className="h-1 w-24 corporate-gradient rounded-full"></div>
    </div>
  )
}
