'use client'

import { usePathname } from 'next/navigation'
import { Navigation } from './navigation'
import { LandingNav } from './landing/LandingNav'

export function ConditionalNav() {
  const pathname = usePathname()
  
  // Landing pages and marketing pages use horizontal navigation
  const landingPages = ['/', '/pricing', '/about', '/contact', '/docs', '/changelog', '/product', '/getting-started', '/privacy', '/terms', '/status', '/footer-demo']
  const isLandingPage = landingPages.includes(pathname) || pathname.startsWith('/blog') || pathname.startsWith('/product') || pathname.startsWith('/getting-started')
  
  if (isLandingPage) {
    return <LandingNav />
  }
  
  // Show sidebar navigation on all app pages (dashboard, runs, search, etc.)
  return <Navigation />
}
