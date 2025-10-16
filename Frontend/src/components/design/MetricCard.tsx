import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps extends React.ComponentProps<typeof Card> {
  title: string
  value: string | number
  subtitle?: string
  icon?: LucideIcon
  trend?: {
    value: number
    label?: string
    isPositive?: boolean
  }
  status?: 'healthy' | 'warning' | 'error' | 'info'
  variant?: 'default' | 'elevated' | 'gradient'
  hoverColor?: 'teal' | 'orange' | 'purple' | 'violet' | 'auto'
}

const statusStyles = {
  healthy: 'border-blue-200 dark:border-blue-600 bg-white dark:bg-slate-900 hover:bg-blue-50/30 dark:hover:bg-blue-950/20 hover:border-blue-300 dark:hover:border-blue-500 shadow-sm shadow-blue-100/30 dark:shadow-blue-900/20',
  warning: 'border-amber-200 dark:border-amber-600 bg-white dark:bg-slate-900 hover:bg-amber-50/30 dark:hover:bg-amber-950/20 hover:border-amber-300 dark:hover:border-amber-500 shadow-sm shadow-amber-100/30 dark:shadow-amber-900/20',
  error: 'border-red-200 dark:border-red-600 bg-white dark:bg-slate-900 hover:bg-red-50/30 dark:hover:bg-red-950/20 hover:border-red-300 dark:hover:border-red-500 shadow-sm shadow-red-100/30 dark:shadow-red-900/20',
  info: 'border-sky-200 dark:border-sky-600 bg-white dark:bg-slate-900 hover:bg-sky-50/30 dark:hover:bg-sky-950/20 hover:border-sky-300 dark:hover:border-sky-500 shadow-sm shadow-sky-100/30 dark:shadow-sky-900/20'
}


const hoverColorStyles = {
  teal: 'hover:shadow-xl hover:shadow-teal-500/40 hover:border-teal-400 dark:hover:border-teal-500 hover:from-teal-50 hover:via-cyan-50 hover:to-emerald-50 dark:hover:from-teal-950/40 dark:hover:via-cyan-950/30 dark:hover:to-emerald-950/40',
  orange: 'hover:shadow-xl hover:shadow-orange-500/40 hover:border-orange-400 dark:hover:border-orange-500 hover:from-orange-50 hover:via-amber-50 hover:to-yellow-50 dark:hover:from-orange-950/40 dark:hover:via-amber-950/30 dark:hover:to-yellow-950/40',
  purple: 'hover:shadow-xl hover:shadow-purple-500/40 hover:border-purple-400 dark:hover:border-purple-500 hover:from-purple-50 hover:via-fuchsia-50 hover:to-pink-50 dark:hover:from-purple-950/40 dark:hover:via-fuchsia-950/30 dark:hover:to-pink-950/40',
  violet: 'hover:shadow-xl hover:shadow-violet-500/40 hover:border-violet-400 dark:hover:border-violet-500 hover:from-violet-50 hover:via-indigo-50 hover:to-blue-50 dark:hover:from-violet-950/40 dark:hover:via-indigo-950/30 dark:hover:to-blue-950/40',
  auto: ''
}

const variantStyles = {
  
  default: 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-sm shadow-slate-200/50 dark:shadow-slate-900/40',
  elevated: 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-md shadow-slate-200/60 dark:shadow-slate-900/50',
  gradient: 'bg-gradient-to-br from-slate-50 to-white dark:from-slate-800 dark:to-slate-900 border border-slate-200 dark:border-slate-700 shadow-md shadow-slate-200/50 dark:shadow-slate-900/40'
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  status,
  variant = 'default',
  hoverColor = 'auto',
  className,
  ...props
}: MetricCardProps) {
  
  const getHoverColor = () => {
    if (hoverColor !== 'auto') return hoverColor;
    
    switch (title.toLowerCase()) {
      case 'database':
        return 'teal';
      case 'cpu usage':
        return 'orange';
      case 'memory':
        return 'purple';
      case 'rule engine':
        return 'violet';
      default:
        return 'teal';
    }
  };

  const selectedHoverColor = getHoverColor();
  return (
    <Card
      className={cn(
        
        'border-2 shadow-lg transition-all duration-300 ease-out backdrop-blur-sm',
        'group transform hover:-translate-y-1 sm:hover:-translate-y-2 lg:hover:-translate-y-3',
        'hover:scale-[1.01] sm:hover:scale-[1.02] lg:hover:scale-[1.03]',
        'cursor-pointer overflow-hidden relative',
        
        'min-h-[120px] sm:min-h-[140px] lg:min-h-[160px]',
        'w-full max-w-none sm:max-w-sm lg:max-w-md',
        
        variantStyles[variant],
        
        status && statusStyles[status],
        
        hoverColorStyles[selectedHoverColor],
        className
      )}
      {...props}
    >
      <CardHeader className="pb-2 sm:pb-3 pt-3 sm:pt-4 px-3 sm:px-6">
        <CardTitle className="flex items-center justify-between text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors duration-300">
          <span className="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-1">
            {Icon && (
              <div className={cn(
                'p-2 sm:p-3 rounded-lg sm:rounded-xl transition-all duration-300 group-hover:scale-105 sm:group-hover:scale-110 shadow-md group-hover:shadow-lg flex-shrink-0',
                
                selectedHoverColor === 'teal' && 'bg-gradient-to-br from-teal-100 to-cyan-100 dark:from-teal-900/60 dark:to-cyan-900/60 group-hover:from-teal-200 group-hover:to-cyan-200 dark:group-hover:from-teal-800/80 dark:group-hover:to-cyan-800/80 shadow-teal-200/50 dark:shadow-teal-900/30',
                selectedHoverColor === 'orange' && 'bg-gradient-to-br from-orange-100 to-amber-100 dark:from-orange-900/60 dark:to-amber-900/60 group-hover:from-orange-200 group-hover:to-amber-200 dark:group-hover:from-orange-800/80 dark:group-hover:to-amber-800/80 shadow-orange-200/50 dark:shadow-orange-900/30',
                selectedHoverColor === 'purple' && 'bg-gradient-to-br from-purple-100 to-fuchsia-100 dark:from-purple-900/60 dark:to-fuchsia-900/60 group-hover:from-purple-200 group-hover:to-fuchsia-200 dark:group-hover:from-purple-800/80 dark:group-hover:to-fuchsia-800/80 shadow-purple-200/50 dark:shadow-purple-900/30',
                selectedHoverColor === 'violet' && 'bg-gradient-to-br from-violet-100 to-indigo-100 dark:from-violet-900/60 dark:to-indigo-900/60 group-hover:from-violet-200 group-hover:to-indigo-200 dark:group-hover:from-violet-800/80 dark:group-hover:to-indigo-800/80 shadow-violet-200/50 dark:shadow-violet-900/30'
              )}>
                <Icon className={cn(
                  'h-4 w-4 sm:h-5 sm:w-5 transition-colors duration-300',
                  
                  selectedHoverColor === 'teal' && 'text-teal-700 dark:text-teal-300 group-hover:text-teal-800 dark:group-hover:text-teal-200',
                  selectedHoverColor === 'orange' && 'text-orange-700 dark:text-orange-300 group-hover:text-orange-800 dark:group-hover:text-orange-200',
                  selectedHoverColor === 'purple' && 'text-purple-700 dark:text-purple-300 group-hover:text-purple-800 dark:group-hover:text-purple-200',
                  selectedHoverColor === 'violet' && 'text-violet-700 dark:text-violet-300 group-hover:text-violet-800 dark:group-hover:text-violet-200'
                )} />
              </div>
            )}
            <span className="text-slate-900 dark:text-slate-100 font-bold group-hover:text-black dark:group-hover:text-white transition-colors duration-300 truncate">{title}</span>
          </span>
          {status && (
            <div className={cn(
              'w-3 h-3 sm:w-4 sm:h-4 rounded-full shadow-lg animate-pulse ring-1 sm:ring-2 ring-white dark:ring-slate-800 group-hover:scale-110 sm:group-hover:scale-125 transition-transform duration-300 flex-shrink-0',
              status === 'healthy' && 'bg-gradient-to-br from-blue-400 to-cyan-500 shadow-blue-400/60',
              status === 'warning' && 'bg-gradient-to-br from-amber-400 to-orange-500 shadow-amber-400/60',
              status === 'error' && 'bg-gradient-to-br from-rose-400 to-red-500 shadow-rose-400/60',
              status === 'info' && 'bg-gradient-to-br from-sky-400 to-blue-500 shadow-sky-400/60'
            )} />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 sm:space-y-3 pb-3 sm:pb-4 px-3 sm:px-6">
        <div className="flex items-baseline justify-between gap-2">
          <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-slate-900 dark:text-white group-hover:text-black dark:group-hover:text-white transition-colors duration-300 drop-shadow-sm min-w-0 flex-1 truncate">
            {value}
          </div>
          {trend && (
            <Badge 
              variant={trend.isPositive ? "success" : "destructive"}
              className={cn(
                'text-xs font-semibold flex-shrink-0',
                trend.isPositive 
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800'
              )}
            >
              {trend.isPositive ? '↗' : '↘'} {Math.abs(trend.value)}%
            </Badge>
          )}
        </div>
        {subtitle && (
          <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 font-semibold group-hover:text-slate-800 dark:group-hover:text-slate-200 transition-colors duration-300 leading-relaxed">
            {subtitle}
            {trend?.label && (
              <span className="ml-1 text-xs text-slate-500 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-400">• {trend.label}</span>
            )}
          </p>
        )}
      </CardContent>
    </Card>
  )
}


export const MetricCardPresets = {
  performance: (props: Partial<MetricCardProps>) => ({
    variant: 'elevated' as const,
    status: 'healthy' as const,
    ...props
  }),
  
  alert: (props: Partial<MetricCardProps>) => ({
    variant: 'default' as const,
    status: 'error' as const,
    ...props
  }),
  
  info: (props: Partial<MetricCardProps>) => ({
    variant: 'gradient' as const,
    status: 'info' as const,
    ...props
  })
}
