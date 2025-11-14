"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Sparkles, ArrowRight, Brain } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface QueryInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit?: () => void
  placeholder?: string
  suggestions?: string[]
  className?: string
  isLoading?: boolean
  disabled?: boolean
}

export function QueryInput({
  value,
  onChange,
  onSubmit,
  placeholder = "Describe your API test in natural language...",
  suggestions = [
    "Login with username admin and password test123",
    "Create a new user account with email verification",
    "Update user profile with avatar upload",
    "Delete inactive users older than 90 days"
  ],
  className,
  isLoading,
  disabled
}: QueryInputProps) {
  const [isFocused, setIsFocused] = React.useState(false)
  const [showSuggestions, setShowSuggestions] = React.useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim() && onSubmit) {
      onSubmit()
      setShowSuggestions(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion)
    setShowSuggestions(false)
  }

  return (
    <div className={cn("relative w-full", className)}>
      <form onSubmit={handleSubmit}>
        <div className="relative">
          {/* Icon */}
          <div className="absolute left-4 top-1/2 -translate-y-1/2 z-10">
            {isLoading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Brain className="h-5 w-5 text-primary" />
              </motion.div>
            ) : (
              <Search className="h-5 w-5 text-muted-foreground" />
            )}
          </div>

          {/* Input */}
          <Input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => {
              setIsFocused(true)
              if (!value) setShowSuggestions(true)
            }}
            onBlur={() => {
              setIsFocused(false)
              setTimeout(() => setShowSuggestions(false), 200)
            }}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className={cn(
              "h-14 pl-12 pr-32 text-base transition-all duration-200",
              isFocused && "ring-2 ring-primary/20 border-primary"
            )}
            aria-label="Natural language query input"
          />

          {/* Submit Button */}
          <div className="absolute right-2 top-1/2 -translate-y-1/2">
            <Button
              type="submit"
              disabled={!value.trim() || disabled || isLoading}
              className="h-10 gap-2"
            >
              {isLoading ? (
                <>Processing...</>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Suggestions Dropdown */}
      <AnimatePresence>
        {showSuggestions && !value && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 w-full mt-2 bg-popover border rounded-lg shadow-lg overflow-hidden"
          >
            <div className="p-2">
              <p className="text-xs text-muted-foreground px-3 py-2 font-medium">
                Try these examples:
              </p>
              <div className="space-y-1">
                {suggestions.map((suggestion, index) => (
                  <motion.button
                    key={suggestion}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="w-full text-left px-3 py-2 rounded-md hover:bg-accent text-sm transition-colors"
                  >
                    {suggestion}
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Character count (optional) */}
      {value && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute -bottom-6 right-0 text-xs text-muted-foreground"
        >
          {value.length} characters
        </motion.div>
      )}
    </div>
  )
}
