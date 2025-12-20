'use client'

import { LayoutDashboard, FileCode, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'

interface DashboardHeaderProps {
    systemStatus: 'healthy' | 'degraded' | 'maintenance'
}

export function DashboardHeader({ systemStatus }: DashboardHeaderProps) {
    const router = useRouter()
    const isHealthy = systemStatus === 'healthy'

    return (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-4 border-b border-border/40">
            <div className="space-y-1">
                <div className="flex items-center gap-4 mb-1">
                    <h1 className="text-4xl font-bold tracking-tight text-foreground">
                        Dashboard
                    </h1>
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-background/50 border border-border/40 backdrop-blur-sm shadow-sm group">
                        <div className="relative flex h-3 w-3">
                            <span className={cn(
                                "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                                isHealthy ? "bg-emerald-400" : "bg-amber-400"
                            )}></span>
                            <span className={cn(
                                "relative inline-flex rounded-full h-3 w-3",
                                isHealthy ? "bg-emerald-500" : "bg-amber-500"
                            )}></span>
                        </div>
                        <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                            {isHealthy ? 'System Operational' : 'System Degraded'}
                        </span>
                    </div>
                </div>
                <p className="text-base text-muted-foreground/90 font-medium">
                    Overview of your semantic search performance and API coverage
                </p>
            </div>

            <div className="flex items-center gap-3">
                <Button variant="outline" size="lg" onClick={() => router.push('/templates')} className="text-sm font-semibold">
                    Templates
                </Button>
                <Button size="lg" onClick={() => router.push('/datasets')} className="text-sm font-bold">
                    Generate Dataset
                </Button>
            </div>
        </div>
    )
}
