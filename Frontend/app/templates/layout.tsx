'use client'

import { ReactNode } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Sidebar } from '@/components/sidebar'
import { LayoutContent } from '@/components/layout-content'
import { MobileNav } from '@/components/MobileNav'

export default function TemplatesLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="relative min-h-screen bg-background">
        <Sidebar />
        <LayoutContent>{children}</LayoutContent>
        <MobileNav />
      </div>
    </ProtectedRoute>
  )
}
