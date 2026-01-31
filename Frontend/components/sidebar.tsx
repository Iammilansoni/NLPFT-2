'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  FileCode,
  Database,
  Settings,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  User,
  LogOut,
  Zap,
  Shield,
  HelpCircle,
} from 'lucide-react'
import { useTheme } from '@/components/theme-provider'
import { useSidebar } from '@/contexts/sidebar-context'
import { useAuth } from '@/contexts/AuthContext'
import { HelpButton } from '@/components/help/HelpButton'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Templates', href: '/templates', icon: FileCode },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
]

/**
 * Command Center Navigation Rail
 * Iconography-led sidebar: 48px collapsed, 240px expanded
 * Features: crisp borders, no shadows, accent active states
 */
export function Sidebar() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const { isCollapsed, setIsCollapsed, setIsSystemLogsOpen, isSystemLogsOpen } = useSidebar()
  const { user, logout, isAuthenticated } = useAuth()
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [isAccountOpen, setIsAccountOpen] = useState(false)

  const isExpanded = !isCollapsed

  const handleLogout = () => {
    logout()
    setIsMobileOpen(false)
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <>
      {/* Mobile Menu Button - Enhanced visibility */}
      <div className="lg:hidden fixed top-3 left-3 z-50 safe-area-inset">
        <Button
          size="icon"
          variant="outline"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="h-12 w-12 md:h-11 md:w-11 rounded-xl bg-background/95 backdrop-blur-md border-border/60 shadow-lg hover:shadow-xl transition-all active:scale-95"
          aria-label={isMobileOpen ? 'Close menu' : 'Open menu'}
        >
          {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          onClick={() => setIsMobileOpen(false)}
          className="lg:hidden fixed inset-0 bg-black/50 z-40 transition-opacity"
        />
      )}

      {/* Navigation Rail */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 flex flex-col z-40',
          'bg-card/95 backdrop-blur-md border-r border-border shadow-2xl lg:shadow-none lg:bg-card lg:backdrop-blur-none',
          'transition-all duration-300 ease-out',
          // Responsive widths: optimized for each breakpoint
          isMobileOpen 
            ? 'w-[85vw] max-w-[320px] sm:w-[300px] md:w-[280px]' 
            : isExpanded ? 'w-[240px]' : 'w-[56px] md:w-[48px]',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
          // Safe area support for notched devices
          'pt-safe-top pb-safe-bottom pl-safe-left'
        )}
      >
        {/* Logo / Brand */}
        <div className={cn(
          "flex items-center h-12 border-b border-border",
          isExpanded ? "px-4" : "px-2 justify-center"
        )}>
          <Link
            href="/"
            className="flex items-center gap-2 overflow-hidden"
            onClick={() => setIsMobileOpen(false)}
          >
            <div className="flex-shrink-0 h-7 w-7 rounded-sm bg-primary flex items-center justify-center">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <path
                  d="M12 2L21 7V17L12 22L3 17V7L12 2Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  fill="none"
                  className="text-primary-foreground"
                />
                <path
                  d="M12 6L17 9V15L12 18L7 15V9L12 6Z"
                  fill="currentColor"
                  className="text-primary-foreground"
                />
              </svg>
            </div>
            {isExpanded && (
              <div className="flex flex-col">
                <span className="font-bold text-base text-foreground whitespace-nowrap leading-tight">
                  NLPForge
                </span>
                <span className="text-[10px] text-muted-foreground tracking-wide">
                  API Testing
                </span>
              </div>
            )}
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-3 px-1.5 space-y-0.5 overflow-y-auto scrollbar-cc">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                title={!isExpanded ? item.name : undefined}
              >
                <div
                  className={cn(
                    'flex items-center gap-3 rounded-lg font-medium transition-colors',
                    isExpanded ? 'px-3 py-3 md:py-2.5 text-sm' : 'px-2 py-3 md:py-2 justify-center',
                    isActive
                      ? 'bg-primary/10 text-primary border-l-2 border-l-primary ml-0 pl-[10px]'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent active:bg-accent/80'
                  )}
                >
                  <Icon className={cn(
                    "flex-shrink-0",
                    isExpanded ? "h-4 w-4" : "h-5 w-5"
                  )} />
                  {isExpanded && (
                    <span className="whitespace-nowrap">{item.name}</span>
                  )}
                </div>
              </Link>
            )
          })}
        </nav>

        {/* Bottom Section */}
        <div className={cn(
          "border-t border-border",
          isExpanded ? "p-3 space-y-2" : "p-1.5 space-y-1"
        )}>
          {/* User Account Section */}
          {isAuthenticated && user && (
            <div className="relative">
              <button
                onClick={() => {
                  if (isCollapsed) {
                    setIsCollapsed(false)
                    setTimeout(() => setIsAccountOpen(true), 150)
                  } else {
                    setIsAccountOpen(!isAccountOpen)
                  }
                }}
                className={cn(
                  'w-full flex items-center gap-2 rounded-sm transition-colors',
                  isExpanded ? 'p-2' : 'p-1 justify-center',
                  'hover:bg-accent',
                  isAccountOpen && 'bg-accent'
                )}
                title={!isExpanded ? user.username || user.email : undefined}
              >
                {/* Avatar */}
                <div className={cn(
                  "flex-shrink-0 rounded-sm bg-primary flex items-center justify-center text-primary-foreground font-medium",
                  isExpanded ? "h-7 w-7 text-xs" : "h-6 w-6 text-[10px]"
                )}>
                  {getInitials(user.username || user.email)}
                </div>

                {isExpanded && (
                  <div className="flex-1 min-w-0 text-left">
                    <p className="text-sm font-medium truncate">{user.username || 'User'}</p>
                    <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                  </div>
                )}
              </button>

              {/* Account Dropdown */}
              {isAccountOpen && (
                <div className="absolute bottom-full left-0 right-0 mb-1 rounded-sm border border-border bg-card overflow-hidden">
                  <div className="p-1">
                    <Link
                      href="/settings"
                      onClick={() => {
                        setIsAccountOpen(false)
                        setIsMobileOpen(false)
                      }}
                    >
                      <div className="flex items-center gap-2 px-2 py-1.5 rounded-sm text-xs text-foreground hover:bg-accent transition-colors">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>My Account</span>
                      </div>
                    </Link>
                    <div className="h-px bg-border my-1" />
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-2 py-1.5 rounded-sm text-xs text-destructive hover:bg-destructive/10 transition-colors"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Help Button */}
          <div className={cn(
            'flex items-center rounded-sm transition-colors hover:bg-accent',
            isExpanded ? 'px-2 py-1.5' : 'p-1 justify-center'
          )}>
            <HelpButton className="!h-auto !w-auto p-0 hover:bg-transparent" />
            {isExpanded && <span className="text-xs text-muted-foreground ml-2">Help</span>}
          </div>

          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className={cn(
              'w-full flex items-center gap-2 rounded-sm transition-colors hover:bg-accent text-foreground',
              isExpanded ? 'px-2 py-1.5' : 'p-1 justify-center'
            )}
          >
            <div className={cn(
              "relative flex-shrink-0",
              isExpanded ? "h-4 w-4" : "h-5 w-5"
            )}>
              <Sun className="h-full w-full rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute inset-0 h-full w-full rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
            </div>
            {isExpanded && <span className="text-xs text-muted-foreground">Toggle theme</span>}
          </button>

          {/* Collapse Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={cn(
              'w-full hidden lg:flex items-center gap-2 rounded-sm transition-colors hover:bg-accent text-foreground',
              isExpanded ? 'px-2 py-1.5' : 'p-1 justify-center'
            )}
          >
            <div className={cn(
              "flex-shrink-0",
              isExpanded ? "h-4 w-4" : "h-5 w-5"
            )}>
              {isCollapsed ? (
                <ChevronRight className="h-full w-full" />
              ) : (
                <ChevronLeft className="h-full w-full" />
              )}
            </div>
            {isExpanded && <span className="text-xs text-muted-foreground">Collapse</span>}
          </button>

          {/* Version Footer */}
          {isExpanded && (
            <div className="pt-2 border-t border-border">
              <p className="text-[10px] text-muted-foreground text-center font-mono">
                v1.0.0
              </p>
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
