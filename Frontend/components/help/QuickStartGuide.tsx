'use client'

import * as React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  X, 
  Sparkles, 
  FileCode, 
  Search, 
  Database, 
  ArrowRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog'

interface GuideStep {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  tip?: string
}

const GUIDE_STEPS: GuideStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to NLPForge!',
    description: 'NLPForge helps you create, manage, and test API templates using semantic search and natural language processing.',
    icon: <Sparkles className="h-8 w-8" />,
    tip: 'This guide will walk you through the key features in just a few steps.',
  },
  {
    id: 'templates',
    title: 'Create API Templates',
    description: 'Define your API endpoints with parameters, intent keywords, and descriptions. Templates are the foundation for semantic search and dataset generation.',
    icon: <FileCode className="h-8 w-8" />,
    tip: 'Start by navigating to Templates and clicking "New Template" to create your first API definition.',
  },
  {
    id: 'search',
    title: 'Semantic API Search',
    description: 'Use natural language to find the right API. Ask questions like "How do I create a user?" and NLPForge will match your intent to the best API.',
    icon: <Search className="h-8 w-8" />,
    tip: 'The dashboard features a powerful semantic search bar. Try typing what you want to accomplish!',
  },
  {
    id: 'datasets',
    title: 'Generate Test Datasets',
    description: 'Automatically generate test data for your approved templates. Export as JSON or CSV for integration with your test suites.',
    icon: <Database className="h-8 w-8" />,
    tip: "Once you've approved templates, head to Datasets to generate training data.",
  },
  {
    id: 'complete',
    title: "You're All Set!",
    description: "You now know the basics of NLPForge. Explore the dashboard, create templates, and start building smarter API integrations.",
    icon: <CheckCircle2 className="h-8 w-8 text-green-500" />,
    tip: 'Press ? at any time to view keyboard shortcuts. Need help? Click the help button in the sidebar.',
  },
]

interface QuickStartGuideProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function QuickStartGuide({ open, onOpenChange }: QuickStartGuideProps) {
  const [currentStep, setCurrentStep] = React.useState(0)
  const step = GUIDE_STEPS[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === GUIDE_STEPS.length - 1

  const handleNext = () => {
    if (isLastStep) {
      onOpenChange(false)
      setCurrentStep(0)
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handleBack = () => {
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const handleSkip = () => {
    onOpenChange(false)
    setCurrentStep(0)
  }

  // Reset step when modal closes
  React.useEffect(() => {
    if (!open) {
      const id = setTimeout(() => setCurrentStep(0), 300)
      return () => clearTimeout(id)
    }
  }, [open])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg p-0 overflow-hidden">
        {/* Progress bar */}
        <div className="h-1 bg-muted">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep + 1) / GUIDE_STEPS.length) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Content */}
        <div className="p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="space-y-6"
            >
              {/* Icon */}
              <div className="flex justify-center">
                <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                  {step.icon}
                </div>
              </div>

              {/* Title & Description */}
              <div className="text-center space-y-3">
                <h2 className="text-2xl font-bold tracking-tight text-foreground">
                  {step.title}
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>

              {/* Tip */}
              {step.tip && (
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                  <p className="text-sm text-primary font-medium">
                    💡 {step.tip}
                  </p>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-8 py-4 bg-muted/30 border-t">
          <div className="flex items-center gap-1">
            {GUIDE_STEPS.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentStep(idx)}
                className={`h-2 rounded-full transition-all ${
                  idx === currentStep
                    ? 'w-6 bg-primary'
                    : 'w-2 bg-muted-foreground/30 hover:bg-muted-foreground/50'
                }`}
                aria-label={`Go to step ${idx + 1}`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {!isFirstStep && (
              <Button variant="ghost" size="sm" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
            {isFirstStep && (
              <Button variant="ghost" size="sm" onClick={handleSkip} className="text-muted-foreground">
                Skip
              </Button>
            )}
            <Button size="sm" onClick={handleNext}>
              {isLastStep ? 'Get Started' : 'Next'}
              {!isLastStep && <ChevronRight className="h-4 w-4 ml-1" />}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default QuickStartGuide
