'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  FileCode,
  Database,
  Settings,
  Moon,
  Sun,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Shield
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { useState } from 'react';
import { useSidebar } from '@/contexts/sidebar-context';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Templates', href: '/templates', icon: FileCode },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Navigation() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const { isCollapsed, setIsCollapsed } = useSidebar();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <>
      {/* Top Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center justify-between h-16 px-4">
          {/* Left side - Menu toggle and logo */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:flex"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="hidden"
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>

            <Link href="/dashboard" className="flex items-center gap-2.5">
              {/* Professional Enterprise Logo */}
              <div className="h-8 w-8 rounded-md bg-primary flex items-center justify-center">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  className="h-5 w-5"
                  aria-hidden="true"
                >
                  {/* Geometric hexagon with inner precision lines */}
                  <path
                    d="M12 2L21 7V17L12 22L3 17V7L12 2Z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    fill="none"
                    className="text-primary-foreground"
                  />
                  <path
                    d="M12 6L17 9V15L12 18L7 15V9L12 6Z"
                    fill="currentColor"
                    className="text-primary-foreground"
                  />
                </svg>
              </div>
              <div className="hidden sm:flex flex-col">
                <span className="font-semibold text-base leading-tight tracking-tight">NLPForge</span>
                <span className="text-[10px] text-muted-foreground font-medium tracking-wide">API Testing</span>
              </div>
            </Link>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Desktop Sidebar - No animations */}
      <aside
        className={cn(
          "hidden lg:block fixed left-0 top-16 bottom-0 z-40 border-r bg-background",
          isCollapsed ? "w-[72px]" : "w-64"
        )}
      >
        <div className="flex flex-col h-full p-4">
          {/* Back to Home Link */}
          <Link
            href="/"
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 mb-4 rounded-lg text-sm font-medium',
              'hover:bg-accent hover:text-accent-foreground',
              'text-muted-foreground border border-border/50'
            )}
            title={isCollapsed ? 'Back to Home' : undefined}
          >
            <ArrowLeft className="h-5 w-5 flex-shrink-0" />
            {!isCollapsed && <span>Back to Home</span>}
          </Link>

          {/* Divider */}
          <div className="h-px bg-border/50 mb-4" />

          {/* Navigation Items */}
          <nav className="flex-1 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                    'hover:bg-accent hover:text-accent-foreground',
                    isActive
                      ? 'bg-primary/10 text-primary border border-primary/20'
                      : 'text-muted-foreground'
                  )}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon className={cn(
                    "h-5 w-5 flex-shrink-0",
                    isActive && "text-primary"
                  )} />
                  {!isCollapsed && <span>{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          {/* Collapse Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="mt-auto justify-center"
          >
            {!isCollapsed ? (
              <>
                <ChevronLeft className="h-4 w-4 mr-2" />
                <span>Collapse</span>
              </>
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>
      </aside>

      {/* Mobile Sidebar Overlay - hidden on mobile (bottom nav bar used instead) */}
      {mobileMenuOpen && false && (
        <>
          <div
            className="lg:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="lg:hidden fixed left-0 top-16 bottom-0 w-64 z-50 border-r bg-background shadow-xl">
            <div className="flex flex-col h-full p-4">
              {/* Back to Home Link */}
              <Link
                href="/"
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 mb-4 rounded-lg text-sm font-medium',
                  'hover:bg-accent hover:text-accent-foreground',
                  'text-muted-foreground border border-border/50'
                )}
                onClick={() => setMobileMenuOpen(false)}
              >
                <ArrowLeft className="h-5 w-5 flex-shrink-0" />
                <span>Back to Home</span>
              </Link>

              {/* Divider */}
              <div className="h-px bg-border/50 mb-4" />

              <nav className="flex-1 space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                        'hover:bg-accent hover:text-accent-foreground',
                        isActive
                          ? 'bg-primary/10 text-primary border border-primary/20'
                          : 'text-muted-foreground'
                      )}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          </aside>
        </>
      )}

      {/* Spacer for fixed sidebar (desktop) */}
      <div
        className={cn(
          "hidden lg:block flex-shrink-0",
          isCollapsed ? "w-[72px]" : "w-64"
        )}
      />
    </>
  );
}