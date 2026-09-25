'use client';

import { LandingNav } from '@/components/landing/LandingNav';
import UserJourneyTimeline from '@/components/diagrams/UserJourneyTimeline';
import { 
  ArrowRight, 
  BookOpen, 
  CheckCircle2,
  Lightbulb,
  Rocket,
  Clock,
  Target
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

/**
 * Getting Started Page
 * 
 * Comprehensive guide showing the complete user flow
 * from authentication to semantic search results
 */

export default function GettingStartedPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <LandingNav />

      {/* Hero Section */}
      <section className="pt-32 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <BookOpen className="w-4 h-4" />
            Getting Started Guide
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-foreground tracking-tight mb-6">
            Getting started with <span className="text-primary">NLPForge</span>
          </h1>
          <p className="text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
            From an empty catalogue to routing plain-English requests to validated
            API calls. The demo account skips straight to the last step.
          </p>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="px-4 sm:px-6 lg:px-8 pb-12">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-border bg-card text-center">
              <div className="text-3xl font-bold text-primary mb-1">20</div>
              <div className="text-sm text-muted-foreground">Demo APIs seeded</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-card text-center">
              <div className="text-3xl font-bold text-primary mb-1">1</div>
              <div className="text-sm text-muted-foreground">docker compose up</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-card text-center">
              <div className="text-3xl font-bold text-primary mb-1">3</div>
              <div className="text-sm text-muted-foreground">Pipeline stages</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-card text-center">
              <div className="text-3xl font-bold text-primary mb-1">0</div>
              <div className="text-sm text-muted-foreground">API keys needed locally</div>
            </div>
          </div>
        </div>
      </section>

      {/* Prerequisites */}
      <section className="px-4 sm:px-6 lg:px-8 pb-12">
        <div className="max-w-4xl mx-auto">
          <div className="p-6 rounded-2xl border border-warning/25 dark:border-warning bg-warning/10 dark:bg-warning/30">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-warning/10 dark:bg-warning/50 flex items-center justify-center flex-shrink-0">
                <Lightbulb className="w-5 h-5 text-warning dark:text-warning" />
              </div>
              <div>
                <h3 className="font-semibold text-warning dark:text-warning-foreground mb-2">Prerequisites</h3>
                <ul className="space-y-2 text-sm text-warning dark:text-warning">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Docker with Compose v2.24+ (or Python 3.11 and Node 20 to run without Docker)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Nothing else for local mode: Ollama runs in the stack. A Gemini key is only needed for LLM dataset generation
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    For your own APIs: endpoint, method and a JSON Schema for each request body
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content - Complete User Journey */}
      <main className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-6xl mx-auto">
          <UserJourneyTimeline />
        </div>
      </main>

      {/* Summary Cards */}
      <section className="px-4 sm:px-6 lg:px-8 pb-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">Phase Summary</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Phase</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Key Actions</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-success/10 dark:bg-success/30 text-success dark:text-success text-xs font-medium">
                      Authentication
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Sign up, verify email, sign in</td>
                  <td className="px-4 py-3 text-sm text-foreground">Access to dashboard</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-info/10 dark:bg-info/30 text-info dark:text-info text-xs font-medium">
                      Templates
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Create one, then switch it on (only you can)</td>
                  <td className="px-4 py-3 text-sm text-foreground">Approved template ready</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-warning/10 dark:bg-warning/30 text-warning dark:text-warning text-xs font-medium">
                      Settings
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Configure LLM provider, set embedding model</td>
                  <td className="px-4 py-3 text-sm text-foreground">AI models configured</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-primary/10 dark:bg-primary/30 text-primary dark:text-primary text-xs font-medium">
                      Datasets
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Select template, configure, generate</td>
                  <td className="px-4 py-3 text-sm text-foreground">CSV dataset created</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-info/10 dark:bg-info/30 text-info dark:text-info text-xs font-medium">
                      Embedding
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Embed utterances into pgvector</td>
                  <td className="px-4 py-3 text-sm text-foreground">Searchable embeddings</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-brand-2/10 dark:bg-brand-2/30 text-brand-2 dark:text-brand-2 text-xs font-medium">
                      Search
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Enter query, two-stage retrieval</td>
                  <td className="px-4 py-3 text-sm text-foreground">Matched APIs ranked</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded-full bg-success/10 dark:bg-success/30 text-success dark:text-success text-xs font-medium">
                      Output
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">View JSON, use in application</td>
                  <td className="px-4 py-3 text-sm text-foreground">Executable test case</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 sm:px-6 lg:px-8 pb-24">
        <div className="max-w-4xl mx-auto">
          <div className="p-10 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20 text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mx-auto mb-6">
              <Rocket className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-4">Ready to Begin?</h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              Open the demo tenant and route a request, or sign up and describe your own APIs.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button asChild size="lg" className="h-12 px-8">
                <Link href="/auth/register">
                  Create Account
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 px-8">
                <Link href="/dashboard">
                  Go to Dashboard
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-4">
        <div className="max-w-4xl mx-auto text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} NLPForge. Open Source under MIT License.</p>
        </div>
      </footer>
    </div>
  );
}
