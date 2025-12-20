import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricCardProps {
    label: string
    value: string | number
    subtitle?: string
    icon?: React.ReactNode
    trend?: {
        value: number
        label?: string
        direction: 'up' | 'down' | 'neutral'
    }
    progress?: {
        value: number
        total: number
        label?: string
    }
    className?: string
    onClick?: () => void
}

export function MetricCard({
    label,
    value,
    subtitle,
    icon,
    trend,
    progress,
    className,
    onClick
}: MetricCardProps) {
    return (
        <div
            className={cn(
                "group relative bg-card/50 backdrop-blur-sm border border-border/60 hover:border-border hover:shadow-sm p-5 rounded-xl transition-all duration-300",
                onClick && "cursor-pointer hover:bg-accent/5",
                className
            )}
            onClick={onClick}
        >
            <div className="flex items-start justify-between mb-4">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{label}</h3>
                {icon && (
                    <div className="p-2 rounded-lg bg-primary/5 text-primary/70 group-hover:text-primary group-hover:bg-primary/10 transition-colors">
                        {icon}
                    </div>
                )}
            </div>

            <div className="space-y-3">
                <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold tracking-tight text-foreground font-mono tabular-nums">
                        {value}
                    </span>
                    {trend && (
                        <span className={cn(
                            "text-xs font-medium px-1.5 py-0.5 rounded-full bg-opacity-10 scale-90 origin-left",
                            trend.direction === 'up' && "text-emerald-600 bg-emerald-500/10",
                            trend.direction === 'down' && "text-red-600 bg-red-500/10",
                            trend.direction === 'neutral' && "text-muted-foreground bg-muted"
                        )}>
                            {trend.direction === 'up' ? '↑' : trend.direction === 'down' ? '↓' : ''} {trend.value}%
                        </span>
                    )}
                </div>

                {progress ? (
                    <div className="space-y-1.5">
                        <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary/60 rounded-full transition-all duration-1000 group-hover:bg-primary"
                                style={{ width: `${Math.min((progress.value / progress.total) * 100, 100)}%` }}
                            />
                        </div>
                        {progress.label && (
                            <p className="text-xs text-muted-foreground/80">{progress.label}</p>
                        )}
                    </div>
                ) : (
                    subtitle && (
                        <p className="text-xs text-muted-foreground/80 truncate">
                            {subtitle}
                        </p>
                    )
                )}
            </div>
        </div>
    )
}
