"use client"

import * as React from "react"
import { Search, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn, debounce } from "@/lib/utils"
import { Badge } from "./badge"

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  suggestions?: string[]
  onSuggestionClick?: (suggestion: string) => void
  debounceMs?: number
  className?: string
  autoFocus?: boolean
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search...",
  suggestions = [],
  onSuggestionClick,
  debounceMs = 300,
  className,
  autoFocus = false,
}: SearchInputProps) {
  const [localValue, setLocalValue] = React.useState(value)
  const [isFocused, setIsFocused] = React.useState(false)
  const [isMounted, setIsMounted] = React.useState(false)
  const inputRef = React.useRef<HTMLInputElement>(null)

  // Only enable client-side features after mount
  React.useEffect(() => {
    setIsMounted(true)
  }, [])

  // Debounced onChange
  const debouncedOnChange = React.useMemo(
    () => debounce((val: string) => onChange(val), debounceMs),
    [onChange, debounceMs]
  )

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setLocalValue(newValue)
    debouncedOnChange(newValue)
  }

  const handleClear = () => {
    setLocalValue("")
    onChange("")
    inputRef.current?.focus()
  }

  const handleSuggestionClick = (suggestion: string) => {
    setLocalValue(suggestion)
    onChange(suggestion)
    onSuggestionClick?.(suggestion)
    setIsFocused(false)
  }

  React.useEffect(() => {
    if (value !== localValue) {
      setLocalValue(value)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return (
    <div className={cn("relative w-full", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={localValue}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          placeholder={placeholder}
          autoFocus={isMounted && autoFocus}
          className={cn(
            "w-full h-11 pl-10 pr-10 rounded-lg border border-input bg-background",
            "text-sm placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            "transition-all duration-200",
            isFocused && "ring-2 ring-ring ring-offset-2"
          )}
        />
        <AnimatePresence>
          {localValue && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.15 }}
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Suggestions */}
      <AnimatePresence>
        {isFocused && suggestions.length > 0 && !localValue && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute z-50 w-full mt-2 p-3 bg-popover border border-border rounded-lg shadow-lg"
          >
            <p className="text-xs text-muted-foreground mb-2">Try searching:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, index) => (
                <motion.div
                  key={suggestion}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Badge
                    variant="outline"
                    className="cursor-pointer hover:bg-accent transition-colors"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </Badge>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
