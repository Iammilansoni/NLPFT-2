'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/contexts/sidebar-context'
import { Sidebar } from '@/components/sidebar'
import { SystemLogsSidebar } from '@/components/system-logs-sidebar'

interface CommandCenterLayoutProps {
    children: React.ReactNode
}

/**
 * Command Center Layout
 * Three-column architecture for Fortune 500 enterprise interface:
 * - Left: Navigation rail (48px collapsed, 240px expanded)
 * - Center: Fluid central canvas
 * - Right: Activity & Audit sidebar (320px, collapsible)
 */
export function CommandCenterLayout({ children }: CommandCenterLayoutProps) {
    const { isCollapsed, isSystemLogsOpen } = useSidebar()

    return (
        <div className="min-h-screen bg-background">
            {/* Left Navigation Rail */}
            <Sidebar />

            {/* Main Content Area */}
            <div
                className={cn(
                    'min-h-screen transition-all duration-200 ease-out',
                    // Left padding for sidebar
                    isCollapsed ? 'lg:pl-[48px]' : 'lg:pl-[240px]',
                    // Right padding for activity sidebar
                    isSystemLogsOpen ? 'lg:pr-[320px]' : 'lg:pr-0'
                )}
            >
                {/* Central Canvas */}
                <main
                    id="main-content"
                    className="min-h-screen"
                >
                    {children}
                </main>
            </div>

            {/* Right Activity & Audit Sidebar */}
            <SystemLogsSidebar />
        </div>
    )
}

export default CommandCenterLayout
