'use client';

import Link from 'next/link';
import { Activity, Github, Linkedin, Mail, MapPin } from 'lucide-react';
import { Separator } from '@/components/ui/separator';

export function Footer() {
  return (
    <footer className="border-t border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="absolute inset-0 corporate-gradient rounded-lg blur-md opacity-30"></div>
                  <div className="relative p-2 corporate-gradient rounded-lg">
                    <Activity className="h-6 w-6 text-white" />
                  </div>
                </div>
                <div>
                  <span className="font-bold text-lg corporate-gradient-text">NLPForge</span>
                  <div className="text-xs text-muted-foreground">Enterprise AI Platform</div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Advanced natural language processing solutions for enterprise automation. 
                Transforming business operations through AI-powered innovation.
              </p>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4 text-primary" />
                <span>Bangalore, India</span>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Platform</h3>
              <ul className="space-y-3">
                {[
                  { name: 'Dashboard', href: '/' },
                  { name: 'AI Converter', href: '/convert' },
                  { name: 'Dictionary', href: '/dictionary' },
                  { name: 'Health Monitor', href: '/health' },
                ].map((link) => (
                  <li key={link.name}>
                    <Link 
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-primary transition-colors duration-300 hover:underline"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Solutions</h3>
              <ul className="space-y-3">
                {[
                  'Text Processing',
                  'Rule Engine',
                  'Pattern Matching',
                  'Enterprise Integration',
                ].map((solution) => (
                  <li key={solution}>
                    <span className="text-sm text-muted-foreground">
                      {solution}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-foreground">Connect</h3>
              <div className="flex space-x-4">
                <a 
                  href="mailto:contact@nlpforge.com"
                  className="p-2 rounded-lg bg-muted hover:bg-primary/10 hover:text-primary transition-all duration-300 hover:scale-110"
                  aria-label="Email"
                >
                  <Mail className="h-4 w-4" />
                </a>
                <a 
                  href="#"
                  className="p-2 rounded-lg bg-muted hover:bg-primary/10 hover:text-primary transition-all duration-300 hover:scale-110"
                  aria-label="LinkedIn"
                >
                  <Linkedin className="h-4 w-4" />
                </a>
                <a 
                  href="#"
                  className="p-2 rounded-lg bg-muted hover:bg-primary/10 hover:text-primary transition-all duration-300 hover:scale-110"
                  aria-label="GitHub"
                >
                  <Github className="h-4 w-4" />
                </a>
              </div>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>Enterprise Solutions</p>
                <p>24/7 Technical Support</p>
                <p>Custom Integration Services</p>
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-6" />

        <div className="py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="text-sm text-muted-foreground">
              © 2025 NLPForge Enterprise. All rights reserved.
            </div>
            <div className="flex items-center space-x-6 text-sm">
              <Link 
                href="#" 
                className="text-muted-foreground hover:text-primary transition-colors duration-300"
              >
                Privacy Policy
              </Link>
              <Link 
                href="#" 
                className="text-muted-foreground hover:text-primary transition-colors duration-300"
              >
                Terms of Service
              </Link>
              <Link 
                href="#" 
                className="text-muted-foreground hover:text-primary transition-colors duration-300"
              >
                Enterprise License
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
