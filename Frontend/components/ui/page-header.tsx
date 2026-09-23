import * as React from 'react'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  icon?: React.ReactNode
  title: string
  description?: React.ReactNode
  /** Right-aligned actions (buttons, status pills). */
  actions?: React.ReactNode
  className?: string
}

/**
 * The one page header used by every signed-in page: brand-gradient icon chip,
 * display-face title, muted description, actions on the right.
 */
export function PageHeader({ icon, title, description, actions, className }: PageHeaderProps) {
  return (
    <header
      className={cn(
        'flex flex-col gap-5 border-b border-border/60 pb-7 md:flex-row md:items-end md:justify-between',
        className
      )}
    >
      <div className="flex items-start gap-4">
        {icon && (
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-gradient text-white shadow-glow [&_svg]:h-5 [&_svg]:w-5">
            {icon}
          </div>
        )}
        <div>
          <h1 className="font-display text-[1.9rem] font-bold leading-tight tracking-tight text-foreground">{title}</h1>
          {description && <p className="mt-1 max-w-2xl text-[15px] text-muted-foreground">{description}</p>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2.5">{actions}</div>}
    </header>
  )
}

/** Small status pill used in page headers ("Operational", "Degraded"). */
export function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-card px-3 py-1.5 text-sm font-medium text-muted-foreground shadow-xs">
      <span className="relative flex h-2 w-2">
        <span className={cn('absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', ok ? 'bg-success' : 'bg-warning')} />
        <span className={cn('relative inline-flex h-2 w-2 rounded-full', ok ? 'bg-success' : 'bg-warning')} />
      </span>
      {label}
    </span>
  )
}
