'use client';

import React, { useState, useCallback, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X, Zap } from 'lucide-react';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * LandingNav - Enterprise-grade landing page navigation
 * 
 * Features:
 * - Sticky with backdrop blur
 * - Responsive: hamburger menu on mobile
 * - Accessible: keyboard navigation, ARIA labels, focus management
 * - Follows "Enterprise Calm" design direction
 */

const NAV_LINKS = [
  { href: '/product', label: 'Product' },
  { href: '/docs', label: 'Docs' },
  { href: '/help', label: 'Help' },
  { href: '/about', label: 'About' },
] as const;

export function LandingNav() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true); // Prevent hydration flash

  // Check if user is authenticated on mount (client-side only)
  useEffect(() => {
    try {
      // Tokens live in HttpOnly cookies (not readable from JS). Use the
      // cached, non-sensitive user profile as the signed-in UX hint -
      // real authorization is always enforced server-side.
      const user = localStorage.getItem('nlpforge_user');
      setIsAuthenticated(!!user);
    } catch {
      // localStorage not available (SSR, private browsing, etc.)
      setIsAuthenticated(false);
    } finally {
      setIsAuthLoading(false);
    }
  }, []);

  // Close mobile menu on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isMobileMenuOpen]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  const toggleMobileMenu = useCallback(() => {
    setIsMobileMenuOpen((prev) => !prev);
  }, []);

  const closeMobileMenu = useCallback(() => {
    setIsMobileMenuOpen(false);
  }, []);

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/95 backdrop-blur-sm supports-[backdrop-filter]:bg-background/80"
        role="banner"
      >
        <nav
          className="container mx-auto px-4 sm:px-6 lg:px-8"
          role="navigation"
          aria-label="Main navigation"
        >
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link
              href="/"
              className="flex items-center gap-3 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              aria-label="NLPForge home"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground font-semibold text-sm">
                <Zap className="h-5 w-5" />
              </div>
              <span className="font-bold text-xl tracking-tight text-foreground">
                NLPForge
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                >
                  {link.label}
                </Link>
              ))}
            </div>

            {/* Desktop Actions */}
            <div className="hidden md:flex items-center gap-3">
              <ThemeToggle />
              {isAuthLoading ? (
                // Neutral loading state - show Get Started only to prevent flash
                <Button asChild size="sm" className="h-9 px-4">
                  <Link href="/getting-started">Get Started</Link>
                </Button>
              ) : isAuthenticated ? (
                <Button asChild size="sm" className="h-9 px-4">
                  <Link href="/dashboard">Dashboard</Link>
                </Button>
              ) : (
                <>
                  <Link
                    href="/auth/login"
                    className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-md px-3 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  >
                    Sign In
                  </Link>
                  <Button asChild size="sm" className="h-9 px-4">
                    <Link href="/auth/register">Get Started</Link>
                  </Button>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <div className="flex md:hidden items-center gap-2">
              <ThemeToggle />
              <button
                type="button"
                onClick={toggleMobileMenu}
                className="inline-flex items-center justify-center p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                aria-expanded={isMobileMenuOpen}
                aria-controls="mobile-menu"
                aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              >
                {isMobileMenuOpen ? (
                  <X className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Menu className="h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        </nav>
      </header>

      {/* Mobile Menu Overlay */}
      <div
        className={cn(
          'fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden transition-opacity duration-200',
          isMobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        aria-hidden="true"
        onClick={closeMobileMenu}
      />

      {/* Mobile Menu Panel */}
      <div
        id="mobile-menu"
        className={cn(
          'fixed top-16 left-0 right-0 z-50 bg-background border-b border-border shadow-lg md:hidden',
          'transition-all duration-200 ease-out',
          isMobileMenuOpen ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 -translate-y-2 pointer-events-none'
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation"
      >
        <nav className="container mx-auto px-4 py-4">
          <ul className="space-y-1">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  onClick={closeMobileMenu}
                  className="block px-3 py-3 text-base font-medium text-foreground hover:bg-muted rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>

          <div className="mt-4 pt-4 border-t border-border space-y-3">
            {isAuthLoading ? (
              // Neutral loading state for mobile
              <Button asChild className="w-full h-11">
                <Link href="/getting-started" onClick={closeMobileMenu}>
                  Get Started
                </Link>
              </Button>
            ) : isAuthenticated ? (
              <Button asChild className="w-full h-11">
                <Link href="/dashboard" onClick={closeMobileMenu}>
                  Dashboard
                </Link>
              </Button>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  onClick={closeMobileMenu}
                  className="block px-3 py-3 text-base font-medium text-muted-foreground hover:text-foreground rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  Sign In
                </Link>
                <Button asChild className="w-full h-11">
                  <Link href="/auth/register" onClick={closeMobileMenu}>
                    Get Started
                  </Link>
                </Button>
              </>
            )}
          </div>
        </nav>
      </div>
    </>
  );
}

export default LandingNav;
