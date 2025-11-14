import * as React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
    variant?: 'default' | 'outline' | 'ghost'
  }
  size?: 'sm' | 'md' | 'lg'
  variant?: 'card' | 'inline'
}

const sizeStyles = {
  sm: {
    icon: 'h-8 w-8',
    title: 'text-lg font-semibold',
    description: 'text-sm',
    spacing: 'space-y-3',
    padding: 'p-6'
  },
  md: {
    icon: 'h-12 w-12',
    title: 'text-xl font-semibold',
    description: 'text-base',
    spacing: 'space-y-4',
    padding: 'p-8'
  },
  lg: {
    icon: 'h-16 w-16',
    title: 'text-2xl font-bold',
    description: 'text-lg',
    spacing: 'space-y-6',
    padding: 'p-12'
  }
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  size = 'md',
  variant = 'card',
  className,
  ...props
}: EmptyStateProps) {
  const styles = sizeStyles[size]

  const content = (
    <div className={cn(
      'flex flex-col items-center text-center',
      styles.spacing,
      variant === 'card' && styles.padding,
      className
    )}>
      {Icon && (
        <div className="flex items-center justify-center rounded-full bg-muted/30 p-4">
          <Icon className={cn(styles.icon, 'text-muted-foreground')} />
        </div>
      )}
      
      <div className="space-y-2">
        <h3 className={cn(styles.title, 'text-foreground')}>
          {title}
        </h3>
        <p className={cn(styles.description, 'text-muted-foreground max-w-md')}>
          {description}
        </p>
      </div>
      
      {action && (
        <Button
          onClick={action.onClick}
          variant={action.variant || 'default'}
          className="mt-2"
        >
          {action.label}
        </Button>
      )}
    </div>
  )

  if (variant === 'card') {
    return (
      <Card className="corporate-card" {...props}>
        <CardContent className="p-0">
          {content}
        </CardContent>
      </Card>
    )
  }

  return (
    <div {...props}>
      {content}
    </div>
  )
}


export const EmptyStatePresets = {
  noData: {
    title: 'No data available',
    description: 'There is no data to display at the moment. Try refreshing or check back later.'
  },
  
  noResults: {
    title: 'No results found',
    description: 'Your search didn\'t match any items. Try adjusting your search terms or filters.'
  },
  
  noItems: {
    title: 'No items yet',
    description: 'Get started by adding your first item.'
  },
  
  error: {
    title: 'Something went wrong',
    description: 'We encountered an error while loading the data. Please try again.'
  },
  
  loading: {
    title: 'Loading...',
    description: 'Please wait while we fetch your data.'
  }
}
