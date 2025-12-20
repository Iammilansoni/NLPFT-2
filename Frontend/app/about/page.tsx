'use client';

import { LandingNav } from '@/components/landing/LandingNav';
import {
    Zap,
    Search,
    Database,
    Shield,
    Cpu,
    GitBranch,
    ArrowRight,
    Github,
    ExternalLink
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

/**
 * About Us Page - NLPForge
 * 
 * Blog-style page with comprehensive project information
 * following the "Enterprise Calm" design direction
 */

interface FeatureCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
    return (
        <div className="group p-6 rounded-xl border border-border bg-card hover:shadow-lg hover:border-primary/30 transition-all duration-300">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:bg-primary/20 transition-colors">
                {icon}
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
        </div>
    );
}

interface TechBadgeProps {
    name: string;
    category: 'frontend' | 'backend' | 'database' | 'ai';
}

function TechBadge({ name, category }: TechBadgeProps) {
    const colors = {
        frontend: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        backend: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
        database: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
        ai: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    };

    return (
        <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${colors[category]}`}>
            {name}
        </span>
    );
}

export default function AboutPage() {
    return (
        <div className="min-h-screen bg-background">
            {/* Navigation */}
            <LandingNav />

            {/* Hero Section */}
            <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
                        <Zap className="w-4 h-4" />
                        AI-Powered API Testing Platform
                    </div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground tracking-tight mb-6">
                        About <span className="text-primary">NLPForge</span>
                    </h1>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
                        Transform natural language queries into executable API test cases using
                        LLM-powered semantic understanding. Built for developers, by developers.
                    </p>
                </div>
            </section>

            {/* Main Content - Blog Style */}
            <main className="px-4 sm:px-6 lg:px-8 pb-24">
                <div className="max-w-4xl mx-auto">

                    {/* Mission Section */}
                    <article className="prose dark:prose-invert max-w-none mb-16">
                        <div className="p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/20 mb-12">
                            <h2 className="text-2xl font-bold text-foreground mb-4 mt-0">Our Mission</h2>
                            <p className="text-muted-foreground text-lg leading-relaxed mb-0">
                                NLPForge bridges the gap between natural language and API testing. We believe that
                                describing what you want to test should be as simple as writing a sentence. Our platform
                                understands your intent, matches the most relevant API templates, extracts parameters,
                                and generates complete executable test cases—all automatically.
                            </p>
                        </div>

                        {/* How It Works */}
                        <section className="mb-16">
                            <h2 className="text-3xl font-bold text-foreground mb-8">How It Works</h2>
                            <div className="grid gap-6">
                                <div className="flex gap-4 p-5 rounded-xl border border-border bg-card">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">1</div>
                                    <div>
                                        <h3 className="font-semibold text-foreground mb-1">Understand Your Intent</h3>
                                        <p className="text-muted-foreground text-sm">Our semantic search engine uses advanced embeddings to deeply understand what you want to test, going beyond simple keyword matching.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 p-5 rounded-xl border border-border bg-card">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">2</div>
                                    <div>
                                        <h3 className="font-semibold text-foreground mb-1">Match to API Templates</h3>
                                        <p className="text-muted-foreground text-sm">Two-stage retrieval with vector similarity search and FlashRank re-ranking ensures the most relevant API template is selected.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 p-5 rounded-xl border border-border bg-card">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">3</div>
                                    <div>
                                        <h3 className="font-semibold text-foreground mb-1">Extract Values Automatically</h3>
                                        <p className="text-muted-foreground text-sm">LLM-powered slot extraction pulls values like emails, passwords, and IDs from your natural language query to populate request parameters.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 p-5 rounded-xl border border-border bg-card">
                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">4</div>
                                    <div>
                                        <h3 className="font-semibold text-foreground mb-1">Generate Executable Test Cases</h3>
                                        <p className="text-muted-foreground text-sm">Get complete, ready-to-run API test cases with populated request bodies, headers, and endpoints—no manual work required.</p>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Example Box */}
                        <section className="mb-16">
                            <h2 className="text-3xl font-bold text-foreground mb-6">See It In Action</h2>
                            <div className="rounded-xl border border-border overflow-hidden">
                                <div className="bg-muted/30 px-5 py-3 border-b border-border">
                                    <span className="text-sm font-medium text-foreground">Example Query</span>
                                </div>
                                <div className="p-5 bg-card">
                                    <p className="text-muted-foreground mb-4 italic">
                                        "Authenticate with email krishna@nlpforge.com and password secure123"
                                    </p>
                                    <div className="flex items-center gap-2 text-primary mb-4">
                                        <ArrowRight className="w-4 h-4" />
                                        <span className="text-sm font-medium">NLPForge Processing</span>
                                    </div>
                                    <pre className="bg-muted/50 rounded-lg p-4 text-sm overflow-x-auto">
                                        {`{
  "api_name": "User_Login",
  "base_url": "https://api.example.com",
  "endpoint": "/auth/login",
  "method": "POST",
  "extracted_request_body": {
    "email": "krishna@nlpforge.com",
    "password": "secure123"
  }
}`}
                                    </pre>
                                </div>
                            </div>
                        </section>
                    </article>

                    {/* Features Grid */}
                    <section className="mb-16">
                        <h2 className="text-3xl font-bold text-foreground mb-8 text-center">Core Features</h2>
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                            <FeatureCard
                                icon={<Search className="w-6 h-6" />}
                                title="Semantic Search"
                                description="Two-stage retrieval with vector similarity and FlashRank re-ranking for precise API template matching."
                            />
                            <FeatureCard
                                icon={<Cpu className="w-6 h-6" />}
                                title="LLM Slot Extraction"
                                description="Automatically extract values from natural language queries to populate API request schemas."
                            />
                            <FeatureCard
                                icon={<Database className="w-6 h-6" />}
                                title="Synthetic Datasets"
                                description="Generate diverse test data using local LLMs and embed them for semantic search capabilities."
                            />
                            <FeatureCard
                                icon={<GitBranch className="w-6 h-6" />}
                                title="Template Builder"
                                description="Create and manage API templates with JSON schemas, approval workflows, and version control."
                            />
                            <FeatureCard
                                icon={<Shield className="w-6 h-6" />}
                                title="Enterprise Security"
                                description="JWT authentication, complete audit trails, and multi-tenant data isolation for compliance."
                            />
                            <FeatureCard
                                icon={<Zap className="w-6 h-6" />}
                                title="Local-First AI"
                                description="All AI processing runs locally via Ollama. Your data never leaves your infrastructure."
                            />
                        </div>
                    </section>

                    {/* Technology Stack */}
                    <section className="mb-16">
                        <h2 className="text-3xl font-bold text-foreground mb-8 text-center">Technology Stack</h2>
                        <div className="p-8 rounded-2xl border border-border bg-card">
                            <div className="grid sm:grid-cols-2 gap-8">
                                <div>
                                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                        Frontend
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        <TechBadge name="Next.js 14" category="frontend" />
                                        <TechBadge name="TypeScript" category="frontend" />
                                        <TechBadge name="Tailwind CSS" category="frontend" />
                                        <TechBadge name="shadcn/ui" category="frontend" />
                                        <TechBadge name="React Query" category="frontend" />
                                    </div>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                        Backend
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        <TechBadge name="FastAPI" category="backend" />
                                        <TechBadge name="Python 3.11+" category="backend" />
                                        <TechBadge name="SQLAlchemy" category="backend" />
                                        <TechBadge name="Pydantic" category="backend" />
                                    </div>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                        Database
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        <TechBadge name="PostgreSQL 15" category="database" />
                                        <TechBadge name="Redis Stack" category="database" />
                                        <TechBadge name="RediSearch" category="database" />
                                    </div>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                                        AI / ML
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        <TechBadge name="Ollama" category="ai" />
                                        <TechBadge name="FlashRank" category="ai" />
                                        <TechBadge name="Llama 3.1" category="ai" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Embedding Models */}
                    <section className="mb-16">
                        <h2 className="text-3xl font-bold text-foreground mb-8 text-center">Embedding Models</h2>
                        <div className="overflow-hidden rounded-xl border border-border">
                            <table className="w-full">
                                <thead className="bg-muted/50">
                                    <tr>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Model</th>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Dimensions</th>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Speed</th>
                                        <th className="px-6 py-4 text-left text-sm font-semibold text-foreground">Best For</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border bg-card">
                                    <tr>
                                        <td className="px-6 py-4">
                                            <span className="font-mono text-sm text-primary">nomic-embed-text</span>
                                        </td>
                                        <td className="px-6 py-4 text-muted-foreground">768</td>
                                        <td className="px-6 py-4 text-muted-foreground">⚡ Fast</td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-foreground font-medium">General use, recommended default</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="px-6 py-4">
                                            <span className="font-mono text-sm text-primary">all-minilm</span>
                                        </td>
                                        <td className="px-6 py-4 text-muted-foreground">384</td>
                                        <td className="px-6 py-4 text-muted-foreground">⚡⚡ Fastest</td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-foreground">Prototyping, low-resource environments</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="px-6 py-4">
                                            <span className="font-mono text-sm text-primary">mxbai-embed-large</span>
                                        </td>
                                        <td className="px-6 py-4 text-muted-foreground">1024</td>
                                        <td className="px-6 py-4 text-muted-foreground">🐢 Moderate</td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-foreground">Maximum accuracy, enterprise search</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>



                    {/* CTA Section */}
                    <section className="text-center">
                        <div className="p-10 rounded-2xl bg-primary/5 border border-primary/20">
                            <h2 className="text-3xl font-bold text-foreground mb-4">Ready to Get Started?</h2>
                            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
                                Transform your API testing workflow with AI-powered test case generation.
                                Sign up free and start creating test cases in seconds.
                            </p>
                            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                                <Button asChild size="lg" className="h-12 px-8">
                                    <Link href="/dashboard">
                                        Launch Dashboard
                                        <ArrowRight className="w-4 h-4 ml-2" />
                                    </Link>
                                </Button>
                                <Button asChild variant="outline" size="lg" className="h-12 px-8">
                                    <a
                                        href="https://github.com/Iammilansoni/NLPForge-Tester"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        <Github className="w-4 h-4 mr-2" />
                                        View on GitHub
                                        <ExternalLink className="w-3 h-3 ml-2" />
                                    </a>
                                </Button>
                            </div>
                        </div>
                    </section>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-border py-8 px-4">
                <div className="max-w-4xl mx-auto text-center text-sm text-muted-foreground">
                    <p className="mt-2">
                        © {new Date().getFullYear()} NLPForge. Open Source under MIT License.
                    </p>
                </div>
            </footer>
        </div>
    );
}
