'use client'

import { useEffect, ReactNode, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
  children: ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [hasCookie, setHasCookie] = useState(false)

  // Check for cookie on mount
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const cookieExists = document.cookie.includes('nlpforge_access_token')
      setHasCookie(cookieExists)
      console.log('🛡️ ProtectedRoute check:', { 
        isAuthenticated, 
        isLoading, 
        hasCookie: cookieExists,
        pathname 
      })
    }
  }, [isAuthenticated, isLoading, pathname])

  useEffect(() => {
    // Only redirect if we're done loading AND no auth AND no cookie
    if (!isLoading && !isAuthenticated && !hasCookie) {
      console.log('❌ Not authenticated, redirecting to login')
      console.log('State:', { isLoading, isAuthenticated, hasCookie })
      
      // Add delay to prevent immediate redirect loop
      const timer = setTimeout(() => {
        router.push(`/auth/login?from=${encodeURIComponent(pathname)}`)
      }, 1000)
      
      return () => clearTimeout(timer)
    }
  }, [isAuthenticated, isLoading, hasCookie, router, pathname])

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // If authenticated OR has cookie, render content
  // (Cookie check allows rendering while AuthContext initializes)
  if (isAuthenticated || hasCookie) {
    console.log('✅ Rendering protected content')
    return <>{children}</>
  }

  // Not authenticated and no cookie - don't render (will redirect)
  return null
}
