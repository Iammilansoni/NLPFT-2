import * as React from 'react'
import { cn } from '@/lib/utils'
import { LucideIcon, Loader2 } from 'lucide-react'

interface LoadingOverlayProps extends React.HTMLAttributes<HTMLDivElement> {
  isLoading: boolean
  title?: string
  description?: string
  icon?: LucideIcon
  variant?: 'overlay' | 'inline' | 'card'
  size?: 'sm' | 'md' | 'lg'
  spinner?: 'default' | 'dots' | 'pulse'
}

const sizeStyles = {
  sm: {
    spinner: 'h-6 w-6',
    title: 'text-sm font-medium',
    description: 'text-xs',
    spacing: 'space-y-2'
  },
  md: {
    spinner: 'h-8 w-8',
    title: 'text-base font-semibold',
    description: 'text-sm',
    spacing: 'space-y-3'
  },
  lg: {
    spinner: 'h-12 w-12',
    title: 'text-xl font-bold',
    description: 'text-base',
    spacing: 'space-y-4'
  }
}

const SpinnerComponent = ({ 
  type, 
  size, 
  className 
}: { 
  type: string
  size: string
  className?: string 
}) => {
  if (type === 'dots') {
    return (
      <div className={cn('flex space-x-1', className)}>
        <div className={cn('rounded-full bg-primary animate-pulse', size === 'h-6 w-6' ? 'h-2 w-2' : size === 'h-8 w-8' ? 'h-3 w-3' : 'h-4 w-4')} 
             style={{ animationDelay: '0ms' }} />
        <div className={cn('rounded-full bg-primary animate-pulse', size === 'h-6 w-6' ? 'h-2 w-2' : size === 'h-8 w-8' ? 'h-3 w-3' : 'h-4 w-4')} 
             style={{ animationDelay: '150ms' }} />
        <div className={cn('rounded-full bg-primary animate-pulse', size === 'h-6 w-6' ? 'h-2 w-2' : size === 'h-8 w-8' ? 'h-3 w-3' : 'h-4 w-4')} 
             style={{ animationDelay: '300ms' }} />
      </div>
    )
  }

  if (type === 'pulse') {
    return (
      <div className={cn('rounded-full border-4 border-primary/20 animate-pulse-strong', size, className)} />
    )
  }

  
  return <Loader2 className={cn('animate-spin text-primary', size, className)} />
}

export function LoadingOverlay({
  isLoading,
  title,
  description,
  icon: Icon,
  variant = 'overlay',
  size = 'md',
  spinner = 'default',
  className,
  children,
  ...props
}: LoadingOverlayProps) {
  const styles = sizeStyles[size]

  if (!isLoading && variant !== 'overlay') {
    return <>{children}</>
  }

  const loadingContent = (
    <div className={cn(
      'flex flex-col items-center justify-center text-center',
      styles.spacing,
      variant === 'card' && 'p-8 rounded-lg bg-card border shadow-sm',
      className
    )}>
      <div className="relative">
        {Icon ? (
          <div className="relative">
            <Icon className={cn(styles.spinner, 'text-muted-foreground')} />
            <div className="absolute inset-0 flex items-center justify-center">
              <SpinnerComponent 
                type={spinner} 
                size={styles.spinner} 
                className="absolute" 
              />
            </div>
          </div>
        ) : (
          <SpinnerComponent type={spinner} size={styles.spinner} />
        )}
      </div>
      
      {(title || description) && (
        <div className="space-y-1">
          {title && (
            <h3 className={cn(styles.title, 'text-foreground')}>
              {title}
            </h3>
          )}
          {description && (
            <p className={cn(styles.description, 'text-muted-foreground')}>
              {description}
            </p>
          )}
        </div>
      )}
    </div>
  )

  if (variant === 'overlay') {
    return (
      <div className="relative" {...props}>
        {children}
        {isLoading && (
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
            {loadingContent}
          </div>
        )}
      </div>
    )
  }

  if (variant === 'inline') {
    return isLoading ? loadingContent : <>{children}</>
  }

  
  return loadingContent
}


export function SkeletonCard({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-6 animate-pulse',
        className
      )}
      {...props}
    >
      <div className="space-y-3">
        <div className="skeleton h-4 w-3/4 rounded"></div>
        <div className="skeleton h-8 w-1/2 rounded"></div>
        <div className="skeleton h-3 w-full rounded"></div>
      </div>
    </div>
  )
}

export function SkeletonTable({ 
  rows = 5, 
  columns = 4, 
  className,
  ...props 
}: { 
  rows?: number
  columns?: number 
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('space-y-2', className)} {...props}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex space-x-4">
          {Array.from({ length: columns }).map((_, j) => (
            <div
              key={j}
              className={cn(
                'skeleton h-4 rounded',
                j === 0 && 'w-24', 
                j === 1 && 'flex-1', 
                j > 1 && 'w-20'     
              )}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
