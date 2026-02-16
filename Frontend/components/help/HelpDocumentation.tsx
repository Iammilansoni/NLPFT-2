'use client'

import * as React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Book,
  FileCode,
  Search,
  Database,
  Settings,
  Shield,
  Keyboard,
  ChevronRight,
  ExternalLink,
  Sparkles,
  Zap,
  Target,
  HelpCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'

// ============================================================================
// DOCUMENTATION SECTIONS
// ============================================================================

interface DocSection {
  id: string
  title: string
  icon: React.ReactNode
  content: React.ReactNode
}

const GettingStartedContent = () => (
  <div className="space-y-4">
    <p className="text-muted-foreground">
      NLPForge is an AI-powered platform for semantic API discovery and test data generation.
    </p>
    
    <div className="space-y-3">
      <h4 className="font-semibold flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary text-sm">1</span>
        Create API Templates
      </h4>
      <p className="text-sm text-muted-foreground ml-8">
        Define your API endpoints with parameters, sample requests, and expected responses. Templates are the foundation for semantic search.
      </p>
      
      <h4 className="font-semibold flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary text-sm">2</span>
        Generate Test Datasets
      </h4>
      <p className="text-sm text-muted-foreground ml-8">
        Use AI to generate diverse test cases for your templates. Export as CSV/JSON for integration with your test suites.
      </p>
      
      <h4 className="font-semibold flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary text-sm">3</span>
        Semantic API Search
      </h4>
      <p className="text-sm text-muted-foreground ml-8">
        Ask questions in natural language like &quot;How do I create a user?&quot; and find the right API instantly.
      </p>
    </div>

    <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-4">
      <p className="text-sm font-medium text-primary">Pro Tip</p>
      <p className="text-sm text-muted-foreground mt-1">
        Press <kbd className="px-1.5 py-0.5 text-xs font-mono bg-muted rounded">?</kbd> anytime to see keyboard shortcuts.
      </p>
    </div>
  </div>
)

const TemplatesContent = () => (
  <div className="space-y-4">
    <p className="text-muted-foreground">
      Templates define your API endpoints and are used for semantic search and dataset generation.
    </p>

    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">Creating a Template</h4>
        <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
          <li>Click <strong>New Template</strong> in the Templates page</li>
          <li>Enter API name, description, and endpoint URL</li>
          <li>Define request parameters with types and examples</li>
          <li>Add 2-3 sample requests with expected responses</li>
          <li>Add domain tags for better search categorization</li>
          <li>Save as Draft or Submit for Review</li>
        </ol>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Template Status Workflow</h4>
        <div className="flex items-center gap-2 text-sm">
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">Draft</span>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">Review</span>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
          <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">Approved</span>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Only <strong>Approved</strong> templates are indexed for semantic search.
        </p>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Best Practices</h4>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li>Use descriptive API names (e.g., &quot;Create User Account&quot;)</li>
          <li>Include multiple sample requests covering edge cases</li>
          <li>Add relevant domain tags for better discoverability</li>
          <li>Document expected responses with realistic data</li>
        </ul>
      </div>
    </div>
  </div>
)

const DatasetsContent = () => (
  <div className="space-y-4">
    <p className="text-muted-foreground">
      Datasets contain query-API mappings used for training and semantic search.
    </p>

    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">AI Dataset Generation</h4>
        <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
          <li>Select an approved template</li>
          <li>Choose the number of examples (50-500 recommended)</li>
          <li>Click <strong>Generate</strong> to create synthetic data</li>
          <li>Monitor progress in the generation queue</li>
          <li>Download as CSV or JSON when complete</li>
        </ol>
      </div>

      <div>
        <h4 className="font-semibold mb-2">CSV Upload</h4>
        <p className="text-sm text-muted-foreground">
          Upload your own datasets in CSV format. Required columns:
        </p>
        <ul className="text-sm text-muted-foreground mt-2 space-y-1 list-disc list-inside">
          <li><code className="text-xs bg-muted px-1 rounded">query</code> - Natural language query</li>
          <li><code className="text-xs bg-muted px-1 rounded">api_name</code> - Target API name</li>
          <li><code className="text-xs bg-muted px-1 rounded">endpoint</code> - API endpoint</li>
        </ul>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Embedding to Vector DB</h4>
        <p className="text-sm text-muted-foreground">
          After creating/uploading a dataset, embed it to Redis for semantic search:
        </p>
        <ol className="text-sm text-muted-foreground mt-2 space-y-1 list-decimal list-inside">
          <li>Click the <strong>Embed</strong> button on any dataset</li>
          <li>Select embedding model (or use default from Settings)</li>
          <li>Wait for embedding to complete</li>
          <li>Dataset is now searchable via semantic queries</li>
        </ol>
      </div>
    </div>
  </div>
)

const SearchContent = () => (
  <div className="space-y-4">
    <p className="text-muted-foreground">
      Semantic search uses AI to understand your intent and find matching APIs.
    </p>

    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">How It Works</h4>
        <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
          <li>Your query is converted to a vector embedding</li>
          <li>Vector similarity search finds closest matches in Redis</li>
          <li>Results are re-ranked using cross-encoder models</li>
          <li>Top matches are returned with confidence scores</li>
        </ol>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Example Queries</h4>
        <ul className="text-sm text-muted-foreground space-y-2">
          <li className="flex items-start gap-2">
            <Search className="h-4 w-4 text-primary mt-0.5 shrink-0" />
            <span>&quot;How do I create a new user account?&quot;</span>
          </li>
          <li className="flex items-start gap-2">
            <Search className="h-4 w-4 text-primary mt-0.5 shrink-0" />
            <span>&quot;Get product details by SKU&quot;</span>
          </li>
          <li className="flex items-start gap-2">
            <Search className="h-4 w-4 text-primary mt-0.5 shrink-0" />
            <span>&quot;Update customer billing address&quot;</span>
          </li>
        </ul>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Understanding Results</h4>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li><strong>Confidence Score</strong>: 0-100% match quality</li>
          <li><strong>Vector Score</strong>: Raw embedding similarity</li>
          <li><strong>Rerank Score</strong>: Cross-encoder confirmation</li>
        </ul>
      </div>
    </div>
  </div>
)

const SettingsContent = () => (
  <div className="space-y-4">
    <p className="text-muted-foreground">
      Configure embedding models and platform preferences.
    </p>

    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">Embedding Models (15+ via Ollama)</h4>
        <p className="text-sm text-muted-foreground mb-2">
          Choose from various models based on speed, accuracy, and context length needs:
        </p>
        <table className="w-full text-sm mt-2">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Model</th>
              <th className="text-left py-2">Speed</th>
              <th className="text-left py-2">Best For</th>
            </tr>
          </thead>
          <tbody className="text-muted-foreground">
            <tr className="border-b">
              <td className="py-2 font-medium">nomic-embed-text</td>
              <td className="py-2 text-emerald-600">Fast</td>
              <td className="py-2">RAG, Long docs (Recommended)</td>
            </tr>
            <tr className="border-b">
              <td className="py-2">all-minilm</td>
              <td className="py-2 text-emerald-600">Fastest</td>
              <td className="py-2">Prototyping, Edge devices</td>
            </tr>
            <tr className="border-b">
              <td className="py-2">mxbai-embed-large</td>
              <td className="py-2 text-amber-600">Moderate</td>
              <td className="py-2">State-of-the-art accuracy</td>
            </tr>
            <tr className="border-b">
              <td className="py-2">bge-m3</td>
              <td className="py-2 text-amber-600">Moderate</td>
              <td className="py-2">Multilingual (100+ langs)</td>
            </tr>
            <tr className="border-b">
              <td className="py-2">snowflake-arctic-embed</td>
              <td className="py-2 text-emerald-600">Fast</td>
              <td className="py-2">Enterprise retrieval</td>
            </tr>
            <tr>
              <td className="py-2">qwen3-embedding</td>
              <td className="py-2 text-red-600">Slow</td>
              <td className="py-2">Maximum quality (0.6-8B)</td>
            </tr>
          </tbody>
        </table>
        <p className="text-xs text-muted-foreground mt-2">
          More: bge-base/large, granite-embedding, paraphrase-multilingual, embeddinggemma
        </p>
      </div>

      <div className="bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Important</p>
        <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
          Changing the embedding model requires re-embedding all datasets for consistent search results.
        </p>
      </div>
    </div>
  </div>
)

const SecurityContent = () => (
  <div className="space-y-4">
    <p className="text-muted-foreground">
      NLPForge includes comprehensive audit logging and security features.
    </p>

    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">Audit Logging</h4>
        <p className="text-sm text-muted-foreground">
          All actions are logged including:
        </p>
        <ul className="text-sm text-muted-foreground mt-2 space-y-1 list-disc list-inside">
          <li>Template create/update/delete operations</li>
          <li>Dataset generation and uploads</li>
          <li>Embedding operations</li>
          <li>User authentication events</li>
          <li>Settings changes</li>
        </ul>
      </div>

      <div>
        <h4 className="font-semibold mb-2">Access Control</h4>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
          <li><strong>User</strong>: Create drafts, view templates</li>
          <li><strong>Expert</strong>: Submit for review</li>
          <li><strong>Reviewer</strong>: Approve/reject templates</li>
          <li><strong>Admin</strong>: Full access, manage users</li>
        </ul>
      </div>
    </div>
  </div>
)

const DOCUMENTATION_SECTIONS: DocSection[] = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: <Sparkles className="h-5 w-5" />,
    content: <GettingStartedContent />,
  },
  {
    id: 'templates',
    title: 'API Templates',
    icon: <FileCode className="h-5 w-5" />,
    content: <TemplatesContent />,
  },
  {
    id: 'datasets',
    title: 'Datasets',
    icon: <Database className="h-5 w-5" />,
    content: <DatasetsContent />,
  },
  {
    id: 'search',
    title: 'Semantic Search',
    icon: <Search className="h-5 w-5" />,
    content: <SearchContent />,
  },
  {
    id: 'settings',
    title: 'Settings',
    icon: <Settings className="h-5 w-5" />,
    content: <SettingsContent />,
  },
  {
    id: 'security',
    title: 'Security & Audit',
    icon: <Shield className="h-5 w-5" />,
    content: <SecurityContent />,
  },
]

// ============================================================================
// HELP DOCUMENTATION MODAL
// ============================================================================

interface HelpDocumentationProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function HelpDocumentation({ open, onOpenChange }: HelpDocumentationProps) {
  const [activeSection, setActiveSection] = React.useState('getting-started')

  const currentSection = DOCUMENTATION_SECTIONS.find((s) => s.id === activeSection)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh] p-0 overflow-hidden">
        <div className="flex h-full">
          {/* Sidebar */}
          <div className="w-64 border-r bg-muted/30 p-4 flex flex-col">
            <DialogHeader className="mb-4">
              <DialogTitle className="flex items-center gap-2">
                <Book className="h-5 w-5 text-primary" />
                Documentation
              </DialogTitle>
            </DialogHeader>

            <nav className="space-y-1 flex-1">
              {DOCUMENTATION_SECTIONS.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === section.id
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  {section.icon}
                  {section.title}
                </button>
              ))}
            </nav>

            <div className="pt-4 border-t mt-4">
              <p className="text-xs text-muted-foreground">
                Need more help? Use the Report Issue button to contact support.
              </p>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                {currentSection?.icon}
                {currentSection?.title}
              </h2>
            </div>

            <ScrollArea className="flex-1 p-6">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeSection}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {currentSection?.content}
                </motion.div>
              </AnimatePresence>
            </ScrollArea>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default HelpDocumentation
