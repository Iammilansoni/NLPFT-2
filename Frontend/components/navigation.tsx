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
  Plus,
  Moon, 
  Sun, 
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Home,
  ArrowLeft
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
      {/* Top Bar - Only logo and actions */}
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
              className="lg:hidden"
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>

            <Link href="/dashboard" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold">
                N
              </div>
              <span className="font-heading font-bold text-xl hidden sm:inline">NLPForge</span>
            </Link>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center gap-3">
            <Link href="/run/new" className="hidden sm:block">
              <Button size="sm" className="font-medium">
                <Plus className="h-4 w-4 mr-1" />
                New Run
              </Button>
            </Link>
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

      {/* Desktop Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isCollapsed ? 72 : 256,
          transition: { duration: 0.3, ease: 'easeInOut' }
        }}
        className="hidden lg:block fixed left-0 top-16 bottom-0 z-40 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      >
        <div className="flex flex-col h-full p-4">
          {/* Back to Home Link */}
          <Link
            href="/"
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 mb-4 rounded-lg text-sm font-medium transition-all duration-200',
              'hover:bg-accent hover:text-accent-foreground',
              'text-muted-foreground border border-border/50'
            )}
            title={isCollapsed ? 'Back to Home' : undefined}
          >
            <ArrowLeft className="h-5 w-5 flex-shrink-0" />
            <AnimatePresence mode="wait">
              {!isCollapsed && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                  className="whitespace-nowrap overflow-hidden"
               >
                  Back to Home
                </motion.span>
              )}
            </AnimatePresence>
          </Link>

          {/* Divider */}
          <div className="h-px bg-border/50 mb-4" />

          {/* Navigation Items */}
          <nav className="flex-1 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                    'hover:bg-accent hover:text-accent-foreground',
                    isActive 
                      ? 'bg-primary/10 text-primary border border-primary/20 shadow-sm' 
                      : 'text-muted-foreground'
                  )}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon className={cn(
                    "h-5 w-5 flex-shrink-0",
                    isActive && "text-primary"
                  )} />
                  <AnimatePresence mode="wait">
                    {!isCollapsed && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                        transition={{ duration: 0.2 }}
                        className="whitespace-nowrap overflow-hidden"
                      >
                        {item.name}
                      </motion.span>
                    )}
                  </AnimatePresence>
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
      </motion.aside>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className="lg:hidden fixed left-0 top-16 bottom-0 w-64 z-50 border-r bg-background shadow-xl"
            >
              <div className="flex flex-col h-full p-4">
                {/* Back to Home Link */}
                <Link
                  href="/"
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 mb-4 rounded-lg text-sm font-medium transition-all',
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

                <nav className="flex-1 space-y-2">
                  {navigation.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;
                    
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={cn(
                          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
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
                  })

}
                </nav>

                <div className="pt-4 border-t">
                  <Link href="/run/new" className="block mb-3">
                    <Button size="sm" className="w-full font-medium">
                      <Plus className="h-4 w-4 mr-2" />
                      New Run
                    </Button>
                  </Link>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Spacer for fixed sidebar (desktop) */}
      <div 
        className="hidden lg:block transition-all duration-300"
        style={{ 
          width: isCollapsed ? '72px' : '256px',
          flexShrink: 0 
        }}
      />
    </>
  );
}