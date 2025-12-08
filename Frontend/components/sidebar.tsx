'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
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
  Sparkles,
  Menu,
  X,
  User,
  LogOut,
  ChevronUp,
} from 'lucide-react'
import { useTheme } from '@/components/theme-provider'
import { useSidebar } from '@/contexts/sidebar-context'
import { useAuth } from '@/contexts/AuthContext'
import { HealthIndicator } from '@/components/health-indicator'
import { GlassCard } from '@/components/ui/GlassCard'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Templates', href: '/templates', icon: FileCode },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const { isCollapsed, setIsCollapsed } = useSidebar()
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
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          size="icon"
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="h-12 w-12 rounded-xl shadow-lg bg-background/80 backdrop-blur-md border border-border/50"
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
            className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isExpanded ? 280 : 90,
          x: isMobileOpen ? 0 : 0,
        }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className={cn(
          'fixed inset-y-0 left-0 flex flex-col z-40 overflow-x-hidden',
          'bg-background/60 backdrop-blur-xl border-r border-white/5',
          isMobileOpen ? 'flex' : 'hidden lg:flex'
        )}
      >
        {/* Logo / Brand */}
        <div className="flex flex-col p-6">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-3 overflow-hidden group" onClick={() => setIsMobileOpen(false)}>
              <div className="relative flex-shrink-0 h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold shadow-lg group-hover:shadow-primary/50 transition-shadow duration-500">
                <Sparkles className="h-5 w-5" />
                <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <AnimatePresence>
                {isExpanded && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                    className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70 whitespace-nowrap"
                  >
                    NLPForge
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
          </div>
          
          {/* Health Indicator */}
          {isExpanded && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-4"
            >
              <HealthIndicator />
            </motion.div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-2 px-4 py-2 overflow-y-auto overflow-x-hidden custom-scrollbar">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')

            return (
              <Link key={item.name} href={item.href} onClick={() => setIsMobileOpen(false)} title={item.name}>
                <div className="relative group">
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active-bg"
                      className="absolute inset-0 rounded-xl bg-primary/10 border border-primary/20"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                  
                  <motion.div
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      'relative flex items-center gap-4 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300',
                      isActive
                        ? 'text-primary'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                    )}
                  >
                    <div
                      className={cn(
                        'flex-shrink-0 h-5 w-5 transition-colors duration-300',
                        isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'
                      )}
                      title={item.name}
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
                  </motion.div>

                  {/* Tooltip for collapsed state */}
                  {!isExpanded && (
                    <div className="absolute left-full ml-4 top-1/2 -translate-y-1/2 px-3 py-2 bg-popover text-popover-foreground text-sm rounded-lg shadow-xl border border-border/50 opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-200 whitespace-nowrap z-50 translate-x-2 group-hover:translate-x-0">
                      {item.name}
                    </div>
                  )}
                </div>
              </Link>
            )
          })}
        </nav>

        {/* Bottom actions */}
        <div className="p-4 space-y-3">
          {/* User Account Section */}
          {isAuthenticated && user && (
            <div className="relative">
              <motion.button
                onClick={() => {
                  // Auto-expand sidebar if collapsed when clicking user profile
                  if (isCollapsed) {
                    setIsCollapsed(false)
                    // Small delay to let sidebar expand before opening dropdown
                    setTimeout(() => setIsAccountOpen(true), 150)
                  } else {
                    setIsAccountOpen(!isAccountOpen)
                  }
                }}
                className={cn(
                  'w-full flex items-center gap-3 p-2 rounded-xl transition-all duration-200',
                  'hover:bg-muted/50 group',
                  isAccountOpen && 'bg-muted/50'
                )}
              >
                {/* Avatar */}
                <div className="relative flex-shrink-0 h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-sm font-semibold shadow-md">
                  {getInitials(user.username || user.email)}
                  <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 bg-emerald-500 rounded-full border-2 border-background" />
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="flex-1 min-w-0 text-left"
                    >
                      <p className="text-sm font-medium truncate">{user.username || 'User'}</p>
                      <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {isExpanded && (
                  <motion.div
                    animate={{ rotate: isAccountOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  </motion.div>
                )}
              </motion.button>

              {/* Account Dropdown */}
              <AnimatePresence>
                {isAccountOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.96 }}
                    transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                    className={cn(
                      'absolute bottom-full left-0 right-0 mb-2 z-50',
                      'rounded-xl border border-border/50 bg-background/95 backdrop-blur-xl shadow-xl overflow-hidden'
                    )}
                  >
                    <div className="p-1.5 space-y-0.5">
                      {/* View Profile / Account */}
                      <Link 
                        href="/settings" 
                        onClick={() => {
                          setIsAccountOpen(false)
                          setIsMobileOpen(false)
                        }}
                      >
                        <motion.div
                          whileHover={{ x: 2 }}
                          className={cn(
                            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm',
                            'text-foreground hover:bg-muted/50 transition-colors cursor-pointer'
                          )}
                        >
                          <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                            <User className="h-4 w-4 text-primary" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium">My Account</p>
                            <p className="text-xs text-muted-foreground">View profile & settings</p>
                          </div>
                        </motion.div>
                      </Link>

                      {/* Divider */}
                      <div className="h-px bg-border/50 mx-2 my-1" />

                      {/* Logout */}
                      <motion.button
                        whileHover={{ x: 2 }}
                        onClick={handleLogout}
                        className={cn(
                          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm',
                          'text-red-600 dark:text-red-400 hover:bg-red-500/10 transition-colors'
                        )}
                      >
                        <div className="h-8 w-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                          <LogOut className="h-4 w-4" />
                        </div>
                        <div className="flex-1 text-left">
                          <p className="font-medium">Sign Out</p>
                          <p className="text-xs opacity-70">Log out of your account</p>
                        </div>
                      </motion.button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Collapsed state tooltip */}
              {!isExpanded && (
                <div className="absolute left-full ml-4 top-1/2 -translate-y-1/2 px-3 py-2 bg-popover text-popover-foreground text-sm rounded-lg shadow-xl border border-border/50 opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-200 whitespace-nowrap z-50 translate-x-2 group-hover:translate-x-0">
                  {user.username || user.email}
                </div>
              )}
            </div>
          )}

          <GlassCard className="p-1 space-y-1 bg-black/5 dark:bg-white/5 border-none">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size={isExpanded ? 'default' : 'icon'}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className={cn(
                'w-full justify-start gap-3 hover:bg-background/50',
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
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="whitespace-nowrap overflow-hidden"
                  >
                    Toggle theme
                  </motion.span>
                )}
              </AnimatePresence>
            </Button>

            {/* Collapse Toggle */}
            <Button
              variant="ghost"
              size={isExpanded ? 'default' : 'icon'}
              onClick={() => setIsCollapsed(!isCollapsed)}
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              className={cn(
                'w-full justify-start gap-3 hover:bg-background/50',
                !isExpanded && 'px-0 justify-center'
              )}
            >
              <div className="h-5 w-5 flex items-center justify-center">
                {isCollapsed ? (
                  <ChevronRight className="h-5 w-5" />
                ) : (
                  <ChevronLeft className="h-5 w-5" />
                )}
              </div>
              <AnimatePresence>
                {isExpanded && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="whitespace-nowrap overflow-hidden"
                  >
                    Collapse
                  </motion.span>
                )}
              </AnimatePresence>
            </Button>
          </GlassCard>
        </div>
      </motion.aside>
    </>
  )
}
