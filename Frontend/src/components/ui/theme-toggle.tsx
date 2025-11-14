'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useTheme } from 'next-themes'
import { Sun, Moon, Laptop2, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useCursor } from '@/components/ui/animated-cursor'


function useSafeCursor() {
  try {
    return useCursor()
  } catch {
    return { setVariant: () => {}, setText: () => {}, reset: () => {}, isEnabled: false }
  }
}

interface Option {
  value: 'light' | 'dark' | 'system'
  label: string
  icon: React.ReactElement
  description: string
}

const options: Option[] = [
  { value: 'light', label: 'Light', description: 'Bright interface', icon: <Sun className="h-4 w-4" aria-hidden="true" /> },
  { value: 'dark', label: 'Dark', description: 'Low light mode', icon: <Moon className="h-4 w-4" aria-hidden="true" /> },
  { value: 'system', label: 'System', description: 'Follow OS theme', icon: <Laptop2 className="h-4 w-4" aria-hidden="true" /> }
]


export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme, systemTheme } = useTheme()
  const { setVariant, setText, reset, isEnabled } = useSafeCursor()
  const [open, setOpen] = useState(false)
  const [mounted, setMounted] = useState(false)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const listRef = useRef<HTMLDivElement | null>(null)
  const activeValue = theme
  const resolvedTheme = theme === 'system' ? systemTheme : theme
  const effectiveTheme: 'light' | 'dark' | 'system' = (resolvedTheme === 'light' || resolvedTheme === 'dark')
    ? resolvedTheme
    : (activeValue === 'system' ? 'system' : 'light') 
  const [focusIndex, setFocusIndex] = useState(() => options.findIndex(o => o.value === activeValue) || 0)

  useEffect(() => { setMounted(true) }, [])

  const close = useCallback(() => {
    setOpen(false)
    triggerRef.current?.focus()
    reset()
  }, [reset])

  
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (!listRef.current || listRef.current.contains(e.target as Node) || triggerRef.current?.contains(e.target as Node)) return
      close()
    }
    window.addEventListener('mousedown', handler)
    return () => window.removeEventListener('mousedown', handler)
  }, [open, close])

  
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      if (e.key === 'ArrowDown') { e.preventDefault(); setFocusIndex(i => (i + 1) % options.length) }
      if (e.key === 'ArrowUp') { e.preventDefault(); setFocusIndex(i => (i - 1 + options.length) % options.length) }
      if (e.key === 'Home') { e.preventDefault(); setFocusIndex(0) }
      if (e.key === 'End') { e.preventDefault(); setFocusIndex(options.length - 1) }
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        const opt = options[focusIndex]
        if (opt) { setTheme(opt.value); close() }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, close, focusIndex, setTheme])

  
  const setAccentCursor = () => { if (isEnabled) { setVariant('accent'); setText('Theme'); } }
  const clearCursor = () => { if (isEnabled) reset() }

  if (!mounted) {
    return (
      <button
        aria-label="Loading theme toggle"
        className={cn('theme-toggle-trigger relative inline-flex h-9 w-9 items-center justify-center rounded-xl animate-pulse text-slate-500 dark:text-slate-400', className)}
        disabled
      >
        <Sun className="h-5 w-5 opacity-60" aria-hidden="true" />
      </button>
    )
  }

  return (
    <div className={cn('relative', className)} data-cursor="button" data-cursor-text="Theme">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Theme: ${resolvedTheme ?? 'unknown'}. Activate to choose theme.`}
        onClick={() => setOpen(o => !o)}
        onMouseEnter={setAccentCursor}
        onMouseLeave={clearCursor}
        className={cn(
          'theme-toggle-trigger group relative inline-flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-300 text-slate-700 dark:text-slate-200',
          open && 'scale-[1.02]'
        )}
      >
        <span className="sr-only">Select theme</span>
        <span className="relative flex items-center justify-center h-5 w-5">
          {effectiveTheme === 'light' && <Sun className="h-5 w-5 text-amber-500 transition-all" aria-hidden="true" />}
          {effectiveTheme === 'dark' && <Moon className="h-5 w-5 text-blue-300 transition-all" aria-hidden="true" />}
          {effectiveTheme === 'system' && <Laptop2 className="h-5 w-5 text-slate-500 dark:text-slate-300 transition-all" aria-hidden="true" />}
        </span>
        <span
          className="absolute -bottom-7 px-2 py-1 rounded-md text-[10px] font-semibold tracking-wide uppercase bg-black/70 text-white opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all pointer-events-none"
        >{resolvedTheme}</span>
      </button>

      <div
        ref={listRef}
        role="listbox"
        aria-label="Select theme"
        tabIndex={-1}
        className={cn(
          'absolute right-0 mt-2 w-52 origin-top-right rounded-xl border border-slate-200/60 dark:border-slate-700/60 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl shadow-xl shadow-black/5 dark:shadow-black/40 p-1.5 flex flex-col gap-0.5 transition-all duration-200 theme-transition',
          open ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 -translate-y-1 pointer-events-none'
        )}
      >
        {options.map((opt, i) => {
          const active = activeValue === opt.value
          const focused = i === focusIndex
          return (
            <button
              key={opt.value}
              role="option"
              aria-selected={active}
              data-focus={focused || undefined}
              className={cn(
                'flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-medium relative group text-left cursor-pointer select-none transition-colors',
                active ? 'bg-blue-500/15 text-blue-700 dark:text-blue-300 dark:bg-blue-400/10 ring-1 ring-blue-500/30' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-200/50 dark:hover:bg-slate-700/40',
                focused && !active && 'ring-1 ring-slate-400/40 dark:ring-slate-500/40'
              )}
              onClick={() => { setTheme(opt.value); close() }}
              onMouseEnter={() => { setFocusIndex(i); setAccentCursor(); setText(opt.label); }}
              onMouseLeave={() => { clearCursor(); setText('Theme'); }}
              data-cursor-text={opt.label}
              data-cursor-variant="accent"
            >
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/60 dark:bg-slate-800/70 shadow-inner">
                {opt.icon}
              </span>
              <span className="flex flex-col leading-tight">
                <span>{opt.label}</span>
                <span className="text-[10px] font-normal opacity-70">{opt.description}</span>
              </span>
              {active && <Check className="ml-auto h-4 w-4 text-blue-600 dark:text-blue-400" aria-hidden="true" />}
              <span className="pointer-events-none absolute inset-0 rounded-lg ring-2 ring-blue-500/0 group-hover:ring-blue-400/30 transition" />
            </button>
          )
        })}
      </div>
    </div>
  )
}
