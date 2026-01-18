'use client'

import * as React from 'react'
import { HelpCircle, Book, Keyboard, Sparkles, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal'
import { QuickStartGuide } from './QuickStartGuide'
import { HelpDocumentation } from './HelpDocumentation'

interface HelpButtonProps {
  className?: string
  showRestartTour?: boolean
  onRestartTour?: () => void
}

/**
 * In-App Help Button
 * Provides quick access to documentation, keyboard shortcuts, and support resources
 */
export function HelpButton({ className, showRestartTour = true, onRestartTour }: HelpButtonProps) {
  const [showShortcuts, setShowShortcuts] = React.useState(false)
  const [showGuide, setShowGuide] = React.useState(false)
  const [showDocs, setShowDocs] = React.useState(false)

  const handleRestartTour = () => {
    // Clear tour completion from localStorage
    const TOUR_COMPLETED_KEY = 'nlpforge_tour_completed'
    localStorage.removeItem(TOUR_COMPLETED_KEY)
    
    if (onRestartTour) {
      onRestartTour()
    } else {
      // Force reload to restart tour
      window.location.reload()
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className={className}
            aria-label="Help and resources"
          >
            <HelpCircle className="h-5 w-5 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>Help & Resources</DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          {/* Quick Start Guide */}
          <DropdownMenuItem onClick={() => setShowGuide(true)} className="cursor-pointer">
            <Sparkles className="mr-2 h-4 w-4" />
            Quick Start Guide
          </DropdownMenuItem>
          
          {/* Full Documentation */}
          <DropdownMenuItem onClick={() => setShowDocs(true)} className="cursor-pointer">
            <Book className="mr-2 h-4 w-4" />
            Documentation
          </DropdownMenuItem>
          
          {/* Keyboard Shortcuts */}
          <DropdownMenuItem onClick={() => setShowShortcuts(true)} className="cursor-pointer">
            <Keyboard className="mr-2 h-4 w-4" />
            Keyboard Shortcuts
            <span className="ml-auto text-xs text-muted-foreground">?</span>
          </DropdownMenuItem>
          
          <DropdownMenuSeparator />
          
          {/* Restart Tour */}
          {showRestartTour && (
            <DropdownMenuItem onClick={handleRestartTour} className="cursor-pointer">
              <RotateCcw className="mr-2 h-4 w-4" />
              Restart Tour
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Modals */}
      <KeyboardShortcutsModal open={showShortcuts} onOpenChange={setShowShortcuts} />
      <QuickStartGuide open={showGuide} onOpenChange={setShowGuide} />
      <HelpDocumentation open={showDocs} onOpenChange={setShowDocs} />
    </>
  )
}

/**
 * Help Tooltip Component
 * Wraps any element with a helpful tooltip
 */
interface HelpTooltipProps {
  children: React.ReactNode
  content: string
  side?: 'top' | 'bottom' | 'left' | 'right'
}

export function HelpTooltip({ children, content, side = 'top' }: HelpTooltipProps) {
  return (
    <TooltipProvider>
      <Tooltip delayDuration={300}>
        <TooltipTrigger asChild>
          {children}
        </TooltipTrigger>
        <TooltipContent side={side} className="max-w-xs">
          <p className="text-sm">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * Info Icon with Tooltip
 * Shows a help icon that displays information on hover
 */
interface InfoTooltipProps {
  content: string
  className?: string
}

export function InfoTooltip({ content, className }: InfoTooltipProps) {
  return (
    <TooltipProvider>
      <Tooltip delayDuration={300}>
        <TooltipTrigger asChild>
          <HelpCircle className={`h-4 w-4 text-muted-foreground cursor-help ${className || ''}`} />
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <p className="text-sm">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export default HelpButton
