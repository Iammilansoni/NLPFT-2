'use client';

import { LandingNav } from '@/components/landing/LandingNav';
import { UserFlowDiagram } from '@/components/diagrams/UserFlowDiagram';
import {
    Zap,
    Search,
    Database,
    Shield,
    Cpu,
    GitBranch,
    ArrowRight,
    CheckCircle2,
    Layers,
    Target,
    Workflow
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

/**
 * Product Page - NLPForge
 * 
 * Showcases the product features and capabilities
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

interface BenefitItemProps {
    text: string;
}

function BenefitItem({ text }: BenefitItemProps) {
    return (
        <li className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <span className="text-muted-foreground">{text}</span>
        </li>
    );
}

export default function ProductPage() {
    return (
        <div className="min-h-screen bg-background">
            {/* Navigation */}
            <LandingNav />

            {/* Hero Section */}
            <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
                        <Zap className="w-4 h-4" />
                        Intelligent API Testing
                    </div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground tracking-tight mb-6">
                        Transform Your <span className="text-primary">API Testing</span> Workflow
                    </h1>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto mb-8">
                        NLPForge uses advanced AI to understand your natural language queries and 
                        automatically generate precise, executable API test cases.
                    </p>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Button asChild size="lg" className="h-12 px-8">
                            <Link href="/dashboard">
                                Try It Now
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </Link>
                        </Button>
                        <Button asChild variant="outline" size="lg" className="h-12 px-8">
                            <Link href="/about">Learn More</Link>
                        </Button>
                    </div>
                </div>
            </section>

            {/* Main Content */}
            <main className="px-4 sm:px-6 lg:px-8 pb-24">
                <div className="max-w-6xl mx-auto">

                    {/* Core Features */}
                    <section className="mb-20">
                        <h2 className="text-3xl font-bold text-foreground mb-4 text-center">Core Capabilities</h2>
                        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
                            Everything you need to streamline API testing with AI-powered intelligence
                        </p>
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
                                title="AI Dataset Generation"
                                description="Generate diverse test datasets from templates using any configured LLM. Export as CSV or JSON for testing."
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
                                title="Multi-Provider AI"
                                description="Choose from 7 LLM providers: OpenAI, Google Gemini, Anthropic Claude, Grok, DeepSeek, Ollama (local), and HuggingFace."
                            />
                        </div>
                    </section>

                    {/* How It Works */}
                    <section className="mb-20">
                        <h2 className="text-3xl font-bold text-foreground mb-4 text-center">How It Works</h2>
                        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
                            From natural language to executable test cases in seconds
                        </p>
                        
                        {/* Quick Overview Cards */}
                        <div className="grid md:grid-cols-4 gap-6 mb-12">
                            <div className="text-center p-6 rounded-xl border border-border bg-card">
                                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">1</div>
                                <h3 className="font-semibold text-foreground mb-2">Describe Your Test</h3>
                                <p className="text-sm text-muted-foreground">Write what you want to test in plain English</p>
                            </div>
                            <div className="text-center p-6 rounded-xl border border-border bg-card">
                                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">2</div>
                                <h3 className="font-semibold text-foreground mb-2">AI Understanding</h3>
                                <p className="text-sm text-muted-foreground">Our semantic engine understands your intent</p>
                            </div>
                            <div className="text-center p-6 rounded-xl border border-border bg-card">
                                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">3</div>
                                <h3 className="font-semibold text-foreground mb-2">Template Matching</h3>
                                <p className="text-sm text-muted-foreground">Best matching API template is selected</p>
                            </div>
                            <div className="text-center p-6 rounded-xl border border-border bg-card">
                                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">4</div>
                                <h3 className="font-semibold text-foreground mb-2">Execute Test</h3>
                                <p className="text-sm text-muted-foreground">Get ready-to-run test cases instantly</p>
                            </div>
                        </div>

                        {/* Detailed Pipeline Diagram */}
                        <div className="p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/20">
                            <h3 className="text-xl font-semibold text-foreground mb-6 text-center">Detailed Processing Pipeline</h3>
                            <UserFlowDiagram />
                        </div>
                    </section>

                    {/* Benefits */}
                    <section className="mb-20">
                        <div className="grid lg:grid-cols-2 gap-12 items-center">
                            <div>
                                <h2 className="text-3xl font-bold text-foreground mb-6">Why Choose NLPForge?</h2>
                                <ul className="space-y-4">
                                    <BenefitItem text="Save hours of manual test case creation with AI-powered automation" />
                                    <BenefitItem text="Reduce errors with intelligent parameter extraction from natural language" />
                                    <BenefitItem text="Keep your data secure with local-first AI processing" />
                                    <BenefitItem text="Scale your testing with synthetic dataset generation" />
                                    <BenefitItem text="Integrate seamlessly with your existing workflow" />
                                    <BenefitItem text="Enterprise-grade security with JWT authentication and audit trails" />
                                </ul>
                            </div>
                            <div className="p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/20">
                                <div className="grid grid-cols-2 gap-6">
                                    <div className="text-center">
                                        <div className="text-4xl font-bold text-primary mb-2">10x</div>
                                        <p className="text-sm text-muted-foreground">Faster Test Creation</p>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-4xl font-bold text-primary mb-2">95%</div>
                                        <p className="text-sm text-muted-foreground">Accuracy Rate</p>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-4xl font-bold text-primary mb-2">100%</div>
                                        <p className="text-sm text-muted-foreground">Data Privacy</p>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-4xl font-bold text-primary mb-2">24/7</div>
                                        <p className="text-sm text-muted-foreground">Local Processing</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* CTA Section */}
                    <section className="text-center">
                        <div className="p-10 rounded-2xl bg-primary/5 border border-primary/20">
                            <h2 className="text-3xl font-bold text-foreground mb-4">Ready to Transform Your Testing?</h2>
                            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
                                Start generating API test cases with natural language today. 
                                No credit card required.
                            </p>
                            <Button asChild size="lg" className="h-12 px-8">
                                <Link href="/dashboard">
                                    Get Started Free
                                    <ArrowRight className="w-4 h-4 ml-2" />
                                </Link>
                            </Button>
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
