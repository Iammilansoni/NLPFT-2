import * as React from "react"

import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: 'default' | 'glass' | 'premium'
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: "border border-input bg-background focus-visible:ring-2 focus-visible:ring-ring",
      glass: "border border-white/10 bg-white/5 backdrop-blur-md focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:border-primary/30",
      premium: "border border-primary/20 bg-gradient-to-br from-background to-muted/30 shadow-lg shadow-primary/5 focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-primary/50 focus-visible:shadow-primary/20"
    }
    
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-xl px-4 py-3 text-sm text-foreground ring-offset-background",
          "placeholder:text-muted-foreground/60",
          "focus-visible:outline-none focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "transition-all duration-300 ease-out",
          "resize-none",
          variants[variant],
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
