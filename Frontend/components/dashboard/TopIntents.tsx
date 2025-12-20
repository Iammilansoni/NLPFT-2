'use client'

import { useState, useEffect } from 'react'

import { Target } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

interface TopIntentsProps {
    intents: Array<[string, number | unknown]>
    isLoading: boolean
}

export function TopIntents({ intents, isLoading }: TopIntentsProps) {
    // Animation state
    const [isVisible, setIsVisible] = useState(false)

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true)
                    observer.disconnect() // Only animate once
                }
            },
            { threshold: 0.1 } // Trigger when 10% visible
        )

        const element = document.getElementById('top-intents-container')
        if (element) {
            observer.observe(element)
        }

        return () => observer.disconnect()
    }, [isLoading]) // Re-run if loading state changes (content appears)

    if (isLoading) {
        return (
            <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full bg-muted/40" />
                ))}
            </div>
        )
    }

    if (intents.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground/50">
                <Target className="w-8 h-8 mb-2" />
                <p className="text-sm">No intents recorded yet</p>
            </div>
        )
    }

    const maxCount = intents[0][1] as number

    return (
        <div id="top-intents-container" className="space-y-4">
            {intents.map(([intent, count]) => {
                const value = count as number
                const percentage = Math.round((value / maxCount) * 100)

                return (
                    <div key={intent} className="group cursor-default">
                        <div className="flex items-center justify-between text-xs mb-1.5">
                            <span className="font-medium text-foreground/80 truncate max-w-[200px]" title={intent}>
                                {intent}
                            </span>
                            <span className="text-muted-foreground font-mono tabular-nums">
                                {value}
                            </span>
                        </div>
                        <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary/60 rounded-full transition-all duration-[1500ms] ease-out group-hover:bg-primary"
                                style={{
                                    width: isVisible ? `${percentage}%` : '0%',
                                }}
                            />
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
