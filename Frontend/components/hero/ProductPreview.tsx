'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Database, Cpu, CheckCircle2, Play, Loader2, FileJson } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * ProductPreview - Interactive demo of the NLPForge pipeline
 * 
 * Features:
 * - Typewriter animation for placeholder text
 * - Editable query input (stops animation on focus/type)
 * - Animated demo flow on "Run Test Suite" click
 * - Shows the full pipeline: Query → Embedding → Search → Match → Result
 */

// Example queries for typewriter and demo - Telecom & Defense domains
const EXAMPLE_QUERIES = [
    {
        query: 'Configure 5G NR cell with frequency band n78 and 100MHz bandwidth',
        endpoint: '/api/v1/network/cells',
        method: 'POST',
        body: '{\n  "cell_type": "5G_NR",\n  "band": "n78",\n  "bandwidth_mhz": 100\n}'
    },
    {
        query: 'Get satellite link status for ground station GS-ALPHA',
        endpoint: '/api/v1/satcom/links/GS-ALPHA',
        method: 'GET',
        body: '// No request body'
    },
    {
        query: 'Update RF power level for radar system XBAND-01 to 500W',
        endpoint: '/api/v1/defense/radar/XBAND-01',
        method: 'PUT',
        body: '{\n  "radar_id": "XBAND-01",\n  "power_watts": 500\n}'
    },
    {
        query: 'Terminate inactive spectrum allocations older than 24 hours',
        endpoint: '/api/v1/spectrum/cleanup',
        method: 'DELETE',
        body: '{\n  "inactive_hours": 24,\n  "confirm": true\n}'
    },
];

type DemoPhase = 'idle' | 'embedding' | 'searching' | 'reranking' | 'resolving' | 'complete';

export function ProductPreview() {
    const [query, setQuery] = useState('');
    const [isUserTyping, setIsUserTyping] = useState(false);
    const [typewriterText, setTypewriterText] = useState('');
    const [phase, setPhase] = useState<DemoPhase>('idle');
    const [currentExample, setCurrentExample] = useState(EXAMPLE_QUERIES[0]);
    const [confidence, setConfidence] = useState(98.2);
    const inputRef = useRef<HTMLInputElement>(null);

    // Typewriter effect - cycles through examples
    useEffect(() => {
        if (isUserTyping || phase !== 'idle') return;

        let exampleIndex = 0;
        let charIndex = 0;
        let isDeleting = false;
        let timeoutId: NodeJS.Timeout;

        const typeWriter = () => {
            const currentQuery = EXAMPLE_QUERIES[exampleIndex].query;

            if (!isDeleting) {
                // Typing forward
                setTypewriterText(currentQuery.slice(0, charIndex + 1));
                charIndex++;

                if (charIndex === currentQuery.length) {
                    // Pause at end before deleting
                    timeoutId = setTimeout(() => {
                        isDeleting = true;
                        typeWriter();
                    }, 2000);
                    return;
                }
            } else {
                // Deleting
                setTypewriterText(currentQuery.slice(0, charIndex - 1));
                charIndex--;

                if (charIndex === 0) {
                    isDeleting = false;
                    exampleIndex = (exampleIndex + 1) % EXAMPLE_QUERIES.length;
                }
            }

            // Typing speed: faster for deleting
            const speed = isDeleting ? 30 : 50;
            timeoutId = setTimeout(typeWriter, speed);
        };

        timeoutId = setTimeout(typeWriter, 500);

        return () => clearTimeout(timeoutId);
    }, [isUserTyping, phase]);

    // Handle input focus - stop typewriter and use current typewriter text
    const handleFocus = useCallback(() => {
        if (!isUserTyping) {
            setQuery(typewriterText);
            setIsUserTyping(true);
        }
    }, [isUserTyping, typewriterText]);

    // Handle input blur - start timer to resume typewriter
    const handleBlur = useCallback(() => {
        // After 5 seconds of no interaction, resume typewriter
        const timeoutId = setTimeout(() => {
            setIsUserTyping(false);
            setQuery('');
        }, 5000);

        // Store timeout ID to clear if user refocuses
        (inputRef.current as any)?._blurTimeoutId && clearTimeout((inputRef.current as any)._blurTimeoutId);
        if (inputRef.current) {
            (inputRef.current as any)._blurTimeoutId = timeoutId;
        }
    }, []);

    // Handle input change
    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(e.target.value);
        if (!isUserTyping) {
            setIsUserTyping(true);
        }
        // Clear any pending blur timeout since user is actively typing
        if ((inputRef.current as any)?._blurTimeoutId) {
            clearTimeout((inputRef.current as any)._blurTimeoutId);
        }
    }, [isUserTyping]);

    // Run the demo animation
    const runDemo = useCallback(() => {
        if (phase !== 'idle') return;

        const queryToUse = isUserTyping ? query : typewriterText;
        if (!queryToUse.trim()) return;

        // Pick a matching example based on query keywords
        const matchedExample = EXAMPLE_QUERIES.find(e =>
            queryToUse.toLowerCase().includes('order') ? e.endpoint.includes('orders') :
                queryToUse.toLowerCase().includes('user') ? e.endpoint.includes('users') :
                    queryToUse.toLowerCase().includes('inventory') ? e.endpoint.includes('inventory') :
                        queryToUse.toLowerCase().includes('session') ? e.endpoint.includes('sessions') :
                            true
        ) || EXAMPLE_QUERIES[0];

        setCurrentExample(matchedExample);
        setConfidence(Math.round((90 + Math.random() * 9.5) * 10) / 10);

        // Phase 1: Embedding
        setPhase('embedding');

        setTimeout(() => {
            // Phase 2: Vector Search
            setPhase('searching');
            setTimeout(() => {
                // Phase 3: Re-ranking
                setPhase('reranking');
                setTimeout(() => {
                    // Phase 4: Resolve API
                    setPhase('resolving');
                    setTimeout(() => {
                        // Complete
                        setPhase('complete');
                        setTimeout(() => {
                            setPhase('idle');
                        }, 3000);
                    }, 500);
                }, 500);
            }, 600);
        }, 600);
    }, [phase, query, typewriterText, isUserTyping]);

    // Display text: user's query or typewriter animation
    const displayText = isUserTyping ? query : typewriterText;

    return (
        <div className="relative w-full max-w-lg mx-auto">
            {/* Main Card */}
            <div className="relative bg-card border border-border rounded-xl shadow-lg overflow-hidden">
                {/* Header Bar */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/30">
                    <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-red-400" />
                        <div className="w-3 h-3 rounded-full bg-amber-400" />
                        <div className="w-3 h-3 rounded-full bg-green-400" />
                    </div>
                    <span className="text-xs font-medium text-muted-foreground ml-2">
                        NLPForge Dashboard
                    </span>
                    {phase !== 'idle' && phase !== 'complete' && (
                        <span className="ml-auto flex items-center gap-1.5 text-xs text-primary">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Processing...
                        </span>
                    )}
                    {phase === 'complete' && (
                        <span className="ml-auto flex items-center gap-1.5 text-xs text-green-500">
                            <CheckCircle2 className="w-3 h-3" />
                            Match found!
                        </span>
                    )}
                </div>

                {/* Content */}
                <div className="p-4 space-y-4">
                    {/* Query Input with Typewriter */}
                    <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Natural Language Query
                        </label>
                        <div className="relative flex items-center gap-2 bg-muted/50 border border-border rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-primary/50 focus-within:ring-offset-1 focus-within:ring-offset-background transition-all">
                            <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />

                            {/* Show typewriter text when not focused */}
                            {!isUserTyping && (
                                <span className="absolute left-10 text-sm text-foreground pointer-events-none">
                                    {typewriterText}
                                    <span className="animate-pulse text-primary">|</span>
                                </span>
                            )}

                            <input
                                ref={inputRef}
                                type="text"
                                value={query}
                                onChange={handleChange}
                                onFocus={handleFocus}
                                onBlur={handleBlur}
                                placeholder={isUserTyping ? "Type your API request..." : ""}
                                className={cn(
                                    "flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none",
                                    !isUserTyping && "text-transparent caret-transparent"
                                )}
                                disabled={phase !== 'idle'}
                            />
                        </div>
                        {!isUserTyping && (
                            <p className="text-[10px] text-muted-foreground">
                                Click to type your own query
                            </p>
                        )}
                    </div>

                    {/* Pipeline Steps - Actual Backend Flow (4 steps) */}
                    <div className="grid grid-cols-4 gap-1.5">
                        <PipelineCard
                            icon={<Cpu className="w-4 h-4" />}
                            label="Embed"
                            status="768D vector"
                            isActive={phase === 'embedding'}
                            isComplete={['searching', 'reranking', 'resolving', 'complete'].includes(phase)}
                        />
                        <PipelineCard
                            icon={<Database className="w-4 h-4" />}
                            label="Search"
                            status="Redis KNN"
                            isActive={phase === 'searching'}
                            isComplete={['reranking', 'resolving', 'complete'].includes(phase)}
                        />
                        <PipelineCard
                            icon={<Search className="w-4 h-4" />}
                            label="Re-rank"
                            status="Top-K score"
                            isActive={phase === 'reranking'}
                            isComplete={['resolving', 'complete'].includes(phase)}
                        />
                        <PipelineCard
                            icon={<FileJson className="w-4 h-4" />}
                            label="Resolve"
                            status="API match"
                            isActive={phase === 'resolving'}
                            isComplete={phase === 'complete'}
                        />
                    </div>

                    {/* Results Preview */}
                    <div
                        className={cn(
                            "space-y-2 transition-all duration-300",
                            phase === 'complete' ? "opacity-100 translate-y-0" : "opacity-60"
                        )}
                    >
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                                Matched API Template
                            </span>
                            <span
                                className={cn(
                                    "inline-flex items-center gap-1 text-xs font-medium transition-all duration-300",
                                    phase === 'complete' ? "text-green-500 scale-105" : "text-muted-foreground"
                                )}
                            >
                                <CheckCircle2 className={cn(
                                    "w-3 h-3 transition-transform duration-300",
                                    phase === 'complete' && "animate-bounce"
                                )} />
                                {confidence}% confidence
                            </span>
                        </div>

                        <div className={cn(
                            "bg-muted/30 border border-border rounded-lg p-3 font-mono text-xs transition-all duration-500",
                            phase === 'complete' && "border-green-500/30 bg-green-500/5"
                        )}>
                            <div className="flex items-center gap-2 mb-2">
                                <span className={cn(
                                    "px-1.5 py-0.5 rounded text-[10px] font-semibold",
                                    currentExample.method === 'GET' && "bg-blue-500/20 text-blue-600 dark:text-blue-400",
                                    currentExample.method === 'POST' && "bg-green-500/20 text-green-600 dark:text-green-400",
                                    currentExample.method === 'PUT' && "bg-amber-500/20 text-amber-600 dark:text-amber-400",
                                    currentExample.method === 'DELETE' && "bg-red-500/20 text-red-600 dark:text-red-400"
                                )}>
                                    {currentExample.method}
                                </span>
                                <span className="text-muted-foreground">{currentExample.endpoint}</span>
                            </div>
                            <pre className="text-muted-foreground overflow-hidden whitespace-pre-wrap">
                                {currentExample.body}
                            </pre>
                        </div>
                    </div>

                    {/* Action Button */}
                    <button
                        onClick={runDemo}
                        disabled={phase !== 'idle' || (!query.trim() && !typewriterText.trim())}
                        className={cn(
                            "w-full flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition-all duration-200",
                            phase === 'idle' && (query.trim() || typewriterText.trim())
                                ? "bg-primary text-primary-foreground hover:bg-primary/90 cursor-pointer"
                                : "bg-muted text-muted-foreground cursor-not-allowed",
                            phase === 'complete' && "bg-green-600 text-white"
                        )}
                    >
                        {phase === 'idle' && (
                            <>
                                <Play className="w-4 h-4" />
                                Run Test Suite
                            </>
                        )}
                        {phase === 'embedding' && (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Generating embedding...
                            </>
                        )}
                        {phase === 'searching' && (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Searching Redis...
                            </>
                        )}
                        {phase === 'reranking' && (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Re-ranking results...
                            </>
                        )}
                        {phase === 'resolving' && (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Resolving API...
                            </>
                        )}
                        {phase === 'complete' && (
                            <>
                                <CheckCircle2 className="w-4 h-4" />
                                Test case generated!
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Decorative Elements */}
            <div className="absolute -z-10 top-4 -right-4 w-full h-full bg-primary/5 rounded-xl" />
            <div className="absolute -z-20 top-8 -right-8 w-full h-full bg-primary/3 rounded-xl" />
        </div>
    );
}

function PipelineCard({
    icon,
    label,
    status,
    isActive,
    isComplete,
}: {
    icon: React.ReactNode;
    label: string;
    status: string;
    isActive?: boolean;
    isComplete?: boolean;
}) {
    return (
        <div
            className={cn(
                "bg-muted/30 border rounded-lg p-2.5 text-center transition-all duration-300",
                isActive && "border-primary bg-primary/10 scale-105 shadow-md",
                isComplete && "border-green-500/50 bg-green-500/10",
                !isActive && !isComplete && "border-border"
            )}
        >
            <div className={cn(
                "flex items-center justify-center mb-1.5 transition-colors duration-300",
                isActive && "text-primary",
                isComplete && "text-green-500",
                !isActive && !isComplete && "text-muted-foreground"
            )}>
                {isActive ? <Loader2 className="w-4 h-4 animate-spin" /> : icon}
            </div>
            <p className={cn(
                "text-xs font-medium mb-0.5 transition-colors duration-300",
                isActive && "text-primary",
                isComplete && "text-green-600 dark:text-green-400",
                !isActive && !isComplete && "text-foreground"
            )}>
                {label}
            </p>
            <p className={cn(
                "text-[10px] font-medium transition-colors duration-300",
                isActive && "text-primary/80",
                isComplete && "text-green-500",
                !isActive && !isComplete && "text-muted-foreground"
            )}>
                {isComplete ? '✓ Done' : status}
            </p>
        </div>
    );
}

export default ProductPreview;
