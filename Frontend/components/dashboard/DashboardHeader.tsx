'use client'

import { LayoutDashboard, Plus, ArrowRight } from 'lucide-react'
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
        <section className="relative overflow-hidden border-b border-border/40 -mx-6 md:-mx-8 px-6 md:px-8">
            {/* Background Decorations */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/5 rounded-full blur-3xl" />
                <div className="absolute top-20 -left-20 w-60 h-60 bg-blue-500/5 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-border to-transparent" />
            </div>

            <div className="relative py-10 lg:py-14">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/10">
                                <LayoutDashboard className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-3xl lg:text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                                    Dashboard
                                </h1>
                                <p className="text-muted-foreground mt-1">
                                    Your semantic search performance overview
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* System Status */}
                        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-background/60 border border-border/50 backdrop-blur-sm">
                            <div className="relative flex h-2.5 w-2.5">
                                <span className={cn(
                                    "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                                    isHealthy ? "bg-emerald-400" : "bg-amber-400"
                                )}></span>
                                <span className={cn(
                                    "relative inline-flex rounded-full h-2.5 w-2.5",
                                    isHealthy ? "bg-emerald-500" : "bg-amber-500"
                                )}></span>
                            </div>
                            <span className="text-sm font-medium text-muted-foreground">
                                {isHealthy ? 'Operational' : 'Degraded'}
                            </span>
                        </div>

                        <div className="h-8 w-px bg-border/60" />

                        <Button 
                            variant="outline" 
                            onClick={() => router.push('/templates')} 
                            className="h-10 gap-2 rounded-xl border-dashed"
                        >
                            Templates
                        </Button>
                        
                        <Button 
                            onClick={() => router.push('/datasets')} 
                            className="h-10 gap-2 rounded-xl shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all"
                        >
                            <Plus className="h-4 w-4" />
                            Generate Dataset
                        </Button>
                    </div>
                </div>
            </div>
        </section>
    )
}
