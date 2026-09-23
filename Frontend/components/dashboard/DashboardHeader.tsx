'use client'

import Link from 'next/link'
import { LayoutDashboard, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageHeader, StatusPill } from '@/components/ui/page-header'

interface DashboardHeaderProps {
    systemStatus: 'healthy' | 'degraded' | 'maintenance'
}

export function DashboardHeader({ systemStatus }: DashboardHeaderProps) {
    const isHealthy = systemStatus === 'healthy'
    return (
        <PageHeader
            icon={<LayoutDashboard />}
            title="Dashboard"
            description="Route natural-language requests to your API catalogue."
            actions={
                <>
                    <StatusPill ok={isHealthy} label={isHealthy ? 'Operational' : 'Degraded'} />
                    <Button asChild variant="outline" className="rounded-full">
                        <Link href="/templates">Templates</Link>
                    </Button>
                    <Button asChild className="gap-1.5 rounded-full shadow-glow">
                        <Link href="/datasets">
                            <Plus className="h-4 w-4" /> Generate dataset
                        </Link>
                    </Button>
                </>
            }
        />
    )
}
