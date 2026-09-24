'use client'

import { useEffect, useRef, useState } from 'react'
import { SendHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SearchSectionProps {
    query: string
    setQuery: (q: string) => void
    onSearch: (q?: string) => void
    isSearching: boolean
    examples?: string[]
}

export function SearchSection({ query, setQuery, onSearch, isSearching, examples = [] }: SearchSectionProps) {
    const [isFocused, setIsFocused] = useState(false)
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
        if (!textareaRef.current) return
        textareaRef.current.style.height = 'auto'
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }, [query])

    return (
        <div className="relative w-full max-w-3xl mx-auto space-y-5 px-4 sm:px-0">
            <div
                className={cn(
                    'relative flex w-full items-end gap-2 rounded-[1.75rem] pl-6 pr-3 py-3',
                    'transition-all duration-300 ease-out bg-muted/40 backdrop-blur-md border border-border/40',
                    isFocused ? 'bg-background shadow-xl shadow-black/10 dark:shadow-black/40 border-border/60' : 'hover:shadow-md'
                )}
            >
                <textarea
                    ref={textareaRef}
                    rows={1}
                    value={query}
                    aria-label="Describe the API call you want"
                    placeholder="Describe the API call you want, e.g. refund order 8820…"
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault()
                            onSearch()
                        }
                    }}
                    className="w-full bg-transparent resize-none overflow-hidden py-2 text-lg font-medium leading-relaxed text-foreground placeholder:text-muted-foreground/50 border-none outline-none focus:ring-0"
                />
                <Button
                    size="icon"
                    aria-label="Route query"
                    onClick={() => onSearch()}
                    disabled={!query.trim() || isSearching}
                    className={cn(
                        'h-11 w-11 shrink-0 rounded-full transition-all',
                        query.trim() ? 'bg-foreground text-background hover:bg-foreground/90' : 'bg-transparent text-muted-foreground hover:bg-muted'
                    )}
                >
                    {isSearching ? (
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    ) : (
                        <SendHorizontal className="w-5 h-5 ml-0.5" />
                    )}
                </Button>
            </div>

            {examples.length > 0 && (
                <div className="flex flex-wrap justify-center gap-2">
                    {examples.map((text) => (
                        <button
                            key={text}
                            disabled={isSearching}
                            onClick={() => {
                                setQuery(text)
                                onSearch(text)
                            }}
                            className="px-3.5 py-1.5 text-sm bg-muted/30 text-muted-foreground rounded-full border border-border/40 hover:bg-muted/60 hover:text-foreground transition disabled:opacity-50"
                        >
                            {text}
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}
