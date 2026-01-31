import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

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
    gradient?: string
    className?: string
    onClick?: () => void
}

// Helper to compute safe percentage
function computePercent(value: number, total: number): number {
    if (total <= 0) return 0
    const percent = (value / total) * 100
    return Math.max(0, Math.min(percent, 100))
}

// Helper to render trend icon based on direction
function TrendIcon({ direction }: { direction: 'up' | 'down' | 'neutral' }) {
    switch (direction) {
        case 'up':
            return <TrendingUp className="h-3 w-3" />
        case 'down':
            return <TrendingDown className="h-3 w-3" />
        case 'neutral':
        default:
            return <Minus className="h-3 w-3" />
    }
}

export function MetricCard({
    label,
    value,
    subtitle,
    icon,
    trend,
    progress,
    gradient,
    className,
    onClick
}: MetricCardProps) {
    // Use gradient style if provided
    if (gradient) {
        return (
            <div
                className={cn(
                    "relative overflow-hidden rounded-2xl p-6",
                    "bg-gradient-to-br border border-white/10",
                    "shadow-lg shadow-black/5",
                    "transition-all duration-300 hover:scale-[1.02] hover:shadow-xl",
                    gradient,
                    onClick && "cursor-pointer",
                    className
                )}
                onClick={onClick}
            >
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/20" />
                    <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/10" />
                </div>
                
                <div className="relative">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm">
                            {icon}
                        </div>
                        {trend && (
                            <div className="flex items-center gap-1 text-xs font-medium text-white/80">
                                <TrendIcon direction={trend.direction} />
                                {trend.value > 0 ? '+' : ''}{trend.value}% {trend.label}
                            </div>
                        )}
                    </div>
                    <div className="text-3xl font-bold text-white mb-1">{value}</div>
                    <div className="text-sm font-medium text-white/80">{label}</div>
                    {subtitle && <div className="text-xs text-white/60 mt-1">{subtitle}</div>}
                    
                    {progress && (
                        <div className="mt-3 space-y-1.5">
                            <div className="h-1.5 w-full bg-white/20 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-white/60 rounded-full transition-all duration-1000"
                                    style={{ width: `${computePercent(progress.value, progress.total)}%` }}
                                />
                            </div>
                            {progress.label && (
                                <p className="text-xs text-white/70">{progress.label}</p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        )
    }

    // Default card style (non-gradient)
    return (
        <div
            className={cn(
                "group relative bg-card border border-border/50 hover:border-border hover:shadow-lg",
                "p-6 rounded-2xl transition-all duration-300",
                onClick && "cursor-pointer hover:bg-accent/5",
                className
            )}
            onClick={onClick}
        >
            <div className="flex items-start justify-between mb-4">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{label}</h3>
                {icon && (
                    <div className="p-2.5 rounded-xl bg-primary/5 text-primary/70 group-hover:text-primary group-hover:bg-primary/10 transition-colors">
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
                            "inline-flex items-center gap-1 text-xs font-medium px-1.5 py-0.5 rounded-full scale-90 origin-left",
                            trend.direction === 'up' && "text-emerald-600 bg-emerald-500/10",
                            trend.direction === 'down' && "text-red-600 bg-red-500/10",
                            trend.direction === 'neutral' && "text-muted-foreground bg-muted"
                        )}>
                            <TrendIcon direction={trend.direction} />
                            {trend.value}%
                        </span>
                    )}
                </div>

                {progress ? (
                    <div className="space-y-1.5">
                        <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary/60 rounded-full transition-all duration-1000 group-hover:bg-primary"
                                style={{ width: `${computePercent(progress.value, progress.total)}%` }}
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
