'use client'

import Link from 'next/link'
import { Github, Network } from 'lucide-react'
import { REPO_URL } from '@/lib/constants'

const LINKS = [
  { label: 'Documentation', href: '/docs' },
  { label: 'Getting started', href: '/getting-started' },
  { label: 'System status', href: '/status' },
  { label: 'About', href: '/about' },
]

export function LandingFooter() {
  return (
    <footer className="border-t border-border/40 bg-slate-950 text-slate-300">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row gap-6 md:items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 text-white font-semibold">
          <Network className="w-5 h-5 text-primary" /> NLPForge
        </Link>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-white transition-colors">
              {l.label}
            </Link>
          ))}
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:text-white transition-colors">
            <Github className="w-4 h-4" /> GitHub
          </a>
        </nav>
        <p className="text-xs text-slate-500">MIT licensed · built by Milan Soni</p>
      </div>
    </footer>
  )
}
