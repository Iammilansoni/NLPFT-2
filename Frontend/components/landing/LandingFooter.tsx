'use client'

import Link from 'next/link'
import { Brain, Github, Twitter, Linkedin, Mail } from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Separator } from '@/components/ui/separator'

const footerLinks = {
  product: [
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'API Testing', href: '/api-testing' },
    { label: 'Integrations', href: '/integrations' },
  ],
  solutions: [
    { label: 'Enterprise', href: '/enterprise' },
    { label: 'Startups', href: '/startups' },
    { label: 'Development Teams', href: '/teams' },
    { label: 'QA Automation', href: '/qa' },
  ],
  resources: [
    { label: 'Documentation', href: '/docs' },
    { label: 'API Reference', href: '/api' },
    { label: 'Guides & Tutorials', href: '/guides' },
    { label: 'Blog', href: '/blog' },
  ],
  company: [
    { label: 'About Us', href: '/about' },
    { label: 'Careers', href: '/careers' },
    { label: 'Contact', href: '/contact' },
    { label: 'Partners', href: '/partners' },
  ],
}

const socialLinks = [
  { icon: Github, href: 'https://github.com', label: 'GitHub' },
  { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
  { icon: Linkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
  { icon: Mail, href: 'mailto:hello@nlpforge.com', label: 'Email' },
]

export function LandingFooter() {
  return (
    <footer className="border-t border-border/40 bg-slate-950 dark:bg-slate-950 text-slate-100">
      <div className="container mx-auto px-6 py-16 md:py-20 max-w-7xl">
        {/* Main Footer Content */}
        <div className="grid gap-12 md:gap-8 grid-cols-1 md:grid-cols-6 lg:grid-cols-6">
          {/* Brand Section */}
          <div className="md:col-span-2 space-y-5">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                NLPForge
              </span>
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed max-w-xs">
              Transform natural language into production-ready API tests with AI-powered intelligence.
            </p>
            
            {/* Social Links */}
            <div className="flex items-center gap-3 pt-2">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="h-10 w-10 rounded-lg bg-slate-800/50 hover:bg-slate-700 border border-slate-700/50 hover:border-violet-500/50 flex items-center justify-center transition-all duration-300 hover:scale-110 hover:shadow-lg hover:shadow-violet-500/20"
                  aria-label={social.label}
                >
                  <social.icon className="h-4.5 w-4.5 text-slate-400 group-hover:text-violet-400" />
                </a>
              ))}
            </div>
          </div>

          {/* Product Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-white text-base">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Solutions Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-white text-base">Solutions</h3>
            <ul className="space-y-3">
              {footerLinks.solutions.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-white text-base">Resources</h3>
            <ul className="space-y-3">
              {footerLinks.resources.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div className="space-y-4">
            <h3 className="font-semibold text-white text-base">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Separator className="my-10 bg-slate-800/50" />

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} NLPForge. All rights reserved.
          </p>
          
          <div className="flex items-center gap-6">
            <Link 
              href="/privacy" 
              className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
            >
              Privacy Policy
            </Link>
            <Link 
              href="/terms" 
              className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
            >
              Terms of Service
            </Link>
            <Link 
              href="/cookies" 
              className="text-sm text-slate-400 hover:text-violet-400 transition-colors duration-200"
            >
              Cookie Policy
            </Link>
            <div className="flex items-center gap-2 ml-2">
              <span className="text-sm text-slate-400">Theme:</span>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
