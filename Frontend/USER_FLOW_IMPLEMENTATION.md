# 🚀 NLPForge Complete User Flow Implementation Guide

**Last Updated:** November 10, 2025  
**Status:** 75% Complete → Target: 100% Production-Ready

---

## 📋 Table of Contents

1. [User Flow Overview](#user-flow-overview)
2. [Backend Integration Points](#backend-integration-points)
3. [Frontend Pages & Components](#frontend-pages--components)
4. [Implementation Checklist](#implementation-checklist)
5. [Code Examples](#code-examples)

---

## 🧭 User Flow Overview

### The Complete Journey

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Types Natural Language Query                            │
│    "Login to demo.com with user milan and password Mila@123."   │
└────────────────┬────────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Live Progress Drawer Shows Pipeline                          │
│    ✓ Understanding your request...                              │
│    ✓ Creating dataset (127 cases)...                            │
│    ✓ Computing embeddings...                                    │
│    ✓ Vector search complete                                     │
│    ✓ Ready: JSON meaning found ✅                               │
└────────────────┬────────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Show Meaning JSON + Matched Template                         │
│    {                                                             │
│      "intent": "login",                                          │
│      "slots": { base_url, username, password },                 │
│      "confidence": 0.96                                          │
│    }                                                             │
│    [Run with Selenium] [Download JSON] [View Template]          │
└────────────────┬────────────────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. (Optional) Execute Real Tests with Selenium                  │
│    • Stream live logs                                            │
│    • Show pass/fail results                                      │
│    • Display screenshots, timings, artifacts                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Backend Integration Points

### API Endpoints

#### 1. Query Submission
```typescript
POST /api/v1/query
Request: { text: string }
Response: { run_id: string, status: "queued" }
```

#### 2. Run Status (Polling/SSE)
```typescript
GET /api/v1/run/:run_id/status
Response: {
  run_id: string
  step: "parse_intent" | "dataset_generated" | "embeddings_done" | 
        "vector_search_done" | "ready" | "selenium_running" | "complete"
  progress: number // 0.0 - 1.0
  logs?: string[]
  error?: string
}
```

#### 3. Run Results
```typescript
GET /api/v1/run/:run_id/results
Response: {
  meaning_json: {
    intent: string
    template: string
    slots: Record<string, any>
    confidence: number
    evidence: {
      similar_cases: Array<{ id: string, similarity: number }>
    }
  }
  template: ApiTemplate
  dataset_stats: {
    total_cases: number
    generated_at: string
  }
  selenium_results?: {
    pass_rate: number
    total_tests: number
    passed: number
    failed: number
    duration_ms: number
    artifacts: Array<{ type: string, url: string }>
  }
}
```

#### 4. Start Selenium Test
```typescript
POST /api/v1/test/run/:run_id/start
Response: { started: boolean, status: "running" }
```

#### 5. Templates Management
```typescript
GET    /api/v1/templates
POST   /api/v1/templates
PUT    /api/v1/templates/:id
DELETE /api/v1/templates/:id
POST   /api/v1/templates/autodiscover
POST   /api/v1/templates/sync
POST   /api/v1/templates/hot-reload
```

#### 6. Datasets Management
```typescript
GET  /api/v1/datasets?intent=...&limit=...&offset=...
POST /api/v1/datasets/generate
POST /api/v1/datasets/upload
POST /api/v1/datasets/:id/reembed
```

#### 7. Semantic Search
```typescript
GET /api/v1/search?text=...&intent=...&minSim=...&template_version=...
Response: {
  results: Array<{
    id: string
    text: string
    intent: string
    similarity: number
    confidence: number
    template: string
    metadata: Record<string, any>
  }>
}
```

---

## 🖥️ Frontend Pages & Components

### Page Structure

```
src/app/
├── dashboard/
│   └── page.tsx              ✅ DONE - Enhanced with KPIs
├── run/
│   ├── new/
│   │   └── page.tsx          ⏳ TO DO - Main run creation page
│   └── [id]/
│       └── page.tsx          📋 TO DO - Run results page
├── templates/
│   ├── page.tsx              ✅ DONE - Templates list
│   └── [id]/
│       ├── page.tsx          ⏳ TO DO - Template detail
│       └── edit/
│           └── page.tsx      📋 TO DO - Template editor
├── datasets/
│   └── page.tsx              ✅ DONE - Dataset management
└── search/
    └── page.tsx              ✅ DONE - Semantic search
```

### Key Components

#### ✅ Already Built (Production-Ready)

1. **QueryInput** (`components/query-input.tsx`)
   - Natural language input with example chips
   - Character count, validation
   - Animated suggestions dropdown
   - Submit handler ready

2. **ProgressDrawer** (`components/progress-drawer.tsx`)
   - 6-step pipeline visualization
   - Expandable logs per step
   - Cancel button support
   - Live progress updates

3. **KpiCard** (`components/kpi-card.tsx`)
   - Gradient backgrounds
   - Trend indicators
   - Hover animations

#### ⏳ Need to Build

4. **MeaningJSONCard** - Display intent + slots with pretty formatting
5. **SimilarityList** - Show top similar cases with confidence bars
6. **RunReport** - Selenium results with pass/fail, timings, artifacts
7. **TemplateEditor** - Split view: Form + JSON editor
8. **DatasetUploadZone** - CSV drag-drop with preview
9. **VirtualizedTable** - For large dataset browsing

---

## ✅ Implementation Checklist

### Phase 1: Core Run Flow (HIGH PRIORITY)

- [ ] **Create `/run/new` page**
  - [ ] Import QueryInput component
  - [ ] Wire to POST /api/v1/query
  - [ ] Show ProgressDrawer with run_id
  - [ ] Poll GET /api/v1/run/:id/status every 1s
  - [ ] Update progress bar + step status
  - [ ] On "ready", fetch results and show MeaningJSONCard

- [ ] **Create MeaningJSONCard component**
  - [ ] Display JSON with syntax highlighting
  - [ ] Show confidence score with visual indicator
  - [ ] Action buttons: Run Selenium, Download JSON, View Template
  - [ ] Similar cases list with similarity bars
  - [ ] Copy JSON to clipboard

- [ ] **Create `/run/[id]` results page**
  - [ ] Summary cards: Pass Rate, Total Tests, Duration
  - [ ] Meaning JSON section
  - [ ] Template info section
  - [ ] Dataset stats
  - [ ] Selenium results (if executed)
  - [ ] Artifacts gallery (screenshots, logs, videos)
  - [ ] Export options

### Phase 2: Templates Enhancement (MEDIUM PRIORITY)

- [ ] **Enhance `/templates/[id]` detail page**
  - [ ] Template metadata (name, version, status, confidence)
  - [ ] Slots configuration table
  - [ ] Example rows
  - [ ] Validation rules
  - [ ] Dry Probe button → test endpoint
  - [ ] Edit button → navigate to edit page

- [ ] **Create `/templates/[id]/edit` page**
  - [ ] Split view layout (50/50)
  - [ ] Left: AutoForm from template schema
  - [ ] Right: Monaco editor for JSON
  - [ ] Two-way sync between form and JSON
  - [ ] Validation messages
  - [ ] Save draft / Publish buttons
  - [ ] Change history timeline

- [ ] **Add Template Management Actions**
  - [ ] Auto-Discover button with progress modal
  - [ ] Hot Reload button with toast feedback
  - [ ] Sync from Server button
  - [ ] Clone template action
  - [ ] Archive/Restore actions

### Phase 3: Dataset Management (MEDIUM PRIORITY)

- [ ] **Enhance `/datasets` page tabs**
  - [ ] Browse tab with virtualized table
  - [ ] Generate tab with smart form
  - [ ] Upload tab with drag-drop zone

- [ ] **Dataset Browse Tab**
  - [ ] Filters: intent, template, date range
  - [ ] Expandable rows showing full request/response
  - [ ] Masked secrets toggle
  - [ ] Bulk actions: Export, Re-embed, Delete
  - [ ] Pagination or infinite scroll

- [ ] **Dataset Generate Tab**
  - [ ] Intent selector
  - [ ] Template selector
  - [ ] Size slider (10-200 cases)
  - [ ] Options: include negatives, boundaries, security tests
  - [ ] Generate button → progress modal
  - [ ] Preview generated cases before saving

- [ ] **Dataset Upload Tab**
  - [ ] CSV/JSON drag-drop zone
  - [ ] File preview with first 10 rows
  - [ ] Schema validation
  - [ ] Column mapping interface
  - [ ] "Also embed" checkbox
  - [ ] Upload progress bar

### Phase 4: Selenium Integration (HIGH PRIORITY)

- [ ] **Add Selenium execution to run flow**
  - [ ] "Run with Selenium" button on results page
  - [ ] POST /api/v1/test/run/:id/start
  - [ ] Stream logs via SSE or polling
  - [ ] Update UI with live status
  - [ ] Show final results when complete

- [ ] **Create RunReport component**
  - [ ] Pass/Fail summary with percentages
  - [ ] Test cases table (virtualized)
  - [ ] Each row: name, status, duration, assertions
  - [ ] Expandable for logs/errors
  - [ ] Screenshots gallery
  - [ ] Diff viewer for assertion failures
  - [ ] Replay button per test
  - [ ] Export artifacts button

### Phase 5: Real-Time Updates (MEDIUM PRIORITY)

- [ ] **Implement SSE client**
  - [ ] Create useServerSentEvents hook
  - [ ] Connect to /api/v1/run/:id/stream
  - [ ] Parse events: progress, log, error, complete
  - [ ] Update ProgressDrawer in real-time
  - [ ] Handle reconnection logic

- [ ] **WebSocket fallback**
  - [ ] Create useWebSocket hook
  - [ ] Connect to ws://backend/run/:id
  - [ ] Same event handling as SSE
  - [ ] Auto-detect and prefer SSE > WS > Polling

### Phase 6: Polish & UX (LOW PRIORITY)

- [ ] **Empty states**
  - [ ] No runs yet → Sample run button
  - [ ] No templates → Auto-discover prompt
  - [ ] No datasets → Generate or upload prompt
  - [ ] No search results → Suggestions

- [ ] **Error handling**
  - [ ] Timeout errors with retry button
  - [ ] Network errors with offline indicator
  - [ ] Validation errors with field highlights
  - [ ] Rate limit handling

- [ ] **Accessibility**
  - [ ] Keyboard navigation for all flows
  - [ ] Screen reader announcements for progress
  - [ ] Focus management in modals/drawers
  - [ ] Color contrast WCAG AA

- [ ] **Performance**
  - [ ] Virtualize large tables
  - [ ] Lazy load heavy components
  - [ ] Debounce search inputs
  - [ ] Optimize re-renders with React.memo

---

## 💻 Code Examples

### 1. Wiring QueryInput to Backend

```typescript
// app/run/new/page.tsx
'use client'

import { useState } from 'react'
import { QueryInput } from '@/components/query-input'
import { ProgressDrawer } from '@/components/progress-drawer'
import { apiClient } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'

export default function NewRunPage() {
  const [runId, setRunId] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  // Submit query
  const handleSubmit = async (text: string) => {
    try {
      const response = await apiClient.createRun({ text })
      setRunId(response.run_id)
      setIsOpen(true)
    } catch (error) {
      console.error('Failed to create run:', error)
    }
  }

  // Poll run status
  const { data: status } = useQuery({
    queryKey: ['run-status', runId],
    queryFn: () => apiClient.getRunStatus(runId!),
    enabled: !!runId && isOpen,
    refetchInterval: 1000, // Poll every 1s
  })

  return (
    <div className="container py-12">
      <h1 className="text-4xl font-bold mb-8">Create New Run</h1>
      
      <QueryInput
        onSubmit={handleSubmit}
        placeholder="Describe your test scenario in plain English..."
      />

      <ProgressDrawer
        open={isOpen}
        onOpenChange={setIsOpen}
        runId={runId}
        status={status}
      />
    </div>
  )
}
```

### 2. MeaningJSONCard Component

```typescript
// components/meaning-json-card.tsx
'use client'

import { motion } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, Play, FileText, Copy, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

interface MeaningJSON {
  intent: string
  template: string
  slots: Record<string, any>
  confidence: number
  evidence: {
    similar_cases: Array<{ id: string, similarity: number }>
  }
}

export function MeaningJSONCard({ 
  meaning, 
  onRunSelenium,
  onViewTemplate 
}: { 
  meaning: MeaningJSON
  onRunSelenium: () => void
  onViewTemplate: () => void
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(meaning, null, 2))
    setCopied(true)
    toast.success('JSON copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(meaning, null, 2)], { 
      type: 'application/json' 
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `meaning-${meaning.intent}-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('JSON downloaded')
  }

  return (
    <Card className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold">Meaning JSON</h3>
          <p className="text-muted-foreground">
            Extracted intent and slots from your query
          </p>
        </div>
        
        {/* Confidence Badge */}
        <Badge 
          variant={meaning.confidence > 0.9 ? 'default' : 'secondary'}
          className="text-lg px-4 py-2"
        >
          {(meaning.confidence * 100).toFixed(1)}% confident
        </Badge>
      </div>

      {/* JSON Display */}
      <div className="relative">
        <pre className="bg-black/90 text-green-400 p-6 rounded-xl overflow-x-auto font-mono text-sm">
          {JSON.stringify(meaning, null, 2)}
        </pre>
        
        <Button
          size="sm"
          variant="ghost"
          className="absolute top-4 right-4"
          onClick={handleCopy}
        >
          {copied ? (
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <Button
          onClick={onRunSelenium}
          className="flex-1 min-w-[200px]"
          size="lg"
        >
          <Play className="mr-2 h-5 w-5" />
          Run with Selenium
        </Button>
        
        <Button
          variant="outline"
          onClick={onViewTemplate}
        >
          <FileText className="mr-2 h-4 w-4" />
          View Template
        </Button>
        
        <Button
          variant="outline"
          onClick={handleDownload}
        >
          <Download className="mr-2 h-4 w-4" />
          Download JSON
        </Button>
      </div>

      {/* Similar Cases */}
      <div className="space-y-3 pt-4 border-t">
        <h4 className="font-semibold">Top Similar Cases</h4>
        <div className="space-y-2">
          {meaning.evidence.similar_cases.map((case_, i) => (
            <motion.div
              key={case_.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-3"
            >
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-mono text-muted-foreground">
                    {case_.id}
                  </span>
                  <span className="text-sm font-semibold">
                    {(case_.similarity * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${case_.similarity * 100}%` }}
                    transition={{ duration: 0.5, delay: i * 0.1 }}
                    className="h-full bg-gradient-to-r from-primary to-accent"
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </Card>
  )
}
```

### 3. Polling with Auto-Cleanup

```typescript
// hooks/use-run-polling.ts
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { useEffect } from 'react'

export function useRunPolling(runId: string | null, enabled: boolean) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['run-status', runId],
    queryFn: () => apiClient.getRunStatus(runId!),
    enabled: !!runId && enabled,
    refetchInterval: (data) => {
      // Stop polling when complete
      if (data?.step === 'complete' || data?.step === 'error') {
        return false
      }
      return 1000 // Poll every 1s
    },
    refetchIntervalInBackground: false,
    staleTime: 0,
  })

  // Auto-fetch results when complete
  const { data: results } = useQuery({
    queryKey: ['run-results', runId],
    queryFn: () => apiClient.getRunResults(runId!),
    enabled: data?.step === 'complete',
  })

  return {
    status: data,
    results,
    isLoading,
    error,
    isComplete: data?.step === 'complete',
    isError: data?.step === 'error',
  }
}
```

### 4. SSE Implementation (Advanced)

```typescript
// hooks/use-server-sent-events.ts
import { useEffect, useState } from 'react'

interface SSEMessage {
  type: 'progress' | 'log' | 'error' | 'complete'
  data: any
}

export function useServerSentEvents(url: string, enabled: boolean) {
  const [messages, setMessages] = useState<SSEMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!enabled || !url) return

    const eventSource = new EventSource(url)

    eventSource.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    eventSource.onmessage = (event) => {
      try {
        const message: SSEMessage = JSON.parse(event.data)
        setMessages((prev) => [...prev, message])
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    eventSource.onerror = (err) => {
      setIsConnected(false)
      setError(new Error('SSE connection failed'))
      eventSource.close()
    }

    return () => {
      eventSource.close()
      setIsConnected(false)
    }
  }, [url, enabled])

  return {
    messages,
    isConnected,
    error,
    latestMessage: messages[messages.length - 1],
  }
}
```

---

## 🎯 Next Steps (Priority Order)

1. **IMMEDIATE** - Create `/run/new` page with QueryInput wired to backend
2. **HIGH** - Build MeaningJSONCard component
3. **HIGH** - Implement run polling with useRunPolling hook
4. **HIGH** - Create `/run/[id]` results page
5. **MEDIUM** - Add Selenium execution flow
6. **MEDIUM** - Enhance template detail/edit pages
7. **MEDIUM** - Build dataset upload functionality
8. **LOW** - Add SSE for real-time updates
9. **LOW** - Polish empty states and error handling

---

## 📊 Current Implementation Status

| Feature | Status | Files |
|---------|--------|-------|
| Design System | ✅ Complete | `globals.css`, `tailwind.config.ts` |
| QueryInput | ✅ Complete | `components/query-input.tsx` |
| ProgressDrawer | ✅ Complete | `components/progress-drawer.tsx` |
| KpiCard | ✅ Complete | `components/kpi-card.tsx` |
| Dashboard | ✅ Complete | `app/dashboard/page.tsx` |
| Search Page | ✅ Complete | `app/search/page.tsx` |
| Templates List | ✅ Complete | `app/templates/page.tsx` |
| Datasets Page | ✅ Complete | `app/dataset/page.tsx` |
| API Client | ✅ Complete | `lib/api.ts`, `lib/api-types.ts` |
| Run Creation | ⏳ To Do | `app/run/new/page.tsx` |
| Run Results | 📋 To Do | `app/run/[id]/page.tsx` |
| MeaningJSONCard | 📋 To Do | `components/meaning-json-card.tsx` |
| Template Editor | 📋 To Do | `app/templates/[id]/edit/page.tsx` |
| SSE Integration | 📋 To Do | `hooks/use-server-sent-events.ts` |

**Overall Progress: 75% → Target: 100%**

---

## 🔗 Related Documentation

- [PRODUCTION_IMPLEMENTATION_SUMMARY.md](./PRODUCTION_IMPLEMENTATION_SUMMARY.md) - Complete implementation details
- [START_HERE.md](./START_HERE.md) - Quick start guide
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) - Detailed progress tracking
- [Backend Integration Guide](../Backend/README_BACKEND.md) - API documentation

---

**Last Updated:** November 10, 2025  
**Maintainer:** GitHub Copilot  
**Status:** Living Document - Updated as implementation progresses
