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
    /** @deprecated Cards share one neutral style; kept so existing callers compile. */
    gradient?: string
    className?: string
    onClick?: () => void
}

function computePercent(value: number, total: number): number {
    if (total <= 0) return 0
    return Math.max(0, Math.min((value / total) * 100, 100))
}

function TrendIcon({ direction }: { direction: 'up' | 'down' | 'neutral' }) {
    if (direction === 'up') return <TrendingUp className="h-3 w-3" />
    if (direction === 'down') return <TrendingDown className="h-3 w-3" />
    return <Minus className="h-3 w-3" />
}

/**
 * KPI card. One style everywhere: neutral surface, a small brand-gradient icon
 * chip (icons are rendered white inside it), and a large tabular figure.
 */
export function MetricCard({ label, value, subtitle, icon, trend, progress, className, onClick }: MetricCardProps) {
    return (
        <div
            className={cn(
                'group relative overflow-hidden rounded-xl border border-border/70 bg-card p-5 shadow-xs',
                'transition-all duration-200 hover:-translate-y-0.5 hover:border-border hover:shadow-md',
                onClick && 'cursor-pointer',
                className
            )}
            onClick={onClick}
        >
            <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-primary/[0.06] blur-2xl transition-opacity group-hover:opacity-100" />
            <div className="relative flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-muted-foreground">{label}</p>
                {icon && (
                    <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-brand-gradient text-white shadow-sm [&_svg]:h-[18px] [&_svg]:w-[18px] [&_svg]:text-white">
                        {icon}
                    </div>
                )}
            </div>

            <div className="relative mt-3 flex items-baseline gap-2">
                <span className="font-display text-3xl font-semibold tracking-tight text-foreground tabular-nums truncate">
                    {value}
                </span>
                {trend && (
                    <span className={cn(
                        'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-xs font-medium',
                        trend.direction === 'up' && 'bg-success/10 text-success',
                        trend.direction === 'down' && 'bg-destructive/10 text-destructive',
                        trend.direction === 'neutral' && 'bg-muted text-muted-foreground'
                    )}>
                        <TrendIcon direction={trend.direction} />
                        {trend.value}%
                    </span>
                )}
            </div>

            {progress ? (
                <div className="relative mt-3 space-y-1.5">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                            className="h-full rounded-full bg-brand-gradient transition-all duration-700"
                            style={{ width: `${computePercent(progress.value, progress.total)}%` }}
                        />
                    </div>
                    {progress.label && <p className="text-xs text-muted-foreground">{progress.label}</p>}
                </div>
            ) : (
                subtitle && <p className="relative mt-1 truncate text-xs text-muted-foreground">{subtitle}</p>
            )}
        </div>
    )
}
