'use client'

import { useState, useEffect, useCallback } from 'react'
import Joyride, { CallBackProps, STATUS, Step } from 'react-joyride'
import { useAuth } from '@/contexts/AuthContext'

// ============================================================================
// TOUR STEP DEFINITIONS
// ============================================================================

// Dashboard tour steps
const DASHBOARD_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="search"]',
    title: 'Semantic Search',
    content: 'Search your API endpoints using natural language. Type what you want to do and our AI finds the matching API.',
    placement: 'bottom',
    disableBeacon: true,
  },
  {
    target: '[data-tour="metrics"]',
    title: 'System Metrics',
    content: 'View key metrics including total embeddings, approved templates, and active intents at a glance.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="model-selector"]',
    title: 'Embedding Model',
    content: 'Select the AI model used for semantic search. Different models offer different accuracy and speed tradeoffs.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="search-results"]',
    title: 'Search Results',
    content: 'Results show matched APIs with confidence scores. Higher scores mean better semantic match to your query.',
    placement: 'top',
  },
]

// Templates tour steps
const TEMPLATES_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="template-list"]',
    title: 'API Templates',
    content: 'Browse and manage your API templates. Each template defines an API endpoint with its parameters and expected responses.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '[data-tour="template-search"]',
    title: 'Search & Filter',
    content: 'Filter templates by name, status, or method type. Use the search bar for quick lookup.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="create-template"]',
    title: 'Create Template',
    content: 'Click here to create a new API template with endpoint, HTTP method, parameters, and sample requests.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="template-status"]',
    title: 'Template Status',
    content: 'Templates progress through Draft → Review → Approved states. Only approved templates are used for semantic search.',
    placement: 'left',
  },
  {
    target: '[data-tour="template-actions"]',
    title: 'Quick Actions',
    content: 'Edit, duplicate, or delete templates. Use the toggle to enable/disable templates for search indexing.',
    placement: 'left',
  },
]

// Datasets tour steps
const DATASETS_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="dataset-list"]',
    title: 'Your Datasets',
    content: 'View all generated and uploaded datasets. Each dataset contains query-API mappings for training and testing.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '[data-tour="generate-dataset"]',
    title: 'AI Dataset Generation',
    content: 'Generate synthetic datasets using AI. Select a template and specify the number of examples to create.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="upload-dataset"]',
    title: 'Upload CSV',
    content: 'Import your own datasets from CSV files. The system will validate and process your data automatically.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="embed-dataset"]',
    title: 'Embed to Vector DB',
    content: 'Embed datasets to Redis vector database for semantic search. This creates searchable embeddings from your data.',
    placement: 'left',
  },
  {
    target: '[data-tour="dataset-stats"]',
    title: 'Dataset Statistics',
    content: 'View embedding status, row counts, and model information for each dataset.',
    placement: 'top',
  },
]

// Settings tour steps
const SETTINGS_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="embedding-settings"]',
    title: 'Embedding Configuration',
    content: 'Configure the default embedding model used across the platform. This affects search accuracy and performance.',
    placement: 'bottom',
    disableBeacon: true,
  },
  {
    target: '[data-tour="model-select"]',
    title: 'Select Model',
    content: 'Choose from available embedding models. Larger models are more accurate but slower. Changes apply to new embeddings.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="save-settings"]',
    title: 'Save Settings',
    content: 'Remember to save your changes. Settings are stored per-user and persist across sessions.',
    placement: 'top',
  },
]

// Query tour steps  
const QUERY_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="query-input"]',
    title: 'Natural Language Query',
    content: 'Enter your query in plain English. For example: "Create a new user account" or "Get product details by ID".',
    placement: 'bottom',
    disableBeacon: true,
  },
  {
    target: '[data-tour="query-submit"]',
    title: 'Execute Query',
    content: 'Click to find the best matching API. The system uses semantic search to understand your intent.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="query-results"]',
    title: 'Query Results',
    content: 'View matched APIs with confidence scores, endpoints, and request/response schemas.',
    placement: 'top',
  },
]

// Audit tour steps
const AUDIT_TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="audit-logs"]',
    title: 'Audit Logs',
    content: 'Track all system activities including template changes, dataset operations, and user actions.',
    placement: 'bottom',
    disableBeacon: true,
  },
  {
    target: '[data-tour="audit-filters"]',
    title: 'Filter Logs',
    content: 'Filter by action type, date range, or user. Useful for compliance and debugging.',
    placement: 'bottom',
  },
]

// Tour ID type
export type TourId = 'dashboard' | 'templates' | 'datasets' | 'settings' | 'query' | 'audit'

// Map tour IDs to their steps
const TOUR_STEPS_MAP: Record<TourId, Step[]> = {
  dashboard: DASHBOARD_TOUR_STEPS,
  templates: TEMPLATES_TOUR_STEPS,
  datasets: DATASETS_TOUR_STEPS,
  settings: SETTINGS_TOUR_STEPS,
  query: QUERY_TOUR_STEPS,
  audit: AUDIT_TOUR_STEPS,
}

// Storage key for tour completion
const TOUR_COMPLETED_KEY = 'nlpforge_tour_completed'

// ============================================================================
// ONBOARDING TOUR COMPONENT
// ============================================================================

interface OnboardingTourProps {
  tourId: TourId
  run?: boolean
  onComplete?: () => void
}

export function OnboardingTour({ tourId, run: runProp, onComplete }: OnboardingTourProps) {
  const { user } = useAuth()
  const [run, setRun] = useState(false)

  // Get steps based on tour ID
  const steps = TOUR_STEPS_MAP[tourId] || []

  // Check if tour should run (first-time user)
  useEffect(() => {
    if (runProp !== undefined) {
      setRun(runProp)
      return
    }

    // Check localStorage for tour completion
    let completed: Record<string, boolean> = {}
    try {
      const completedTours = localStorage.getItem(TOUR_COMPLETED_KEY)
      completed = completedTours ? JSON.parse(completedTours) : {}
    } catch {
      completed = {}
    }
    
    if (!completed[tourId] && user) {
      // Small delay to ensure DOM elements are rendered
      const timer = setTimeout(() => setRun(true), 1500)
      return () => clearTimeout(timer)
    }
  }, [tourId, runProp, user])

  // Handle tour callback
  const handleCallback = useCallback((data: CallBackProps) => {
    const { status } = data

    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      setRun(false)
      
      // Mark tour as completed
      let completed: Record<string, boolean> = {}
      try {
        const completedTours = localStorage.getItem(TOUR_COMPLETED_KEY)
        completed = completedTours ? JSON.parse(completedTours) : {}
      } catch {
        completed = {}
      }
      completed[tourId] = true
      localStorage.setItem(TOUR_COMPLETED_KEY, JSON.stringify(completed))
      
      onComplete?.()
    }
  }, [tourId, onComplete])

  if (!user || steps.length === 0) return null

  return (
    <Joyride
      steps={steps}
      run={run}
      callback={handleCallback}
      continuous
      showProgress
      showSkipButton
      hideCloseButton
      spotlightPadding={8}
      styles={{
        options: {
          primaryColor: '#3b82f6',
          backgroundColor: '#ffffff',
          textColor: '#1f2937',
          arrowColor: '#ffffff',
          overlayColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 10000,
        },
        tooltip: {
          borderRadius: 12,
          padding: '16px 20px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        },
        tooltipTitle: {
          fontSize: 16,
          fontWeight: 600,
        },
        tooltipContent: {
          fontSize: 14,
          lineHeight: 1.5,
        },
        buttonNext: {
          borderRadius: 8,
          padding: '8px 16px',
          fontSize: 14,
          fontWeight: 500,
        },
        buttonBack: {
          color: '#6b7280',
          marginRight: 8,
        },
        buttonSkip: {
          color: '#6b7280',
        },
        spotlight: {
          borderRadius: 8,
        },
      }}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Done',
        next: 'Next',
        skip: 'Skip tour',
      }}
    />
  )
}

// ============================================================================
// HOOK TO MANUALLY TRIGGER TOUR
// ============================================================================

export function useOnboardingTour(tourId: TourId) {
  const startTour = useCallback(() => {
    // Reset tour completion for this tour
    let completed: Record<string, boolean> = {}
    try {
      const completedTours = localStorage.getItem(TOUR_COMPLETED_KEY)
      completed = completedTours ? JSON.parse(completedTours) : {}
    } catch {
      completed = {}
    }
    delete completed[tourId]
    localStorage.setItem(TOUR_COMPLETED_KEY, JSON.stringify(completed))
    
    // Force page reload to restart tour
    window.location.reload()
  }, [tourId])

  const resetAllTours = useCallback(() => {
    localStorage.removeItem(TOUR_COMPLETED_KEY)
    window.location.reload()
  }, [])

  return { startTour, resetAllTours }
}

export default OnboardingTour
