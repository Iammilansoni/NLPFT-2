'use client'

import { usePathname } from 'next/navigation'
import { useSidebar } from '@/contexts/sidebar-context'
import { cn } from '@/lib/utils'

/**
 * Command Center Layout Content
 * Handles responsive spacing for three-column architecture
 */
export function LayoutContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed, isSystemLogsOpen } = useSidebar()
  const pathname = usePathname()

  // Landing pages and marketing pages don't need sidebar padding
  const landingPages = ['/', '/pricing', '/about', '/contact', '/docs', '/changelog']
  const isLandingPage = landingPages.includes(pathname) || pathname.startsWith('/blog')

  if (isLandingPage) {
    return <main id="main-content" className="min-h-screen">{children}</main>
  }

  // Command Center: Three-column layout spacing
  // Left: 48px collapsed, 240px expanded
  // Right: 320px when activity open, 0 when closed
  return (
    <main
      id="main-content"
      className={cn(
        "min-h-screen transition-all duration-200 ease-out",
        // Bottom padding for mobile bottom navigation bar (hidden on desktop)
        "pb-20 lg:pb-0",
        // Command Center left spacing
        isCollapsed ? "lg:pl-[48px]" : "lg:pl-[240px]",
        // Command Center right spacing for Activity panel
        isSystemLogsOpen ? "lg:pr-[320px]" : "lg:pr-0"
      )}
    >
      {children}
    </main>
  )
}
