'use client';

import { useState } from 'react';
import { LandingNav } from '@/components/landing/LandingNav';
import {
    Mail,
    MessageSquare,
    MapPin,
    Phone,
    Send,
    Github,
    ExternalLink,
    CheckCircle2
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

/**
 * Contact Page - NLPForge
 * 
 * Contact form and information page
 * following the "Enterprise Calm" design direction
 */

interface ContactInfoProps {
    icon: React.ReactNode;
    title: string;
    value: string;
    href?: string;
}

function ContactInfo({ icon, title, value, href }: ContactInfoProps) {
    const content = (
        <div className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
                {icon}
            </div>
            <div>
                <p className="text-sm text-muted-foreground mb-1">{title}</p>
                <p className="font-medium text-foreground">{value}</p>
            </div>
        </div>
    );

    if (href) {
        return (
            <a href={href} target="_blank" rel="noopener noreferrer" className="block">
                {content}
            </a>
        );
    }

    return content;
}

export default function ContactPage() {
    const [formState, setFormState] = useState({
        name: '',
        email: '',
        subject: '',
        message: ''
    });
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        setFormState(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        // Simulate form submission
        await new Promise(resolve => setTimeout(resolve, 1000));

        setIsSubmitting(false);
        setIsSubmitted(true);
        setFormState({ name: '', email: '', subject: '', message: '' });
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Navigation */}
            <LandingNav />

            {/* Hero Section */}
            <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
                        <MessageSquare className="w-4 h-4" />
                        Get In Touch
                    </div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground tracking-tight mb-6">
                        Contact <span className="text-primary">Us</span>
                    </h1>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
                        Have questions about NLPForge? We&apos;re here to help.
                        Reach out and we&apos;ll get back to you as soon as possible.
                    </p>
                </div>
            </section>

            {/* Main Content */}
            <main className="px-4 sm:px-6 lg:px-8 pb-24">
                <div className="max-w-6xl mx-auto">
                    <div className="grid lg:grid-cols-5 gap-12">

                        {/* Contact Form */}
                        <div className="lg:col-span-3">
                            <div className="p-8 rounded-2xl border border-border bg-card">
                                <h2 className="text-2xl font-bold text-foreground mb-6">Send us a message</h2>

                                {isSubmitted ? (
                                    <div className="text-center py-12">
                                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                            <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
                                        </div>
                                        <h3 className="text-xl font-semibold text-foreground mb-2">Message Sent!</h3>
                                        <p className="text-muted-foreground mb-6">
                                            Thank you for reaching out. We&apos;ll get back to you within 24 hours.
                                        </p>
                                        <Button onClick={() => setIsSubmitted(false)} variant="outline">
                                            Send Another Message
                                        </Button>
                                    </div>
                                ) : (
                                    <form onSubmit={handleSubmit} className="space-y-6">
                                        <div className="grid sm:grid-cols-2 gap-6">
                                            <div>
                                                <label htmlFor="name" className="block text-sm font-medium text-foreground mb-2">
                                                    Your Name
                                                </label>
                                                <input
                                                    type="text"
                                                    id="name"
                                                    name="name"
                                                    value={formState.name}
                                                    onChange={handleChange}
                                                    required
                                                    className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
                                                    placeholder="John Doe"
                                                />
                                            </div>
                                            <div>
                                                <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                                                    Email Address
                                                </label>
                                                <input
                                                    type="email"
                                                    id="email"
                                                    name="email"
                                                    value={formState.email}
                                                    onChange={handleChange}
                                                    required
                                                    className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
                                                    placeholder="john@example.com"
                                                />
                                            </div>
                                        </div>

                                        <div>
                                            <label htmlFor="subject" className="block text-sm font-medium text-foreground mb-2">
                                                Subject
                                            </label>
                                            <select
                                                id="subject"
                                                name="subject"
                                                value={formState.subject}
                                                onChange={handleChange}
                                                required
                                                className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
                                            >
                                                <option value="">Select a topic</option>
                                                <option value="general">General Inquiry</option>
                                                <option value="support">Technical Support</option>
                                                <option value="feature">Feature Request</option>
                                                <option value="bug">Bug Report</option>
                                                <option value="enterprise">Enterprise Licensing</option>
                                                <option value="partnership">Partnership Opportunity</option>
                                            </select>
                                        </div>

                                        <div>
                                            <label htmlFor="message" className="block text-sm font-medium text-foreground mb-2">
                                                Message
                                            </label>
                                            <textarea
                                                id="message"
                                                name="message"
                                                value={formState.message}
                                                onChange={handleChange}
                                                required
                                                rows={5}
                                                className="w-full px-4 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none"
                                                placeholder="Tell us how we can help..."
                                            />
                                        </div>

                                        <Button
                                            type="submit"
                                            size="lg"
                                            className="w-full h-12"
                                            disabled={isSubmitting}
                                        >
                                            {isSubmitting ? (
                                                'Sending...'
                                            ) : (
                                                <>
                                                    Send Message
                                                    <Send className="w-4 h-4 ml-2" />
                                                </>
                                            )}
                                        </Button>
                                    </form>
                                )}
                            </div>
                        </div>

                        {/* Contact Information */}
                        <div className="lg:col-span-2 space-y-6">
                            <div>
                                <h2 className="text-2xl font-bold text-foreground mb-6">Contact Information</h2>
                                <div className="space-y-4">
                                    <ContactInfo
                                        icon={<Mail className="w-5 h-5" />}
                                        title="Email"
                                        value="support@nlpforge.io"
                                        href="mailto:support@nlpforge.io"
                                    />
                                    <ContactInfo
                                        icon={<Github className="w-5 h-5" />}
                                        title="GitHub"
                                        value="Open Source Repository"
                                        href="https://github.com/Iammilansoni/NLPForge-Tester"
                                    />
                                    <ContactInfo
                                        icon={<MapPin className="w-5 h-5" />}
                                        title="Location"
                                        value="Remote-First Team"
                                    />
                                </div>
                            </div>

                            {/* FAQ Section */}
                            <div className="p-6 rounded-2xl bg-primary/5 border border-primary/20">
                                <h3 className="font-semibold text-foreground mb-4">Quick Links</h3>
                                <ul className="space-y-3">
                                    <li>
                                        <Link
                                            href="/about"
                                            className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                            <span>About NLPForge</span>
                                        </Link>
                                    </li>
                                    <li>
                                        <Link
                                            href="/dashboard"
                                            className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                            <span>Try the Dashboard</span>
                                        </Link>
                                    </li>
                                    <li>
                                        <a
                                            href="https://github.com/Iammilansoni/NLPForge-Tester/issues"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                            <span>Report an Issue</span>
                                        </a>
                                    </li>
                                </ul>
                            </div>

                            {/* Response Time */}
                            <div className="p-6 rounded-xl border border-border bg-card">
                                <h3 className="font-semibold text-foreground mb-2">Response Time</h3>
                                <p className="text-sm text-muted-foreground">
                                    We typically respond within 24 hours during business days.
                                    For urgent matters, please indicate so in your message subject.
                                </p>
                            </div>
                        </div>
                    </div>
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
