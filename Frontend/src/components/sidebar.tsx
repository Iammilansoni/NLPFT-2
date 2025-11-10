'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  PlayCircle,
  Search,
  FileCode,
  Database,
  Settings,
  Plus,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Menu,
  X,
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { useSidebar } from '@/contexts/sidebar-context'
import { HealthIndicator } from '@/components/health-indicator'

const navigation = [
  { name: 'Home', href: '/', icon: Sparkles },
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Runs', href: '/runs', icon: PlayCircle },
  { name: 'Search', href: '/search', icon: Search },
  { name: 'Templates', href: '/templates', icon: FileCode },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const { isCollapsed, setIsCollapsed } = useSidebar()
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  const isExpanded = !isCollapsed

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          size="icon"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="h-12 w-12 rounded-xl shadow-lg"
        >
          {isMobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </Button>
      </div>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsMobileOpen(false)}
            className="lg:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isExpanded ? 256 : 80,
          x: isMobileOpen ? 0 : 0,
        }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className={cn(
          'fixed inset-y-0 left-0 flex flex-col border-r bg-card/50 backdrop-blur-sm z-40 overflow-x-hidden',
          isMobileOpen ? 'flex' : 'hidden lg:flex'
        )}
      >
      {/* Logo / Brand */}
      <div className="flex flex-col border-b">
        <div className="flex h-16 items-center px-4">
          <Link href="/dashboard" className="flex items-center gap-3 overflow-hidden">
            <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold shadow-lg">
              <Sparkles className="h-5 w-5" />
            </div>
            <AnimatePresence>
              {isExpanded && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2 }}
                  className="font-bold text-xl whitespace-nowrap"
                >
                  NLPForge
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
        </div>
        
        {/* Health Indicator */}
        {isExpanded && (
          <div className="px-3 pb-3">
            <HealthIndicator />
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3 overflow-y-auto overflow-x-hidden">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/')

          return (
            <Link key={item.name} href={item.href} onClick={() => setIsMobileOpen(false)}>
              <motion.div
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  'group relative flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary/10 text-primary shadow-sm'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                {/* Active indicator */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 h-8 w-1 rounded-r-full bg-primary"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}

                <div
                  className={cn(
                    'flex-shrink-0 h-9 w-9 rounded-lg flex items-center justify-center transition-colors',
                    isActive
                      ? 'bg-primary/15 text-primary'
                      : 'bg-muted/50 text-muted-foreground group-hover:bg-muted group-hover:text-foreground'
                  )}
                >
                  <Icon className="h-5 w-5" />
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.2 }}
                      className="whitespace-nowrap"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </AnimatePresence>

                {/* Tooltip for collapsed state */}
                {!isExpanded && (
                  <div className="absolute left-full ml-2 px-3 py-2 bg-popover text-popover-foreground text-sm rounded-lg shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                    {item.name}
                  </div>
                )}
              </motion.div>
            </Link>
          )
        })}
      </nav>

      {/* Bottom actions */}
      <div className="border-t p-3 space-y-2">
        {/* New Run Button */}
        <Link href="/run/new">
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              className={cn(
                'w-full justify-start gap-3 shadow-md',
                !isExpanded && 'px-0 justify-center'
              )}
              size={isExpanded ? 'default' : 'icon'}
            >
              <Plus className="h-5 w-5 flex-shrink-0" />
              <AnimatePresence>
                {isExpanded && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className="whitespace-nowrap"
                  >
                    New Run
                  </motion.span>
                )}
              </AnimatePresence>
            </Button>
          </motion.div>
        </Link>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size={isExpanded ? 'default' : 'icon'}
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className={cn(
            'w-full justify-start gap-3',
            !isExpanded && 'px-0 justify-center'
          )}
        >
          <div className="relative h-5 w-5 flex-shrink-0">
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute inset-0 h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </div>
          <AnimatePresence>
            {isExpanded && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="whitespace-nowrap"
              >
                Toggle theme
              </motion.span>
            )}
          </AnimatePresence>
        </Button>

        {/* Collapse Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </Button>
      </div>
      </motion.aside>
    </>
  )
}
