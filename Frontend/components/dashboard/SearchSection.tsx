'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, AlertTriangle, SendHorizontal, Cpu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// Model interface for props
interface EmbeddingModelInfo {
    model_id: string
    label?: string // Optional, will fallback to model_id
    dimension?: number
}

// Default models while loading or if API fails
const DEFAULT_MODELS: EmbeddingModelInfo[] = [
    { model_id: 'nomic-embed-text', label: 'Nomic Embed Text', dimension: 768 },
]

const getEmbeddingModelInfo = (model: string, models: EmbeddingModelInfo[]) =>
    models.find(m => m.model_id === model) || { model_id: model, label: model }

const areModelsCompatible = (a: string, b: string) =>
    a === b || (a.includes('nomic') && b.includes('nomic'))

interface SearchSectionProps {
    query: string
    setQuery: (q: string) => void
    model: string
    setModel: (m: string) => void
    onSearch: () => void
    isSearching: boolean
    settingsModel: string | null
    models?: EmbeddingModelInfo[] // Dynamic models from backend
}

export function SearchSection({
    query,
    setQuery,
    model,
    setModel,
    onSearch,
    isSearching,
    settingsModel,
    models = DEFAULT_MODELS
}: SearchSectionProps) {
    const [isFocused, setIsFocused] = useState(false)
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
        if (!textareaRef.current) return
        textareaRef.current.style.height = 'auto'
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }, [query])

    const modelMismatch =
        settingsModel && model !== settingsModel && !areModelsCompatible(model, settingsModel)

    const quickPrompts = [
        'Create user account',
        'Authenticate with OAuth',
        'Get payment history',
        'Update profile'
    ]

    return (
        <div className="relative w-full max-w-3xl mx-auto space-y-6 px-4 sm:px-0">
            {/* PROFESSIONAL LIGHTING LAYER */}
            <div
                className={cn(
                    'absolute inset-0 -z-10 rounded-[2.5rem]',
                    'bg-[radial-gradient(1200px_300px_at_50%_-40%,hsl(var(--foreground)/0.08),transparent_70%)]',
                    'dark:bg-[radial-gradient(1200px_300px_at_50%_-40%,hsl(var(--foreground)/0.12),transparent_70%)]'
                )}
            />

            {/* Search Container */}
            <div
                className={cn(
                    'relative flex flex-col w-full rounded-[2rem] overflow-hidden',
                    'transition-all duration-300 ease-out',
                    'bg-muted/40 backdrop-blur-md',
                    'border border-border/40',
                    isFocused
                        ? 'bg-background shadow-xl shadow-black/10 dark:shadow-black/40'
                        : 'hover:shadow-md'
                )}
            >
                {/* Input */}
                <div className="flex w-full min-h-[56px] pl-6 pr-4 py-3">
                    <textarea
                        ref={textareaRef}
                        rows={1}
                        value={query}
                        placeholder="Ask about your API semantics..."
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                onSearch()
                            }
                        }}
                        className={cn(
                            'w-full bg-transparent resize-none overflow-hidden',
                            'text-lg font-medium leading-relaxed',
                            'text-foreground placeholder:text-muted-foreground/50',
                            'border-none outline-none',
                            'focus:outline-none focus:ring-0 focus-visible:ring-0'
                        )}
                    />
                </div>

                {/* Bottom Bar */}
                <div className="flex items-center justify-between px-4 pb-3 pt-1">
                    {/* Model Selector */}
                    <div className="relative">
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-muted-foreground border border-transparent hover:text-foreground hover:bg-muted/70 hover:border-border/60 hover:scale-105 transition-all duration-200 cursor-pointer">
                            <Cpu className="w-3.5 h-3.5 transition-transform group-hover:rotate-12" />
                            <span>{getEmbeddingModelInfo(model, models).label || getEmbeddingModelInfo(model, models).model_id}</span>
                            <ChevronDown className="w-3 h-3 opacity-50 transition-opacity hover:opacity-100" />
                        </div>


                        <select
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            className="absolute inset-0 opacity-0 cursor-pointer"
                        >
                            {models.map(m => (
                                <option key={m.model_id} value={m.model_id}>
                                    {m.label || m.model_id} {m.dimension ? `(${m.dimension}D)` : ''}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Send Button */}
                    <Button
                        size="icon"
                        onClick={onSearch}
                        disabled={!query.trim() || isSearching}
                        className={cn(
                            'h-10 w-10 rounded-full transition-all',
                            query.trim()
                                ? 'bg-foreground text-background hover:bg-foreground/90'
                                : 'bg-transparent text-muted-foreground hover:bg-muted'
                        )}
                    >
                        {isSearching ? (
                            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <SendHorizontal className="w-5 h-5 ml-0.5" />
                        )}
                    </Button>
                </div>
            </div>

            {/* Warning */}
            {modelMismatch && (
                <div className="flex items-center gap-2 px-4 py-2 text-xs text-amber-600 bg-amber-50/50 rounded-lg">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Model mismatch detected
                </div>
            )}

            {/* Quick Prompts */}
            {!query && !isSearching && (
                <div className="flex flex-wrap justify-center gap-2">
                    {quickPrompts.map(text => (
                        <button
                            key={text}
                            onClick={() => {
                                setQuery(text)
                                setTimeout(() => textareaRef.current?.focus(), 10)
                            }}
                            className="px-4 py-1.5 text-sm font-medium bg-muted/20 text-muted-foreground rounded-full hover:bg-muted/40 hover:text-foreground transition"
                        >
                            {text}
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}
