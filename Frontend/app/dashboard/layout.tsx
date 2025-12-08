/**
 * Dashboard Layout
 * Protected layout for dashboard pages
 */

'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

import { Sidebar } from '@/components/sidebar';
import { LayoutContent } from '@/components/layout-content';
import { SystemLogsSidebar } from '@/components/system-logs-sidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="relative min-h-screen bg-background">
        <Sidebar />
        <SystemLogsSidebar />
        <LayoutContent>{children}</LayoutContent>
      </div>
    </ProtectedRoute>
  );
}
