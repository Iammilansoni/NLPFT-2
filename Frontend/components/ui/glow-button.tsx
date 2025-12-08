'use client'

import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

export interface GlowButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean
  variant?: 'default' | 'outline' | 'ghost'
}

export const GlowButton = forwardRef<HTMLButtonElement, GlowButtonProps>(
  ({ className, children, isLoading, variant = 'default', disabled, ...props }, ref) => {
    const baseStyles = 'rounded-xl px-5 h-11 font-semibold transition-all focus-glow active:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none'
    
    const variantStyles = {
      default: 'btn-gradient edge-glow text-white',
      outline: 'border-2 border-primary/50 hover:bg-primary/10 hover:border-primary hover:shadow-glow',
      ghost: 'hover:bg-primary/10 hover:text-primary',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          baseStyles,
          variantStyles[variant],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin inline" />
            {children}
          </>
        ) : (
          children
        )}
      </button>
    )
  }
)

GlowButton.displayName = 'GlowButton'
