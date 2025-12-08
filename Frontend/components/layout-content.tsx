'use client'

import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { useSidebar } from '@/contexts/sidebar-context'
import { cn } from '@/lib/utils'

export function LayoutContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar()
  const pathname = usePathname()
  
  // Landing pages and marketing pages don't need sidebar padding
  const landingPages = ['/', '/pricing', '/about', '/contact', '/docs', '/changelog']
  const isLandingPage = landingPages.includes(pathname) || pathname.startsWith('/blog')
  
  if (isLandingPage) {
    return <div className="min-h-screen">{children}</div>
  }

  // App pages with sidebar navigation - adjust padding based on collapsed state
  const { isSystemLogsOpen } = useSidebar()

  return (
    <motion.div
      animate={{
        paddingLeft: isCollapsed ? '80px' : '256px',
        paddingRight: isSystemLogsOpen ? '400px' : '0px',
      }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="min-h-screen pt-16"
    >
      {children}
    </motion.div>
  )
}
