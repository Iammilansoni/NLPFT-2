'use client'

import { ReactNode } from 'react'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

export default function StatusLayout({ children }: { children: ReactNode }) {
  return <ProtectedRoute>{children}</ProtectedRoute>
}
